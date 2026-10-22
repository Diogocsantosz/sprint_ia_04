# Relatório de Evolução — Sprint 04

**Challenge FIAP × GoodWe · Ciência da Computação, 2º semestre · Prompt and Artificial Intelligence · Prof. Jorge Luiz Gomes · 20/10/2026**

Grupo: Diogo Chiaradia Santos (RM 570246), Rafael Laprega Gontijo Magalhaes (RM 561975), Gustavo Torres de Oliveira (RM 572952) e Lucas Furquim Lima (RM 568690).

## 1. Evolução do produto

Nas Sprints 1 e 2, o assistente recebia um JSON com os produtos dentro do próprio prompt. Na Sprint 03, entraram chains do LangChain, memória por sessão, saída estruturada e filtros de escopo. Nesta sprint, os documentos ficam em uma base local: o programa procura trechos relacionados à pergunta e mostra de onde tirou as informações. O trabalho está na pasta `sprint-ia4`; a Sprint 03 continua separada.

O caminho de uma pergunta é o seguinte: os arquivos MD, TXT ou PDF são divididos em trechos de até 800 caracteres, com 120 de sobreposição; o `nomic-embed-text` transforma esses trechos em vetores, guardados no Chroma; a busca escolhe os mais próximos da pergunta e o modelo gera uma resposta com arquivo e seção. A CLI e a tela em Streamlit usam essa mesma lógica. Também há um script para comparar modelos e versões do prompt com os mesmos trechos.

## 2. Tabela comparativa obrigatória: Antes × Depois

| Aspecto | Antes (Sprints 1–3) | Depois (Sprint 04) |
|---|---|---|
| Base de conhecimento | JSON pequeno inserido no system prompt | Quatro documentos MD locais; suporte a TXT/PDF; Chroma persistente |
| Seleção de contexto | Base inteira enviada na conversa | Busca semântica top-k, padrão 4 |
| Fonte visível na resposta | Sem citação de arquivo/seção | Citação validada e lista visível na CLI e no Streamlit |
| Evolução de documentos | Alteração manual da base embutida | Reindexação idempotente e remoção de trechos antigos |
| Prompts | v1/v2 da Sprint 03 | v1/v2/v3 RAG com grounding, escopo e defesa contra instruções em documentos |
| Interface | CLI | CLI e web local Streamlit |
| Avaliação | Sprint 03: 17 casos, métricas próprias | Sprint 04: 4 casos RAG, rubrica explícita Faithfulness/Relevancy e rota opcional RAGAS |
| Dados operacionais | Sem telemetria; campos nulos | Continua sem telemetria; FAQ e resposta recusam números atuais |

As notas da Sprint 03 e desta sprint vêm de perguntas e critérios diferentes, então não dá para compará-las diretamente. Nas quatro perguntas avaliadas aqui, a média da rubrica foi de **0,938 na v1**, **0,988 na v2** e **1,000 na v3**. As respostas, os trechos usados e as justificativas estão em `evals/eval_results.json`. Essas notas foram dadas em uma revisão assistida por IA. Elas ajudam a acompanhar as mudanças entre prompts, mas não são resultados do RAGAS nem substituem uma avaliação humana independente.

## 3. Problemas encontrados e soluções

**Citação copiada do exemplo.** Na primeira tentativa, o prompt pedia uma referência no formato `[arquivo.md · seção]`. O modelo copiou o exemplo ao pé da letra. O programa bloqueou a resposta, mas a pergunta ficou sem resposta útil. O prompt passou a pedir `[Fonte N]`; depois, o código troca o número pelo arquivo e pela seção do trecho recuperado. Os testes também verificam que uma referência inexistente ou uma frase de recusa seguida de um dado sem fonte não libera uma resposta factual.

**A busca não trazia o trecho necessário.** Ao perguntar pelo consumo e faturamento de uma estação, apareciam trechos sobre cálculo de tarifa, mas faltava a informação principal: o chatbot não recebe dados da estação. Essa explicação foi acrescentada à FAQ e o índice foi atualizado. Assim, a busca passou a recuperar o trecho, e o prompt v3 responde que é preciso consultar o sistema operacional real.

**Comandos escondidos nos documentos.** Um documento pode conter texto tentando dar ordens ao modelo. O programa trata o documento como fonte de informação e neutraliza algumas formas comuns desse ataque, como uma linha iniciada por `SYSTEM:`. O teste `test_grounding.py` cobre esse caso e uma ordem para ignorar instruções. Ainda é uma proteção limitada: outros tipos de ataque precisariam de novos testes.

**RAGAS não rodou neste ambiente.** Com Python 3.14, a instalação parou em `scikit-network`: não havia um pacote pronto nem compilador C++ para montá-lo. O chatbot e o Streamlit funcionam sem essa dependência. Por isso, a avaliação registrada usa a rubrica de revisão assistida por IA; `eval_ragas.py` fica disponível para executar em um ambiente compatível. O relatório não apresenta nenhuma nota como se fosse do RAGAS.

## 4. Modelos, parâmetros e limites

O modelo padrão é `qwen3:8b`. Sua resposta foi comparada à do `gemma3:1b` para uma pergunta, usando os prompts v2 e v3. O Qwen incluiu uma citação válida nas duas respostas; o Gemma não incluiu, então o programa mostrou a mensagem de falta de evidência. É um teste pequeno demais para concluir que um modelo é melhor em geral. A configuração usa `temperature=0`, `top_p=0.9`, `max_tokens=384` e quatro trechos na busca. A opção Groq existe no código, mas depende de uma chave e não entrou nessa comparação. As respostas e os tempos estão no relatório de modelos.

As regras de condomínio, os preços e os nomes ChargeGrid/EV ChargeOps são exemplos criados para o exercício. As informações da linha HCA têm como referência a [página oficial da GoodWe](https://br.goodwe.com/hca-evcharger). O chatbot não consulta o SEMS nem estações reais. Para instalar equipamentos ou conferir uma cobrança, ainda é preciso consultar o manual atualizado e os responsáveis pela instalação ou operação.

## 5. Divisão de responsabilidades do grupo

Os integrantes listados constam em `sprint-ia3/INTEGRANTES.txt`. Para revisar e apresentar a Sprint 04, cada pessoa fica responsável por uma parte do projeto:

| Integrante | Parte sob sua responsabilidade | O que conferir e explicar |
|---|---|---|
| Diogo Chiaradia Santos | Base RAG e CLI | Explicar carregamento, divisão e indexação dos documentos; executar uma pergunta de ponta a ponta pelo terminal. |
| Gustavo Torres de Oliveira | Prompts e avaliação | Comparar as versões v1, v2 e v3; conferir respostas, notas e justificativas da rubrica. |
| Lucas Furquim Lima | Interface e documentação | Testar a tela em Streamlit, conferir as fontes exibidas e revisar os guias e relatórios. |
| Rafael Laprega Gontijo Magalhaes | Grounding e segurança | Verificar escopo, citações, instruções escondidas nos documentos e recusa de orientações elétricas inadequadas. |

Essa divisão organiza a revisão e a apresentação; ela não é um registro de quem implementou cada arquivo. Antes do envio, cada integrante precisa conferir sua parte e o grupo deve revisar as respostas e as notas da rubrica. Este texto foi preparado com assistência de IA e ainda precisa da revisão dos integrantes.
