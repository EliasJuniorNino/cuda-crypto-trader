import requests
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import env

# Configurações da API
API_KEY = env.coinmarketcap_api_key
API_URL = "https://pro-api.coinmarketcap.com/v3/fear-and-greed/historical"
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
def convert_to_mysql_datetime(epoch_timestamp):
    """Converte um timestamp Unix (segundos) para o formato DATETIME(6) do MySQL."""
    try:
        dt = datetime.utcfromtimestamp(int(epoch_timestamp))
        return dt.strftime('%Y-%m-%d %H:%M:%S.%f')  # Formato com microssegundos
    except (ValueError, TypeError) as e:
        print(f"Erro ao converter timestamp: {e}")
        return None

# Função para obter dados da API
def fetch_data(start=None, limit=50):
    """Obtém os dados da API com parâmetros opcionais."""
    params = {"limit": limit}
    if start:
        params["start"] = start

    try:
        response = requests.get(API_URL, headers=HEADERS, params=params, timeout=10)
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
def record_exists(cursor, timestamp):
    query = "SELECT 1 FROM fear_greed_index WHERE timestamp = %s LIMIT 1"
    cursor.execute(query, (timestamp,))
    return cursor.fetchone() is not None

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

    records = []
    for item in data:
        converted_timestamp = convert_to_mysql_datetime(item.get("timestamp"))
        if converted_timestamp:  # Só adiciona se a conversão for bem-sucedida
            # Verificar se o timestamp já existe no banco
            if not record_exists(cursor, converted_timestamp):
                records.append((converted_timestamp, item["value"], item["value_classification"]))
            else:
                print(f"Registro com timestamp {converted_timestamp} já existe, ignorando.")

    try:
        if records:
            cursor.executemany(insert_query, records)
            connection.commit()
            print(f"{cursor.rowcount} registros inseridos com sucesso!")
        else:
            print("Nenhum registro válido foi encontrado.")
    except Error as e:
        print("Erro ao inserir dados:", e)
    finally:
        cursor.close()

# Executar o fluxo
if __name__ == "__main__":
    db_conn = connect_db()
    if db_conn:
        data = fetch_data(limit=100)  # Buscar até 100 registros
        if data:
            insert_data(db_conn, data)
        db_conn.close()