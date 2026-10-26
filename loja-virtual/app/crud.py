from decimal import Decimal

from db import transacao


class RegraNegocio(Exception):
    """Erro de regra validada no Python (ex.: item em pedido ja pago)."""


def _um(cur, sql, params=()):
    cur.execute(sql, params)
    return cur.fetchone()


def _todos(cur, sql, params=()):
    cur.execute(sql, params)
    return cur.fetchall()


# ============================ CLIENTE ===============================
def criar_cliente(conn, nome, email):
    with transacao(conn) as cur:
        return _um(cur, "INSERT INTO cliente (nome, email) VALUES (%s, %s) "
                        "RETURNING cliente_id", (nome, email))["cliente_id"]


def listar_clientes(conn):
    with transacao(conn) as cur:
        return _todos(cur, "SELECT cliente_id, nome, email FROM cliente ORDER BY cliente_id")


def buscar_cliente(conn, cliente_id):
    with transacao(conn) as cur:
        return _um(cur, "SELECT * FROM cliente WHERE cliente_id = %s", (cliente_id,))


def atualizar_cliente(conn, cliente_id, nome, email):
    with transacao(conn) as cur:
        cur.execute("UPDATE cliente SET nome = %s, email = %s WHERE cliente_id = %s",
                    (nome, email, cliente_id))
        return cur.rowcount  # 0 = id nao existe


def excluir_cliente(conn, cliente_id):
    # Os enderecos caem junto (ON DELETE CASCADE). Pedido do cliente barra a exclusao
    # (FK sem cascade) -> ForeignKeyViolation.
    with transacao(conn) as cur:
        cur.execute("DELETE FROM cliente WHERE cliente_id = %s", (cliente_id,))
        return cur.rowcount


# ============================ ENDERECO ==============================
def criar_endereco(conn, cliente_id, logradouro, numero, cidade, uf, cep):
    with transacao(conn) as cur:
        return _um(cur, """
            INSERT INTO endereco (cliente_id, logradouro, numero, cidade, uf, cep)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING endereco_id""",
            (cliente_id, logradouro, numero, cidade, uf, cep)
        )["endereco_id"]


def listar_enderecos(conn, cliente_id):
    with transacao(conn) as cur:
        return _todos(cur, "SELECT * FROM endereco WHERE cliente_id = %s ORDER BY endereco_id",
                      (cliente_id,))


def atualizar_endereco(conn, endereco_id, logradouro, numero, cidade, uf, cep):
    with transacao(conn) as cur:
        cur.execute("""
            UPDATE endereco SET logradouro=%s, numero=%s, cidade=%s, uf=%s, cep=%s
            WHERE endereco_id = %s""",
            (logradouro, numero, cidade, uf, cep, endereco_id))
        return cur.rowcount


def excluir_endereco(conn, endereco_id):
    # Endereco usado em algum pedido e barrado pela FK composta de pedido.
    with transacao(conn) as cur:
        cur.execute("DELETE FROM endereco WHERE endereco_id = %s", (endereco_id,))
        return cur.rowcount


# ============================ PRODUTO ===============================
def criar_produto(conn, sku, nome, preco):
    with transacao(conn) as cur:
        cur.execute("INSERT INTO produto (sku, nome, preco_atual) VALUES (%s, %s, %s)",
                    (sku, nome, preco))
        return sku


def listar_produtos(conn):
    with transacao(conn) as cur:
        return _todos(cur, "SELECT sku, nome, preco_atual FROM produto ORDER BY sku")


def atualizar_produto(conn, sku, nome, preco):
    # Muda so o preco ATUAL. Pedidos antigos guardam o preco em item_pedido.
    with transacao(conn) as cur:
        cur.execute("UPDATE produto SET nome = %s, preco_atual = %s WHERE sku = %s",
                    (nome, preco, sku))
        return cur.rowcount


def excluir_produto(conn, sku):
    """Produto ja vendido nao pode sumir (historico dos pedidos)."""
    with transacao(conn) as cur:
        if _um(cur, "SELECT 1 FROM item_pedido WHERE sku = %s LIMIT 1", (sku,)):
            raise RegraNegocio(f"Produto {sku} ja foi vendido: nao pode ser excluido.")
        cur.execute("DELETE FROM produto WHERE sku = %s", (sku,))
        return cur.rowcount


# ============================ PEDIDO ================================
def abrir_pedido(conn, cliente_id, endereco_id):
    # Regra fica na function do banco (fn_criar_pedido) -> vale p/ qualquer cliente SQL
    with transacao(conn) as cur:
        return _um(cur, "SELECT fn_criar_pedido(%s, %s) AS id",
                   (cliente_id, endereco_id))["id"]


