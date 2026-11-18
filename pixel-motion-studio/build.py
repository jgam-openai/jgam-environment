"""Bundle the editable viewer and lossless sprite PNGs into a file:// entry point."""
import base64
import json
from pathlib import Path

root = Path(__file__).resolve().parent
src = root / "src"
manifest = json.loads((root / "assets/manifest.json").read_text())
sheets = {}
for clip in manifest["clips"].values():
    path = clip["sheet"]
    data = base64.b64encode((root / "assets" / path).read_bytes()).decode()
    sheets[path] = "data:image/png;base64," + data

html = (src / "template.html").read_text()
html = html.replace("/* STYLES */", (src / "studio.css").read_text())
html = html.replace("/* VIEWER */", (src / "viewer.js").read_text())
html = html.replace("/* PROJECT */", json.dumps({"manifest": manifest, "sheets": sheets}).replace("<", "\\u003c"))
(root / "index.html").write_text(html)
