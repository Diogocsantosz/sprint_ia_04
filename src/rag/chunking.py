"""Divide documentos antes da vetorização, preservando metadados de origem."""

import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 800 caracteres cabem com folga no contexto de modelos locais pequenos.
# A sobreposição de 120 caracteres reduz a perda de sentido nas fronteiras
# entre trechos; mais sobreposição aumentaria o índice e repetiria resultados.
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120


def dividir_documentos(
    documentos: list[Document],
    tamanho: int = CHUNK_SIZE,
    sobreposicao: int = CHUNK_OVERLAP,
) -> list[Document]:
    """Separa por parágrafos e frases antes de cortar caracteres isolados."""
    if tamanho <= 0 or not 0 <= sobreposicao < tamanho:
        raise ValueError("Use tamanho > 0 e 0 <= sobreposição < tamanho.")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=tamanho,
        chunk_overlap=sobreposicao,
        separators=["\n\n", "\n", ". ", " ", ""],
        add_start_index=True,
    )
    trechos = splitter.split_documents(documentos)
    originais = {
        (doc.metadata.get("source"), doc.metadata.get("page")): doc.page_content
        for doc in documentos
    }
    for indice, trecho in enumerate(trechos):
        trecho.metadata["chunk_index"] = indice
        original = originais.get((trecho.metadata.get("source"), trecho.metadata.get("page")), "")
        inicio = int(trecho.metadata.get("start_index", 0))
        cabecalhos = list(re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*$", original))
        anteriores = [item for item in cabecalhos if item.start() <= inicio]
        if anteriores:
            secao = anteriores[-1].group(1)
        elif cabecalhos and cabecalhos[0].start() < inicio + len(trecho.page_content):
            secao = cabecalhos[0].group(1)
        else:
            secao = "Visão geral"
        trecho.metadata["section"] = secao
    return trechos
