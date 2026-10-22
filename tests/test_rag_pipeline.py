"""Teste local da ingestão e da persistência, sem depender de Ollama."""

import tempfile
import unittest
from pathlib import Path

from langchain_core.embeddings import Embeddings

from src.rag.chunking import dividir_documentos
from src.rag.loader import carregar_documentos
from src.rag.retriever import formatar_contexto, recuperar
from src.rag.vector_store import abrir_base, sincronizar_base


class EmbeddingsDeterministicos(Embeddings):
    """Vetores simples para testar armazenamento, sem simular qualidade semântica."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(texto) for texto in texts]

    def embed_query(self, text: str) -> list[float]:
        texto = text.lower()
        return [float(texto.count(termo)) + 0.01 for termo in ("recarga", "tarifa", "condomínio")]


class TesteRagPipeline(unittest.TestCase):
    def test_reindexacao_e_reabertura(self) -> None:
        with tempfile.TemporaryDirectory() as temporario:
            raiz = Path(temporario)
            docs = raiz / "docs"
            docs.mkdir()
            (docs / "guia.md").write_text("Recarga de veículos em condomínio.", encoding="utf-8")
            (docs / "tarifa.txt").write_text("Tarifa de recarga por kWh.", encoding="utf-8")
            indice = raiz / "indice"
            embeddings = EmbeddingsDeterministicos()

            trechos = dividir_documentos(carregar_documentos(docs), tamanho=100, sobreposicao=10)
            base = abrir_base(indice, embeddings)
            self.assertEqual(sincronizar_base(base, trechos), (2, 0))
            self.assertEqual(sincronizar_base(base, trechos), (0, 0))

            reaberta = abrir_base(indice, embeddings)
            encontrados = recuperar(reaberta, "tarifa de recarga", k=2)
            self.assertEqual(len(encontrados), 2)
            self.assertIn("tarifa.txt", formatar_contexto(encontrados))

            (docs / "tarifa.txt").unlink()
            restantes = dividir_documentos(carregar_documentos(docs), tamanho=100, sobreposicao=10)
            self.assertEqual(sincronizar_base(reaberta, restantes), (0, 1))
            self.assertEqual(len(reaberta.get(include=[])["ids"]), 1)


if __name__ == "__main__":
    unittest.main()
