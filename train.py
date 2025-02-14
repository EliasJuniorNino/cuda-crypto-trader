import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Dados fornecidos
data = [
    ("2025-02-12", 35, 0.314, 0.2847),
    ("2025-02-11", 35, 0.01962, 0.01744),
    ("2025-02-10", 35, 0.00807, 0.00734),
    ("2025-02-09", 35, 0.1199, 0.1046),
    ("2025-01-07", 48, 0.7151, 0.6925),
    ("2025-01-06", 61, 0.22512, 0.206),
    ("2024-12-24", 55, 0.001445, 0.000981),
    ("2024-12-24", 55, 0.066, 0.0519),
]

# Criando o DataFrame
df = pd.DataFrame(data, columns=["date", "fear_index", "price_max", "price_min"])

# Convertendo a coluna 'date' para datetime
df["date"] = pd.to_datetime(df["date"])

# Extraindo features da data
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month
df["day"] = df["date"].dt.day
df["day_of_week"] = df["date"].dt.weekday
df["timestamp"] = df["date"].astype("int64") // 10**9

# Removendo a coluna original 'date'
df.drop(columns=["date"], inplace=True)

# Separando X (features) e y (targets)
X = df.drop(columns=["price_max", "price_min"])  # Variáveis de entrada
y = df[["price_max", "price_min"]]  # Valores a serem previstos

# Normalizando os dados
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Dividindo os dados em treino (80%) e teste (20%)
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# Criando o modelo
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Fazendo previsões
y_pred = model.predict(X_test)

# Avaliando o modelo
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print(f"MAE: {mae:.6f}")
print(f"RMSE: {rmse:.6f}")

# Fazendo uma previsão para um novo exemplo
novo_dado = np.array([[35, 2025, 2, 12, 2, 1739299200]])  # Exemplo: Fear index 35, Data 2025-02-12
novo_dado_scaled = scaler.transform(novo_dado)
previsao = model.predict(novo_dado_scaled)
print(f"Previsão de preço: {previsao}")