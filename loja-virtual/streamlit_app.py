"""Vitrine da Loja Virtual (Grupo 2) em Streamlit. Dados ficticios, em memoria.

Rodar:  python -m streamlit run streamlit_app.py
"""
from datetime import datetime
from decimal import Decimal

import streamlit as st

st.set_page_config(page_title="Loja Virtual - Grupo 2", page_icon="🛒", layout="wide")

FORMAS = {"PIX": "Pix", "BOLETO": "Boleto", "CARTAO_CREDITO": "Cartão de crédito",
          "CARTAO_DEBITO": "Cartão de débito"}
ETAPAS = ["ABERTO", "PAGO", "ENVIADO", "ENTREGUE"]

PRODUTOS = {  # sku: (nome, preco, icone, descricao)
    "TEC-001": ("Teclado", Decimal("180.00"), "⌨️", "Teclado mecânico ABNT2"),
    "MOU-001": ("Mouse", Decimal("75.00"), "🖱️", "Mouse sem fio 1600 DPI"),
    "MON-001": ("Monitor 24\"", Decimal("899.90"), "🖥️", "Full HD, painel IPS"),
    "CAB-001": ("Cabo HDMI", Decimal("29.90"), "🔌", "Cabo HDMI 2.0, 1,5 m"),
    "FON-001": ("Headset", Decimal("149.90"), "🎧", "Headset com microfone"),
    "WEB-001": ("Webcam", Decimal("120.00"), "📷", "Webcam HD 720p"),
}

CLIENTES = {
    "Beatriz Souza": "Rua das Flores, 120 - São Paulo/SP",
    "Leonardo Lima": "Av. Brasil, 455 - Rio de Janeiro/RJ",
    "Carla Mendes": "Rua da Paz, 78 - Curitiba/PR",
}


def brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def total(itens):
    return sum((PRODUTOS[s][1] * q for s, q in itens.items()), Decimal("0"))


def pedidos_iniciais():  # mesmos pedidos do sql/seed.sql
    return [
        {"id": 1, "cliente": "Beatriz Souza", "data": datetime(2026, 10, 20, 14, 5), "status": "PAGO",
         "itens": {"TEC-001": 1, "MOU-001": 2},
         "pagamento": {"forma": "CARTAO_CREDITO", "parcelas": 3, "situacao": "APROVADO"}},
        {"id": 2, "cliente": "Leonardo Lima", "data": datetime(2026, 10, 21, 9, 30), "status": "ENTREGUE",
         "itens": {"MON-001": 1, "CAB-001": 2},
         "pagamento": {"forma": "PIX", "parcelas": 1, "situacao": "APROVADO"}},
        {"id": 3, "cliente": "Carla Mendes", "data": datetime(2026, 10, 22, 18, 45), "status": "ABERTO",
         "itens": {"TEC-001": 1},
         "pagamento": {"forma": "BOLETO", "parcelas": 1, "situacao": "PENDENTE"}},
    ]


st.session_state.setdefault("carrinho", {})
st.session_state.setdefault("pedidos", pedidos_iniciais())
st.session_state.setdefault("cliente", "Beatriz Souza")

# ------------------------------ barra lateral -----------------------------
qtd_carrinho = sum(st.session_state.carrinho.values())
with st.sidebar:
    st.title("🛒 Loja Virtual")
    st.caption("Grupo 2 · Banco de Dados")
    pagina = st.radio("Menu", ["Vitrine", "Carrinho", "Meus pedidos"], key="pagina",
                      label_visibility="collapsed")
    st.caption(f"🛒 {qtd_carrinho} item(ns) no carrinho")
    st.divider()
    st.selectbox("Comprando como", list(CLIENTES), key="cliente")
    st.caption(f"📍 {CLIENTES[st.session_state.cliente]}")


# --------------------------------- vitrine --------------------------------
def vitrine():
    st.header("Vitrine")
    st.write("Escolha os produtos e adicione ao carrinho.")
    busca = st.text_input("Buscar produto", placeholder="teclado, mouse...").strip().lower()
    itens = [(s, p) for s, p in PRODUTOS.items() if busca in p[0].lower() or busca in p[3].lower()]
    if not itens:
        st.info("Nenhum produto encontrado.")
    colunas = st.columns(3)
    for i, (sku, (nome, preco, icone, desc)) in enumerate(itens):
        with colunas[i % 3].container(border=True):
            st.markdown(f"<div style='font-size:64px;text-align:center'>{icone}</div>",
                        unsafe_allow_html=True)
            st.subheader(nome)
            st.caption(f"{desc} · SKU {sku}")
            st.markdown(f"**{brl(preco)}**")
            c1, c2 = st.columns([1, 2])
            qtd = c1.number_input("Qtd", 1, 20, 1, key=f"q_{sku}", label_visibility="collapsed")
            if c2.button("Adicionar", key=f"a_{sku}", type="primary"):
                st.session_state.carrinho[sku] = st.session_state.carrinho.get(sku, 0) + qtd
                st.toast(f"{qtd}x {nome} no carrinho", icon="🛒")
                st.rerun()


