"""Configuration partagée par les scripts (surcharge possible via variables d'environnement)."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Ollama
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:1.5b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

# PostgreSQL (la chaîne de connexion est fournie localement)
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Base vectorielle (ChromaDB persistante sur disque)
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", BASE_DIR / "chroma_db"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "fragrance")

# Découpage des documents indexés
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))  # en caractères

# Recherche
TOP_K = int(os.getenv("TOP_K", "4"))
