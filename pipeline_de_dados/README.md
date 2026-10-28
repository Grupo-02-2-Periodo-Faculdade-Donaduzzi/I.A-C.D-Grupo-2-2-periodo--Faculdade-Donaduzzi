# Pipeline de Dados: NYC Táxi Amarelo (Grupo 02)

Pipeline de ponta a ponta (Extract, Transform, Load) com as corridas de táxi amarelo de Nova York em janeiro de 2024.

## Pergunta de negócio
1. Quais zonas de embarque geram mais receita por hora do dia?
2. Quais bairros rendem mais por milha rodada?

## Fontes (pasta `fonte/`)
- `yellow_tripdata_2024-01.parquet`: viagens (2.964.624 linhas, 19 colunas; o pipeline lê só 5 colunas).
- `taxi_zone_lookup.csv`: zonas (265 linhas).
- `taxi_zones.zip`: só para desenhar o mapa extra. Se não estiver na pasta, o notebook baixa sozinho (precisa de internet).

## Camadas (pasta `data/`, gerada pelo pipeline)
- **Bronze** (`data/bronze`): cópia fiel da fonte, só com as colunas necessárias, mais `_data_extracao` e `_origem`. Nenhuma correção.
- **Silver** (`data/silver`): dado limpo e junto (viagens + zonas), com 2.926.603 linhas.
- **Gold** (`data/gold`): `receita_zona_hora` (5.295 linhas) e `eficiencia_bairro` (8 linhas), em Parquet e em SQLite (`gold.db`). Também o modelo dimensional (`dim_tempo`, `dim_zona`, `fato_corrida`) e os gráficos PNG em `data/gold/graficos`.

## Decisões de transformação
- Removemos 19 duplicados (linhas iguais nas 5 colunas de dado).
- Removemos `total_amount` negativo ou zero, tarifa negativa e `total_amount` acima de US$ 1.000 (parâmetro `total_max`).
- Removemos 18 embarques fora de janeiro de 2024.
- Os textos `N/A` da tabela de zonas viraram rótulos (`Fora de NYC`, `Zona desconhecida`, `Sem classificação`), porque significam zona não identificada.
- Mantivemos as corridas com distância zero (têm receita real). Na Gold 2 elas ficam fora do cálculo de receita por milha.
- Junção `left join` com `validate="many_to_one"`, para não multiplicar viagens.

## Configuração
Tudo fica no dicionário `CONFIG`, no topo do notebook (caminhos, nomes de arquivo e parâmetros). Para mudar o período ou o limite de valor, é só mudar `CONFIG["regras"]`. O notebook também grava `pipeline.log` e `historico_execucoes.csv` (com os parâmetros de cada execução).

## Como rodar
1. Instale as bibliotecas: `pip install -r requirements.txt`
2. Abra `Lista_de_atividades_Aula_09.ipynb` **dentro da pasta do projeto** (a que tem a pasta `fonte`).
3. Rode tudo, de cima para baixo (Run All).

Ordem de execução: instalação, CONFIG, limpeza, Blocos 3 a 9 (funções `extract`, `transform`, `load` e `pipeline`), Bloco 10 (testes com outros parâmetros). A célula de limpeza apaga tudo que o pipeline gera (`data`, `historico_execucoes.csv` e `pipeline.log`). A pasta `fonte` nunca é apagada.

Para gerar tudo de novo sem rodar o notebook inteiro, basta chamar `pipeline()` depois de rodar as células que definem as funções.

## Observações
- O `gold.db` passa de 100 MB, por isso não vai para o Git. Ele é gerado quando o pipeline roda.
- O pipeline é reexecutável: apagando a pasta `data` e rodando `pipeline()` uma vez, a Gold volta idêntica.
