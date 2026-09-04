from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.api.models.Collection import Collection


COLLECTION_NAME = "invima_memoria_transversal"
REQUIRED_METADATA = (
    "document_id",
    "modulo_seccion",
    "version",
    "fecha",
    "rango_folios",
    "tipo_producto",
)


@dataclass
class Evidence:
    text: str
    metadata: Dict[str, str]
    distance: Optional[float] = None


class EvidenceRetriever:
    def __init__(self, persist_directory: str = "./chroma_db") -> None:
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection: Collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
        tipo_producto: Optional[str] = None,
        modules: tuple[str, ...] = ("Módulo 3", "Módulo 4", "Módulo 5"),
    ) -> List[Evidence]:
        where: Dict[str, Any] = {}
        if tipo_producto:
            where["tipo_producto"] = tipo_producto
        # The module constraint is applied after vector search because Chroma's
        # where syntax cannot express a portable prefix match across versions.
        result = self.collection.query(
            query_texts=[query],
            n_results=max(top_k * 3, top_k),
            where=where or None,
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        evidence: List[Evidence] = []
        for text, metadata, distance in zip(documents, metadatas, distances):
            section = str(metadata.get("modulo_seccion", ""))
            if any(section.startswith(module) for module in modules):
                evidence.append(Evidence(text=text, metadata=metadata, distance=distance))
            if len(evidence) == top_k:
                break
        return evidence

    def count(self) -> int:
        return self.collection.count()


def get_retriever() -> EvidenceRetriever:
    return EvidenceRetriever(os.getenv("CHROMA_PATH", "./chroma_db"))
