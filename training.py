import numpy as np
import tensorflow as tf

# Dados simulados: índices de medo e preços
fear_index = np.array([i*1.0 for i in range(1024)])  # Exemplo de índice de medo
crypto_prices = np.array([i*2.0 for i in range(1024)])  # Exemplo de preços

# Criar dados de entrada com janela temporal
def create_dataset(data1, data2, window_size=7):
    x, y = [], []
    for i in range(len(data1) - window_size):
        x.append(np.hstack((data1[i:i+window_size], data2[i:i+window_size])))
        y.append(data2[i+window_size])  # Prever o preço futuro
    return np.array(x), np.array(y)

x, y = create_dataset(fear_index, crypto_prices)
x = x.reshape(x.shape[0], x.shape[1], 1)

# Dividir em treino e teste
train_size = int(len(x) * 0.8)
x_train, x_test = x[:train_size], x[train_size:]
y_train, y_test = y[:train_size], y[train_size:]

# Modelo LSTM
model = tf.keras.models.Sequential([
    tf.keras.layers.LSTM(50, return_sequences=True, input_shape=(x_train.shape[1], x_train.shape[2])),
    tf.keras.layers.LSTM(50),
    tf.keras.layers.Dense(1)
])

model.compile(optimizer='adam', loss='mse')
model.fit(x_train, y_train, epochs=20, batch_size=32, validation_data=(x_test, y_test))

# Save model
model.save('trade_model.h5')

# Avaliação
loss = model.evaluate(x_test, y_test)
print(f"Loss: {loss}")