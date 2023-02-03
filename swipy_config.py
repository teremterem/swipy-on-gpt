import os

import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.environ["OPENAI_API_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ALLOWED_USERS = os.environ["ALLOWED_USERS"].split(",")
# read various ways of writing boolean values in configs
MOCK_GPT = (os.environ.get("MOCK_GPT") or "false").lower() in ("true", "1", "yes", "y")

SWIPY_DJANGO_HOST = os.environ["SWIPY_DJANGO_HOST"]
SWIPY_DJANGO_BASE_URL = f"https://{SWIPY_DJANGO_HOST}"

# TODO oleksandr: do we need this line or what we have in django settings is enough ?
# logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
