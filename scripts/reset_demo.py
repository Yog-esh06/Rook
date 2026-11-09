from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
for path in [ROOT / "rook.db", ROOT / "test-rook.db"]:
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(f"{path}{suffix}")
        if candidate.exists():
            candidate.unlink()
            print(f"removed {candidate.relative_to(ROOT)}")
print("Demo reset complete. The API will recreate deterministic seed data on startup.")
