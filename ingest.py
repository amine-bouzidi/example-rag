"""Extrait les données métier de PostgreSQL et les indexe dans ChromaDB."""

from __future__ import annotations

import hashlib
import sys
from typing import Any

import psycopg
from psycopg.rows import dict_row

import config
import rag

ENTITY_QUERIES = {
    "fragrance": """
        SELECT f.fragrance_id AS source_id, f.nom, f.famille_olfactive,
               f.cible_genre, f.origine_naturelle_pct, f.positionnement,
               f.volume_min_tranche_kg, f.prix_indicatif_eur_kg,
               f.delai_proposition_jours_ouvres, f.description_courte,
               (SELECT string_agg(categorie, ', ' ORDER BY categorie)
                FROM fragrance_categories WHERE fragrance_id = f.fragrance_id) AS categories,
               (SELECT string_agg(facette, ', ' ORDER BY facette)
                FROM fragrance_facets WHERE fragrance_id = f.fragrance_id) AS facets,
               (SELECT string_agg(aroma, ', ' ORDER BY aroma)
                FROM fragrance_aromas WHERE fragrance_id = f.fragrance_id) AS aromas,
               (SELECT string_agg(certification, ', ' ORDER BY certification)
                FROM fragrance_certifications WHERE fragrance_id = f.fragrance_id) AS certifications,
               (SELECT string_agg(marche, ', ' ORDER BY marche)
                FROM fragrance_markets WHERE fragrance_id = f.fragrance_id) AS markets
        FROM fragrances f
    """,
    "trend": """
        SELECT t.tendance_id AS source_id, t.nom, t.theme, t.marche, t.croissance,
               t.indice_momentum_0_100, t.periode, t.source,
               (SELECT string_agg(famille, ', ' ORDER BY famille)
                FROM trend_families WHERE tendance_id = t.tendance_id) AS families,
               (SELECT string_agg(facette, ', ' ORDER BY facette)
                FROM trend_facets WHERE tendance_id = t.tendance_id) AS facets,
               (SELECT string_agg(aroma, ', ' ORDER BY aroma)
                FROM trend_aromas WHERE tendance_id = t.tendance_id) AS aromas,
               (SELECT string_agg(attribut, ', ' ORDER BY attribut)
                FROM trend_attributes WHERE tendance_id = t.tendance_id) AS attributes
        FROM trends t
    """,
    "market_rule": """
        SELECT r.regle_id AS source_id, r.type_regle, r.objet, r.effet,
               r.message, r.avertissement,
               (SELECT string_agg(marche, ', ' ORDER BY marche)
                FROM market_rule_markets WHERE regle_id = r.regle_id) AS markets
        FROM market_rules r
    """,
    "category_dosage": """
        SELECT categorie_produit AS source_id, categorie_produit,
               dosage_min_pct, dosage_max_pct, dosage_recommande_pct, note
        FROM category_dosages
    """,
    "brief_field": """
        SELECT champ || ':' || etape::text AS source_id, champ, etape, libelle,
               obligatoire, condition_text, field_type, valeurs_possibles, origine
        FROM brief_fields
    """,
    "need": """
        SELECT besoin || ':' || type_cible || ':' || cible AS source_id,
               besoin, type_cible, cible, poids, justification
        FROM needs_taxonomy
    """,
    "brief": """
        SELECT b.brief_id AS source_id, b.langue, b.type_brief, b.texte_libre,
               b.cible_genre, b.mode_direction, b.produit_reference,
               b.famille_olfactive, b.facette, b.volume_tranche_kg,
               b.budget_min_eur, b.budget_max_eur, b.marche_vente,
               b.positionnement, b.commentaire, b.completude,
               b.comportement_attendu, b.is_synthetic,
               (SELECT string_agg(categorie, ', ' ORDER BY categorie)
                FROM brief_categories WHERE brief_id = b.brief_id) AS categories,
               (SELECT string_agg(aroma, ', ' ORDER BY aroma)
                FROM brief_aromas WHERE brief_id = b.brief_id) AS aromas,
               (SELECT string_agg(certification, ', ' ORDER BY certification)
                FROM brief_certifications WHERE brief_id = b.brief_id) AS certifications,
               (SELECT string_agg(champ, ', ' ORDER BY champ)
                FROM brief_missing_fields WHERE brief_id = b.brief_id) AS missing_fields,
               (SELECT string_agg(fragrance_id, ', ' ORDER BY fragrance_id)
                FROM brief_expected_fragrances WHERE brief_id = b.brief_id) AS expected_fragrances
        FROM briefs b
    """,
    "evaluation": """
        SELECT e.eval_id AS source_id, e.brief_id, e.fragrance_id, f.nom AS fragrance_name,
               b.texte_libre AS brief_text, e.intensite_percue, e.tenue,
               e.fidelite_au_brief_1_5, e.commentaire, e.decision,
               e.ajustement_suggere, e.note_globale_1_5, e.is_synthetic
        FROM evaluations e
        JOIN briefs b ON b.brief_id = e.brief_id
        JOIN fragrances f ON f.fragrance_id = e.fragrance_id
    """,
    "vocabulary": """
        SELECT type || ':' || valeur AS source_id, type, valeur
        FROM vocabularies
    """,
}

