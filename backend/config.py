import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANOMALY_THRESHOLD = int(os.getenv("ANOMALY_THRESHOLD", "3"))
ANOMALY_WINDOW_SECONDS = int(os.getenv("ANOMALY_WINDOW_SECONDS", "60"))

DB_PATH = ROOT / "devops_agent.db"
SAMPLE_SERVICE_DIR = ROOT / "sample_service"
