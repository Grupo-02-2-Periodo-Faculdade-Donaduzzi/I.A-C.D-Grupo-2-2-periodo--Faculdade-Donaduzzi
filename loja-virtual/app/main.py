import re
import sys
from decimal import Decimal, InvalidOperation

import psycopg2
from psycopg2 import errors

import crud
from db import conectar

STATUS = ("ABERTO", "PAGO", "ENVIADO", "ENTREGUE", "CANCELADO")
FORMAS = ("PIX", "BOLETO", "CARTAO_CREDITO", "CARTAO_DEBITO")
SITUACOES = ("PENDENTE", "APROVADO", "RECUSADO", "ESTORNADO")


# ------------------------- leitura validada --------------------------
def ler_texto(msg, minimo=1, opcional=False):
    while True:
        v = input(msg).strip()
        if opcional and not v:
            return None
        if len(v) >= minimo:
            return v
        print(f"  -> minimo de {minimo} caractere(s).")


def ler_int(msg, minimo=1, maximo=None):
    while True:
        try:
            v = int(input(msg))
            if v >= minimo and (maximo is None or v <= maximo):
                return v
        except ValueError:
            pass
        print(f"  -> digite um inteiro >= {minimo}" + (f" e <= {maximo}" if maximo else "") + ".")


def ler_dinheiro(msg):
    while True:
        try:
            v = Decimal(input(msg).replace(",", "."))   # aceita 180,00 ou 180.00
            if v >= 0 and v == v.quantize(Decimal("0.01")):
                return v
        except InvalidOperation:
            pass
        print("  -> valor invalido (ex.: 180,00).")


def ler_email(msg):
    while True:
        v = input(msg).strip().lower()
        if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v):
            return v
        print("  -> e-mail invalido.")


def ler_opcao(msg, opcoes):
    while True:
        v = input(f"{msg} {'/'.join(opcoes)}: ").strip().upper()
        if v in opcoes:
            return v
        print("  -> opcao invalida.")


def ler_endereco():
    log = ler_texto("Logradouro: ", 3)
    num = ler_texto("Numero: ")
    cid = ler_texto("Cidade: ", 2)
    while True:
        uf = input("UF: ").strip().upper()
        if re.fullmatch(r"[A-Z]{2}", uf):
            break
        print("  -> UF com 2 letras.")
    while True:
        cep = re.sub(r"\D", "", input("CEP: "))   # tira ponto/traco
        if len(cep) == 8:
            break
        print("  -> CEP com 8 digitos.")
    return log, num, cid, uf, cep


def tabela(linhas):
    if not linhas:
        print("  (nenhum registro)")
        return
    cols = list(linhas[0].keys())
    larg = {c: max(len(c), *(len(str(l[c])) for l in linhas)) for c in cols}
    print("  " + " | ".join(c.ljust(larg[c]) for c in cols))
    print("  " + "-+-".join("-" * larg[c] for c in cols))
    for l in linhas:
        print("  " + " | ".join(str(l[c] if l[c] is not None else "").ljust(larg[c]) for c in cols))


def resultado(n, ok="Feito.", nao="Registro nao encontrado."):
    print(ok if n else nao)


# ------------------------------ menus --------------------------------
def menu_clientes(conn):
    op = input("[1] Cadastrar [2] Listar [3] Editar [4] Excluir [5] + Endereco "
               "[6] Ver enderecos [7] Editar endereco [8] Excluir endereco: ")
    if op == "1":
        cid = crud.criar_cliente(conn, ler_texto("Nome: ", 2), ler_email("E-mail: "))
        print(f"Cliente {cid} cadastrado.")
        tabela([crud.buscar_cliente(conn, cid)])          # prova que gravou
    elif op == "2":
        tabela(crud.listar_clientes(conn))
    elif op == "3":
        resultado(crud.atualizar_cliente(conn, ler_int("ID: "),
                                         ler_texto("Novo nome: ", 2), ler_email("Novo e-mail: ")))
    elif op == "4":
        resultado(crud.excluir_cliente(conn, ler_int("ID: ")))
    elif op == "5":
        cli = ler_int("ID do cliente: ")
        eid = crud.criar_endereco(conn, cli, *ler_endereco())
        print(f"Endereco {eid} cadastrado.")
        tabela(crud.listar_enderecos(conn, cli))
    elif op == "6":
        tabela(crud.listar_enderecos(conn, ler_int("ID do cliente: ")))
    elif op == "7":
        resultado(crud.atualizar_endereco(conn, ler_int("ID do endereco: "), *ler_endereco()))
    elif op == "8":
        resultado(crud.excluir_endereco(conn, ler_int("ID do endereco: ")))
    else:
        print("Opcao invalida.")


