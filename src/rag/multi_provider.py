"""Compara modelos/provedores e prompts usando os mesmos trechos RAG."""

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama

from src.rag.answer import responder_com_trechos
from src.rag.embeddings import criar_embeddings
from src.rag.prompt_rag import PROMPTS
from src.rag.retriever import recuperar
from src.rag.vector_store import abrir_base

RAIZ = Path(__file__).resolve().parents[2]
TEMPERATURE = 0.0
TOP_P = 0.9
MAX_TOKENS = 384


@dataclass(frozen=True)
class Modelo:
    provedor: str
    nome: str

    @classmethod
    def interpretar(cls, valor: str) -> "Modelo":
        if ":" not in valor:
            raise ValueError("Use PROVEDOR:MODELO, por exemplo ollama:qwen3:8b.")
        provedor, nome = valor.split(":", 1)
        if provedor not in {"ollama", "groq"} or not nome:
            raise ValueError(f"Modelo/provedor inválido: {valor}")
        return cls(provedor, nome)


def criar_modelo(modelo: Modelo) -> BaseChatModel:
    """Instancia o provedor escolhido; nenhuma chave é salva no projeto."""
    if modelo.provedor == "ollama":
        return ChatOllama(
            model=modelo.nome,
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            temperature=TEMPERATURE,
            top_p=TOP_P,
            num_predict=MAX_TOKENS,
            reasoning=False,
        )
    if modelo.provedor == "groq":
        if not os.getenv("GROQ_API_KEY"):
            raise RuntimeError("GROQ_API_KEY ausente; configure-a no ambiente.")
        try:
            from langchain_groq import ChatGroq
        except ImportError as exc:
            raise RuntimeError("Instale langchain-groq para usar Groq.") from exc
        return ChatGroq(
            model=modelo.nome,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            model_kwargs={"top_p": TOP_P},
            reasoning_format="hidden",
        )
    raise ValueError(f"Provedor não suportado: {modelo.provedor}")


def comparar(
    pergunta: str,
    base,
    modelos: list[Modelo],
    prompts: list[str],
    k: int = 4,
) -> list[dict]:
    """Recupera uma vez para manter exatamente o mesmo contexto em cada rodada."""
    if not modelos or not prompts:
        raise ValueError("Informe pelo menos um modelo e um prompt.")
    invalidos = set(prompts) - set(PROMPTS)
    if invalidos:
        raise ValueError(f"Prompts inválidos: {', '.join(sorted(invalidos))}")
    trechos = recuperar(base, pergunta, k=k)
    resultados = []
    for modelo in modelos:
        llm = criar_modelo(modelo)
        for versao in prompts:
            resposta = responder_com_trechos(pergunta, trechos, llm, versao)
            resultados.append({
                "provedor": modelo.provedor,
                "modelo": modelo.nome,
                "prompt": versao,
                "top_k": k,
                "temperature": TEMPERATURE,
                "top_p": TOP_P,
                "max_tokens": MAX_TOKENS,
                "resposta": resposta.texto,
                "fontes": list(resposta.fontes),
                "latencia_s": resposta.latencia_s,
            })
    return resultados


def main() -> None:
    parser = argparse.ArgumentParser(description="Comparação multi-provider do RAG")
    parser.add_argument("pergunta")
    parser.add_argument("--provider", action="append", dest="modelos", required=True,
                        help="Repita: ollama:qwen3:8b ou groq:MODELO")
    parser.add_argument("--prompt", action="append", dest="prompts", required=True,
                        choices=sorted(PROMPTS))
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--indice", type=Path, default=RAIZ / "data/chroma")
    parser.add_argument("--saida", type=Path, help="salva também o JSON da comparação")
    args = parser.parse_args()
    base = abrir_base(args.indice, criar_embeddings(
        os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        os.getenv("MODELO_EMBEDDING", "nomic-embed-text"),
    ))
    resultados = comparar(
        args.pergunta, base, [Modelo.interpretar(v) for v in args.modelos],
        args.prompts, args.top_k,
    )
    texto = json.dumps(resultados, ensure_ascii=False, indent=2)
    if args.saida:
        args.saida.parent.mkdir(parents=True, exist_ok=True)
        args.saida.write_text(texto + "\n", encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
