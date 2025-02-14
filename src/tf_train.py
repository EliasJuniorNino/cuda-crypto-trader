import mysql.connector
from mysql.connector import Error
from datetime import timedelta
import pandas as pd
import os
import joblib
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Habilitar o uso da GPU no TensorFlow para macOS com chip M2
physical_devices = tf.config.list_physical_devices('GPU')
print('physical_devices', physical_devices)
if physical_devices:
    tf.config.set_visible_devices(physical_devices[0], 'GPU')
    print('GPU enabled')

def train_model(df, coin):
    """Treina um modelo de rede neural e salva o arquivo."""
    X = df.drop(columns=[f"{coin}_max_price", f"{coin}_min_price"])
    y = df[[f"{coin}_max_price", f"{coin}_min_price"]].shift(1, fill_value=0)

    X = X.iloc[1:]
    y = y.iloc[1:]

    # Normalizando os dados
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    y_scaled = scaler.fit_transform(y)

    # Definindo o modelo de rede neural
    model = Sequential([
        Dense(64, input_dim=X_scaled.shape[1], activation='relu'),
        Dropout(0.2),
        Dense(32, activation='relu'),
        Dense(2)  # Saída para max_price e min_price
    ])

    model.compile(optimizer='adam', loss='mean_squared_error')

    # Treinando o modelo
    model.fit(X_scaled, y_scaled, epochs=100, batch_size=32, verbose=1)

    # Criando diretório se não existir
    os.makedirs("models", exist_ok=True)

    # Salvando o modelo
    model_path = f"models/model_{coin}.keras"
    model.save(model_path)
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

    cursor.execute("SELECT * FROM fear_greed_index ORDER BY date DESC LIMIT 6")
    for (fear_id, fear_date, fear_value, fear_class) in cursor.fetchall():
        crypto_values = {'fear_date': fear_date, 'fear_value': fear_value}
        for coin in coin_names:
            crypto_values[f"{coin}_max_price"] = 0
            crypto_values[f"{coin}_min_price"] = 0

        cursor.execute("""
            SELECT symbol, 
                   MAX(price) AS max_price, 
                   MIN(price) AS min_price
            FROM coin_price_history
            WHERE date BETWEEN %s AND %s AND symbol in ( 
                SELECT DISTINCT symbol
                FROM binance_cryptos_names
            )
            GROUP BY symbol
        """, (fear_date, fear_date + timedelta(days=1)))
        for (coin, max_price, min_price) in cursor.fetchall():
            crypto_values[f"{coin}_max_price"] = max_price
            crypto_values[f"{coin}_min_price"] = min_price

        if len(crypto_values.keys()) > 2:
            data.append(crypto_values)

    # Criando DataFrame
    df = pd.DataFrame.from_records(data)

    # Convertendo timestamp
    df["fear_date"] = pd.to_datetime(df["fear_date"])
    df["year"] = df["fear_date"].dt.year
    df["month"] = df["fear_date"].dt.month
    df["day"] = df["fear_date"].dt.day
    df["day_of_week"] = df["fear_date"].dt.weekday
    df["timestamp"] = df["fear_date"].astype('int64') // 10 ** 9  # Convertendo timestamp para Unix time
    df.drop(columns=["fear_date"], inplace=True)

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