def listar_pedidos(conn):
    with transacao(conn) as cur:
        return _todos(cur, """
            SELECT p.pedido_id, p.data_pedido::date AS data, c.nome AS cliente,
                   p.status, fn_total_pedido(p.pedido_id) AS total
            FROM pedido p JOIN cliente c ON c.cliente_id = p.cliente_id
            ORDER BY p.pedido_id""")


def detalhar_pedido(conn, pedido_id):
    with transacao(conn) as cur:
        total = _um(cur, "SELECT fn_total_pedido(%s) AS t", (pedido_id,))["t"]  # erro se nao existe
        itens = _todos(cur, """
            SELECT i.sku, pr.nome AS produto, i.quantidade, i.preco_unitario,
                   i.quantidade * i.preco_unitario AS subtotal
            FROM item_pedido i JOIN produto pr ON pr.sku = i.sku
            WHERE i.pedido_id = %s ORDER BY i.sku""", (pedido_id,))
        pags = _todos(cur, "SELECT pagamento_id, forma_pagamento, parcelas, valor, data, situacao "
                           "FROM pagamento WHERE pedido_id = %s ORDER BY pagamento_id",
                      (pedido_id,))
        return itens, pags, total


# Fluxo permitido. 'PAGO' so nasce por pagamento aprovado (registrar_pagamento /
# atualizar_situacao_pagamento), nunca por troca manual de status.
TRANSICOES = {
    "ABERTO": {"CANCELADO"},
    "PAGO": {"ENVIADO", "CANCELADO"},
    "ENVIADO": {"ENTREGUE"},
    "ENTREGUE": set(),
    "CANCELADO": set(),
}


def atualizar_status(conn, pedido_id, status):
    with transacao(conn) as cur:
        p = _um(cur, "SELECT status FROM pedido WHERE pedido_id = %s FOR UPDATE", (pedido_id,))
        if not p:
            return 0
        atual = p["status"]
        if status == atual:
            return 1
        if status not in TRANSICOES[atual]:
            permitidos = ", ".join(sorted(TRANSICOES[atual])) or "nenhum"
            raise RegraNegocio(f"Pedido {atual}: nao pode ir para '{status}' "
                               f"(permitido: {permitidos}). 'PAGO' so via pagamento aprovado.")
        cur.execute("UPDATE pedido SET status = %s WHERE pedido_id = %s", (status, pedido_id))
        return 1


def excluir_pedido(conn, pedido_id):
    # Itens caem junto (CASCADE). Com pagamento registrado, a FK (sem cascade) barra.
    with transacao(conn) as cur:
        cur.execute("DELETE FROM pedido WHERE pedido_id = %s", (pedido_id,))
        return cur.rowcount


# ========================= ITEM DO PEDIDO ===========================
def _pedido_aberto(cur, pedido_id):
    # FOR UPDATE trava a linha do pedido ate o commit: ninguem paga/fecha no meio
    p = _um(cur, "SELECT status FROM pedido WHERE pedido_id = %s FOR UPDATE", (pedido_id,))
    if not p:
        raise RegraNegocio(f"Pedido {pedido_id} nao existe.")
    if p["status"] != "ABERTO":
        raise RegraNegocio(f"Pedido {pedido_id} esta '{p['status']}'; so pedido ABERTO aceita alteracoes.")


def adicionar_item(conn, pedido_id, sku, quantidade):
    """Copia o preco ATUAL do produto para o item. Se o SKU ja esta no pedido, soma a qtd."""
    with transacao(conn) as cur:
        _pedido_aberto(cur, pedido_id)
        prod = _um(cur, "SELECT preco_atual FROM produto WHERE sku = %s", (sku,))
        if not prod:
            raise RegraNegocio(f"Produto {sku} nao existe.")
        cur.execute("""
            INSERT INTO item_pedido (pedido_id, sku, quantidade, preco_unitario)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (pedido_id, sku)
            DO UPDATE SET quantidade = item_pedido.quantidade + EXCLUDED.quantidade""",
            (pedido_id, sku, quantidade, prod["preco_atual"]))


def alterar_quantidade(conn, pedido_id, sku, quantidade):
    with transacao(conn) as cur:
        _pedido_aberto(cur, pedido_id)
        cur.execute("UPDATE item_pedido SET quantidade = %s WHERE pedido_id = %s AND sku = %s",
                    (quantidade, pedido_id, sku))
        return cur.rowcount


