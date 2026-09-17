import pathlib

p = pathlib.Path("web/viewer.js")
c = p.read_text(encoding="utf8")
c = c.replace(
    "setLoading(${mode} failed: . Trying fallback.);", "setLoading(`${mode} failed: ${err.message}. Trying fallback…`);"
)
c = c.replace(
    "console.warn(`Representation '${mode}' failed: `);",
    "console.warn(`Representation '${mode}' failed: ${err.message}`);",
)
c = c.replace(
    "setLoading(`${mode} failed. Trying next representation…`);",
    "setLoading(`${mode} failed. Trying next representation…`);",
)
p.write_text(c, encoding="utf8")
