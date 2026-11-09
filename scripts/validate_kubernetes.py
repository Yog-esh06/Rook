from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
paths = sorted((ROOT / "deployment" / "kubernetes").glob("*.yaml"))
if not paths:
    raise SystemExit("No Kubernetes manifests found")
for path in paths:
    documents = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
    if not documents or any(not document.get("apiVersion") or not document.get("kind") for document in documents if document):
        raise SystemExit(f"Invalid Kubernetes document: {path}")
print(f"Validated {len(paths)} Kubernetes manifest files")