# --------------------------- carrinho + checkout --------------------------
def carrinho():
    st.header("Carrinho")
    cart = st.session_state.carrinho
    if not cart:
        st.info("Seu carrinho está vazio. Vá até a Vitrine para escolher produtos.")
        return

    for sku, qtd in list(cart.items()):
        nome, preco, icone, _ = PRODUTOS[sku]
        c = st.columns([4, 2, 2, 1])
        c[0].markdown(f"{icone} **{nome}**  \n{brl(preco)} cada")
        nova = c[1].number_input("Qtd", 1, 20, qtd, key=f"c_{sku}", label_visibility="collapsed")
        c[2].markdown(f"**{brl(preco * nova)}**")
        if c[3].button("🗑️", key=f"r_{sku}", help="Remover"):
            del cart[sku]
            st.rerun()
        if nova != qtd:
            cart[sku] = nova
            st.rerun()

    st.divider()
    st.metric("Total do pedido", brl(total(cart)))

    st.subheader("Pagamento")
    forma = st.radio("Forma de pagamento", list(FORMAS), format_func=FORMAS.get, horizontal=True)
    parcelas = 1
    if forma == "CARTAO_CREDITO":
        valor = total(cart)
        parcelas = st.select_slider("Parcelas", options=list(range(1, 13)), value=1,
                                    format_func=lambda n: f"{n}x de {brl(valor / n)}")
    st.write(f"Entrega em: **{CLIENTES[st.session_state.cliente]}**")

    if st.button("Finalizar compra", type="primary"):
        aprovado = forma != "BOLETO"  # Pix e cartao aprovam na hora; boleto fica pendente
        pedido = {
            "id": max(p["id"] for p in st.session_state.pedidos) + 1,
            "cliente": st.session_state.cliente, "data": datetime.now(),
            "status": "PAGO" if aprovado else "ABERTO", "itens": dict(cart),
            "pagamento": {"forma": forma, "parcelas": parcelas,
                          "situacao": "APROVADO" if aprovado else "PENDENTE"},
        }
        st.session_state.pedidos.append(pedido)
        st.session_state.carrinho = {}
        st.session_state.ultimo = pedido["id"]
        st.rerun()


def confirmacao():
    pid = st.session_state.pop("ultimo", None)
    if pid:
        st.success(f"Pedido #{pid} criado! Acompanhe em **Meus pedidos**.")
        st.balloons()


# ------------------------------- meus pedidos -----------------------------
def meus_pedidos():
    st.header("Meus pedidos")
    meus = [p for p in st.session_state.pedidos if p["cliente"] == st.session_state.cliente]
    if not meus:
        st.info(f"{st.session_state.cliente} ainda não fez pedidos.")
        return
    for p in sorted(meus, key=lambda p: -p["id"]):
        pg = p["pagamento"]
        with st.expander(f"Pedido #{p['id']} · {p['status']} · {brl(total(p['itens']))}",
                         expanded=p["id"] == meus[-1]["id"]):
            if p["status"] in ETAPAS:
                st.progress((ETAPAS.index(p["status"]) + 1) / len(ETAPAS), text=p["status"])
            st.caption(f"Feito em {p['data']:%d/%m/%Y às %H:%M}")
            st.dataframe(
                [{"SKU": s, "Produto": PRODUTOS[s][0], "Qtd": q,
                  "Preço unit.": brl(PRODUTOS[s][1]), "Subtotal": brl(PRODUTOS[s][1] * q)}
                 for s, q in p["itens"].items()],
                hide_index=True)
            c1, c2, c3 = st.columns(3)
            c1.metric("Total", brl(total(p["itens"])))
            c2.metric("Pagamento", FORMAS[pg["forma"]] + (f" {pg['parcelas']}x" if pg["parcelas"] > 1 else ""))
            c3.metric("Situação", pg["situacao"])


confirmacao()
if pagina == "Vitrine":
    vitrine()
elif pagina == "Carrinho":
    carrinho()
else:
    meus_pedidos()
