import pandas as pd
import requests

url = "https://brasilapi.com.br/api/ibge/uf/v1"

resp = requests.get(url)

if resp.status_code == 200:
    dados = resp.json()
    df = pd.DataFrame(dados)
    print(df.head())
else:
    print("Erro:", resp.status_code)
    print(resp.text)

    