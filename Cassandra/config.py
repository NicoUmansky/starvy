from pathlib import Path


CASSANDRA_HOST = "127.0.0.1"
CASSANDRA_PORT = 9042
KEYSPACE = "starvy"

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "DATASET"