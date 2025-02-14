import mysql.connector
from mysql.connector import Error
from datetime import timedelta
import pandas as pd
import os
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline


def train_model(df, coin):
    """Treina um modelo de Random Forest e salva o arquivo."""
    X = df.drop(columns=[f"{coin}_max_price", f"{coin}_min_price"])
    y = df[[f"{coin}_max_price", f"{coin}_min_price"]]

    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('model', RandomForestRegressor(n_estimators=200, max_depth=20, random_state=42, n_jobs=-1))
    ])

    pipeline.fit(X, y)

    # Criando diretório se não existir
    os.makedirs("models", exist_ok=True)

    # Salvando o modelo
    model_path = f"models/model_{coin}.pkl"
    joblib.dump(pipeline, model_path)
    print(f"Modelo salvo em {model_path}")


DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "trader",
    "password": "trader",
    "database": "crypto_trader"
}


def connect_db():
    """Conecta ao banco de dados e retorna a conexão."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print("Erro ao conectar ao banco:", e)
        return None


def get_data(db_connection):
    """Busca os dados do banco, realiza pré-processamento e treina modelos para cada moeda."""
    cursor = db_connection.cursor()

    data = []
    column_names = ['fear_timestamp', 'fear_value']
    coin_names = []

    cursor.execute("SELECT symbol FROM binance_cryptos_names GROUP BY symbol")
    for (coin,) in cursor.fetchall():
        coin_names.append(coin)
        column_names.append(f"{coin}_max_price")
        column_names.append(f"{coin}_min_price")

    cursor.execute("SELECT * FROM fear_greed_index ORDER BY timestamp DESC LIMIT 6")
    for (fear_id, fear_timestamp, fear_value, fear_class) in cursor.fetchall():
        params = (
            fear_timestamp,
            fear_timestamp + timedelta(days=1)
        )
        cursor.execute("""
            SELECT coin, 
                   MAX(price) AS max_price, 
                   MIN(price) AS min_price
            FROM coin_price_history
            WHERE date BETWEEN %s AND %s AND coin in ( 
                SELECT DISTINCT symbol
                FROM binance_cryptos_names 
            )
            GROUP BY coin
        """, params)

        crypto_values = {'fear_timestamp': fear_timestamp, 'fear_value': fear_value}
        for coin in coin_names:
            crypto_values[f"{coin}_max_price"] = 0
            crypto_values[f"{coin}_min_price"] = 0

        for (coin, max_price, min_price) in cursor.fetchall():
            crypto_values[f"{coin}_max_price"] = max_price
            crypto_values[f"{coin}_min_price"] = min_price

        if len(crypto_values.keys()) > 2:
            data.append(crypto_values)

    # Criando DataFrame
    df = pd.DataFrame.from_records(data)

    # Convertendo timestamp
    df["fear_timestamp"] = pd.to_datetime(df["fear_timestamp"])
    df["year"] = df["fear_timestamp"].dt.year
    df["month"] = df["fear_timestamp"].dt.month
    df["day"] = df["fear_timestamp"].dt.day
    df["day_of_week"] = df["fear_timestamp"].dt.weekday
    df["timestamp"] = df["fear_timestamp"].astype('int64') // 10 ** 9  # Convertendo timestamp para Unix time
    df.drop(columns=["fear_timestamp"], inplace=True)

    # Normalizando dados numéricos (exceto as colunas de preço)
    features_to_normalize = [col for col in df.columns if col not in column_names]
    scaler = StandardScaler()
    df[features_to_normalize] = scaler.fit_transform(df[features_to_normalize])

    # Treinando modelo para cada moeda
    for coin in coin_names:
        train_model(df.copy(), coin)


if __name__ == "__main__":
    db_conn = connect_db()
    if db_conn:
        get_data(db_conn)
        db_conn.close()