import pandas as pd

# Criando um DataFrame simples
df = pd.DataFrame({'A': [5, 4, 3, 2, 1], 'B': [50, 40, 30, 20, 10]})

# Deslocando a coluna 'A' por 2 posições
df['B'] = df['B'].shift(1, fill_value=0)

df = df.iloc[1:]

# O DataFrame após a operação de deslocamento
print(df)