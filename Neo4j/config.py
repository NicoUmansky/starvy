import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "DATASET"


def cargar_env_local():
    """
    Carga variables desde .env sin depender de librerias externas.
    Primero lee .env del proyecto y despues Neo4j/.env si existen.
    """
    for env_path in (BASE_DIR / ".env", Path(__file__).resolve().parent / ".env"):
        if not env_path.exists():
            continue

        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


cargar_env_local()


# Instancia Aura StarvyNeo.
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://b7da37c0.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME", "b7da37c0")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "b7da37c0")
NEO4J_CONNECTION_TIMEOUT = float(os.getenv("NEO4J_CONNECTION_TIMEOUT", "10"))
AURA_INSTANCEID = os.getenv("AURA_INSTANCEID", "b7da37c0")
AURA_INSTANCENAME = os.getenv("AURA_INSTANCENAME", "StarvyNeo")
