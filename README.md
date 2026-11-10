# Fragrance RAG API

API de recherche et de questions-réponses sur les briefs clients et les données
métier de parfumerie. PostgreSQL est la source de vérité ; ChromaDB conserve
l'index vectoriel des documents préparés à partir des tables PostgreSQL. Ollama
calcule les embeddings et génère les réponses.

## Architecture

- `ingest.py` lit les tables métier de PostgreSQL, crée des documents descriptifs,
  calcule leurs embeddings et les synchronise dans ChromaDB.
- `rag.py` partage les clients ChromaDB et Ollama, ainsi que les fonctions
  d'embedding et de génération.
- `api.py` expose `/health`, `/search` et `/ask`. Les sources retournées indiquent
  leur type, leur identifiant et si elles sont synthétiques.
- `list.py` affiche les documents indexés ; `clean.py` supprime la collection
  ChromaDB.

Les briefs, parfums, tendances, règles de marché, dosages, champs de brief,
évaluations, taxonomie des besoins et vocabulaires sont indexés. Les tables
relationnelles associées (catégories, arômes, facettes, certifications et marchés)
sont réunies dans le document de leur entité.

La recherche vectorielle sert à retrouver des informations sémantiquement
pertinentes. Pour une sélection nécessitant des filtres exacts (par exemple une
fourchette de budget, un marché ou un dosage), il faudra compléter le RAG par des
requêtes SQL structurées.

## Prérequis

- Python 3.10+
- PostgreSQL local, avec le schéma métier créé et des données chargées
- [Ollama](https://ollama.com) démarré localement

## Installation

Créer et activer un environnement virtuel sous Windows PowerShell :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Télécharger les modèles par défaut :

```powershell
ollama pull nomic-embed-text
ollama pull qwen2.5:1.5b
```

`qwen2.5:1.5b` est le modèle LLM initial ; il pourra être comparé à d'autres
modèles lors du benchmark. `nomic-embed-text` est le modèle d'embeddings et n'est
pas un LLM de génération.

## Connexion PostgreSQL et ingestion

Dans le même terminal PowerShell, définissez la chaîne de connexion en remplaçant
les valeurs par celles de votre installation. Ne commitez pas cette valeur :

```powershell
$env:DATABASE_URL = "postgresql://UTILISATEUR:MOT_DE_PASSE@localhost:5432/NOM_BASE"
python ingest.py
```

L'ingestion lit les tables du schéma décrit par le projet et indexe les
documents dans `chroma_db/`. Elle est relançable : les documents existants sont
mis à jour et les documents supprimés de PostgreSQL sont retirés de l'index.
Les embeddings sont calculés et enregistrés par lots de 32 documents, avec
affichage de la progression.
Les données dont `is_synthetic` vaut `TRUE` restent marquées comme synthétiques
et l'API les signale dans ses sources.

Pour repartir de zéro, supprimez la collection vectorielle puis relancez
l'ingestion :

```powershell
python clean.py
python ingest.py
```

## Lancer l'API

```powershell
python api.py
```

Documentation interactive : http://127.0.0.1:8000/docs

### Endpoints

| Méthode | Route     | Rôle |
|---------|-----------|------|
| GET     | `/health` | Nombre de documents indexés et modèles configurés |
| POST    | `/search` | Sources retrouvées sans génération |
| POST    | `/ask`    | Réponse du LLM avec les sources |

Exemple de requête :

```json
{"question": "Quels parfums floraux conviennent au marché français ?", "top_k": 4}
```

Chaque source retourne son `source_type`, son `source_id`, le texte indexé, un
score de similarité et l'indicateur `is_synthetic`.

## Configuration

| Variable       | Défaut                  | Rôle |
|----------------|-------------------------|------|
| `DATABASE_URL` | non défini              | Connexion PostgreSQL requise par l'ingestion |
| `LLM_MODEL`    | `qwen2.5:1.5b`          | Modèle de génération Ollama |
| `EMBED_MODEL`  | `nomic-embed-text`      | Modèle d'embeddings Ollama |
| `OLLAMA_HOST`  | `http://localhost:11434`| Adresse d'Ollama |
| `CHROMA_DIR`   | `./chroma_db`           | Dossier de l'index ChromaDB |
| `COLLECTION_NAME` | `fragrance`          | Collection ChromaDB |
| `CHUNK_SIZE`   | `800`                   | Taille maximale d'un document indexé, en caractères |
| `TOP_K`        | `4`                     | Nombre de sources retournées par défaut |

Si vous changez de modèle d'embeddings, supprimez l'ancienne collection puis
réingérez les données : les vecteurs de modèles différents ne sont pas
compatibles.
