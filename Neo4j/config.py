import os
from pathlib import Path


NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "contraseñatpo"

# Si usan Neo4j Desktop con una base llamada starvy, cambiar a "starvy"
# o definir la variable de entorno NEO4J_DATABASE.
NEO4J_DATABASE = "starvy"

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "DATASET"
