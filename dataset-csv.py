# %% [markdown]
# BIBLIOTECAS USADAS PARA O SCRIPT DO CSV

# %%
import sys
import urllib.request
import urllib.error

# %%
# ------------------- CONFIGURAÇÕES (pode usar qualquer planílha) -------------------
SPREADSHEET_ID = "1AXXhB4dHOKUdjLG86tc_yAfCxorfuzOl3yYm-cmZXsc"
GID = "1099775441"                      # aba específica da planilha
ARQUIVO_SAIDA = "dados_planilha.csv"    # nome do arquivo CSV a ser salvo

# %% [markdown]
# ESSA É A VARIAVEL DE EXPORTAÇÃO QUE USAMOS FUNÇÃO E COLOCAMOS O LINK QUE DESEJARMOS

# %%
URL_EXPORTACAO = (
    f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
    f"/export?format=csv&gid={GID}"
)

# %% [markdown]
# ESSA JA É A FUNÇÃO QUE IREMOS USAR A VARIAVEL ACIMA PARA BAIXAR O CSV

# %%
def baixar_csv():
    print(f"Baixando planilha de:\n{URL_EXPORTACAO}\n")
    try:
        with urllib.request.urlopen(URL_EXPORTACAO) as resposta:
            conteudo = resposta.read()
    except urllib.error.HTTPError as erro:
        print(f"Falha ao baixar (HTTP {erro.code}).")
        print("Verifique se o compartilhamento está como 'Qualquer pessoa com o link'.")
        sys.exit(1)
 
    with open(ARQUIVO_SAIDA, "wb") as f:
        f.write(conteudo)
    print(f"Planilha salva em '{ARQUIVO_SAIDA}' ({len(conteudo)} bytes).")

# %% [markdown]
# SE O NOME FOR CERTO, BAIXA O ARQUIVO CSV

# %%
if __name__ == "__main__":
    baixar_csv()