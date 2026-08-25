import pandas as pd
import numpy as np

url = "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv"
df = pd.read_csv(url)

print("PASSO 1 - Dados extraídos com sucesso!")
print(f"Linhas: {df.shape[0]} | Colunas: {df.shape[1]}\n")

### 2) EXIBIR AS INFORMAÇÕES GERAIS DO DATASET 
print("=" * 60)
print("PASSO 2 - Informações gerais (df.info())")
print("=" * 60)
df.info()

### 3) EXIBIR ESTATÍSTICAS DESCRITIVAS DO DATASET
print("\n" + "=" * 60)
print("PASSO 3 - Estatísticas descritivas (df.describe())")
print("=" * 60)
print(df.describe())

### 4) VALORES AUSENTES POR COLUNA
print("\n" + "=" * 60)
print("PASSO 4 - Valores ausentes por coluna")
print("=" * 60)
print(df.isnull().sum())

### 5) PREENCHER IDADE FALTANTE UTILIZANDO MEDIANA AGRUPADA POR CLASSE E SEX
df["Age"] = df.groupby(["Pclass", "Sex"])["Age"].transform(
    lambda idade: idade.fillna(idade.median())
)

### 6) SE SOBRAR ALGUEM AUSENTE, PREENCHE COM A MEDIANA GERAL
df["Age"] = df["Age"].fillna(df["Age"].median())

print("\nPASSO 5 e 6 - Idades ausentes preenchidas.")
print(f"Valores ausentes restantes em Age: {df['Age'].isnull().sum()}")

### 7) EMBARKED: PREENCHER AUSENTES COM VALOR MAIS FREQUENTE (moda)
porto_mais_frequente = df["Embarked"].mode()[0]
df["Embarked"] = df["Embarked"].fillna(porto_mais_frequente)

print(f"\nPASSO 7 - Embarked preenchido com o valor mais frequente: '{porto_mais_frequente}'")


### 8) CABIN: CRIAR FEATURE INDICADORA (1 = TINHA CABINE, 0 = NÃO TINHA)
df["Has_Cabin"] = df["Cabin"].notnull().astype(int)

print("\nPASSO 8 - Nova coluna 'Has_Cabin' criada (1 = tinha cabine, 0 = não tinha).")


### 9) FARE: PREENCHER AUSENTES COM A MÉDIA AGRUPADA POR CLASSE (Pclass)
df["Fare"] = df.groupby("Pclass")["Fare"].transform(
    lambda tarifa: tarifa.fillna(tarifa.mean())
)

print(f"\nPASSO 9 - Fare preenchido. Valores ausentes restantes: {df['Fare'].isnull().sum()}")

### 10) AGE: CRIAR UMA FEATURE INDICATIVA (CRIANÇA, ADOLESCENTE, ADULTO JOVEM, ADULTO, IDOSO)
faixas_idade = [0, 12, 18, 35, 60, 100]
nomes_idade = ["Criança", "Adolescente", "Adulto Jovem", "Adulto", "Idoso"]
df["Faixa_Idade"] = pd.cut(df["Age"], bins=faixas_idade, labels=nomes_idade)

print("\nPASSO 10 - Nova coluna 'Faixa_Idade' criada:")
print(df["Faixa_Idade"].value_counts())

### 11) FARE: CRIAR UMA FEATURE INDICATIVA (BAIXO, MÉDIO-BAIXO, MÉDIO-ALTO, ALTO)
faixas_tarifa = [0, 7.91, 14.45, 31, 600]
nomes_tarifa = ["Baixo", "Médio-Baixo", "Médio-Alto", "Alto"]
df["Faixa_Tarifa"] = pd.cut(df["Fare"], bins=faixas_tarifa, labels=nomes_tarifa)

print("\nPASSO 11 - Nova coluna 'Faixa_Tarifa' criada:")
print(df["Faixa_Tarifa"].value_counts())

### RESULTADO FINAL 
print("\n" + "=" * 60)
print("RESULTADO FINAL - primeiras linhas do dataset tratado")
print("=" * 60)
print(df[["Name", "Pclass", "Sex", "Age", "Faixa_Idade",
          "Fare", "Faixa_Tarifa", "Has_Cabin", "Embarked"]].head(10))

print("\nValores ausentes finais em todo o dataset:")
print(df.isnull().sum())

### SALVA TUDO EM CSV
df.to_csv("titanic_tratado.csv", index=False)
print("\nArquivo 'titanic_tratado.csv' salvo com sucesso!")
