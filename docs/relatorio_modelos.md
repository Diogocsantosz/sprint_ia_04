# Relatório de modelos e parâmetros — Sprint 04

**Teste local feito em 20/10/2026.** A pergunta “No exemplo, a tarifa de ponta é real?” foi usada para ver como dois modelos Ollama respondiam com os prompts v2 e v3. O script `src/rag/multi_provider.py` buscou os quatro trechos uma vez e passou os mesmos textos para todas as combinações. As respostas e os tempos estão em `docs/multi_provider_results.json`. Uma única pergunta mostra se a troca funciona, mas não permite classificar os modelos de forma geral.

| Provedor | Modelo | Prompt | Resposta com citação válida? | Latência observada |
|---|---|---|---|---:|
| Ollama | `qwen3:8b` | v2 | Sim; tarifa fictícia | 1,186 s |
| Ollama | `qwen3:8b` | v3 | Sim; tarifa fictícia | 1,065 s |
| Ollama | `gemma3:1b` | v2 | Não; fallback por falta de citação válida | 4,577 s |
| Ollama | `gemma3:1b` | v3 | Não; fallback por falta de citação válida | 0,435 s |

Os tempos variam conforme o modelo já esteja carregado e conforme o uso da máquina. Isso ajuda a explicar por que a primeira chamada ao `gemma3:1b` demorou mais que a segunda. `qwen3:8b` ficou como padrão porque citou a tabela corretamente nas duas tentativas. O Gemma não colocou uma citação válida, e o programa preferiu mostrar a mensagem de falta de evidência. Isso não prova que o conteúdo bruto da resposta do Gemma estava errado.

## Parâmetros controlados

| Parâmetro | Valor | Razão |
|---|---:|---|
| `temperature` | 0,0 | reduz variação entre rodadas factuais |
| `top_p` | 0,9 | restringe amostragem de baixa probabilidade |
| `max_tokens` / `num_predict` | 384 | limita respostas longas e custo de inferência |
| `top-k` do retriever | 4 | inclui trechos úteis sem enviar a base inteira |
| embeddings | `nomic-embed-text` | mesmo vetor para documentos e perguntas |

`top-k` define quantos trechos a busca entrega ao modelo. `top_p` atua depois, na escolha das palavras da resposta. Os valores ficam em `src/rag/multi_provider.py`; na CLI e na interface é possível mudar o top-k e a versão do prompt.

O código também aceita `groq:MODELO` se `GROQ_API_KEY` estiver definida no ambiente. Essa opção não foi testada na rodada registrada aqui. Para experimentá-la, instale `requirements.txt`, configure a chave e execute `python -m src.rag.multi_provider "A tarifa de ponta é real?" --provider ollama:qwen3:8b --provider groq:MODELO_DISPONIVEL --prompt v2 --prompt v3`. Use o nome de um modelo disponível na conta Groq.
