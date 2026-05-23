import os
from pathlib import Path


MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://starvy:UbgjoaVrG4AV3KKJ@starvy.6sncnig.mongodb.net/"
)
DB_NAME = os.getenv("MONGO_DB_NAME", "starvy")

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "DATASET"
