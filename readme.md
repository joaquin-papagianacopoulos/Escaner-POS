<div align="center">

```
███████╗███████╗ ██████╗ █████╗ ███╗   ██╗███████╗██████╗       ██████╗  ██████╗ ███████╗
██╔════╝██╔════╝██╔════╝██╔══██╗████╗  ██║██╔════╝██╔══██╗      ██╔══██╗██╔═══██╗██╔════╝
█████╗  ███████╗██║     ███████║██╔██╗ ██║█████╗  ██████╔╝█████╗██████╔╝██║   ██║███████╗
██╔══╝  ╚════██║██║     ██╔══██║██║╚██╗██║██╔══╝  ██╔══██╗╚════╝██╔═══╝ ██║   ██║╚════██║
███████╗███████║╚██████╗██║  ██║██║ ╚████║███████╗██║  ██║      ██║     ╚██████╔╝███████║
╚══════╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝      ╚═╝      ╚═════╝ ╚══════╝
```

### 🔍 Sistema Web de Escaneo de Códigos de Barras con Integración POS

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://mysql.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/Licencia-Propietaria-red?style=for-the-badge)](.)

<br/>

> **Actualizá precios, gestioná productos y generá etiquetas de góndola**  
> **desde cualquier dispositivo — sin tocar la computadora de caja.**

</div>

---

## 📌 ¿Qué es Escaner-POS?

**Escaner-POS** es una plataforma SaaS **multicliente** que permite a supermercados y comercios gestionar su catálogo de productos de forma centralizada. El sistema POS del local consume los precios actualizados vía API REST, eliminando la necesidad de intervenir físicamente en la caja registradora para cada cambio.

```
          CELULAR / TABLET                     CAJA REGISTRADORA
        ┌─────────────────┐                   ┌──────────────────┐
        │  📷 Escanear     │                   │   💻 POS / Caja  │
        │  código barras  │                   │                  │
        │                 │   ┌───────────┐   │  consulta precio │
        │  ✏️  Editar       ├──►│  API REST │◄──│  en tiempo real  │
        │  precio/nombre  │   │  (Flask)  │   │                  │
        │                 │   └─────┬─────┘   └──────────────────┘
        │  🏷️  Generar      │         │
        │  etiqueta PDF   │   ┌─────▼─────┐
        └─────────────────┘   │  MySQL DB │
                              │ por cliente│
                              └───────────┘
```

---

## ✨ Características Principales

| Feature | Descripción |
|---|---|
| 📱 **Escáner Web** | Lector de códigos de barras desde la cámara del celular/tablet, sin apps nativas |
| 🏢 **Multicliente** | Cada comercio tiene su propio subdominio y base de datos aislada |
| 🔄 **Sincronización en tiempo real** | Los cambios de precio se reflejan instantáneamente en el POS |
| 🏷️ **Generador de etiquetas** | Crea etiquetas de góndola en PDF listas para imprimir |
| 🔐 **Auth por Bearer Token** | Cada cliente tiene un token único de 32 caracteres |
| 🌐 **SSL automático** | Certificados wildcard via Let's Encrypt por subdominio |
| ⚡ **Alta/baja instantánea** | Activar o desactivar clientes sin reiniciar el servidor |
| 📊 **Logs de acceso** | Auditoría completa de requests por cliente |

---

## 🏗️ Arquitectura

```
comparappargentina.com                →  Panel de administración / Landing
cliente1.comparappargentina.com       →  Supermercado 1
cliente2.comparappargentina.com       →  Supermercado 2
sanmartin.comparappargentina.com      →  Supermercado San Martín
          ...
```

### Flujo de autenticación

```
  Request  ──►  Nginx  ──►  Flask extrae subdominio
                               │
                               ▼
                    Busca cliente en comparapp_admin
                               │
                    ┌──────────┴──────────┐
                    │  Valida Bearer Token │
                    └──────────┬──────────┘
                               │
              ┌────────────────┴─────────────────┐
              │ ✅ Válido                          │ ❌ Inválido
              ▼                                   ▼
    Conecta a cliente_X_db                   401 / 403
    y procesa el request
```

### Base de datos

