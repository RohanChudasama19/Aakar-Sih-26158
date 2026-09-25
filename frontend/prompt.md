# Frontend Extraction & System Recreation Prompt

All frontend files have been successfully extracted into the `Final_frontend` directory.

Below is the prompt you can use to generate the exact themes and layout for this system in another AI tool or for a future project.

***

### Prompt to Generate the Themes and Layout

**Role & Objective:**
You are an expert Frontend Developer specializing in React, Vite, and CSS Modules. I need you to build a complex, modern dashboard application with a robust theming engine (17 distinct themes) and a specific layout structure tailored for an aerospace/3D reconstruction platform.

**1. Theming Engine Requirements:**
Implement a CSS-variable based theming system using `data-theme` attributes. Create the following themes in an `index.css` file:
*   **Base Variables:** `--bg-primary`, `--bg-secondary`, `--bg-card`, `--bg-elevated`, `--accent-primary`, `--accent-secondary`, `--accent-premium`, `--color-success`, `--color-warning`, `--color-danger`, `--text-primary`, `--text-secondary`, `--border-color`, `--shadow-subtle`, `--glass-bg`, `--glass-border`, `--font-main: 'Inter', sans-serif`, `--radius-sm/md/lg`.
*   **Default Theme (Dark Aerospace):** Dark blue/black backgrounds (`#071014`, `#0A171C`), teal (`#19D3C5`), and blue (`#4DA3FF`) accents.
*   **Other Themes to Include:** `light`, `solarized-dark`, `high-contrast`, `glassmorphic` (with box-shadow based glass effects), `poppy`, `cartoonic` (with hard black borders and drop shadows), `turquoise`, `saffron`, `amethyst`, `emerald`, `ruby`, and their light variants (`light-turquoise`, `light-saffron`, `light-amethyst`, `light-emerald`, `light-ruby`). Ensure background, card, and text colors are carefully contrasted for each.

**2. Layout Requirements (MainLayout.jsx & MainLayout.module.css):**
*   **Container:** Full height `100vh`, flex or grid layout split between a sidebar and a main content area.
*   **Sidebar (Left):**
    *   **Logo Area:** A cube logo with text "AEROVISTA" and subtitle "SIH26158".
    *   **Navigation:** Vertical list of links using `react-router-dom` `NavLink`. Include an ID (e.g., "01"), a `lucide-react` icon (Rocket, Map, Database, Box, etc.), and a label.
    *   **System Status Widget:** Fixed at the bottom of the sidebar. Shows a list of system components (GNSS, Camera, AI Engine, GPU, Storage) with an "OK" status badge for each.
*   **Main Content (Right):**
    *   **Header:** Top bar containing the page title (e.g., "Mission Control") and description on the left. On the right, display a pulsating status dot with "Reconstruction Engine Online" and a primary button "+ New Reconstruction".
    *   **Workspace (Outlet):** A scrollable container below the header where page components are rendered.

**3. Dashboard Page Requirements (Dashboard.jsx & Dashboard.module.css):**
*   **KPI Grid (Top):** 4 summary cards. Each card must have a label, a `lucide-react` icon, a large metric value, and a small trend indicator (e.g., "+1 this week"). The 4th card ("Avg. Quality") must include a small area sparkline chart using the `recharts` library with a gradient fill based on `--accent-primary`.
*   **Video Upload Section:** A dashed-border card allowing users to select a video file and an "Upload Video" button.
*   **Active Mission Area (Below KPI):**
    *   **Mission Card (Left):** Displays mission name, status, and a large progress percentage. Below this, render a horizontal or vertical timeline pipeline of steps (e.g., "active", "completed") with dots and connecting lines. Below the timeline, show a 3-column grid of detailed metrics: Frames, Keyframes, Trajectory Length, Flight Duration, Avg. Altitude, and GNSS Confidence.
    *   **Alerts Panel (Right):** A vertical list of recent system alerts with a warning or clock icon, timestamp, and message.

**Technical Stack Constraints:**
*   React 18+, Vite, React Router DOM v6.
*   Use `lucide-react` for all icons.
*   Use `recharts` for the sparkline.
*   Use standard CSS Modules (`.module.css`) for all component styling, relying heavily on the CSS variables defined in the theming engine.
*   Ensure the application is fully responsive.
