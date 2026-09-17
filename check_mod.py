from pathlib import Path

p = Path("web/app.js")
js = p.read_text(encoding="utf-8")

# Let's import measurements.js logic inside app.js
# Or better, we can inject the module import and then the logic.
# Wait, app.js is a module? No, in index.html, <script type="module" src="/app.js"></script> ?
# Let's check index.html.
