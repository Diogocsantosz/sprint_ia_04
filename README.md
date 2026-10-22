# EV Challenge GoodWe — Sprint 04 (RAG local)

Este projeto usa documentos locais para responder perguntas sobre recarga de veículos elétricos. Ele fica separado da Sprint 03, que foi preservada. Quando recebe uma pergunta, o programa procura trechos relevantes no índice Chroma, envia esses trechos ao modelo no Ollama e mostra as fontes junto da resposta.

Entregáveis: [relatório RAG](docs/relatorio_rag.md), [comparação de modelos](docs/relatorio_modelos.md), [relatório de evolução](docs/relatorio_evolucao.md), [avaliação e respostas brutas](evals/eval_results.json) e [interface](app/README.md).

## Requisitos

- Python 3.11 ou superior (validado nesta máquina com Python 3.14.4).
- Ollama em execução, com `nomic-embed-text` e um modelo de chat, por padrão `qwen3:8b`.
- Espaço em disco para os modelos e para o índice local.

```bash
cd sprint-ia4
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
ollama pull nomic-embed-text
ollama pull qwen3:8b
python main.py indexar
python main.py perguntar "A tarifa de ponta é real?"
python main.py conversar
streamlit run app/app.py
```

`/sair` encerra a conversa. O comando `indexar` pode ser repetido: trechos inalterados não são vetorizados novamente, e versões antigas são removidas. O banco fica em `data/chroma/` e não deve ser enviado na entrega. Para usar outro host ou modelo, defina `OLLAMA_HOST`, `MODELO_EMBEDDING` ou `MODELO_CHAT` antes de iniciar. Se mudar o modelo de embeddings, crie um índice novo com `--indice` apontando para outra pasta.

## Estrutura

| Caminho | Papel |
|---|---|
| `data/knowledge_base/` | Quatro documentos Markdown da base local |
| `src/rag/loader.py` | Lê MD/TXT com `TextLoader` e PDF com `PyMuPDFLoader`; conserva origem e página |
| `src/rag/chunking.py` | Divide documentos com `RecursiveCharacterTextSplitter` (800 caracteres, 120 de sobreposição) |
| `src/rag/embeddings.py` | Configura `OllamaEmbeddings` com `nomic-embed-text` |
| `src/rag/vector_store.py` | Abre o Chroma persistente e sincroniza trechos por ID de conteúdo |
| `src/rag/retriever.py` | Recupera até `k` trechos e formata fontes |
| `src/rag/prompt_rag.py` | Prompts v1/v2/v3, grounding e isolamento dos documentos |
| `src/rag/answer.py` | Gera resposta e valida citações de arquivo e seção |
| `src/rag/multi_provider.py` | Alterna Ollama/Groq e compara modelos e prompts |
| `main.py` | CLI de indexação e perguntas |
| `app/` | Web Streamlit com fontes e trechos visíveis |
| `evals/` | Rubrica manual reproduzível e avaliador RAGAS opcional |
| `docs/` | Relatórios e respostas do comparativo de modelos |
| `tests/` | Verifica persistência, grounding, citações e escopo sem exigir Ollama |

## Como verificar

```bash
python -m unittest discover -s tests -v
python main.py indexar
python main.py indexar  # esperado: 0 adicionados, 0 removidos
python main.py perguntar "Qual é a diferença entre Tipo 2 e CCS2?"
python main.py perguntar "A tarifa de ponta de R$ 1,10 é real?"
python main.py perguntar "Tipo 2 e CCS2 são iguais?" --prompt v2 --k 5
python -m src.rag.multi_provider "A tarifa de ponta é real?" \
  --provider ollama:qwen3:8b --provider ollama:gemma3:1b \
  --prompt v2 --prompt v3
python evals/eval_fallback.py resumir
```

Ao testar, abra os trechos citados e confira se eles realmente sustentam a resposta. O código verifica se o arquivo e a seção existem, mas não consegue garantir que o modelo interpretou cada frase corretamente. Às vezes a busca encontra um texto parecido com a pergunta sem trazer a informação necessária.

## Dados e limites

Os modelos HCA de 7, 11 e 22 kW constam na [página oficial GoodWe](https://br.goodwe.com/hca-evcharger) e no [manual oficial da série HCA](https://br.goodwe.com/Ftp/EN/Downloads/User%20Manual/GW_HCA%20Series_User%20Manual-EN.pdf). Os documentos de condomínio, as tarifas e os fluxos chamados ChargeGrid/EV ChargeOps são **simulações didáticas**. O chatbot não consulta telemetria, contas reais, contratos ou sistemas da GoodWe. Para decisões de instalação, cobrança ou aplicação de regras, consulte documentação e profissionais responsáveis.

O índice não deve misturar vetores gerados por modelos de embeddings diferentes; use outro diretório de índice ao mudar de modelo. O caminho padrão usa Ollama local e não requer credenciais de API. Groq só é ativado quando `GROQ_API_KEY` está definida no ambiente.

## Avaliação RAGAS opcional

As notas em `eval_results.json` vieram de uma revisão assistida por IA, com justificativas para cada pergunta. **Não são notas do RAGAS.** Para executar o avaliador RAGAS separadamente e gravar `evals/ragas_results.json`, use:

```bash
python -m pip install -r requirements-eval.txt
python evals/eval_ragas.py --juiz qwen3:8b
```

Nesta máquina, a instalação parou em `scikit-network`: com Python 3.14, foi necessário compilar o pacote, mas não havia compilador C++. Para tentar essa etapa opcional, use Python 3.12 ou 3.13 com pacotes prontos para as dependências. O arquivo `requirements-eval.txt` fixa RAGAS 0.3.9. A versão 0.4.3 tem [um problema de importação registrado pelos desenvolvedores](https://github.com/vibrantlabsai/ragas/issues/2745) com versões atuais do LangChain. Se o modelo usado como avaliador não devolver o formato exigido pelo RAGAS, o script apresentará o erro em vez de inventar uma nota.
