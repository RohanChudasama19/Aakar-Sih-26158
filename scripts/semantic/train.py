import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms.functional as TF
import torchvision.transforms as transforms
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision.models.segmentation import LRASPP_MobileNet_V3_Large_Weights, lraspp_mobilenet_v3_large
from torchvision.models.segmentation.lraspp import LRASPPHead

COLOR_MAP = {
    (0, 0, 0): 0,
    (128, 0, 0): 1,
    (128, 64, 128): 2,
    (0, 128, 0): 3,
    (128, 128, 0): 4,
    (64, 0, 128): 5,
    (192, 0, 192): 6,
    (64, 64, 0): 7,
}

CLASS_NAMES = ["Clutter", "Building", "Road", "Tree", "Low Vegetation", "Moving Car", "Static Car", "Human"]


def rgb_to_mask(img_np):
    mask = np.zeros(img_np.shape[:2], dtype=np.int64)
    known = np.zeros(img_np.shape[:2], dtype=bool)

    for color, cls_id in COLOR_MAP.items():
        match = (img_np == color).all(axis=-1)
        mask[match] = cls_id
        known |= match

    unknown_pixels = ~known
    if unknown_pixels.any():
        unique_unknown = np.unique(img_np[unknown_pixels], axis=0)
        raise ValueError(f"Unknown colors found in mask: {unique_unknown}")

    return torch.from_numpy(mask)


class UAVidDataset(Dataset):
    def __init__(self, root, split="train", crop_size=(512, 512), augment=False):
        self.root = Path(root) / split
        self.crop_size = crop_size
        self.augment = augment

        self.images = []
        self.masks = []

        if self.root.exists():
            for seq in self.root.iterdir():
                if seq.is_dir():
                    img_dir = seq / "Images"
                    mask_dir = seq / "Labels"

                    if img_dir.exists() and mask_dir.exists():
                        for img_path in sorted(img_dir.glob("*.png")):
                            mask_path = mask_dir / img_path.name
                            if mask_path.exists():
                                self.images.append(img_path)
                                self.masks.append(mask_path)

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_path = self.images[idx]
        mask_path = self.masks[idx]

        # Load as PIL
        img = Image.open(img_path).convert("RGB")
        mask = Image.open(mask_path).convert("RGB")

        # Geometric transforms
        if self.augment:
            if random.random() > 0.5:
                img = TF.hflip(img)
                mask = TF.hflip(mask)

            # Random Crop
            i, j, h, w = torch.distributions.uniform.Uniform(0, 1).sample((4,))
            # We just do random crop natively
            i, j, h, w = transforms.RandomCrop.get_params(img, output_size=self.crop_size)
            img = TF.crop(img, i, j, h, w)
            mask = TF.crop(mask, i, j, h, w)

            # Color Jitter only on image
            img = TF.adjust_brightness(img, random.uniform(0.8, 1.2))
            img = TF.adjust_contrast(img, random.uniform(0.8, 1.2))
        else:
            # Deterministic center crop for validation
            img = TF.center_crop(img, self.crop_size)
            mask = TF.center_crop(mask, self.crop_size)

        # To Tensor
        img_t = TF.to_tensor(img)
        img_t = TF.normalize(img_t, mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])

        # Convert Mask
        mask_np = np.array(mask)
        mask_t = rgb_to_mask(mask_np)

        return img_t, mask_t


def build_model(num_classes=8):
    weights = LRASPP_MobileNet_V3_Large_Weights.COCO_WITH_VOC_LABELS_V1
    model = lraspp_mobilenet_v3_large(weights=weights)

    # Replace classifier head for 8 classes
    model.classifier.low_classifier = nn.Conv2d(40, num_classes, 1)
    model.classifier.high_classifier = nn.Conv2d(128, num_classes, 1)

    return model, weights


