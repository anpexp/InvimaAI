"""
Memoria transversal mínima: recuperación por similitud TF-IDF sobre los
fragmentos de evidencia primaria (M3/M4/M5).

Deliberadamente NO usa ChromaDB/Pinecone para que el agente arranque en
segundos y sin dependencias pesadas ni llaves de API. Si luego el equipo
monta la base vectorial "oficial" (compartida con el resto del sistema),
esta clase se puede reemplazar sin tocar main.py — solo respeta la misma
interfaz: cargar(fragmentos) y buscar(pregunta, top_k).
"""
from dataclasses import dataclass
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from schemas import EvidenciaFragmento

# sklearn no trae stopwords en español; sin esto, palabras funcionales
# ("el", "en", "de", "la"...) infllan la similitud entre textos que no
# tienen nada que ver clínicamente y rompen el guardarraíl anti-alucinación.
STOPWORDS_ES = [
    "a", "al", "algo", "algunas", "algunos", "ante", "antes", "como", "con",
    "contra", "cual", "cuando", "de", "del", "desde", "donde", "durante",
    "e", "el", "ella", "ellas", "ellos", "en", "entre", "era", "erais",
    "eran", "eras", "eres", "es", "esa", "esas", "ese", "eso", "esos",
    "esta", "estas", "este", "esto", "estos", "fue", "fueron", "ha", "han",
    "hasta", "hay", "la", "las", "le", "les", "lo", "los", "más", "me",
    "mi", "mis", "mucho", "muchos", "muy", "no", "nos", "nosotros", "o",
    "os", "otra", "otras", "otro", "otros", "para", "pero", "poco", "por",
    "porque", "que", "quien", "se", "ser", "si", "sin", "sobre", "su",
    "sus", "también", "te", "tiene", "tienen", "todo", "todos", "tu",
    "tus", "un", "una", "uno", "unos", "y", "ya", "yo",
]


@dataclass
class ResultadoBusqueda:
    fragmento: EvidenciaFragmento
    score: float


class RAGStore:
    def __init__(self):
        self._fragmentos: List[EvidenciaFragmento] = []
        self._vectorizer = None
        self._matriz = None

    def cargar(self, fragmentos: List[EvidenciaFragmento]) -> None:
        self._fragmentos = fragmentos
        textos = [f.texto for f in fragmentos]
        if not textos:
            self._vectorizer = None
            self._matriz = None
            return
        self._vectorizer = TfidfVectorizer(stop_words=STOPWORDS_ES).fit(textos)
        self._matriz = self._vectorizer.transform(textos)

    def buscar(self, pregunta: str, top_k: int = 2) -> List[ResultadoBusqueda]:
        if not self._fragmentos or self._vectorizer is None:
            return []

        vec_pregunta = self._vectorizer.transform([pregunta])
        sims = cosine_similarity(vec_pregunta, self._matriz)[0]

        pares = sorted(
            zip(self._fragmentos, sims), key=lambda par: par[1], reverse=True
        )
        return [
            ResultadoBusqueda(fragmento=frag, score=float(score))
            for frag, score in pares[:top_k]
        ]
