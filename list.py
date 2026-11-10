"""Liste le contenu métier de la base vectorielle.

Usage :
    python list.py          # aperçu de chaque morceau
    python list.py --full   # texte complet de chaque morceau
"""

import argparse

import config
import rag

PREVIEW_CHARS = 120


def main() -> None:
    parser = argparse.ArgumentParser(description="Liste les documents stockés dans l'index.")
    parser.add_argument("--full", action="store_true", help="affiche le texte complet de chaque morceau")
    args = parser.parse_args()

    client = rag.get_chroma_client()
    if config.COLLECTION_NAME not in [c.name for c in client.list_collections()]:
        print(f"La collection '{config.COLLECTION_NAME}' n'existe pas : lance `python ingest.py`.")
        return

    collection = client.get_collection(config.COLLECTION_NAME)
    data = collection.get(include=["documents", "metadatas"])
    rows = sorted(
        zip(data["ids"], data["documents"], data["metadatas"]),
        key=lambda row: (
            row[2].get("source_type", ""),
            row[2].get("source_id", ""),
            row[2].get("chunk_index", 0),
        ),
    )

    print(f"Collection : {config.COLLECTION_NAME} ({config.CHROMA_DIR})")
    print(f"Modèle d'embeddings : {collection.metadata.get('embed_model', 'inconnu')}")
    print(f"Morceaux : {len(rows)}")

    current_source_type = None
    for id_, doc, meta in rows:
        if meta.get("source_type") != current_source_type:
            current_source_type = meta.get("source_type")
            print(f"\n=== {current_source_type} ===")
        if args.full:
            print(
                f"\n[{meta.get('source_id', id_)}] "
                f"({len(doc)} caractères)\n{doc}"
            )
        else:
            preview = " ".join(doc.split())
            if len(preview) > PREVIEW_CHARS:
                preview = preview[:PREVIEW_CHARS] + "..."
            print(
                f"[{meta.get('source_id', id_)}] "
                f"({len(doc)} car.) {preview}"
            )


if __name__ == "__main__":
    main()
