-- ============================================
-- SETUP INICIAL DE COMPARAPP SAAS
-- ============================================

-- 1. Crear base de datos administrativa
CREATE DATABASE IF NOT EXISTS comparapp_admin
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE comparapp_admin;

-- ============================================
-- TABLA DE CLIENTES
-- ============================================

CREATE TABLE IF NOT EXISTS clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    subdominio VARCHAR(100) NOT NULL UNIQUE,
    db_name VARCHAR(100) NOT NULL UNIQUE,
    token VARCHAR(64) NOT NULL UNIQUE,
    activo TINYINT(1) DEFAULT 1,
    fecha_alta DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_vencimiento DATE NULL,
    email_contacto VARCHAR(255) NULL,
    telefono VARCHAR(50) NULL,
    notas TEXT NULL,
    INDEX idx_subdominio (subdominio),
    INDEX idx_token (token),
    INDEX idx_activo (activo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- TABLA DE LOGS DE ACCESO (opcional)
-- ============================================

CREATE TABLE IF NOT EXISTS logs_acceso (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    ip VARCHAR(45) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
    INDEX idx_cliente (cliente_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- INSERTAR CLIENTE DE EJEMPLO
-- ============================================

INSERT INTO clientes (nombre, subdominio, db_name, token, activo)
VALUES 
    ('Comercio Demo', 'demo', 'cliente_demo', 'demo_token_12345abcdef', 1),
    ('Supermercado Los Andes', 'losandes', 'cliente_losandes', 'token_losandes_xyz789', 1);

-- ============================================
-- CREAR BASE DE DATOS PARA CLIENTE DEMO
-- ============================================

CREATE DATABASE IF NOT EXISTS cliente_demo
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE cliente_demo;

-- Tabla de productos (compatible con Unicenta/Chromis)
CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(36) PRIMARY KEY,
    reference VARCHAR(255) NOT NULL,
    code VARCHAR(255) NOT NULL UNIQUE,
    codetype VARCHAR(50) DEFAULT 'EAN-13',
    name VARCHAR(255) NOT NULL,
    pricebuy DECIMAL(10,2) DEFAULT 0.00,
    pricesell DECIMAL(10,2) DEFAULT 0.00,
    category VARCHAR(50) DEFAULT '000',
    taxcat VARCHAR(50) DEFAULT '002',
    stockcost DECIMAL(10,2) DEFAULT 0.00,
    stockvolume DECIMAL(10,3) DEFAULT 0.000,
    stockunits DECIMAL(10,3) DEFAULT 0.000,
    supplier VARCHAR(50) DEFAULT '0',
    texttip TEXT,
    warranty TINYINT(1) DEFAULT 0,
    INDEX idx_code (code),
    INDEX idx_reference (reference)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertar productos de ejemplo
INSERT INTO products (id, reference, code, name, pricebuy, pricesell)
VALUES
    (UUID(), 'COCA-2L', '7790895000010', 'Coca Cola 2L', 1500.00, 2000.00),
    (UUID(), 'PAN-LAC', '7790310012345', 'Pan Lactal', 800.00, 1200.00),
    (UUID(), 'LECHE-1L', '7798024950013', 'Leche Entera 1L', 600.00, 900.00);

-- ============================================
-- CREAR BASE DE DATOS PARA CLIENTE 2
-- ============================================

CREATE DATABASE IF NOT EXISTS cliente_losandes
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE cliente_losandes;

CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(36) PRIMARY KEY,
    reference VARCHAR(255) NOT NULL,
    code VARCHAR(255) NOT NULL UNIQUE,
    codetype VARCHAR(50) DEFAULT 'EAN-13',
    name VARCHAR(255) NOT NULL,
    pricebuy DECIMAL(10,2) DEFAULT 0.00,
    pricesell DECIMAL(10,2) DEFAULT 0.00,
    category VARCHAR(50) DEFAULT '000',
    taxcat VARCHAR(50) DEFAULT '002',
    stockcost DECIMAL(10,2) DEFAULT 0.00,
    stockvolume DECIMAL(10,3) DEFAULT 0.000,
    stockunits DECIMAL(10,3) DEFAULT 0.000,
    supplier VARCHAR(50) DEFAULT '0',
    texttip TEXT,
    warranty TINYINT(1) DEFAULT 0,
    INDEX idx_code (code),
    INDEX idx_reference (reference)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- VERIFICACIÓN
-- ============================================

USE comparapp_admin;
SELECT * FROM clientes;

SHOW DATABASES LIKE 'cliente_%';