- **`comparapp_admin`** — Tabla de clientes, tokens, logs de acceso
- **`cliente_X`** — Una base de datos independiente por cliente con tabla `products`

---

## 🚀 Instalación

### Requisitos previos

```bash
apt update
apt install -y docker docker-compose python3-pip mysql-client

pip3 install flask pymysql gunicorn
```

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/escaner-pos.git
cd escaner-pos
```

### 2. Variables de entorno

Crear archivo `.env` en la raíz:

```env
MYSQL_ROOT_PASSWORD=tu_password_seguro
FLASK_SECRET_KEY=tu_secret_key_random
```

### 3. Configurar base de datos

```bash
mysql -u root -p
source setup_database.sql
```

Esto crea automáticamente:
- Base de datos `comparapp_admin` con tabla de clientes
- 2 clientes de ejemplo con sus respectivas bases de datos

### 4. Configurar DNS Wildcard

En tu proveedor DNS (Cloudflare, Route53, etc.):

```
Type    Name                        Value
A       comparappargentina.com      123.45.67.89
A       *.comparappargentina.com    123.45.67.89
```

### 5. Obtener certificado SSL Wildcard

```bash
apt install certbot

certbot certonly --manual --preferred-challenges dns \
  -d comparappargentina.com \
  -d *.comparappargentina.com
```

### 6. Levantar servicios

```bash
# Con Docker Compose (recomendado)
docker-compose up -d

# O directamente
python3 app.py
```

---

## 📡 API Reference

Todos los endpoints requieren:

```http
Authorization: Bearer <token_del_cliente>
Host: <subdominio>.comparappargentina.com
```

### Endpoints

#### `GET /api/producto/<codigo>`
Obtener un producto por código de barras.

```json
{
  "encontrado": true,
  "code": "7790895000010",
  "name": "Coca Cola 2L",
  "pricebuy": 1500.00,
  "pricesell": 2000.00,
  "stockunits": 50
}
```

#### `POST /api/producto`
Crear o actualizar un producto.

```json
{
  "code": "7790895000010",
  "name": "Coca Cola 2.25L",
  "pricebuy": 1600,
  "pricesell": 2100,
  "margen": 30
}
```

#### `DELETE /api/producto/<codigo>`
Eliminar un producto del catálogo.

#### `GET /api/productos`
Listar todos los productos del cliente.

#### `GET /api/pos/precio/<codigo>` — *Endpoint para POS*
Consulta pública simplificada, pensada para integrar directamente con el sistema de caja.

```json
{
  "encontrado": true,
  "codigo": "7790895000010",
  "nombre": "Coca Cola 2L",
  "precio": 2000.00
}
```

#### `GET /api/health`
Health check del servicio.

```json
{ "status": "ok", "service": "comparapp" }
```

---

## 🔧 Administración de Clientes

```bash
python3 admin_cliente.py
```

| Opción | Acción |
|--------|--------|
| 1 | Listar todos los clientes (activos e inactivos) |
| 2 | Crear cliente nuevo con BD automática |
| 3 | Ver token de acceso |
| 4 | Regenerar token |
| 5 | Activar / Desactivar cliente |
| 6 | ⚠️ Eliminar cliente y su BD (irreversible) |

**Ejemplo — dar de alta un cliente:**

```bash
python3 admin_cliente.py
# Seleccionar opción 2

📝 Nombre del cliente: Supermercado San Martin
🌐 Subdominio: sanmartin

✅ Base de datos: cliente_sanmartin
✅ Tabla products creada
✅ Token: abc123xyz789...
✅ URL: https://sanmartin.comparappargentina.com
```

---

## 🔄 Integración con POS

Ejemplo de integración con Unicenta / Chromis u otro sistema POS:

```python
import requests

def obtener_precio(codigo_barras):
    url = f"https://micliente.comparappargentina.com/api/pos/precio/{codigo_barras}"
    headers = {"Authorization": "Bearer mi_token_secreto"}

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.ok:
            data = response.json()
            if data['encontrado']:
                return data['precio']
    except Exception:
        pass

    # Fallback a precio local si la API no responde
    return consultar_precio_local(codigo_barras)