FIELD_LABELS = {
    "nom": "Nom",
    "famille_olfactive": "Famille olfactive",
    "cible_genre": "Cible",
    "origine_naturelle_pct": "Origine naturelle (%)",
    "positionnement": "Positionnement",
    "volume_min_tranche_kg": "Volume minimal",
    "prix_indicatif_eur_kg": "Prix indicatif (€/kg)",
    "delai_proposition_jours_ouvres": "Délai de proposition (jours ouvrés)",
    "description_courte": "Description",
    "categories": "Catégories",
    "facets": "Facettes",
    "aromas": "Arômes",
    "certifications": "Certifications",
    "markets": "Marchés",
    "theme": "Thème",
    "marche": "Marché",
    "croissance": "Croissance",
    "indice_momentum_0_100": "Indice de momentum (0-100)",
    "periode": "Période",
    "source": "Source",
    "families": "Familles",
    "attributes": "Attributs",
    "type_regle": "Type de règle",
    "objet": "Objet",
    "effet": "Effet",
    "message": "Règle",
    "avertissement": "Avertissement",
    "categorie_produit": "Catégorie de produit",
    "dosage_min_pct": "Dosage minimal (%)",
    "dosage_max_pct": "Dosage maximal (%)",
    "dosage_recommande_pct": "Dosage recommandé (%)",
    "note": "Note",
    "champ": "Champ",
    "etape": "Étape",
    "libelle": "Libellé",
    "obligatoire": "Obligatoire",
    "condition_text": "Condition",
    "field_type": "Type de champ",
    "valeurs_possibles": "Valeurs possibles",
    "origine": "Origine",
    "besoin": "Besoin",
    "type_cible": "Type de cible",
    "cible": "Cible",
    "poids": "Poids",
    "justification": "Justification",
    "langue": "Langue",
    "type_brief": "Type de brief",
    "texte_libre": "Demande du client",
    "mode_direction": "Direction créative",
    "produit_reference": "Produit de référence",
    "facette": "Facette",
    "volume_tranche_kg": "Volume demandé",
    "budget_min_eur": "Budget minimum (€)",
    "budget_max_eur": "Budget maximum (€)",
    "marche_vente": "Marché de vente",
    "commentaire": "Commentaire",
    "completude": "Complétude",
    "comportement_attendu": "Comportement attendu",
    "missing_fields": "Informations manquantes",
    "expected_fragrances": "Parfums attendus",
    "brief_id": "Brief associé",
    "fragrance_id": "Parfum associé",
    "fragrance_name": "Nom du parfum",
    "brief_text": "Demande du client",
    "intensite_percue": "Intensité perçue",
    "tenue": "Tenue",
    "fidelite_au_brief_1_5": "Fidélité au brief (1-5)",
    "decision": "Décision",
    "ajustement_suggere": "Ajustement suggéré",
    "note_globale_1_5": "Note globale (1-5)",
    "type": "Type",
    "valeur": "Valeur",
}

EMBED_BATCH_SIZE = 32


def _format_document(row: dict[str, Any]) -> str:
    lines = []
    for field, value in row.items():
        if field == "source_id" or value is None or value == "":
            continue
        label = FIELD_LABELS.get(field, field.replace("_", " ").capitalize())
        lines.append(f"{label} : {value}")
    return "\n".join(lines)


def _make_id(entity_type: str, source_id: str, chunk_index: int) -> str:
    key = f"{entity_type}:{source_id}:{chunk_index}".encode("utf-8")
    return hashlib.sha256(key).hexdigest()


def load_records() -> list[dict[str, Any]]:
    if not config.DATABASE_URL:
        raise RuntimeError(
            "La variable DATABASE_URL n'est pas définie. Configurez-la avec "
            "l'adresse de votre base PostgreSQL locale."
        )

    records = []
    with psycopg.connect(config.DATABASE_URL, row_factory=dict_row) as connection:
        for entity_type, query in ENTITY_QUERIES.items():
            rows = connection.execute(query).fetchall()
            for row in rows:
                document = _format_document(row)
                if not document:
                    continue
                is_synthetic = bool(row.get("is_synthetic", False))
                for chunk_index, start in enumerate(range(0, len(document), config.CHUNK_SIZE)):
                    records.append({
                        "id": _make_id(entity_type, str(row["source_id"]), chunk_index),
                        "document": document[start:start + config.CHUNK_SIZE],
                        "metadata": {
                            "source_type": entity_type,
                            "source_id": str(row["source_id"]),
                            "is_synthetic": is_synthetic,
                            "chunk_index": chunk_index,
                        },
                    })
    return records


def main() -> None:
    try:
        records = load_records()
    except (psycopg.Error, RuntimeError) as exc:
        print(f"Erreur de lecture PostgreSQL : {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    if not records:
        print("Aucune donnée indexable trouvée dans PostgreSQL.", file=sys.stderr)
        raise SystemExit(1)

    print(
        f"{len(records)} documents à indexer avec '{config.EMBED_MODEL}' "
        f"(lots de {EMBED_BATCH_SIZE})...",
        flush=True,
    )
    collection = rag.get_collection()
    for start in range(0, len(records), EMBED_BATCH_SIZE):
        batch = records[start:start + EMBED_BATCH_SIZE]
        embeddings = rag.embed_documents([record["document"] for record in batch])
        collection.upsert(
            ids=[record["id"] for record in batch],
            documents=[record["document"] for record in batch],
            metadatas=[record["metadata"] for record in batch],
            embeddings=embeddings,
        )
        indexed = start + len(batch)
        print(f"Progression : {indexed}/{len(records)} documents indexés.", flush=True)

    current_ids = {record["id"] for record in records}
    existing = collection.get(include=["metadatas"])
    stale_ids = [
        record_id
        for record_id, metadata in zip(existing["ids"], existing["metadatas"])
        if metadata.get("source_type") in ENTITY_QUERIES and record_id not in current_ids
    ]
    if stale_ids:
        collection.delete(ids=stale_ids)

    print(
        f"OK : {collection.count()} documents dans la collection "
        f"'{config.COLLECTION_NAME}' ({config.CHROMA_DIR})"
    )


if __name__ == "__main__":
    main()
