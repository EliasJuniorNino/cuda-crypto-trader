import requests
import mysql.connector
from mysql.connector import Error

# Configurações da API Binance
API_URL_BINANCE = "https://api.binance.com/api/v1/exchangeInfo"

# Configurações do Banco de Dados
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "trader",
    "password": "trader",
    "database": "crypto_trader"
}

# Criar tabela para armazenar nomes das criptomoedas
TABLE_CREATION_QUERY = """
CREATE TABLE IF NOT EXISTS cryptos_names (
    id INT AUTO_INCREMENT PRIMARY KEY,
    coin VARCHAR(50) NOT NULL UNIQUE,
    exchange VARCHAR(255) NOT NULL
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

# Função para buscar a lista de criptomoedas da Binance
def fetch_binance_cryptos():
    try:
        response = requests.get(API_URL_BINANCE, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "symbols" in data:
            return [(symbol["baseAsset"]) for symbol in data["symbols"]]
        else:
            print("[Erro] Resposta inesperada da API:", data)
            return None
    except requests.exceptions.RequestException as e:
        print(f"[Erro] Falha ao obter dados da API: {e}")
        return None

# Função para inserir os símbolos no banco de dados
def insert_binance_cryptos(connection, cursor, cryptos):
    if not cryptos:
        print("[Aviso] Nenhum dado para inserir.")
        return

    insert_query = """
    INSERT INTO cryptos_names (coin, exchange)
    VALUES (%s, 'binance')
    ON DUPLICATE KEY UPDATE coin = VALUES(coin);
    """

    try:
        cursor.executemany(insert_query, [(crypto,) for crypto in cryptos])
        connection.commit()
        print(f"[Sucesso] {cursor.rowcount} criptomoedas inseridas/atualizadas com sucesso!")
    except Error as e:
        print(f"[Erro] Falha ao inserir criptomoedas: {e}")

# Executar o fluxo
if __name__ == "__main__":
    db_conn, db_cursor = connect_db()
    if db_conn and db_cursor:
        cryptos = fetch_binance_cryptos()  # Obtém a lista de criptomoedas
        insert_binance_cryptos(db_conn, db_cursor, cryptos)
        db_cursor.close()
        db_conn.close()
