"""Índice Chroma local com atualização idempotente dos documentos."""

import hashlib
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

COLECAO = "ev_goodwe_sprint04"


def abrir_base(pasta_indice: Path, embeddings: Embeddings) -> Chroma:
    """Cria ou reabre o índice no disco; não refaz embeddings ao reabrir."""
    pasta_indice = Path(pasta_indice)
    pasta_indice.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=COLECAO,
        embedding_function=embeddings,
        persist_directory=str(pasta_indice),
    )


def _id_trecho(trecho: Document) -> str:
    origem = str(trecho.metadata.get("source", ""))
    pagina = str(trecho.metadata.get("page", ""))
    inicio = str(trecho.metadata.get("start_index", ""))
    secao = str(trecho.metadata.get("section", ""))
    conteudo = f"{origem}\0{pagina}\0{inicio}\0{secao}\0{trecho.page_content}"
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()


def sincronizar_base(base: Chroma, trechos: list[Document]) -> tuple[int, int]:
    """Adiciona trechos novos e remove versões antigas ou arquivos excluídos.

    O conjunto de arquivos da pasta de conhecimento é a fonte de verdade.
    IDs por conteúdo evitam vetorização duplicada em execuções repetidas.
    Retorna (quantidade adicionada, quantidade removida).
    """
    if not trechos:
        raise ValueError("A indexação exige pelo menos um trecho.")
    ids_por_trecho = {_id_trecho(trecho): trecho for trecho in trechos}
    ids_atuais = set(base.get(include=[])["ids"])
    ids_desejados = set(ids_por_trecho)
    para_adicionar = sorted(ids_desejados - ids_atuais)
    para_remover = sorted(ids_atuais - ids_desejados)
    if para_adicionar:
        base.add_documents(
            [ids_por_trecho[identificador] for identificador in para_adicionar],
            ids=para_adicionar,
        )
    if para_remover:
        base.delete(ids=para_remover)
    return len(para_adicionar), len(para_remover)
