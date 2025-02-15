import mysql.connector
from mysql.connector import Error
import pandas as pd
import os
import joblib
from sklearn.metrics import mean_squared_error, mean_absolute_error
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Configurações do banco de dados
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
            logging.info("Conexão com o banco de dados estabelecida.")
            return connection
    except Error as e:
        logging.error(f"Erro ao conectar ao banco: {e}")
        return None

def fetch_data(db_connection):
    """Busca os dados do banco de dados e retorna um DataFrame."""
    try:
        cursor = db_connection.cursor()

        # Busca os símbolos das moedas
        cursor.execute("SELECT symbol FROM binance_cryptos_names GROUP BY symbol")
        coin_names = [row[0] for row in cursor.fetchall()]

        # Busca os dados do índice de medo e ganância
        cursor.execute("SELECT * FROM fear_greed_index ORDER BY date ASC")
        fear_data = cursor.fetchall()

        # Busca os preços das moedas
        data = []
        for fear_id, fear_date, fear_value, fear_class in fear_data:
            crypto_values = {'fear_date': fear_date, 'fear_value': fear_value}
            for coin in coin_names:
                crypto_values[f"{coin}_max_price"] = 0
                crypto_values[f"{coin}_min_price"] = 0

            cursor.execute("SELECT * FROM model_params WHERE fear_date = %s", (fear_date,))
            for _id, _fear_date, _fear_value, symbol, max_price, min_price in cursor.fetchall():
                crypto_values[f"{symbol}_max_price"] = max_price
                crypto_values[f"{symbol}_min_price"] = min_price

            if len(crypto_values.keys()) > 2:  # Garante que há dados suficientes
                data.append(crypto_values)

        # Cria o DataFrame
        df = pd.DataFrame(data)

        # Converte a coluna de data para datetime
        df["fear_date"] = pd.to_datetime(df["fear_date"])

        # Extrai features de data
        df["year"] = df["fear_date"].dt.year
        df["month"] = df["fear_date"].dt.month
        df["day"] = df["fear_date"].dt.day
        df["day_of_week"] = df["fear_date"].dt.weekday
        df["timestamp"] = df["fear_date"].astype('int64') // 10**9  # Unix timestamp

        # Remove a coluna de data original
        df.drop(columns=["fear_date"], inplace=True)

        logging.info("Dados carregados com sucesso.")
        return df, coin_names

    except Error as e:
        logging.error(f"Erro ao buscar dados: {e}")
        return None, None

def load_model(coin):
    """Carrega o modelo treinado a partir de um arquivo."""
    try:
        model_path = f"models/model_{coin}.pkl"
        if os.path.exists(model_path):
            model = joblib.load(model_path)
            logging.info(f"Modelo para {coin} carregado com sucesso.")
            return model
        else:
            logging.error(f"Arquivo do modelo não encontrado: {model_path}")
            return None
    except Exception as e:
        logging.error(f"Erro ao carregar o modelo para {coin}: {e}")
        return None

def predict_prices(model, df, coin):
    """Usa o modelo carregado para prever os preços da criptomoeda."""
    try:
        # Separa features (X) e target (y)
        X = df.copy()
        y = df[[f"{coin}_max_price", f"{coin}_min_price"]]

        # Faz as previsões
        y_pred = model.predict(X)

        # Avalia as previsões
        mse = mean_squared_error(y, y_pred)
        mae = mean_absolute_error(y, y_pred)
        logging.info(f"Previsões para {coin} com MSE: {mse:.4f}, MAE: {mae:.4f}")

        return {
            'coin': coin,
            'predict': y_pred[-1]
        }

    except Exception as e:
        logging.error(f"Erro ao fazer previsões para {coin}: {e}")

def main():
    """Função principal para carregar dados, carregar o modelo e prever os preços."""
    db_conn = connect_db()
    if db_conn:
        df, coin_names = fetch_data(db_conn)
        if df is not None:
            for coin in coin_names:
                model = load_model(coin)
                if model is not None:
                    predict_data = predict_prices(model, df, coin)
                    print(predict_data)
        db_conn.close()
        logging.info("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    main()