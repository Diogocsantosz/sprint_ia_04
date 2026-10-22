"""Coleta respostas e consolida uma rubrica manual de 0 a 1.

O programa nunca gera notas sozinho. O avaliador lê resposta e contextos,
preenche `rubrica` com notas e justificativa, então roda `resumir`.
"""

import argparse
import json
import os
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.rag.answer import responder_com_trechos  # noqa: E402
from src.rag.embeddings import criar_embeddings  # noqa: E402
from src.rag.multi_provider import Modelo, criar_modelo, MAX_TOKENS, TEMPERATURE, TOP_P  # noqa: E402
from src.rag.retriever import recuperar  # noqa: E402
from src.rag.vector_store import abrir_base  # noqa: E402

QUESTOES = RAIZ / "evals/questions.json"
RESULTADOS = RAIZ / "evals/eval_results.json"
NOVA_COLETA = RAIZ / "evals/nova_coleta.json"


def coletar(saida: Path, versoes: list[str], modelo: Modelo, k: int) -> dict:
    casos = json.loads(QUESTOES.read_text(encoding="utf-8"))
    base = abrir_base(
        RAIZ / "data/chroma",
        criar_embeddings(os.getenv("OLLAMA_HOST", "http://localhost:11434"),
                         os.getenv("MODELO_EMBEDDING", "nomic-embed-text")),
    )
    if not base.get(limit=1, include=[])["ids"]:
        raise RuntimeError("Índice vazio. Execute python main.py indexar.")
    llm = criar_modelo(modelo)
    dados = {
        "tipo": "rubrica_manual_fallback",
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
        "config": {
            "provedor": modelo.provedor, "modelo": modelo.nome,
            "temperature": TEMPERATURE, "top_p": TOP_P,
            "max_tokens": MAX_TOKENS, "top_k": k,
            "embedding": os.getenv("MODELO_EMBEDDING", "nomic-embed-text"),
        },
        "rubrica": {
            "faithfulness": "fração de afirmações factuais sustentadas pelos contextos recuperados; recusa correta sem fatos inventados recebe 1",
            "answer_relevancy": "grau de atendimento direto dos itens pedidos, com desconto por desvio, repetição ou omissão; ausência justificada de dado operacional conta como atendimento",
            "escala": "0 a 1; notas explícitas em revisao_manual.json, atribuídas em revisão assistida por IA e sujeitas a validação humana",
        },
        "iteracoes": [],
    }
    recuperados = {caso["id"]: recuperar(base, caso["pergunta"], k=k) for caso in casos}
    for versao in versoes:
        resultados = []
        for caso in casos:
            trechos = recuperados[caso["id"]]
            resposta = responder_com_trechos(caso["pergunta"], trechos, llm, versao)
            resultados.append({
                "caso_id": caso["id"], "pergunta": caso["pergunta"],
                "criterios": caso["criterios"], "resposta": resposta.texto,
                "fontes": list(resposta.fontes),
                "contextos": [
                    {"referencia": item.referencia, "texto": item.documento.page_content}
                    for item in trechos
                ],
                "latencia_s": resposta.latencia_s,
                "rubrica": {"faithfulness": None, "answer_relevancy": None,
                            "justificativa": ""},
            })
            print(f"{versao}: {caso['id']} concluído", flush=True)
        dados["iteracoes"].append({"id": versao, "prompt": versao,
                                   "resultados": resultados, "medias": None})
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8")
    return dados


def resumir(caminho: Path) -> dict:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    for iteracao in dados["iteracoes"]:
        for caso in iteracao["resultados"]:
            rubrica = caso["rubrica"]
            for nome in ("faithfulness", "answer_relevancy"):
                valor = rubrica.get(nome)
                if isinstance(valor, bool) or not isinstance(valor, (int, float)) \
                        or not 0 <= valor <= 1:
                    raise ValueError(f"Nota {nome} ausente/inválida em {iteracao['id']}:{caso['caso_id']}")
            if not rubrica.get("justificativa", "").strip():
                raise ValueError(f"Justificativa ausente em {iteracao['id']}:{caso['caso_id']}")
        iteracao["medias"] = {
            nome: round(statistics.mean(
                caso["rubrica"][nome] for caso in iteracao["resultados"]
            ), 3)
            for nome in ("faithfulness", "answer_relevancy")
        }
        iteracao["medias"]["media_geral"] = round(statistics.mean(
            iteracao["medias"].values()
        ), 3)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
    return dados


def aplicar_revisao(caminho: Path, revisao: Path) -> None:
    """Aplica notas escritas por um revisor e preserva as respostas coletadas."""
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    notas = json.loads(revisao.read_text(encoding="utf-8"))
    for iteracao in dados["iteracoes"]:
        for caso in iteracao["resultados"]:
            try:
                caso["rubrica"] = notas[iteracao["id"]][caso["caso_id"]]
            except KeyError as exc:
                raise ValueError(f"Revisão ausente: {iteracao['id']}:{caso['caso_id']}") from exc
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rubrica manual de fallback do RAG")
    sub = parser.add_subparsers(dest="acao", required=True)
    coleta = sub.add_parser("coletar")
    coleta.add_argument("--modelo", default="ollama:qwen3:8b")
    coleta.add_argument("--prompt", action="append", dest="prompts", required=True,
                        choices=["v1", "v2", "v3"])
    coleta.add_argument("--top-k", type=int, default=4)
    coleta.add_argument("--saida", type=Path, default=NOVA_COLETA)
    resumo = sub.add_parser("resumir")
    resumo.add_argument("--entrada", type=Path, default=RESULTADOS)
    revisao = sub.add_parser("anotar")
    revisao.add_argument("--entrada", type=Path, default=RESULTADOS)
    revisao.add_argument("--revisao", type=Path,
                         default=RAIZ / "evals/revisao_manual.json")
    args = parser.parse_args()
    if args.acao == "coletar":
        coletar(args.saida, args.prompts, Modelo.interpretar(args.modelo), args.top_k)
        print(f"Respostas salvas em {args.saida}. Revise e preencha as rubricas antes de resumir.")
    elif args.acao == "anotar":
        aplicar_revisao(args.entrada, args.revisao)
        print(f"Rubricas aplicadas a {args.entrada}. Execute 'resumir'.")
    else:
        dados = resumir(args.entrada)
        for item in dados["iteracoes"]:
            print(item["id"], item["medias"])


if __name__ == "__main__":
    main()
