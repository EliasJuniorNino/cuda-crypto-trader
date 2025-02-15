import mysql.connector
from mysql.connector import Error
import pandas as pd
import os
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from datetime import datetime
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

def train_model(df, coin):
    """Treina um modelo de Random Forest e salva o arquivo."""
    try:
        # Separa features (X) e target (y)
        X = df.copy()
        y = df[[f"{coin}_max_price", f"{coin}_min_price"]].shift(-1)

        # Remove a última linha (NaN devido ao shift)
        X = X.iloc[:-1]
        y = y.iloc[:-1]

        # Divide os dados em treino e teste
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Cria o pipeline de pré-processamento e modelo
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', RandomForestRegressor(n_estimators=500, max_depth=50, random_state=42, n_jobs=-1))
        ])

        # Treina o modelo
        pipeline.fit(X_train, y_train)

        # Avalia o modelo
        y_pred = pipeline.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        logging.info(f"Modelo treinado para {coin} com MSE: {mse:.4f}")

        # Salva o modelo
        os.makedirs("models", exist_ok=True)
        model_path = f"models/model_{coin}.pkl"
        joblib.dump(pipeline, model_path)
        logging.info(f"Modelo salvo em {model_path}")

    except Exception as e:
        logging.error(f"Erro ao treinar o modelo para {coin}: {e}")

def main():
    """Função principal para carregar dados e treinar modelos."""
    db_conn = connect_db()
    if db_conn:
        df, coin_names = fetch_data(db_conn)
        if df is not None and coin_names:
            for coin in coin_names:
                train_model(df.copy(), coin)
        db_conn.close()
        logging.info("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    main()