```

---

## 🔒 Seguridad

- ✅ HTTPS obligatorio con certificados Let's Encrypt
- ✅ Token único de 32 caracteres por cliente
- ✅ Validación de subdominio — un cliente no puede acceder a datos de otro
- ✅ Rate limiting configurado en Nginx
- ✅ Headers de seguridad: HSTS, X-Frame-Options, etc.
- ✅ Logs de auditoría por cliente

**Buenas prácticas recomendadas:**
- Rotar tokens cada 3–6 meses
- Mantener solo los puertos 80, 443 y 22 abiertos en el firewall
- Configurar backups automáticos (ver sección de mantenimiento)

---

## 🛠️ Mantenimiento

### Backup automático

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

mysqldump -u root -p comparapp_admin > $BACKUP_DIR/admin_$DATE.sql

mysql -u root -p -e "SHOW DATABASES LIKE 'cliente_%'" | grep cliente_ | while read db; do
    mysqldump -u root -p $db > $BACKUP_DIR/${db}_$DATE.sql
done

tar -czf $BACKUP_DIR/backup_$DATE.tar.gz $BACKUP_DIR/*.sql
rm $BACKUP_DIR/*.sql
```

Agregar a cron para ejecutar diariamente a las 3AM:

```bash
crontab -e
# Agregar:
0 3 * * * /root/backup.sh
```

### Actualizar el código

```bash
git pull origin main
docker-compose restart app nginx
```

### Ver logs en tiempo real

```bash
docker logs -f comparapp_app      # Aplicación Flask
docker logs -f comparapp_nginx    # Nginx
docker logs -f comparapp_mysql    # MySQL
```

---

## 📈 Escalabilidad

Para instalaciones con más de 50 clientes simultáneos:

- **Redis** para cachear consultas frecuentes de productos
- **Load Balancer** con Nginx + múltiples instancias Flask
- **BDs dedicadas** para clientes con alto volumen de requests
- **CDN** para archivos estáticos y PDFs de etiquetas

---

## 🐛 Troubleshooting

<details>
<summary><b>❌ Error: Cliente no encontrado</b></summary>

**Causa:** El subdominio no existe en `comparapp_admin.clientes`

```sql
SELECT * FROM comparapp_admin.clientes WHERE subdominio = 'micliente';
```
Si no aparece, crearlo con `admin_cliente.py` opción 2.
</details>

<details>
<summary><b>❌ Error: Token inválido (401/403)</b></summary>

**Causa:** Token incorrecto o cliente desactivado.

```bash
python3 admin_cliente.py
# Opción 4: Regenerar token
# Opción 5: Verificar que el cliente esté activo
```
</details>

<details>
<summary><b>❌ Error: Base de datos no existe</b></summary>

```sql
CREATE DATABASE cliente_nombre CHARACTER SET utf8mb4;
USE cliente_nombre;
-- Ejecutar script de tabla products
```
</details>

<details>
<summary><b>❌ Error: SSL certificate expirado</b></summary>

```bash
certbot renew --force-renewal
docker-compose restart nginx
```
</details>

---

## 🧰 Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.10+, Flask |
| Base de datos | MySQL 8 |
| Proxy / SSL | Nginx + Let's Encrypt |
| Infraestructura | Docker, Docker Compose |
| Cloud | VPS Ubuntu 24.04 LTS |
| PDF (etiquetas) | ReportLab |
| Frontend | HTML, CSS, JavaScript |

---

## 📞 Contacto

**Joaquin Papagianacopoulos** — Desarrollador & Co-fundador

[![LinkedIn](https://img.shields.io/badge/LinkedIn-joaquinpapagianacopoulos-0077B5?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/joaquinpapagianacopoulos/)
[![Gmail](https://img.shields.io/badge/Gmail-joaquinpapagianacopoulos@gmail.com-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:joaquinpapagianacopoulos@gmail.com)
[![WhatsApp](https://img.shields.io/badge/WhatsApp-%2B54%209%2011%2064703346-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)](https://wa.me/5491164703346)

---

<div align="center">

**Escaner-POS** · Hecho con 🧉 desde Buenos Aires, Argentina

*© 2026 Joaquin Papagianacopoulos — Todos los derechos reservados*

</div>
