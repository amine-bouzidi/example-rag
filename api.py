"""API de questions/réponses sur les données métier (RAG + Ollama).

Lancement :
    uvicorn api:app --reload
Swagger : http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import config
import rag

SYSTEM_PROMPT = """Tu es un assistant métier spécialisé en parfumerie.
Règles :
- Réponds uniquement à partir des documents fournis, sans inventer de produits, prix ou règles.
- Si les documents ne suffisent pas, indique clairement l'information manquante.
- Les données marquées comme synthétiques sont fictives et ne constituent pas une offre réelle.
- Réponds en français de façon concise et professionnelle."""

app = FastAPI(
    title="Fragrance RAG API",
    description="Pose des questions sur les briefs, parfums et données métier indexés "
                "depuis PostgreSQL dans la base vectorielle.",
    version="1.0.0",
)


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        examples=["Quels parfums floraux conviennent au marché français ?"],
    )
    top_k: int = Field(config.TOP_K, ge=1, le=20, description="Nombre de passages à retrouver")


class Source(BaseModel):
    source_type: str
    source_id: str
    is_synthetic: bool
    text: str
    score: float = Field(description="Similarité cosinus (1 = identique)")


class AskResponse(BaseModel):
    question: str
    answer: str
    model: str
    sources: list[Source]


def retrieve(question: str, top_k: int) -> list[Source]:
    collection = rag.get_collection()
    if collection.count() == 0:
        raise HTTPException(503, "La base est vide : lance d'abord `python ingest.py`.")
    result = collection.query(
        query_embeddings=[rag.embed_query(question)],
        n_results=min(top_k, collection.count()),
    )
    return [
        Source(
            source_type=meta["source_type"],
            source_id=meta["source_id"],
            is_synthetic=meta["is_synthetic"],
            text=doc,
            score=round(1 - dist, 4),
        )
        for doc, meta, dist in zip(result["documents"][0], result["metadatas"][0], result["distances"][0])
    ]


@app.get("/health", tags=["système"])
def health():
    """Vérifie que l'index vectoriel est chargé et indique les modèles utilisés."""
    return {
        "chunks": rag.get_collection().count(),
        "llm_model": config.LLM_MODEL,
        "embed_model": config.EMBED_MODEL,
    }


@app.post("/search", response_model=list[Source], tags=["données métier"])
def search(req: AskRequest):
    """Retourne seulement les documents métier pertinents (sans appeler le LLM)."""
    return retrieve(req.question, req.top_k)


@app.post("/ask", response_model=AskResponse, tags=["données métier"])
def ask(req: AskRequest):
    """Répond à une question métier à partir des documents retrouvés."""
    sources = retrieve(req.question, req.top_k)
    context = "\n\n---\n\n".join(
        f"[{s.source_type} — {s.source_id}; "
        f"{'données synthétiques' if s.is_synthetic else 'données de référence'}]\n{s.text}"
        for s in sources
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Documents métier retrouvés :\n\n{context}\n\nQuestion : {req.question}"},
    ]
    try:
        answer = rag.chat(messages)
    except Exception as exc:  # Ollama injoignable, modèle absent...
        raise HTTPException(502, f"Erreur Ollama : {exc}") from exc
    return AskResponse(question=req.question, answer=answer.strip(), model=config.LLM_MODEL, sources=sources)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
