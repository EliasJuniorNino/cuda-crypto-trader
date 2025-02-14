import mysql.connector


def generate_data(connection, cursor):
    # Criar tabela se não existir
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_params (
            id INT AUTO_INCREMENT PRIMARY KEY,
            fear_date DATETIME NOT NULL,
            fear_value INT NOT NULL,
            symbol VARCHAR(255) NOT NULL UNIQUE,
            max_price DECIMAL(65,30) NOT NULL,
            min_price DECIMAL(65,30) NOT NULL
        );
    """)
    connection.commit()

    # Buscar dados otimizados
    cursor.execute("""
        SELECT
            f.date AS fear_date,
            f.value AS fear_value,
            c.symbol AS symbol,
            MAX(h.price) AS max_price,
            MIN(h.price) AS min_price
        FROM fear_greed_index f
        JOIN coin_price_history h ON h.date BETWEEN f.date AND f.date + INTERVAL 1 DAY
        JOIN binance_cryptos_names c ON h.symbol = c.symbol
        GROUP BY f.date, f.value, c.symbol;
    """)

    # Inserir dados em batch
    data_batch = cursor.fetchall()

    if data_batch:
        cursor.executemany("""
            INSERT INTO model_params (fear_date, fear_value, symbol, max_price, min_price)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                fear_date = VALUES(fear_date),
                fear_value = VALUES(fear_value),
                max_price = VALUES(max_price),
                min_price = VALUES(min_price);
        """, data_batch)
        connection.commit()
        print(f"{len(data_batch)} registros inseridos/atualizados.")


# Executar o fluxo
if __name__ == "__main__":
    db_conn = mysql.connector.connect(**{
        "host": "localhost",
        "port": 3306,
        "user": "trader",
        "password": "trader",
        "database": "crypto_trader"
    })

    if db_conn.is_connected():
        db_cur = db_conn.cursor()
        generate_data(db_conn, db_cur)
        db_cur.close()
        db_conn.close()