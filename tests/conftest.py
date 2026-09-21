"""Dépendances simulées, installées avant l'import des agents.

Les agents chargent normalement Ollama, PostgreSQL, TensorFlow et des fichiers
de modèles. Ces doublures empêchent toute dépendance externe pendant pytest.
"""

import os
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock


# Configuration minimale de test, définie avant l'import du backend.
os.environ.update({
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_NAME": "test_db",
    "DB_USER": "test_user",
    "DB_PASSWORD": "test_password",
    "JWT_SECRET_KEY": "test-secret-key",
    "JWT_ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    "CORS_ALLOWED_ORIGINS": "http://localhost:8081",
    "OLLAMA_HOST": "http://127.0.0.1:11434",
    "OLLAMA_MODEL": "llama3.1",
    "MODEL_DIR": "models",
})


fake_ollama = ModuleType("ollama")
fake_ollama.chat = MagicMock()
sys.modules["ollama"] = fake_ollama

fake_db_connection = ModuleType("db_connection")
fake_db_connection.engine = object()
sys.modules["db_connection"] = fake_db_connection

fake_joblib = ModuleType("joblib")
fake_joblib.load = MagicMock()
sys.modules["joblib"] = fake_joblib

fake_keras = SimpleNamespace(models=SimpleNamespace(load_model=MagicMock()))
fake_tensorflow = ModuleType("tensorflow")
fake_tensorflow.keras = fake_keras
sys.modules["tensorflow"] = fake_tensorflow
