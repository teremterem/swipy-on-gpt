import os

import openai
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = "Swipy"  # TODO oleksandr: read from getMe()

openai.api_key = os.environ["OPENAI_API_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
# read various ways of writing boolean values in configs

SWIPY_DJANGO_HOST = os.environ["SWIPY_DJANGO_HOST"]
SWIPY_DJANGO_BASE_URL = f"https://{SWIPY_DJANGO_HOST}"

DJANGO_LOG_LEVEL = os.environ.get("DJANGO_LOG_LEVEL") or "INFO"
SWIPY_LOG_LEVEL = os.environ.get("SWIPY_LOG_LEVEL") or "INFO"
DEBUG_MODE = (os.environ.get("DEBUG_MODE") or "false").lower() in ("true", "1", "yes", "y")

MOCK_GPT = (os.environ.get("MOCK_GPT") or "false").lower() in ("true", "1", "yes", "y")

# TODO oleksandr: do we need this line or what we have in django settings is enough ?
# logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
