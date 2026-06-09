"""
PDF ingestion utilities for building a RAG knowledge index.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import re

from pypdf import PdfReader


@dataclass
class PDFChunk:
    """Structured chunk generated from uploaded PDF content."""

    chunk_id: str
    skill: str
    content: str
    source_pdf: str
    page_number: int
    topic: str = "pdf_material"

    def to_dict(self) -> Dict[str, str | int]:
        return {
            "chunk_id": self.chunk_id,
            "skill": self.skill,
            "content": self.content,
            "source_pdf": self.source_pdf,
            "page_number": self.page_number,
            "topic": self.topic,
        }


def _clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    if chunk_size <= 0:
        return []

    chunks: List[str] = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_len:
            break
        start = max(end - overlap, start + 1)
    return chunks


def _infer_skill_from_filename(pdf_path: Path, known_skills: List[str]) -> Optional[str]:
    name = pdf_path.stem.lower()
    
    # Check for "Skill X" pattern first since files are named "Skill 1 handout.pdf", etc.
    match = re.search(r"skill\s*(\d+)", name, re.IGNORECASE)
    if match:
        skill_idx = int(match.group(1)) - 1
        if 0 <= skill_idx < len(known_skills):
            return known_skills[skill_idx]

    for skill in known_skills:
        if skill.lower() in name:
            return skill
    for skill in known_skills:
        words = [w for w in re.split(r"[^a-zA-Z0-9]+", skill.lower()) if w]
        if words and all(word in name for word in words[:2]):
            return skill
    return None


def ingest_pdfs(
    pdf_dir: str,
    known_skills: List[str],
    chunk_size: int = 800,
    overlap: int = 120,
) -> List[Dict]:
    """
    Ingest all PDFs in a directory into chunk records suitable for RAG indexing.
    """
    base = Path(pdf_dir)
    if not base.exists():
        raise FileNotFoundError(f"PDF directory not found: {pdf_dir}")

    chunks: List[Dict] = []
    pdf_files = sorted(base.glob("*.pdf"))
    if not pdf_files:
        return chunks

    for pdf_path in pdf_files:
        skill = _infer_skill_from_filename(pdf_path, known_skills) or "General Support"
        reader = PdfReader(str(pdf_path))
        for page_idx, page in enumerate(reader.pages, start=1):
            page_text = _clean_text(page.extract_text() or "")
            if not page_text:
                continue
            for part_idx, part in enumerate(_chunk_text(page_text, chunk_size, overlap), start=1):
                raw_id = f"{pdf_path.name}:{page_idx}:{part_idx}:{part[:80]}"
                chunk_id = hashlib.sha1(raw_id.encode("utf-8")).hexdigest()
                chunk = PDFChunk(
                    chunk_id=chunk_id,
                    skill=skill,
                    content=part,
                    source_pdf=pdf_path.name,
                    page_number=page_idx,
                )
                chunks.append(chunk.to_dict())
    return chunks
