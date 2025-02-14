-- phpMyAdmin SQL Dump
-- version 5.2.2
-- https://www.phpmyadmin.net/
--
-- Host: db_trader
-- Tempo de geração: 14/02/2025 às 14:38
-- Versão do servidor: 9.2.0
-- Versão do PHP: 8.2.27

START TRANSACTION;
SET time_zone = "+00:00";

--
-- Banco de dados: crypto_trader
--

-- --------------------------------------------------------

--
-- Estrutura para tabela binance_cryptos_names
--

CREATE TABLE binance_cryptos_names (
  id int NOT NULL,
  symbol varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela coin_price_history
--

CREATE TABLE coin_price_history (
  id int NOT NULL,
  coin varchar(255) NOT NULL,
  timestamp varchar(255) NOT NULL,
  date datetime DEFAULT NULL,
  price decimal(65,30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela cryptos_names
--

CREATE TABLE cryptos_names (
  id int NOT NULL,
  name varchar(255) NOT NULL,
  symbol varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela fear_greed_index
--

CREATE TABLE fear_greed_index (
  id int NOT NULL,
  timestamp datetime NOT NULL,
  value int NOT NULL,
  classification varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Índices para tabelas despejadas
--

--
-- Índices de tabela binance_cryptos_names
--
ALTER TABLE binance_cryptos_names
  ADD PRIMARY KEY (id),
  ADD UNIQUE KEY symbol (symbol);

--
-- Índices de tabela coin_price_history
--
ALTER TABLE coin_price_history
  ADD PRIMARY KEY (id),
  ADD UNIQUE KEY coin (coin,timestamp);

--
-- Índices de tabela cryptos_names
--
ALTER TABLE cryptos_names
  ADD PRIMARY KEY (id),
  ADD UNIQUE KEY symbol (symbol);

--
-- Índices de tabela fear_greed_index
--
ALTER TABLE fear_greed_index
  ADD PRIMARY KEY (id);

--
-- AUTO_INCREMENT para tabelas despejadas
--

--
-- AUTO_INCREMENT de tabela binance_cryptos_names
--
ALTER TABLE binance_cryptos_names
  MODIFY id int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela coin_price_history
--
ALTER TABLE coin_price_history
  MODIFY id int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela fear_greed_index
--
ALTER TABLE fear_greed_index
  MODIFY id int NOT NULL AUTO_INCREMENT;
COMMIT;
