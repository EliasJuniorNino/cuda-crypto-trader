import pandas as pd

# Criando um DataFrame simples
df = pd.DataFrame(
    {'date':   [5,  4,  3,  2,  1],
     'fear':   [50, 40, 30, 20, 10],
     'price':  [50, 40, 30, 20, 10]})

# Deslocando a coluna 'A' por 2 posições
df['price'] = df['price'].shift(1, fill_value=0)

df = df.iloc[1:]

# O DataFrame após a operação de deslocamento
print(df)