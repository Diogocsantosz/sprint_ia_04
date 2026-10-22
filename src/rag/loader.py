"""Lê documentos locais e guarda a origem necessária para citar respostas."""

from pathlib import Path

from langchain_community.document_loaders import PyMuPDFLoader, TextLoader
from langchain_core.documents import Document

EXTENSOES = {".md", ".txt", ".pdf"}


def carregar_documentos(pasta: Path) -> list[Document]:
    """Lê Markdown, TXT e PDF; a origem é relativa à pasta informada."""
    pasta = Path(pasta).resolve()
    if not pasta.is_dir():
        raise FileNotFoundError(f"Pasta da base não encontrada: {pasta}")

    arquivos = sorted(
        caminho for caminho in pasta.rglob("*")
        if caminho.is_file() and caminho.suffix.lower() in EXTENSOES
    )
    if not arquivos:
        raise ValueError(f"A base não contém .md, .txt ou .pdf: {pasta}")

    documentos: list[Document] = []
    for caminho in arquivos:
        loader = (
            PyMuPDFLoader(str(caminho))
            if caminho.suffix.lower() == ".pdf"
            else TextLoader(str(caminho), encoding="utf-8")
        )
        for documento in loader.load():
            if not documento.page_content.strip():
                continue
            # Caminho relativo é estável entre máquinas e não expõe diretórios locais.
            documento.metadata["source"] = caminho.relative_to(pasta).as_posix()
            documento.metadata["title"] = caminho.stem
            if "page" in documento.metadata:
                documento.metadata["page"] = int(documento.metadata["page"]) + 1
            documentos.append(documento)

    if not documentos:
        raise ValueError("Os arquivos da base estão vazios ou não têm texto extraível.")
    return documentos
