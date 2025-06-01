import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DSN = os.getenv("DATABASE_URL")
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS").split(",")]
MIN_PASS_SCORE = int(os.getenv("MIN_PASS_SCORE", 60))
SUCCESS_PHOTO = os.getenv("SUCCESS_PHOTO")
FAIL_PHOTO = os.getenv("FAIL_PHOTO")
