# Loja Virtual - Grupo 2

CRUD de terminal em Python + PostgreSQL 16 sobre o banco `db2semestre`.
Tabelas: `cliente`, `endereco`, `produto`, `pedido`, `item_pedido`, `pagamento`.

O banco e o schema pertencem ao grupo (seguem o DER). O app se adapta a ele e **nao cria
nem altera tabelas**.

## Estrutura

```
app/main.py      menu de terminal e validacao de entrada
app/crud.py      operacoes e regras de negocio (SQL parametrizado, 1 transacao por operacao)
app/db.py        conexao (credenciais do .env) e context manager de transacao
sql/seed.sql     dados de exemplo (inclui o pedido do DER: R$ 330,00)
tunnel.py        testa a conexao via Cloudflare Tunnel
.env             credenciais (NAO versionar; ja esta no .gitignore)
```

## Como rodar

1. Dependencias: `python -m pip install -r requirements.txt`
2. `.env` com `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
   (o app le exatamente esses nomes; as demais variaveis sao so referencia).
3. Banco em outra maquina, via Cloudflare Tunnel (precisa do `cloudflared`):
   - terminal 1 (deixe aberto):
     `cloudflared access tcp --hostname <DB_TUNNEL_HOSTNAME> --url 127.0.0.1:15436`
   - `.env`: `DB_HOST=127.0.0.1` e `DB_PORT=15436`
   - `python tunnel.py` so testa a conexao.
   - Se o container do tunnel reiniciar, o hostname muda: atualize `DB_TUNNEL_HOSTNAME`.
4. Terminal 2, dentro da pasta do projeto: `python app\main.py`
5. Opcional: `sql/seed.sql` popula o banco vazio com dados de exemplo.

## Valores do banco (sempre MAIUSCULOS)

- Status do pedido: `ABERTO`, `PAGO`, `ENVIADO`, `ENTREGUE`, `CANCELADO`
- Forma de pagamento: `PIX`, `BOLETO`, `CARTAO_CREDITO`, `CARTAO_DEBITO`
- Situacao do pagamento: `PENDENTE`, `APROVADO`, `RECUSADO`, `ESTORNADO`

## Regras de negocio

No banco (valem para qualquer cliente SQL): e-mail unico, UF/CEP no formato, preco >= 0,
quantidade > 0, status/forma/situacao em listas fixas, parcelas de 1 a 24, endereco de
entrega do proprio cliente (FK composta + `fn_criar_pedido`), pedido com pagamento e
produto ja vendido nao podem ser excluidos (FK sem cascade).

No Python (`crud.py`):

- So pedido **ABERTO** aceita itens, alteracoes de pagamento e novos pagamentos.
- O item copia o preco do produto no momento da venda; mudar o preco depois nao altera
  pedidos antigos.
- Parcelas so no `CARTAO_CREDITO` (demais formas: 1).
- Pagamentos **APROVADO + PENDENTE** nao podem passar do total do pedido.
- Quando os pagamentos APROVADOS cobrem o total, o pedido vira **PAGO** automaticamente
  (tambem ao aprovar um pagamento pendente).
- Fluxo de status: `ABERTO -> CANCELADO`; `PAGO -> ENVIADO | CANCELADO`;
  `ENVIADO -> ENTREGUE`. `PAGO` nao pode ser marcado manualmente.
- Excluir cliente apaga tambem os enderecos dele (cascade), mas e barrado se houver pedido.

## Limitacoes conhecidas

- As regras do Python nao protegem contra quem escrever SQL direto no banco
  (seria preciso trigger).
- Nao ha tela para estornar pagamento de pedido ja PAGO (a situacao so muda em pedido ABERTO).
- O e-mail e normalizado para minusculas pelo app, mas o banco diferencia maiusculas.
- O resumo mensal usa SQL dentro do `crud.py` e agrupa pela data do pedido. As views
  `vw_pedidos_detalhados` e `vw_resumo_vendas_mensal` do grupo ainda nao existem no
  banco; quando existirem, o app pode passar a consulta-las.
