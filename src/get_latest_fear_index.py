import requests
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import env
import time

# Configurações da API
API_KEY = env.coinmarketcap_api_key
API_URL = "https://pro-api.coinmarketcap.com/v3/fear-and-greed/latest"
HEADERS = {"X-CMC_PRO_API_KEY": API_KEY}

# Configurações do Banco de Dados
DB_CONFIG = {
    "host": "localhost",
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
    classification VARCHAR(50) NOT NULL,
    UNIQUE (timestamp)  -- Garantir que o timestamp seja único
);
"""

# Função para converter timestamp
def convert_to_mysql_datetime(iso_timestamp):
    """Converte um timestamp ISO 8601 (ex: '2025-02-13T16:53:10.022Z') para o formato DATETIME(6) do MySQL."""
    try:
        dt = datetime.strptime(iso_timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
        return dt.strftime('%Y-%m-%d %H:%M:%S.%f')  # Formato MySQL com microssegundos
    except ValueError as e:
        print(f"Erro ao converter timestamp: {e}")
        return None

# Função para obter dados da API
def fetch_data():
    """Obtém os dados da API com parâmetros opcionais."""
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "data" in data:
            return data["data"]
        else:
            print("Resposta inesperada da API:", data)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição da API: {e}")
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

# Função para verificar se o registro já existe no banco
def record_exists(cursor, iso_timestamp):
    """Verifica se um registro com o timestamp fornecido já existe no banco de dados."""
    try:
        # Converter para o formato DATETIME(6) do MySQL
        dt = datetime.strptime(iso_timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
        formatted_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S.%f')

        query = "SELECT 1 FROM fear_greed_index WHERE timestamp = %s LIMIT 1"
        cursor.execute(query, (formatted_timestamp,))
        return cursor.fetchone() is not None
    except ValueError as e:
        print(f"Erro ao converter timestamp: {e}")
        return False

# Função para inserir dados no banco
def insert_data(connection, data):
    if not data:
        print("Nenhum dado disponível para inserção.")
        return

    cursor = connection.cursor()
    insert_query = """
    INSERT INTO fear_greed_index (timestamp, value, classification)
    VALUES (%s, %s, %s)
    """

    try:
        converted_timestamp = convert_to_mysql_datetime(data.get("update_time"))
        if converted_timestamp:  # Só adiciona se a conversão for bem-sucedida
            # Verificar se o timestamp já existe no banco
            if not record_exists(cursor, converted_timestamp):
                cursor.execute(insert_query, (converted_timestamp, data["value"], data["value_classification"]))
                connection.commit()
                print(f"{cursor.rowcount} registros inseridos com sucesso!")
            else:
                print(f"Registro com timestamp {converted_timestamp} já existe, ignorando.")
    except Error as e:
        print("Erro ao inserir dados:", e)
    finally:
        cursor.close()

# Executar o fluxo
if __name__ == "__main__":
    while True:
        db_conn = connect_db()
        if db_conn:
            data = fetch_data()  # Buscar até 100 registros
            if data:
                insert_data(db_conn, data)
            db_conn.close()
        print("Esperando 15min para proxima consulta")
        time.sleep(60*60)