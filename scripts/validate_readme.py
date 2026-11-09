import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
readme = (ROOT / "README.md").read_text(encoding="utf-8")
assert "\u2014" not in readme, "README contains an em dash"
assert "## See Rook in Action" in readme
paths = re.findall(r"(?:\]\(|src=\")([^\)\"]+)", readme)
missing = []
for raw in paths:
    if raw.startswith(("http://", "https://", "#")):
        continue
    candidate = (ROOT / raw).resolve()
    if not candidate.exists():
        missing.append(raw)
if missing:
    raise SystemExit("Missing README assets: " + ", ".join(missing))
print(f"README paths valid: {len(paths)} local and external references checked")
