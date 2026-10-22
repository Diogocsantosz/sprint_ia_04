# Carregadores GoodWe: referência técnica e operação simulada

> Escopo: material didático da Sprint 04. As especificações da linha HCA abaixo vêm das páginas oficiais da GoodWe. Os fluxos chamados ChargeGrid e EV ChargeOps são cenários **simulados** para testar o chatbot; não são produtos ou serviços cuja existência seja afirmada pela GoodWe.

## Linha HCA (dados de produto)

| Modelo | Potência nominal de saída | Alimentação nominal | Uso |
|---|---:|---|---|
| GW7K-HCA | 7 kW | 230 V, monofásica | Recarga AC residencial ou compartilhada |
| GW11K-HCA | 11 kW | 400 V, trifásica | Recarga AC compartilhada |
| GW22K-HCA | 22 kW | 400 V, trifásica | Recarga AC compartilhada |

A potência real depende também do carregador embarcado do veículo, da instalação, da configuração e da disponibilidade de energia. Um carro limitado a 7 kW em AC não receberá 22 kW apenas porque o ponto tem potência nominal de 22 kW. Não use esta tabela para dimensionar cabos ou proteções. A instalação e a manutenção exigem profissional habilitado e consulta ao manual aplicável ao modelo instalado.

Fontes de produto: [página GoodWe HCA](https://br.goodwe.com/hca-evcharger) e [manual oficial HCA](https://br.goodwe.com/Ftp/EN/Downloads/User%20Manual/GW_HCA%20Series_User%20Manual-EN.pdf). Consulte a revisão do manual do equipamento antes de aplicar qualquer procedimento.

## Cenário didático: ChargeGrid / EV ChargeOps

Nesta simulação, **ChargeGrid** é o nome interno de um painel de reserva de vagas, e **EV ChargeOps** é o nome interno de um fluxo de atendimento. Nenhum deles substitui o aplicativo, o suporte ou a documentação oficial da GoodWe.

Fluxo de atendimento simulado: (1) identificar o ponto e o usuário; (2) verificar no sistema operacional autorizado se há reserva ativa; (3) consultar registros de início e fim da sessão; (4) encaminhar falhas técnicas ao operador e ao instalador habilitado. O chatbot desta entrega não tem acesso a telemetria, disponibilidade ao vivo, consumo medido ou faturamento. Para esses dados, deve pedir consulta ao sistema real e nunca gerar um número.

Se o carregador mostrar falha, interrompa o uso conforme as instruções disponíveis no local e acione o responsável. Não abra o equipamento nem oriente intervenção elétrica por conta própria.
