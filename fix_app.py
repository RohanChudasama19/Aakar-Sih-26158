import re
from pathlib import Path

p = Path("web/app.js")
js = p.read_text(encoding="utf-8")

# Let's locate tab-viewer
start = js.find('<div class="tab-content" id="tab-viewer">')
end = js.find('<div class="tab-content" id="tab-map">')

new_tab_viewer = '''    <div class="tab-content" id="tab-viewer">
      <div class="viewer-selector" style="margin-bottom: 10px;">
        <select id="representation-selector"></select>
        <button id="reset-view" style="margin-left:8px;">Reset View</button>
        <button id="wireframe-btn" style="margin-left:4px;">Wireframe</button>
      </div>
      <div class="viewer" id="viewer">
        <div class="viewer-label"><br>Drag to orbit · right drag to pan · scroll to zoom</div>
      </div>
      <div class="viewer-tools" style="display: flex; gap: 5px; flex-wrap: wrap;">
        <button data-mode="orbit" class="active">Orbit</button>
        <button data-mode="distance">Distance</button>
        <button data-mode="area">Area</button>
        <button data-mode="slope">Slope</button>
        <button data-mode="angle">Angle</button>
        <button id="clear-measure" style="background-color: #552222; color: #ffaaaa; margin-left: auto;">Clear Current</button>
        <button id="clear-all-measure" style="background-color: #552222; color: #ffaaaa;">Clear All</button>
      </div>
      <div id="measure-result" style="background: rgba(0,0,0,0.5); padding: 10px; margin-top: 10px; border-radius: 4px; font-family: monospace; min-height: 40px; font-size: 13px;">
        Select a tool to begin measuring.
      </div>
      <div id="measure-history" style="margin-top: 10px; max-height: 150px; overflow-y: auto; font-size: 13px;">
      </div>
      <div class="notice" id="measure-notice"></div>
    </div>
'''

js = js[:start] + new_tab_viewer + "\n  " + js[end:]
p.write_text(js, encoding="utf-8")
