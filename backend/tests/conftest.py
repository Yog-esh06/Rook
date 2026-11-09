import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test-rook.db")
os.environ.setdefault("DEMO_OBSERVATION_SECONDS", "0.05")
os.environ.setdefault("DEMO_SAMPLE_COUNT", "200")
os.environ.setdefault("LOG_LEVEL", "WARNING")
