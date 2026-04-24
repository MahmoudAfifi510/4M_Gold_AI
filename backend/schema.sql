CREATE DATABASE IF NOT EXISTS `4m_gold_ai` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `4m_gold_ai`;

CREATE TABLE IF NOT EXISTS `users` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `first_name` VARCHAR(100) NOT NULL,
  `last_name` VARCHAR(100) NOT NULL,
  `username` VARCHAR(100) NOT NULL,
  `phone_number` VARCHAR(30) NOT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_username` (`username`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `historical_market_data` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `market_date` DATE NOT NULL,
  `gold_price` DECIMAL(18,6) NOT NULL,
  `oil_price` DECIMAL(18,6) NOT NULL,
  `usd_index` DECIMAL(18,6) NOT NULL,
  `source` VARCHAR(50) NOT NULL DEFAULT 'alpha_vantage',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_market_date` (`market_date`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `market_data_sync_logs` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `sync_type` VARCHAR(50) NOT NULL,
  `sync_date` DATE NOT NULL,
  `market_date` DATE NULL,
  `api_calls_used` INT NOT NULL DEFAULT 0,
  `status` VARCHAR(20) NOT NULL,
  `message` VARCHAR(500) NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_sync_logs_sync_date` (`sync_date`),
  KEY `idx_sync_logs_market_date` (`market_date`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `gold_buy_transactions` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `weight_oz` DECIMAL(18,4) NOT NULL,
  `remaining_weight_oz` DECIMAL(18,4) NOT NULL,
  `karat` INT NOT NULL,
  `price` DECIMAL(18,6) NOT NULL,
  `transaction_date` DATE NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_transactions_user_id` (`user_id`),
  CONSTRAINT `fk_transactions_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `gold_sale_transactions` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `buy_transaction_id` BIGINT NOT NULL,
  `sell_weight_oz` DECIMAL(18,4) NOT NULL,
  `price` DECIMAL(18,6) NOT NULL,
  `profit_loss` DECIMAL(18,6) NOT NULL,
  `transaction_date` DATE NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_sales_user_id` (`user_id`),
  KEY `idx_sales_buy_transaction_id` (`buy_transaction_id`),
  CONSTRAINT `fk_sales_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_sales_buy_transaction` FOREIGN KEY (`buy_transaction_id`) REFERENCES `gold_buy_transactions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `predictions` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `prediction_date` DATE NOT NULL,
  `base_date` DATE NOT NULL,
  `up_probability` DECIMAL(6,3) NOT NULL,
  `down_probability` DECIMAL(6,3) NOT NULL,
  `direction` VARCHAR(10) NOT NULL,
  `model_version` VARCHAR(50) NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_predictions_date` (`prediction_date`)
) ENGINE=InnoDB;
