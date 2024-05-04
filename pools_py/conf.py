import os
import logging
from dotenv import dotenv_values
from pathlib import Path

logging.basicConfig(
    format="%(asctime)s → %(levelname)s → %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve(strict=True).parent
env_path = os.path.join(BASE_DIR, ".env")
config = None

if os.path.exists(env_path):
    config = dotenv_values(env_path)
else:
    logger.error('create .env file')
    exit()

