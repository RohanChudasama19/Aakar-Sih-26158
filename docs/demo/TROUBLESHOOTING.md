# TROUBLESHOOTING

- **Heatmaps not rendering**: Check if .bin files exist in data/<jid>/work/outputs/heatmaps/.
- **Model is black**: Ensure MeshStandardMaterial is compiling correctly. Toggle original texture.
- **Backend disconnected**: Restart uvicorn. Check Redis.
- **Worker offline**: Run q worker aerorecon_tasks.
