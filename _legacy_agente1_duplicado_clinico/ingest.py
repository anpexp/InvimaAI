from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List

from retriever import EvidenceRetriever, REQUIRED_METADATA


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> Iterable[str]:
    words = text.split()
    step = max(1, chunk_size - overlap)
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + chunk_size])
        if chunk:
            yield chunk
        if start + chunk_size >= len(words):
            break


def validate_metadata(metadata: Dict[str, str]) -> Dict[str, str]:
    missing = [key for key in REQUIRED_METADATA if not str(metadata.get(key, "")).strip()]
    extra = set(metadata) - set(REQUIRED_METADATA)
    if missing:
        raise ValueError(f"Metadata faltante: {', '.join(missing)}")
    if extra:
        raise ValueError(f"Metadata no permitida: {', '.join(sorted(extra))}")
    return {key: str(metadata[key]) for key in REQUIRED_METADATA}


def load_records(path: Path) -> List[dict]:
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else payload["documents"]


def ingest(path: str, persist_directory: str = "./chroma_db") -> int:
    retriever = EvidenceRetriever(persist_directory)
    records = load_records(Path(path))
    ids: List[str] = []
    documents: List[str] = []
    metadatas: List[Dict[str, str]] = []
    for record_index, record in enumerate(records):
        metadata = validate_metadata(record["metadata"])
        for chunk_index, chunk in enumerate(chunk_text(record["text"])):
            chunk_id = f"{metadata['document_id']}-{record_index}-{chunk_index}"
            citation = (
                f"[Documento: {metadata['document_id']} | {metadata['version']} | "
                f"{metadata['rango_folios']}] {chunk}"
            )
            ids.append(chunk_id)
            documents.append(citation)
            metadatas.append(metadata)
    if ids:
        retriever.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return len(ids)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingresa evidencia CTD en ChromaDB")
    parser.add_argument("source", help="Archivo .json o .jsonl con documentos CTD")
    parser.add_argument("--persist-directory", default="./chroma_db")
    args = parser.parse_args()
    print(f"Chunks ingresados: {ingest(args.source, args.persist_directory)}")
