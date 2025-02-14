import requests
import mysql.connector
from mysql.connector import Error
import env

# Configurações da API CoinMarketCap
API_KEY = env.coinmarketcap_api_key
API_URL_LISTINGS = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
HEADERS = {"X-CMC_PRO_API_KEY": API_KEY}

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
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    UNIQUE (symbol)  -- Evita duplicações de criptomoedas
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

# Função para buscar a lista de criptomoedas
def fetch_cryptos_list():
    params = {"limit": 5000}  # Limite máximo de criptomoedas a serem listadas

    try:
        response = requests.get(API_URL_LISTINGS, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "data" in data:
            return [(coin["id"], coin["name"], coin["symbol"]) for coin in data["data"]]
        else:
            print("[Erro] Resposta inesperada da API:", data)
            return None
    except requests.exceptions.RequestException as e:
        print(f"[Erro] Falha ao obter dados da API: {e}")
        return None

# Função para inserir as criptomoedas no banco de dados
def insert_cryptos(connection, cursor, cryptos):
    if not cryptos:
        print("[Aviso] Nenhum dado para inserir.")
        return

    insert_query = """
    INSERT INTO cryptos_names (id, name, symbol)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE name = VALUES(name), symbol = VALUES(symbol);
    """

    try:
        cursor.executemany(insert_query, cryptos)
        connection.commit()
        print(f"[Sucesso] {cursor.rowcount} criptomoedas inseridas/atualizadas com sucesso!")
    except Error as e:
        print(f"[Erro] Falha ao inserir criptomoedas: {e}")

# Executar o fluxo
if __name__ == "__main__":
    db_conn, db_cursor = connect_db()
    if db_conn and db_cursor:
        cryptos = fetch_cryptos_list()  # Obtém a lista de criptomoedas
        insert_cryptos(db_conn, db_cursor, cryptos)
        db_cursor.close()
        db_conn.close()