def remover_item(conn, pedido_id, sku):
    with transacao(conn) as cur:
        _pedido_aberto(cur, pedido_id)
        cur.execute("DELETE FROM item_pedido WHERE pedido_id = %s AND sku = %s",
                    (pedido_id, sku))
        return cur.rowcount


# ============================ PAGAMENTO =============================
def total_pedido(conn, pedido_id):
    with transacao(conn) as cur:
        return _um(cur, "SELECT fn_total_pedido(%s) AS t", (pedido_id,))["t"]


def registrar_pagamento(conn, pedido_id, forma, parcelas, valor, situacao):
    """Grava o pagamento e, se os aprovados cobrirem o total, marca o pedido como PAGO.
    As duas escritas estao na MESMA transacao: nunca fica pagamento sem status coerente."""
    with transacao(conn) as cur:
        _pedido_aberto(cur, pedido_id)
        total = _um(cur, "SELECT fn_total_pedido(%s) AS t", (pedido_id,))["t"]
        if total == 0:
            raise RegraNegocio("Pedido sem itens nao pode receber pagamento.")
        # Pendentes tambem reservam valor: senao varios PENDENTES estourariam o total.
        reservado = _valor_pagamentos(cur, pedido_id, ("APROVADO", "PENDENTE"))
        restante = total - reservado
        if Decimal(valor) > restante:
            raise RegraNegocio(f"Valor maior que o restante do pedido (R$ {restante}).")

        pag_id = _um(cur, """
            INSERT INTO pagamento (pedido_id, forma_pagamento, parcelas, valor, situacao)
            VALUES (%s, %s, %s, %s, %s) RETURNING pagamento_id""",
            (pedido_id, forma, parcelas, valor, situacao))["pagamento_id"]

        return pag_id, _quitar_se_pago(cur, pedido_id, total)


def _valor_pagamentos(cur, pedido_id, situacoes, exceto_id=None):
    row = _um(cur, "SELECT COALESCE(SUM(valor), 0) AS s FROM pagamento "
                   "WHERE pedido_id = %s AND situacao = ANY(%s) "
                   "AND pagamento_id IS DISTINCT FROM %s",
              (pedido_id, list(situacoes), exceto_id))
    return row["s"]


def _quitar_se_pago(cur, pedido_id, total):
    """Se os pagamentos APROVADOS cobrem o total, marca o pedido como PAGO."""
    if total > 0 and _valor_pagamentos(cur, pedido_id, ("APROVADO",)) == total:
        cur.execute("UPDATE pedido SET status = 'PAGO' WHERE pedido_id = %s", (pedido_id,))
        return True
    return False


def atualizar_situacao_pagamento(conn, pagamento_id, situacao):
    """Retorna (encontrado, quitado). So mexe em pagamento de pedido ABERTO e
    revalida o total: aprovar um pagamento pode quitar o pedido."""
    with transacao(conn) as cur:
        pag = _um(cur, "SELECT pedido_id, valor FROM pagamento WHERE pagamento_id = %s",
                  (pagamento_id,))
        if not pag:
            return False, False
        pedido_id = pag["pedido_id"]
        _pedido_aberto(cur, pedido_id)
        total = _um(cur, "SELECT fn_total_pedido(%s) AS t", (pedido_id,))["t"]
        if situacao in ("APROVADO", "PENDENTE"):
            outros = _valor_pagamentos(cur, pedido_id, ("APROVADO", "PENDENTE"), pagamento_id)
            if outros + pag["valor"] > total:
                raise RegraNegocio(f"Esse pagamento passaria do total do pedido "
                                   f"(R$ {total - outros} restantes).")
        cur.execute("UPDATE pagamento SET situacao = %s WHERE pagamento_id = %s",
                    (situacao, pagamento_id))
        return True, _quitar_se_pago(cur, pedido_id, total)


# ============================ RELATORIO =============================
def resumo_mensal(conn):
    # Vendido = pedido ja pago (PAGO, ENVIADO ou ENTREGUE). COUNT(DISTINCT) porque o
    # JOIN com itens multiplica as linhas do pedido.
    with transacao(conn) as cur:
        return _todos(cur, """
            SELECT date_trunc('month', p.data_pedido)::date AS mes,
                   COUNT(DISTINCT p.pedido_id)              AS pedidos,
                   SUM(i.quantidade)                        AS itens_vendidos,
                   SUM(i.quantidade * i.preco_unitario)     AS valor_total
            FROM pedido p JOIN item_pedido i ON i.pedido_id = p.pedido_id
            WHERE p.status IN ('PAGO', 'ENVIADO', 'ENTREGUE')
            GROUP BY 1 ORDER BY 1""")
