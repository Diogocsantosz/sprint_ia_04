"""CLI local para indexar e consultar a base RAG da Sprint 04."""

import argparse
import os
import sys
from pathlib import Path

from src.rag.answer import responder
from src.rag.chunking import dividir_documentos
from src.rag.embeddings import criar_embeddings
from src.rag.loader import carregar_documentos
from src.rag.multi_provider import Modelo, criar_modelo
from src.rag.prompt_rag import PROMPTS
from src.rag.vector_store import abrir_base, sincronizar_base

RAIZ = Path(__file__).resolve().parent


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EV Challenge GoodWe — Sprint 04")
    parser.add_argument("--base", type=Path, default=RAIZ / "data/knowledge_base")
    parser.add_argument("--indice", type=Path, default=RAIZ / "data/chroma")
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("indexar", help="sincroniza a base de documentos com o Chroma")
    consultar = sub.add_parser("perguntar", help="faz uma pergunta à base")
    consultar.add_argument("pergunta")
    consultar.add_argument("--k", type=int, default=4)
    consultar.add_argument("--prompt", choices=sorted(PROMPTS), default="v3")
    sub.add_parser("conversar", help="abre um laço de perguntas no terminal")
    return parser.parse_args()


def mostrar_resposta(pergunta: str, base, llm, k: int = 4, prompt: str = "v3") -> None:
    resultado = responder(pergunta, base, llm, k=k, versao_prompt=prompt)
    print(f"\nVolt: {resultado.texto}")
    if resultado.fontes:
        print("\nFontes citadas:")
        for fonte in resultado.fontes:
            print(f"  - {fonte}")
    print()


def main() -> int:
    args = argumentos()
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    modelo_embedding = os.getenv("MODELO_EMBEDDING", "nomic-embed-text")
    embeddings = criar_embeddings(host, modelo_embedding)
    try:
        base = abrir_base(args.indice, embeddings)
        if args.comando == "indexar":
            docs = carregar_documentos(args.base)
            trechos = dividir_documentos(docs)
            adicionados, removidos = sincronizar_base(base, trechos)
            print(
                f"{len(docs)} documentos; {len(trechos)} trechos; "
                f"{adicionados} adicionados; {removidos} removidos."
            )
            return 0

        if not base.get(limit=1, include=[])["ids"]:
            print("Índice vazio. Execute: python main.py indexar", file=sys.stderr)
            return 2
        llm = criar_modelo(Modelo("ollama", os.getenv("MODELO_CHAT", "qwen3:8b")))
        if args.comando == "perguntar":
            mostrar_resposta(args.pergunta, base, llm, args.k, args.prompt)
            return 0

        print("Chatbot EV GoodWe. Digite /sair para encerrar.")
        while True:
            try:
                pergunta = input("Você: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            if pergunta.lower() in {"/sair", "/exit", "/quit"}:
                return 0
            if pergunta:
                mostrar_resposta(pergunta, base, llm)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
