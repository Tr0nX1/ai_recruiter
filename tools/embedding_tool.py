"""Semantic similarity between skill lists (sentence-transformers)."""

from __future__ import annotations

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from sklearn.metrics.pairwise import cosine_similarity

from config import EMBEDDING_MODEL


class EmbeddingInput(BaseModel):
    candidate_skills: list[str] = Field(description="Skills from the resume")
    jd_skills: list[str] = Field(description="Required or preferred skills from the JD")


_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


class SentenceEmbeddingTool(BaseTool):
    name: str = "SentenceEmbeddingTool"
    description: str = (
        "Computes semantic similarity between candidate skills and JD skills; "
        "returns a score from 0–100 (cosine similarity scaled)."
    )
    args_schema: type[BaseModel] = EmbeddingInput

    def _run(self, candidate_skills: list[str], jd_skills: list[str]) -> Any:
        if not candidate_skills or not jd_skills:
            return 0.0
        try:
            model = _get_model()
            c = ", ".join(candidate_skills)
            j = ", ".join(jd_skills)
            embeddings = model.encode([c, j])
            sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return round(float(max(0.0, min(1.0, sim))) * 100, 2)
        except Exception:  # noqa: BLE001
            return 50.0
