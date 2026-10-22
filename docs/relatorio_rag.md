# Relatório técnico do RAG — Sprint 04

**EV Challenge GoodWe · FIAP · Prompt and Artificial Intelligence · 20/10/2026**

## Objetivo e fontes

Na Sprint 03, todo o conteúdo de um JSON pequeno era enviado junto com cada pergunta. Agora, o programa procura primeiro os trechos mais próximos da pergunta e só então pede ao modelo uma resposta. Ele mostra o arquivo e a seção usados. A base tem quatro documentos: um material didático sobre a GoodWe, um regimento de condomínio simulado, uma FAQ e uma tabela de tarifas fictícias. As potências nominais da linha HCA podem ser conferidas na [página da GoodWe](https://br.goodwe.com/hca-evcharger). ChargeGrid, EV ChargeOps, as regras do condomínio e os preços são exemplos do exercício, como a interface também informa.

## Como a busca funciona

1. `loader.py` lê arquivos MD e TXT em UTF-8 e extrai texto de PDFs. Guarda o nome do arquivo e, nos PDFs, a página.
2. `chunking.py` divide o texto em trechos de até **800 caracteres**, com **120 de sobreposição**. Isso evita enviar páginas inteiras ao modelo e reduz a chance de cortar uma informação importante na fronteira entre trechos. O cabeçalho Markdown mais próximo identifica a seção.
3. `embeddings.py` usa `nomic-embed-text` no Ollama para criar os vetores. A indexação e a consulta precisam usar o mesmo modelo.
4. `vector_store.py` guarda os vetores em `data/chroma/`. O identificador de cada trecho considera sua origem e seu conteúdo, evitando duplicações. Quando um arquivo muda ou é excluído, a sincronização remove os trechos antigos.
5. `retriever.py` busca de um a dez trechos e prepara as referências. `prompt_rag.py` guarda as três versões do prompt. Por fim, `answer.py` verifica o escopo e troca `[Fonte 1]` pelo arquivo e pela seção correspondentes. Uma resposta factual sem citação reconhecida é bloqueada.

A distância devolvida pelo Chroma mede proximidade entre vetores. Ela não diz se uma resposta está correta. Como não calibramos um limite de distância, o prompt orienta o modelo a dizer quando falta informação e o código exige uma citação válida para publicar uma resposta factual. Mesmo assim, uma citação válida pode acompanhar uma interpretação errada. Por isso, a interface mostra os trechos para conferência.

## Respostas e proteção contra instruções nos documentos

As três versões do prompt mandam usar apenas os documentos, citar as informações e identificar o que é simulado. A v2 pede mais cuidado com cálculos e comparações. A v3 também orienta o modelo a conferir números e fontes antes de responder, além de tratar perguntas sobre dados atuais da estação. O texto dos documentos fica separado das regras do sistema. Algumas linhas que tentam dar ordens ao modelo são neutralizadas, e referências inexistentes são rejeitadas. Isso diminui o risco de seguir instruções escondidas na base, mas não elimina todos os tipos de ataque.

## Avaliação

O arquivo `evals/questions.json` traz quatro perguntas: diferença entre conectores, tarifa fictícia, potência do carregador e falta de telemetria. Para comparar os prompts, foram mantidas as perguntas, a base, o `qwen3:8b` e o top-k 4. A geração usou `temperature=0`, `top_p=0.9` e `max_tokens=384`. As respostas e os trechos recuperados estão em `evals/eval_results.json`. Cada resposta recebeu notas de 0 a 1 por **revisão assistida por IA**, com justificativas em `evals/revisao_manual.json`. Trata-se de uma rubrica de apoio, **não** de uma execução do RAGAS ou de avaliação humana independente.

| Iteração | Faithfulness manual | Answer Relevancy manual | Média | Latência média da geração |
|---|---:|---:|---:|---:|
| v1 | 0,938 | 0,938 | 0,938 | 3,084 s |
| v2 | 1,000 | 0,975 | 0,988 | 2,736 s |
| v3 | 1,000 | 1,000 | 1,000 | 2,319 s |

A média subiu **0,050 da v1 para a v2** e **0,012 da v2 para a v3**. Na v1, a resposta sobre conectores dizia que algo “é comum em veículos elétricos”, embora o trecho não afirmasse isso. A v2 retirou essa frase. Já a v3 deixou mais clara a potência nominal do GW22K-HCA e respondeu de forma direta à pergunta sobre consumo atual. São só quatro casos, com notas subjetivas; o resultado não permite afirmar que o chatbot acertará todas as perguntas.

Para fazer outra rodada, execute `python evals/eval_fallback.py coletar --prompt v1 --prompt v2 --prompt v3`. As novas respostas serão salvas em `evals/nova_coleta.json`, sem sobrescrever as anteriores. Depois, compare cada resposta com os trechos recuperados, revise as justificativas em `evals/revisao_manual.json` e rode `python evals/eval_fallback.py anotar --entrada evals/nova_coleta.json` e `python evals/eval_fallback.py resumir --entrada evals/nova_coleta.json`. O avaliador RAGAS está em `evals/eval_ragas.py` e usa um arquivo de saída separado. Ele não rodou nesta máquina porque a instalação de `scikit-network` falhou no Python 3.14 sem compilador C++.

## Limites

O chatbot não acessa o SEMS, medições, faturas ou regras e tarifas reais. Quando alguém pede dados atuais de uma estação, a resposta correta é dizer que eles não estão disponíveis neste projeto. Antes de pensar em uso real, seria necessário substituir os exemplos por documentos atuais, pedir revisão técnica e testar muito mais perguntas, inclusive as que tentam induzir respostas erradas.
