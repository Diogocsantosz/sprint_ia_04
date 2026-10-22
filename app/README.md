# Interface Streamlit

No diretório `sprint-ia4`, com o ambiente virtual ativo:

```bash
python main.py indexar
streamlit run app/app.py
```

Abra o endereço mostrado pelo Streamlit, normalmente `http://localhost:8501`. Na barra lateral, escolha o modelo, a versão do prompt e quantos trechos a busca deve trazer. Depois de perguntar, abra **Trechos recuperados para conferência** e veja se eles sustentam a resposta. O botão **Atualizar índice** relê os arquivos de `data/knowledge_base/`. A conversa aparece na tela durante a sessão do navegador, mas cada pergunta é respondida separadamente: o histórico não entra como fonte para a próxima resposta.

Os modelos locais instalados são `ollama:qwen3:8b` e `ollama:gemma3:1b`. A opção Groq só aparece se `GROQ_API_KEY` estiver definida no ambiente; a chave não é salva pelo projeto. Em **Outro modelo**, é possível digitar `ollama:nome` ou `groq:nome`. Trocar o modelo de chat não troca os vetores da base: eles continuam usando o modelo configurado em `MODELO_EMBEDDING`.

Se aparecer o aviso de índice vazio, clique em **Atualizar índice** ou rode `python main.py indexar`. Confira as respostas antes de usá-las: uma citação aponta para um trecho da base, mas não garante que o modelo interpretou o trecho corretamente.
