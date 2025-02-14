import requests
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import time
import env

# Configurações da API CoinMarketCap
API_KEY = env.coinmarketcap_api_key
API_URL = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest"
HEADERS = {"X-CMC_PRO_API_KEY": API_KEY}

# Configurações do Banco de Dados
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "trader",
    "password": "trader",
    "database": "crypto_trader"
}

# Criar tabela para armazenar o histórico de preços
TABLE_CREATION_QUERY = """
CREATE TABLE IF NOT EXISTS coin_price_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(255) NOT NULL,
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
    cursor.execute("SELECT symbol FROM cryptos_names")
    return [row[0] for row in cursor.fetchall()]


# Função para buscar o preço atual de uma criptomoeda
def fetch_crypto_price(symbol):
    params = {"symbol": symbol, "convert": "USD"}
    try:
        response = requests.get(API_URL, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "data" in data and symbol in data["data"]:
            coin_data = data["data"][symbol][0]  # O primeiro elemento da lista contém os dados
            price = coin_data["quote"]["USD"]["price"]
            return 200,price
        else:
            print(f"[Erro] Resposta inesperada da API para {symbol}:", data)
            return 500,None
    except requests.exceptions.RequestException as e:
        print(f"[Erro] Falha ao obter dados da API para {symbol}: {e}")
        return e.response.status_code,None


# Função para inserir o preço no banco de dados
def insert_price(connection, cursor, symbol, price):
    if price is None:
        print(f"[Aviso] Nenhum preço disponível para {symbol}.")
        return

    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    insert_query = """
    INSERT INTO coin_price_history (coin, timestamp, price)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE price = VALUES(price)  -- Atualiza o preço se o timestamp já existir
    """
    try:
        cursor.execute(insert_query, (symbol, timestamp, price))
        connection.commit()
        print(f"[Sucesso] {symbol} registrado: {price} USD em {timestamp}")
    except Error as e:
        print(f"[Erro] Falha ao inserir dados de {symbol}: {e}")


# Executar o fluxo
if __name__ == "__main__":
    db_conn, db_cursor = connect_db()
    if db_conn and db_cursor:
        symbols = fetch_crypto_symbols(db_cursor)  # Obtém os símbolos do banco de dados
        for symbol in symbols:
            status,price = fetch_crypto_price(symbol)
            while price is None and status == 429:
                print(f"[Aviso] Não foi possível obter o preço de {symbol}. Tentando novamente em 1 minuto...")
                time.sleep(60)  # Espera 1 minuto antes de tentar novamente
                satus,price = fetch_crypto_price(symbol)
            if price is not None:
                insert_price(db_conn, db_cursor, symbol, price)
        db_cursor.close()
        db_conn.close()
