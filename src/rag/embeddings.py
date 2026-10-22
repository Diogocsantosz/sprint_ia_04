"""Embeddings locais via Ollama; o mesmo modelo deve indexar e consultar."""

from langchain_ollama import OllamaEmbeddings

MODELO_EMBEDDING = "nomic-embed-text"


def criar_embeddings(
    host: str = "http://localhost:11434",
    modelo: str = MODELO_EMBEDDING,
) -> OllamaEmbeddings:
    """Configura o modelo de vetores sem solicitar rede no construtor."""
    return OllamaEmbeddings(model=modelo, base_url=host)
