"""Busca semântica na base local e montagem de contexto com referências."""

import re
from dataclasses import dataclass

from langchain_chroma import Chroma
from langchain_core.documents import Document


@dataclass(frozen=True)
class TrechoRecuperado:
    documento: Document
    distancia: float

    @property
    def referencia(self) -> str:
        origem = str(self.documento.metadata.get("source", "fonte desconhecida"))
        secao = str(self.documento.metadata.get("section", "Visão geral"))
        pagina = self.documento.metadata.get("page")
        referencia = f"{origem} · {secao}"
        return f"{referencia}, p. {pagina}" if pagina else referencia


def recuperar(
    base: Chroma,
    pergunta: str,
    k: int = 4,
    distancia_maxima: float | None = None,
) -> list[TrechoRecuperado]:
    """Retorna até k trechos e a distância informada pelo Chroma.

    Distância menor significa maior proximidade. Ela não é probabilidade
    de a resposta estar correta; a aplicação ainda precisa verificar se o
    contexto contém evidência suficiente para a pergunta.
    """
    if not pergunta.strip():
        raise ValueError("A pergunta não pode ser vazia.")
    if not 1 <= k <= 10:
        raise ValueError("k deve estar entre 1 e 10.")
    if distancia_maxima is not None and distancia_maxima < 0:
        raise ValueError("A distância máxima não pode ser negativa.")
    resultados = [
        TrechoRecuperado(documento=doc, distancia=float(distancia))
        for doc, distancia in base.similarity_search_with_score(pergunta, k=k)
    ]
    if distancia_maxima is not None:
        resultados = [item for item in resultados if item.distancia <= distancia_maxima]
    return resultados


def formatar_contexto(trechos: list[TrechoRecuperado]) -> str:
    """Delimita fontes e neutraliza linhas com comandos típicos de injection.

    O filtro é uma defesa adicional; o prompt ainda determina que todo o
    conteúdo recuperado seja tratado apenas como dado, nunca como instrução.
    """
    padrao = re.compile(
        r"(?i)^\s*(?:system|developer|assistant)\s*:|"
        r"(?i:ignore\s+(?:as|todas\s+as|previous)\s+instru)|"
        r"(?i:mostre\s+o\s+prompt|revele\s+o\s+prompt)"
    )

    def texto_seguro(texto: str) -> str:
        return "\n".join(
            "[linha de instrução ignorada]" if padrao.search(linha) else linha
            for linha in texto.splitlines()
        )

    return "\n\n".join(
        f"[Fonte {indice}: {trecho.referencia}]\n"
        f"{texto_seguro(trecho.documento.page_content)}"
        for indice, trecho in enumerate(trechos, start=1)
    )