def compute_iou(conf_matrix):
    intersection = np.diag(conf_matrix)
    union = np.sum(conf_matrix, axis=1) + np.sum(conf_matrix, axis=0) - intersection
    iou = np.divide(intersection, union, out=np.zeros_like(intersection, dtype=float), where=union != 0)

    # precision and recall
    precision = np.divide(
        intersection,
        np.sum(conf_matrix, axis=0),
        out=np.zeros_like(intersection, dtype=float),
        where=np.sum(conf_matrix, axis=0) != 0,
    )
    recall = np.divide(
        intersection,
        np.sum(conf_matrix, axis=1),
        out=np.zeros_like(intersection, dtype=float),
        where=np.sum(conf_matrix, axis=1) != 0,
    )

    f1 = 2 * (precision * recall) / (precision + recall + 1e-8)

    return iou, precision, recall, f1


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def main():
    parser = argparse.ArgumentParser(description="Train UAVid Semantic Segmentation Model")
    parser.add_argument("--data_dir", type=str, default="data_external/uavid/converted")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--batch_size", type=int, default=2)
    parser.add_argument("--grad_accum", type=int, default=8)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--crop_size", type=int, default=512)
    parser.add_argument("--smoke_test", action="store_true")
    parser.add_argument("--mini_overfit", action="store_true")
    args = parser.parse_args()

    set_seed(args.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    crop = (args.crop_size, args.crop_size)
    train_dataset = UAVidDataset(args.data_dir, split="train", crop_size=crop, augment=True)
    val_dataset = UAVidDataset(args.data_dir, split="val", crop_size=crop, augment=False)

    if args.smoke_test:
        train_dataset.images = train_dataset.images[:4]
        train_dataset.masks = train_dataset.masks[:4]
        val_dataset.images = val_dataset.images[:2]
        val_dataset.masks = val_dataset.masks[:2]
        args.epochs = 2
        print("--- SMOKE TEST MODE ---")

    if args.mini_overfit:
        train_dataset.images = train_dataset.images[:4]
        train_dataset.masks = train_dataset.masks[:4]
        val_dataset = train_dataset
        args.epochs = 20
        print("--- MINI OVERFIT MODE ---")

    train_loader = DataLoader(
        train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=args.workers, drop_last=False
    )
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=args.workers)

    model, weights_info = build_model(num_classes=8)
    model = model.to(device)

    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()

    scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")

    best_miou = 0.0
    history = []

    for epoch in range(args.epochs):
        model.train()
        train_loss = 0.0
        optimizer.zero_grad()

        t0 = time.time()
        for i, (images, targets) in enumerate(train_loader):
            images, targets = images.to(device), targets.to(device)

            with torch.amp.autocast("cuda", enabled=device.type == "cuda"):
                outputs = model(images)["out"]
                loss = criterion(outputs, targets)
                loss = loss / args.grad_accum

            scaler.scale(loss).backward()

            if (i + 1) % args.grad_accum == 0 or (i + 1) == len(train_loader):
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()

            train_loss += loss.item() * args.grad_accum

        train_loss /= len(train_loader)

        # Validation
        model.eval()
        val_loss = 0.0
        conf_matrix = np.zeros((8, 8), dtype=np.int64)

        with torch.no_grad():
            for images, targets in val_loader:
                images, targets = images.to(device), targets.to(device)
                outputs = model(images)["out"]
                loss = criterion(outputs, targets)
                val_loss += loss.item()

                preds = torch.argmax(outputs, dim=1).cpu().numpy()
                targs = targets.cpu().numpy()

                # Accumulate confusion matrix
                for p, t in zip(preds, targs):
                    conf_matrix += np.bincount(8 * t.flatten() + p.flatten(), minlength=64).reshape(8, 8)

        val_loss /= max(1, len(val_loader))
        iou, precision, recall, f1 = compute_iou(conf_matrix)
        miou = np.mean(iou)

        runtime = time.time() - t0
        peak_vram = torch.cuda.max_memory_allocated() / (1024**2) if device.type == "cuda" else 0

        history.append(
            {"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss, "miou": miou, "peak_vram_mb": peak_vram}
        )

        print(
            f"Epoch {epoch + 1}/{args.epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | mIoU: {miou:.4f} | VRAM: {peak_vram:.0f} MB"
        )

        if miou > best_miou:
            best_miou = miou
            if not args.smoke_test and not args.mini_overfit:
                torch.save(
                    {
                        "epoch": epoch,
                        "model_state": model.state_dict(),
                        "optimizer_state": optimizer.state_dict(),
                        "miou": miou,
                    },
                    "best_model.pth",
                )

    with open("training_log.json", "w") as f:
        json.dump(history, f, indent=2)


if __name__ == "__main__":
    main()
