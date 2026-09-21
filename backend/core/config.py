import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / "backend" / ".env", override=False)


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(
            f"La variable d'environnement obligatoire {name} est absente. "
            "Créez backend/.env à partir de backend/.env.example pour la démo locale."
        )
    return value.strip()


DB_HOST = _required_env("DB_HOST")
DB_PORT = _required_env("DB_PORT")
DB_NAME = _required_env("DB_NAME")
DB_USER = _required_env("DB_USER")
DB_PASSWORD = _required_env("DB_PASSWORD")

SECRET_KEY = _required_env("JWT_SECRET_KEY")
ALGORITHM = _required_env("JWT_ALGORITHM")

try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(_required_env("ACCESS_TOKEN_EXPIRE_MINUTES"))
except ValueError as exc:
    raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES doit être un nombre entier.") from exc

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in _required_env("CORS_ALLOWED_ORIGINS").split(",")
    if origin.strip()
]
if not CORS_ALLOWED_ORIGINS:
    raise RuntimeError("CORS_ALLOWED_ORIGINS doit contenir au moins une origine.")

OLLAMA_HOST = _required_env("OLLAMA_HOST")
OLLAMA_MODEL = _required_env("OLLAMA_MODEL")

_model_dir = Path(_required_env("MODEL_DIR"))
MODEL_DIR = _model_dir if _model_dir.is_absolute() else (PROJECT_ROOT / _model_dir)
