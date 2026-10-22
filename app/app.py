"""Interface local Streamlit do chatbot RAG GoodWe."""

import os
import sys
from pathlib import Path

import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.rag.answer import responder  # noqa: E402
from src.rag.chunking import dividir_documentos  # noqa: E402
from src.rag.embeddings import criar_embeddings  # noqa: E402
from src.rag.loader import carregar_documentos  # noqa: E402
from src.rag.multi_provider import Modelo, criar_modelo  # noqa: E402
from src.rag.prompt_rag import PROMPTS  # noqa: E402
from src.rag.vector_store import abrir_base, sincronizar_base  # noqa: E402


@st.cache_resource
def obter_base(host: str, nome_embedding: str):
    return abrir_base(
        RAIZ / "data/chroma", criar_embeddings(host, nome_embedding)
    )


def exibir_resposta(item: dict) -> None:
    st.markdown(item["texto"])
    if item["fontes"]:
        st.markdown("**Fontes citadas**")
        for fonte in item["fontes"]:
            st.caption(f"• {fonte}")
    if item["trechos"]:
        with st.expander("Trechos recuperados para conferência"):
            for trecho in item["trechos"]:
                st.markdown(f"**{trecho['referencia']}** · distância {trecho['distancia']:.3f}")
                st.text(trecho["texto"])


def main() -> None:
    st.set_page_config(page_title="Volt · EV Challenge GoodWe", page_icon="⚡")
    st.title("Volt · EV Challenge GoodWe")
    st.caption("Consulta RAG local. Tarifas e regras condominiais desta base são simulações didáticas.")

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    nome_embedding = os.getenv("MODELO_EMBEDDING", "nomic-embed-text")
    with st.sidebar:
        st.header("Configuração")
        opcoes = ["ollama:qwen3:8b", "ollama:gemma3:1b"]
        if os.getenv("GROQ_API_KEY"):
            opcoes.append("groq:openai/gpt-oss-20b")
        escolha = st.selectbox("Provedor e modelo", opcoes)
        modelo_personalizado = st.text_input("Outro modelo (opcional)",
                                           placeholder="ollama:meu-modelo")
        versao = st.selectbox("Prompt", sorted(PROMPTS), index=2)
        k = st.slider("Trechos recuperados (top-k)", 1, 10, 4)
        if st.button("Atualizar índice", use_container_width=True):
            try:
                base = obter_base(host, nome_embedding)
                trechos = dividir_documentos(carregar_documentos(
                    RAIZ / "data/knowledge_base"
                ))
                novos, removidos = sincronizar_base(base, trechos)
                st.success(f"{len(trechos)} trechos; {novos} novos; {removidos} removidos.")
            except Exception as exc:
                st.error(f"Não foi possível indexar: {exc}")
        if st.button("Limpar conversa", use_container_width=True):
            st.session_state["mensagens"] = []
            st.rerun()

    if "mensagens" not in st.session_state:
        st.session_state["mensagens"] = []
    for item in st.session_state["mensagens"]:
        with st.chat_message(item["papel"]):
            if item["papel"] == "assistant":
                exibir_resposta(item)
            else:
                st.markdown(item["texto"])

    pergunta = st.chat_input("Pergunte sobre recarga, conectores ou a base GoodWe")
    if not pergunta:
        return
    st.session_state["mensagens"].append({"papel": "user", "texto": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)
    with st.chat_message("assistant"):
        try:
            base = obter_base(host, nome_embedding)
            if not base.get(limit=1, include=[])["ids"]:
                st.warning("Índice vazio. Clique em ‘Atualizar índice’ na barra lateral.")
                return
            especificacao = Modelo.interpretar(modelo_personalizado or escolha)
            with st.spinner("Buscando trechos e preparando a resposta..."):
                resposta = responder(pergunta, base, criar_modelo(especificacao),
                                    k=k, versao_prompt=versao)
            item = {
                "papel": "assistant",
                "texto": resposta.texto,
                "fontes": list(resposta.fontes),
                "trechos": [
                    {
                        "referencia": trecho.referencia,
                        "distancia": trecho.distancia,
                        "texto": trecho.documento.page_content,
                    }
                    for trecho in resposta.trechos
                ],
            }
            exibir_resposta(item)
            st.session_state["mensagens"].append(item)
        except Exception as exc:
            st.error(f"Falha ao consultar: {exc}")


if __name__ == "__main__":
    main()
