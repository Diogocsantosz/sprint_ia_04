"""Resposta RAG com filtro de escopo e validação das citações produzidas."""

import re
import time
import unicodedata
from dataclasses import dataclass

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser

from src.rag.prompt_rag import RECUSA_ESCOPO, SEM_EVIDENCIA, criar_prompt
from src.rag.retriever import TrechoRecuperado, formatar_contexto, recuperar

TERMOS_ESCOPO = (
    "goodwe", "hca", "carreg", "recarga", "veiculo eletrico", "carro eletrico",
    "bateria", "conector", "tipo 2", "type 2", "ccs2", "potencia", "kw",
    "kwh", "tarifa", "ponta", "condominio", "rateio", "wallbox", "estacao",
    "energia solar", "fotovolta", "v2g", "v2h", "bidirecional", "chargegrid",
    "ev chargeops", "instalacao eletrica", "seguranca eletrica",
)
PADROES_INJECAO = (
    "ignore as instrucoes", "ignore todas as instrucoes", "ignore previous",
    "revele o prompt", "mostre o prompt de sistema", "finja ser o sistema",
)
TERMOS_OPERACIONAIS = ("status", "consumo", "faturamento", "disponibilidade")


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.casefold())
    return "".join(letra for letra in texto if not unicodedata.combining(letra))


def dentro_do_escopo(pergunta: str) -> bool:
    texto = _normalizar(pergunta)
    return bool(texto.strip()) and any(termo in texto for termo in TERMOS_ESCOPO)


@dataclass(frozen=True)
class RespostaRAG:
    texto: str
    fontes: tuple[str, ...]
    trechos: tuple[TrechoRecuperado, ...]
    latencia_s: float
    versao_prompt: str


def responder_com_trechos(
    pergunta: str,
    trechos: list[TrechoRecuperado],
    llm: BaseChatModel,
    versao_prompt: str = "v3",
) -> RespostaRAG:
    """Gera com trechos fixos, útil na comparação justa entre prompts/modelos."""
    inicio = time.perf_counter()
    prompt = criar_prompt(versao_prompt)
    if not pergunta.strip():
        raise ValueError("A pergunta não pode ser vazia.")
    normalizada = _normalizar(pergunta)
    if any(padrao in normalizada for padrao in PADROES_INJECAO):
        return RespostaRAG(RECUSA_ESCOPO, (), (), 0.0, versao_prompt)
    if not dentro_do_escopo(pergunta):
        return RespostaRAG(RECUSA_ESCOPO, (), (), 0.0, versao_prompt)
    if not trechos:
        return RespostaRAG(SEM_EVIDENCIA, (), (), 0.0, versao_prompt)

    texto = (prompt | llm | StrOutputParser()).invoke(
        {"contexto": formatar_contexto(trechos), "pergunta": pergunta}
    ).strip()
    por_numero = {str(indice): trecho.referencia
                  for indice, trecho in enumerate(trechos, start=1)}
    texto = re.sub(
        r"\[Fonte\s+(\d+)\]",
        lambda match: f"[{por_numero[match.group(1)]}]"
        if match.group(1) in por_numero else "",
        texto,
        flags=re.IGNORECASE,
    )
    referencias = set(por_numero.values())
    fontes = tuple(dict.fromkeys(
        referencia for referencia in re.findall(r"\[([^\[\]]+)\]", texto)
        if referencia in referencias
    ))
    if not fontes:
        pergunta_atual = (
            any(termo in normalizada for termo in TERMOS_OPERACIONAIS)
            and any(termo in normalizada for termo in ("atual", "agora", "tempo real"))
        )
        if pergunta_atual:
            texto = (
                f"{SEM_EVIDENCIA} Este projeto não acessa telemetria da estação; "
                "consulte o sistema operacional real para verificar consumo, "
                "status e faturamento."
            )
        elif texto not in {SEM_EVIDENCIA, RECUSA_ESCOPO}:
            # Uma frase de recusa embutida não valida fatos sem fonte.
            texto = SEM_EVIDENCIA
    return RespostaRAG(texto, fontes, tuple(trechos),
                       round(time.perf_counter() - inicio, 3), versao_prompt)


def responder(
    pergunta: str,
    base,
    llm: BaseChatModel,
    k: int = 4,
    versao_prompt: str = "v3",
) -> RespostaRAG:
    """Recupera top-k e responde; o top-k é independente da versão do prompt."""
    if not pergunta.strip():
        raise ValueError("A pergunta não pode ser vazia.")
    if not dentro_do_escopo(pergunta):
        return RespostaRAG(RECUSA_ESCOPO, (), (), 0.0, versao_prompt)
    trechos = recuperar(base, pergunta, k=k)
    return responder_com_trechos(pergunta, trechos, llm, versao_prompt)
