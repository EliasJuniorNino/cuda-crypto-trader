from datetime import timedelta
import mysql.connector
from mysql.connector import Error
import pandas as pd
import numpy as np
import os
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error

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


def get_test_data(db_connection):
    """Busca os dados do banco, realiza pré-processamento e retorna DataFrame com as moedas."""
    cursor = db_connection.cursor()

    data = []
    column_names = ['fear_timestamp', 'fear_value']
    coin_names = []

    cursor.execute("SELECT symbol FROM binance_cryptos_names GROUP BY symbol")
    for (coin_name,) in cursor.fetchall():
        coin_names.append(coin_name)
        column_names.append(f"{coin_name}_max_price")
        column_names.append(f"{coin_name}_min_price")

    cursor.execute("SELECT * FROM fear_greed_index ORDER BY timestamp DESC LIMIT 14")
    for (fear_id, fear_timestamp, fear_value, fear_class) in cursor.fetchall():
        params = (fear_timestamp, fear_timestamp + timedelta(days=1))

        cursor.execute("""
            SELECT coin, 
                   MAX(price) AS max_price, 
                   MIN(price) AS min_price
            FROM coin_price_history
            WHERE date BETWEEN %s AND %s 
            AND coin IN (SELECT DISTINCT symbol FROM binance_cryptos_names)
            GROUP BY coin
        """, params)

        crypto_values = {'fear_timestamp': fear_timestamp, 'fear_value': fear_value}

        for coin_name in coin_names:
            crypto_values[f"{coin_name}_max_price"] = 0
            crypto_values[f"{coin_name}_min_price"] = 0

        for (coin_name, max_price, min_price) in cursor.fetchall():
            crypto_values[f"{coin_name}_max_price"] = max_price
            crypto_values[f"{coin_name}_min_price"] = min_price

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

    return df, coin_names


def test_and_predict(df, coin):
    """Carrega o modelo salvo, valida com novos dados e gera previsões."""
    model_path = f"models/model_{coin}.pkl"

    if not os.path.exists(model_path):
        print(f"❌ Modelo para {coin} não encontrado! Pulei a validação.")
        return None, None

    print(f"\n🔍 Testando e prevendo para {coin}...")

    # Carrega o modelo salvo
    model = joblib.load(model_path)

    # Separando features (X) e valores reais (y)
    X_test = df.drop(columns=[f"{coin}_max_price", f"{coin}_min_price"])
    y_real = df[[f"{coin}_max_price", f"{coin}_min_price"]]

    # Normalizando os dados de entrada (o modelo já contém um scaler)
    X_test = model.named_steps['scaler'].transform(X_test)

    # Fazendo previsões
    y_pred = model.named_steps['model'].predict(X_test)

    # Calculando métricas
    mae = mean_absolute_error(y_real, y_pred)
    rmse = np.sqrt(mean_squared_error(y_real, y_pred))

    print(f"📊 Resultados para {coin}:")
    print(f"   MAE:  {mae:.6f}")
    print(f"   RMSE: {rmse:.6f}\n")

    # Criando um DataFrame com os resultados reais vs previstos
    predictions = pd.DataFrame(y_real.copy())
    predictions["pred_max_price"] = y_pred[:, 0]
    predictions["pred_min_price"] = y_pred[:, 1]

    return predictions, coin


if __name__ == "__main__":
    db_conn = connect_db()
    if db_conn:
        df, coin_names = get_test_data(db_conn)
        db_conn.close()

        all_predictions = []

        # Testando e prevendo cada moeda
        for coin in coin_names:
            predictions, coin_name = test_and_predict(df.copy(), coin)
            if predictions is not None:
                predictions["coin"] = coin_name
                all_predictions.append(predictions)

        # Salvando previsões em CSV
        if all_predictions:
            final_predictions = pd.concat(all_predictions, ignore_index=True)
            final_predictions.to_csv("predictions.csv", index=False)
            print("📂 Previsões salvas em 'predictions.csv'.")