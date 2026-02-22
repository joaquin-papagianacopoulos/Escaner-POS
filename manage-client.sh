#!/bin/bash

# Script para gestionar clientes en el sistema multi-tenant
# Uso: ./manage-client.sh [add|remove|list|activate|deactivate] [nombre-cliente]

set -e

CLIENTES_DIR="./clientes"
CLIENTES_JSON="$CLIENTES_DIR/clientes.json"
NGINX_CONF_DIR="./nginx/conf.d"

# Crear directorios si no existen
mkdir -p "$CLIENTES_DIR" "$NGINX_CONF_DIR"

# Inicializar archivo JSON si no existe
if [ ! -f "$CLIENTES_JSON" ]; then
    echo "{}" > "$CLIENTES_JSON"
fi

# Función para generar token aleatorio
generate_token() {
    openssl rand -hex 32
}

# Función para generar ID único
generate_id() {
    echo "client_$(date +%s)_$(openssl rand -hex 4)"
}

# Función para agregar cliente
add_client() {
    local client_name="$1"
    local domain="$2"
    
    if [ -z "$client_name" ] || [ -z "$domain" ]; then
        echo "❌ Uso: $0 add NOMBRE_CLIENTE DOMINIO"
        echo "   Ejemplo: $0 add 'Mi Negocio' cliente1.miapp.com"
        exit 1
    fi
    
    local client_id=$(generate_id)
    local token=$(generate_token)
    local database="${client_name//[^a-zA-Z0-9]/_}_db"
    database=$(echo "$database" | tr '[:upper:]' '[:lower:]')
    
    echo "📝 Creando cliente..."
    echo "   ID: $client_id"
    echo "   Nombre: $client_name"
    echo "   Dominio: $domain"
    echo "   Base de datos: $database"
    echo "   Token: $token"
    
    # Agregar al JSON
    python3 << EOF
import json

with open('$CLIENTES_JSON', 'r') as f:
    data = json.load(f)

data['$client_id'] = {
    'name': '$client_name',
    'domain': '$domain',
    'database': '$database',
    'token': '$token',
    'active': True,
    'created_at': '$(date -I)'
}

with open('$CLIENTES_JSON', 'w') as f:
    json.dump(data, f, indent=2)

print("✅ Cliente agregado al archivo de configuración")
EOF

    # Crear configuración de nginx
    cat > "$NGINX_CONF_DIR/${client_id}.conf" << EOF
server {
    listen 80;
    server_name $domain;

    # Redirigir HTTP a HTTPS (descomentar cuando tengas SSL)
    # return 301 https://\$server_name\$request_uri;

    location / {
        proxy_pass http://app:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Certbot challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
}

# Configuración HTTPS (descomentar cuando tengas SSL)
# server {
#     listen 443 ssl;
#     server_name $domain;
#     
#     ssl_certificate /etc/letsencrypt/live/$domain/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/$domain/privkey.pem;
#     
#     location / {
#         proxy_pass http://app:5000;
#         proxy_set_header Host \$host;
#         proxy_set_header X-Real-IP \$remote_addr;
#         proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
#         proxy_set_header X-Forwarded-Proto \$scheme;
#     }
# }
EOF

    echo "✅ Configuración de Nginx creada: $NGINX_CONF_DIR/${client_id}.conf"
    
# Crear base de datos
    echo "🗄️  Creando base de datos..."
    docker-compose exec -T mariadb mariadb -uroot -p"${DB_ROOT_PASSWORD}" << EOSQL
CREATE DATABASE IF NOT EXISTS \`$database\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE \`$database\`;

CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(255) PRIMARY KEY,
    reference VARCHAR(255) DEFAULT NULL,
    code VARCHAR(255) NOT NULL UNIQUE,
    codetype VARCHAR(255) DEFAULT 'EAN-13',
    name VARCHAR(255) NOT NULL,
    pricebuy DECIMAL(10,2) DEFAULT 0.00,
    pricesell DECIMAL(10,2) DEFAULT 0.00,
    category VARCHAR(255) DEFAULT '000',
    taxcat VARCHAR(255) DEFAULT '002',
    stockcost DECIMAL(10,2) DEFAULT 0.00,
    stockvolume DECIMAL(10,2) DEFAULT 0.00,
    stockunits DECIMAL(10,2) DEFAULT 0.00,
    supplier VARCHAR(255) DEFAULT '0',
    texttip TEXT,
    warranty TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_code (code),
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
EOSQL

    echo "✅ Base de datos creada"
    
    # Recargar nginx
    echo "🔄 Recargando Nginx..."
    docker-compose exec nginx nginx -s reload
    
    echo ""
    echo "🎉 ¡Cliente creado exitosamente!"
    echo ""
    echo "📋 INFORMACIÓN DEL CLIENTE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🆔 ID:       $client_id"
    echo "👤 Nombre:   $client_name"
    echo "🌐 Dominio:  $domain"
    echo "🗄️  Database: $database"
    echo "🔑 Token:    $token"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📱 URL para el cliente:"
    echo "   http://$domain?token=$token"
    echo ""
    echo "⚠️  IMPORTANTE: Guarda el token en un lugar seguro."
    echo "   El cliente lo necesitará para acceder."
}

# Función para desactivar cliente
deactivate_client() {
    local client_id="$1"
    
    if [ -z "$client_id" ]; then
        echo "❌ Uso: $0 deactivate CLIENT_ID"
        exit 1
    fi
    
    python3 << EOF
import json

with open('$CLIENTES_JSON', 'r') as f:
    data = json.load(f)

if '$client_id' in data:
    data['$client_id']['active'] = False
    with open('$CLIENTES_JSON', 'w') as f:
        json.dump(data, f, indent=2)
    print("✅ Cliente desactivado: $client_id")
else:
    print("❌ Cliente no encontrado: $client_id")
EOF

    # Reiniciar app para recargar configuración
    docker-compose restart app
}

# Función para activar cliente
activate_client() {
    local client_id="$1"
    
    if [ -z "$client_id" ]; then
        echo "❌ Uso: $0 activate CLIENT_ID"
        exit 1
    fi
    
    python3 << EOF
import json

with open('$CLIENTES_JSON', 'r') as f:
    data = json.load(f)

if '$client_id' in data:
    data['$client_id']['active'] = True
    with open('$CLIENTES_JSON', 'w') as f:
        json.dump(data, f, indent=2)
    print("✅ Cliente activado: $client_id")
else:
    print("❌ Cliente no encontrado: $client_id")
EOF

    # Reiniciar app para recargar configuración
    docker-compose restart app
}

# Función para listar clientes
list_clients() {
    python3 << 'EOF'
import json

try:
    with open('./clientes/clientes.json', 'r') as f:
        data = json.load(f)
    
    if not data:
        print("📦 No hay clientes registrados")
        exit(0)
    
    print("📋 LISTA DE CLIENTES")
    print("=" * 80)
    
    for client_id, info in data.items():
        status = "✅ ACTIVO" if info.get('active', True) else "❌ INACTIVO"
        print(f"\n🆔 ID:       {client_id}")
        print(f"👤 Nombre:   {info.get('name')}")
        print(f"🌐 Dominio:  {info.get('domain')}")
        print(f"🗄️  Database: {info.get('database')}")
        print(f"🔑 Token:    {info.get('token')}")
        print(f"📅 Creado:   {info.get('created_at', 'N/A')}")
        print(f"📊 Estado:   {status}")
        print(f"🔗 URL:      http://{info.get('domain')}?token={info.get('token')}")
    
    print("\n" + "=" * 80)
except FileNotFoundError:
    print("📦 No hay clientes registrados")
except Exception as e:
    print(f"❌ Error: {e}")
EOF
}

# Menú principal
case "$1" in
    add)
        add_client "$2" "$3"
        ;;
    deactivate)
        deactivate_client "$2"
        ;;
    activate)
        activate_client "$2"
        ;;
    list)
        list_clients
        ;;
    *)
        echo "📚 Uso: $0 {add|deactivate|activate|list} [argumentos]"
        echo ""
        echo "Comandos disponibles:"
        echo "  add NOMBRE DOMINIO    - Agregar nuevo cliente"
        echo "  deactivate CLIENT_ID  - Desactivar cliente (revoca acceso)"
        echo "  activate CLIENT_ID    - Reactivar cliente"
        echo "  list                  - Listar todos los clientes"
        echo ""
        echo "Ejemplos:"
        echo "  $0 add 'Supermercado Central' super1.miapp.com"
        echo "  $0 deactivate client_1234567890_a1b2c3d4"
        echo "  $0 list"
        exit 1
        ;;
esac