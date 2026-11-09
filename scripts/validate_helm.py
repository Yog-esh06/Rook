from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
chart = ROOT / "deployment" / "helm" / "rook"
required = [chart / "Chart.yaml", chart / "values.yaml", chart / "templates" / "deployment.yaml", chart / "templates" / "service.yaml"]
missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
if missing:
    raise SystemExit("Missing Helm files: " + ", ".join(missing))
print("Helm chart structure is present. Run helm lint deployment/helm/rook when Helm is installed.")
