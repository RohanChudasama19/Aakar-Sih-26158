from pathlib import Path

p = Path("web/app.js")
js = p.read_text(encoding="utf-8")

# 1. Add surface_area button
btn_old = '''        <button data-mode="area">Area</button>
        <button data-mode="slope">Slope</button>'''

btn_new = '''        <button data-mode="area">Planar Area</button>
        <button data-mode="surface_area">Surface Area</button>
        <button data-mode="slope">Slope</button>'''

js = js.replace(btn_old, btn_new)

# 2. Update handleMeasureUpdate for surface_area
handle_old = '''} else if (mode === 'area') {'''

handle_new = '''} else if (mode === 'surface_area') {
              if (points.length >= 1) {
                  const sa = Meas.surfaceArea3D(points);
                  resultHtml += <strong>Surface Area:  </strong> ( triangles);
                  summary = Surface  ;
              } else {
                  resultHtml += Click or drag to select mesh triangles.;
              }
              
              if (!['Mesh', 'Textured', 'Semantic', 'Confidence'].includes(window.getCurrentViewerType())) {
                   resultHtml += <br><span style="color:#ffaa00;">Surface area requires a mesh representation. Points clouds are not supported.</span>;
              }
          } else if (mode === 'area') {'''

js = js.replace(handle_old, handle_new)

# 3. Update right-click logic
right_old = '''if (mode === 'distance' || mode === 'area') {'''
right_new = '''if (mode === 'distance' || mode === 'area' || mode === 'surface_area') {'''
js = js.replace(right_old, right_new)

summary_old = '''else if (html.includes("Planar Area:")) summary = html.split("Planar Area:")[1].split("</strong>")[0].replace(/<[^>]+>/g, '').trim();'''
summary_new = '''else if (html.includes("Planar Area:")) summary = html.split("Planar Area:")[1].split("</strong>")[0].replace(/<[^>]+>/g, '').trim();
                 else if (html.includes("Surface Area:")) summary = html.split("Surface Area:")[1].split("</strong>")[0].replace(/<[^>]+>/g, '').trim();'''
js = js.replace(summary_old, summary_new)

p.write_text(js, encoding="utf-8")
