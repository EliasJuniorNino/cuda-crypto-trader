import requests
import mysql.connector
from mysql.connector import Error
import env

# Configurações da API
API_KEY = env.coinmarketcap_api_key
API_URL = "https://pro-api.coinmarketcap.com/v3/fear-and-greed/historical"
HEADERS = {"X-CMC_PRO_API_KEY": API_KEY}

# Configurações do Banco de Dados
DB_CONFIG = {
    "host": "localhost",  # Nome do serviço no docker-compose
    "port": 3306,
    "user": "trader",
    "password": "trader",
    "database": "crypto_trader"
}

# Criar tabela no MySQL
TABLE_CREATION_QUERY = """
CREATE TABLE IF NOT EXISTS fear_greed_index (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    value INT NOT NULL,
    classification VARCHAR(50) NOT NULL
);
"""


# Função para obter dados da API
def fetch_data():
    response = requests.get(API_URL, headers=HEADERS)
    if response.status_code == 200:
        return response.json()["data"]
    else:
        print("Erro na requisição:", response.status_code, response.text)
        return None


# Função para conectar ao banco de dados
def connect_db():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(TABLE_CREATION_QUERY)
            connection.commit()
            return connection
    except Error as e:
        print("Erro ao conectar ao banco:", e)
        return None


# Função para inserir dados no banco
def insert_data(connection, data):
    cursor = connection.cursor()
    insert_query = """
    INSERT INTO fear_greed_index (timestamp, value, classification)
    VALUES (%s, %s, %s)
    """
    records = [(item["timestamp"], item["value"], item["value_classification"]) for item in data]

    try:
        cursor.executemany(insert_query, records)
        connection.commit()
        print(f"{cursor.rowcount} registros inseridos com sucesso!")
    except Error as e:
        print("Erro ao inserir dados:", e)
    finally:
        cursor.close()


# Executar o fluxo
if __name__ == "__main__":
    db_conn = connect_db()
    if db_conn:
        data = fetch_data()
        if data:
            insert_data(db_conn, data)
        db_conn.close()