def menu_produtos(conn):
    op = input("[1] Cadastrar [2] Listar [3] Editar [4] Excluir: ")
    if op == "1":
        sku = ler_texto("SKU: ", 2).upper()
        crud.criar_produto(conn, sku, ler_texto("Nome: ", 2), ler_dinheiro("Preco: "))
        print(f"Produto {sku} cadastrado.")
        tabela([p for p in crud.listar_produtos(conn) if p["sku"] == sku])
    elif op == "2":
        tabela(crud.listar_produtos(conn))
    elif op == "3":
        resultado(crud.atualizar_produto(conn, ler_texto("SKU: ").upper(),
                                         ler_texto("Novo nome: ", 2), ler_dinheiro("Novo preco: ")))
    elif op == "4":
        resultado(crud.excluir_produto(conn, ler_texto("SKU: ").upper()), "Produto excluido.",
                  "Produto nao encontrado.")
    else:
        print("Opcao invalida.")


def menu_pedidos(conn):
    op = input("[1] Abrir [2] Listar [3] Detalhar [4] Add item [5] Alterar qtd "
               "[6] Remover item [7] Mudar status [8] Excluir: ")
    if op == "1":
        pid = crud.abrir_pedido(conn, ler_int("ID do cliente: "), ler_int("ID do endereco: "))
        print(f"Pedido {pid} aberto.")
    elif op == "2":
        tabela(crud.listar_pedidos(conn))
    elif op == "3":
        itens, pags, total = crud.detalhar_pedido(conn, ler_int("ID do pedido: "))
        print("Itens:"); tabela(itens)
        print("Pagamentos:"); tabela(pags)
        print(f"TOTAL: R$ {total}")
    elif op == "4":
        pid = ler_int("ID do pedido: ")
        crud.adicionar_item(conn, pid, ler_texto("SKU: ").upper(), ler_int("Quantidade: "))
        print(f"Item adicionado. Total agora: R$ {crud.total_pedido(conn, pid)}")
    elif op == "5":
        resultado(crud.alterar_quantidade(conn, ler_int("ID do pedido: "),
                                          ler_texto("SKU: ").upper(), ler_int("Nova qtd: ")))
    elif op == "6":
        resultado(crud.remover_item(conn, ler_int("ID do pedido: "), ler_texto("SKU: ").upper()))
    elif op == "7":
        resultado(crud.atualizar_status(conn, ler_int("ID do pedido: "),
                                        ler_opcao("Status", STATUS)))
    elif op == "8":
        resultado(crud.excluir_pedido(conn, ler_int("ID do pedido: ")))
    else:
        print("Opcao invalida.")


def menu_pagamentos(conn):
    op = input("[1] Registrar [2] Mudar situacao [3] Consultar total: ")
    if op == "1":
        pid = ler_int("ID do pedido: ")
        forma = ler_opcao("Forma", FORMAS)
        parc = ler_int("Parcelas: ", 1, 24) if forma == "CARTAO_CREDITO" else 1
        pag, quitado = crud.registrar_pagamento(conn, pid, forma, parc,
                                                ler_dinheiro("Valor: "), ler_opcao("Situacao", SITUACOES))
        print(f"Pagamento {pag} registrado." + (" Pedido QUITADO -> status Pago." if quitado else ""))
    elif op == "2":
        achou, quitado = crud.atualizar_situacao_pagamento(
            conn, ler_int("ID do pagamento: "), ler_opcao("Situacao", SITUACOES))
        resultado(achou, "Feito." + (" Pedido QUITADO -> status Pago." if quitado else ""))
    elif op == "3":
        print(f"Total: R$ {crud.total_pedido(conn, ler_int('ID do pedido: '))}")
    else:
        print("Opcao invalida.")


# --------------------- traducao de erros do banco --------------------
def erro_amigavel(e):
    diag = getattr(e, "diag", None)
    restr = (diag.constraint_name or "") if diag else ""
    if isinstance(e, errors.UniqueViolation):
        return "Ja existe um registro com esse valor (e-mail ou SKU duplicado)."
    if isinstance(e, errors.ForeignKeyViolation):
        return ("Operacao barrada: o registro esta ligado a outro "
                "(ex.: cliente ou endereco com pedidos, pedido com pagamento) "
                "ou o id referenciado nao existe.")
    if isinstance(e, errors.CheckViolation):
        return f"Valor fora das regras do banco (restricao {restr})."
    if isinstance(e, errors.RaiseException):          # RAISE EXCEPTION das functions
        return diag.message_primary
    return f"Erro no banco: {e}"


def main():
    try:
        conn = conectar()
    except psycopg2.OperationalError as e:
        sys.exit(f"Nao conectou no PostgreSQL. Confira o .env e se o container esta de pe.\n{e}")

    menus = {"1": menu_clientes, "2": menu_produtos, "3": menu_pedidos, "4": menu_pagamentos}
    try:
        while True:
            op = input("\n=== LOJA VIRTUAL ===\n[1] Clientes [2] Produtos [3] Pedidos "
                       "[4] Pagamentos [5] Resumo mensal [0] Sair: ").strip()
            if op == "0":
                break
            try:
                if op == "5":
                    tabela(crud.resumo_mensal(conn))
                elif op in menus:
                    menus[op](conn)
                else:
                    print("Opcao invalida.")
            except crud.RegraNegocio as e:
                print(f"Regra: {e}")
            except psycopg2.Error as e:
                print(erro_amigavel(e))
    except (KeyboardInterrupt, EOFError):
        print("\nEncerrado.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
