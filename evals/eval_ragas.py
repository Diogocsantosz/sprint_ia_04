"""Faithfulness e Answer Relevancy oficiais do RAGAS (execução opcional).

Usa a API compatível com OpenAI do Ollama local como juiz e embeddings.
Os resultados ficam em arquivo separado da rubrica manual; falhas do juiz
não são convertidas silenciosamente em notas fictícias.
"""

import argparse
import asyncio
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


async def avaliar(entrada: Path, saida: Path, modelo_juiz: str) -> None:
    try:
        from openai import AsyncOpenAI
        from ragas.embeddings.base import embedding_factory
        from ragas.llms import llm_factory
        from ragas.metrics.collections import AnswerRelevancy, Faithfulness
    except ImportError as exc:
        raise RuntimeError(
            "RAGAS não instalado. Execute: pip install -r requirements-eval.txt"
        ) from exc

    dados = json.loads(entrada.read_text(encoding="utf-8"))
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    cliente = AsyncOpenAI(base_url=f"{host}/v1", api_key="ollama")
    juiz = llm_factory(modelo_juiz, client=cliente)
    embeddings = embedding_factory(
        "openai", model=os.getenv("MODELO_EMBEDDING", "nomic-embed-text"),
        client=cliente, interface="modern",
    )
    fidelidade = Faithfulness(llm=juiz)
    relevancia = AnswerRelevancy(llm=juiz, embeddings=embeddings)
    saida_dados = {
        "tipo": "ragas", "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
        "juiz": modelo_juiz, "entrada": str(entrada), "iteracoes": [],
    }
    for iteracao in dados["iteracoes"]:
        resultados = []
        for caso in iteracao["resultados"]:
            contexto = [item["texto"] for item in caso["contextos"]]
            faith = await fidelidade.ascore(
                user_input=caso["pergunta"], response=caso["resposta"],
                retrieved_contexts=contexto,
            )
            relev = await relevancia.ascore(
                user_input=caso["pergunta"], response=caso["resposta"],
            )
            if not math.isfinite(float(faith.value)) or not math.isfinite(float(relev.value)):
                raise RuntimeError(
                    f"RAGAS devolveu nota inválida em {iteracao['id']}:{caso['caso_id']}"
                )
            resultados.append({
                "caso_id": caso["caso_id"],
                "faithfulness": float(faith.value),
                "answer_relevancy": float(relev.value),
            })
            print(f"RAGAS {iteracao['id']}:{caso['caso_id']} concluído", flush=True)
        saida_dados["iteracoes"].append({"id": iteracao["id"],
                                        "resultados": resultados})
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(saida_dados, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8")
    print(f"Resultados RAGAS: {saida}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Métricas RAGAS da Sprint 04")
    parser.add_argument("--entrada", type=Path, default=RAIZ / "evals/eval_results.json")
    parser.add_argument("--saida", type=Path, default=RAIZ / "evals/ragas_results.json")
    parser.add_argument("--juiz", default="qwen3:8b")
    args = parser.parse_args()
    try:
        asyncio.run(avaliar(args.entrada, args.saida, args.juiz))
    except (ImportError, RuntimeError) as exc:
        print(f"RAGAS indisponível: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
