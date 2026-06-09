"""
Build a persistent RAG index from uploaded skill PDFs.

Usage:
    python scripts/ingest_pdfs.py --pdf-dir data/skills_pdfs
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.rag.embedder import Embedder
from app.rag.faiss_index import FAISSIndex
from app.rag.pdf_ingestor import ingest_pdfs
from app.services.skill_service import SkillService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest skill PDFs and build FAISS index.")
    parser.add_argument("--pdf-dir", default="data/skills_pdfs", help="Directory containing PDFs.")
    parser.add_argument("--index-dir", default="data/vector_index", help="Output index directory.")
    parser.add_argument("--chunk-size", type=int, default=800, help="Chunk size in characters.")
    parser.add_argument("--overlap", type=int, default=120, help="Chunk overlap in characters.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pdf_dir = (ROOT / args.pdf_dir).resolve()
    index_dir = (ROOT / args.index_dir).resolve()
    index_dir.mkdir(parents=True, exist_ok=True)

    skill_service = SkillService()
    known_skills = [s.get("skill", "") for s in skill_service.get_all_skills() if s.get("skill")]

    chunks = ingest_pdfs(
        pdf_dir=str(pdf_dir),
        known_skills=known_skills,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
    )
    if not chunks:
        print(f"No chunks generated. Check PDFs under: {pdf_dir}")
        return 1

    embedder = Embedder()
    vectors = embedder.embed([c["content"] for c in chunks])
    if vectors.ndim == 1:
        vectors = vectors.reshape(1, -1)

    index = FAISSIndex(dimension=vectors.shape[1], metric="l2")
    index.add(vectors, chunks, start_id=0)
    index.save(str(index_dir))

    manifest = {
        "pdf_dir": str(pdf_dir),
        "chunks": len(chunks),
        "embedding_dim": int(vectors.shape[1]),
        "index_dir": str(index_dir),
    }
    with open(index_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=True, indent=2)

    print(f"Index built successfully with {len(chunks)} chunks at {index_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
