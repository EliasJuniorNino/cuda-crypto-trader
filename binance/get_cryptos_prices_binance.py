import requests
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import time

# Configurações do Banco de Dados
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "trader",
    "password": "trader",
    "database": "crypto_trader"
}

# Configuração da API Binance
BINANCE_API_URL = "https://api.binance.com/api/v3/klines"
INTERVAL = "1m"  # Intervalo de tempo
LIMIT = 60*24  # Número de registros a buscar
END_TIME = datetime.combine(datetime.today(), datetime.min.time()) - timedelta(days=7)

# Criar tabela para armazenar o histórico de preços
TABLE_CREATION_QUERY = """
CREATE TABLE IF NOT EXISTS coin_price_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    coin VARCHAR(255) NOT NULL,
    timestamp VARCHAR(255) NOT NULL,
    date datetime NULL,
    price DECIMAL(65,30) NOT NULL,
    UNIQUE (coin, timestamp, date)
);
"""


# Função para conectar ao banco de dados
def connect_db():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(TABLE_CREATION_QUERY)
            connection.commit()
            return connection, cursor
    except Error as e:
        print(f"[Erro] Falha na conexão com o banco: {e}")
        return None, None


# Função para buscar os símbolos das criptomoedas
def fetch_crypto_symbols(cursor):
    cursor.execute("SELECT symbol FROM binance_cryptos_names")
    return [row[0] for row in cursor.fetchall()]


# Função para buscar o histórico de preços de uma criptomoeda na Binance
def fetch_crypto_history(symbol):
    symbol_pair = f"{symbol}USDT"  # Binance usa pares como BTCUSDT, ETHUSDT
    params = {"symbol": symbol_pair, "interval": INTERVAL, "limit": LIMIT, "endTime": int(END_TIME.timestamp() * 1000)}

    try:
        response = requests.get(BINANCE_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Cada entrada contém: [timestamp, open, high, low, close, volume, ...]
        price_history = [{"timestamp": entry[0] // 1000, "price": float(entry[4])} for entry in data]
        return 200, price_history
    except requests.exceptions.RequestException as e:
        print(f"[Erro] Falha ao obter dados da Binance para {symbol}: {e}")
        status = 429
        if e.response != None and e.response.status_code != None:
            status = e.response.status_code
        return status, None


# Função para inserir preços no banco de dados
def insert_price_history(connection, cursor, symbol, price_history):
    if not price_history:
        print(f"[Aviso] Nenhum histórico de preços disponível para {symbol}.")
        return

    insert_query = """
    INSERT INTO coin_price_history (coin, timestamp, date, price)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE price = VALUES(price)
    """
    try:
        for entry in price_history:
            timestamp = entry["timestamp"]
            date = datetime.fromtimestamp(int(timestamp))
            price = entry["price"]
            cursor.execute(insert_query, (symbol, timestamp, date, price))

        connection.commit()
        print(f"[Sucesso] Histórico de {symbol} armazenado com sucesso.")
    except Error as e:
        print(f"[Erro] Falha ao inserir histórico de {symbol}: {e}")


# Executar o fluxo
if __name__ == "__main__":
    db_conn, db_cursor = connect_db()
    if db_conn and db_cursor:
        symbols = fetch_crypto_symbols(db_cursor)  # Obtém os símbolos do banco de dados
        for symbol in symbols:
            status, history = fetch_crypto_history(symbol)
            while history is None and status == 429:
                print(f"[Aviso] Limite de requisições atingido para {symbol}. Tentando novamente em 1 minuto...")
                time.sleep(60)
                status, history = fetch_crypto_history(symbol)

            if history:
                insert_price_history(db_conn, db_cursor, symbol, history)

        db_cursor.close()
        db_conn.close()