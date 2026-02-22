# 🏢 ComparApp SaaS - Sistema Multicliente de Gestión de Precios

Sistema web para actualización centralizada de precios que los sistemas POS consumen vía API.

---

## 🎯 Características

✅ **Multicliente**: Un cliente = un subdominio = una base de datos  
✅ **Autenticación simple**: Token Bearer por cliente  
✅ **Aislamiento total**: Cada cliente tiene su propia BD  
✅ **Alta/baja instantánea**: Activar/desactivar clientes sin reiniciar  
✅ **API REST**: Endpoints para POS y administración web  
✅ **SSL automático**: Let's Encrypt con wildcard subdominios  

---

## 🏗️ Arquitectura

```
comparappargentina.com          → Admin/Landing
cliente1.comparappargentina.com → Cliente 1
cliente2.comparappargentina.com → Cliente 2
```

### Base de Datos

- **`comparapp_admin`**: Tabla de clientes, logs, tokens
- **`cliente_X`**: Una BD por cliente con tabla `products`

### Flujo de Autenticación

1. Request llega a `cliente1.comparappargentina.com`
2. Nginx pasa Host header a Flask
3. Flask extrae subdominio → busca cliente en `comparapp_admin`
4. Valida token del header `Authorization: Bearer XXX`
5. Si válido → conecta a `cliente1_db` y procesa request
6. Si inválido → 401/403

---

## 🚀 Instalación

### 1. Requisitos Previos

```bash
# Instalar dependencias
apt update
apt install -y docker docker-compose python3-pip mysql-client

# Python dependencies
pip3 install flask pymysql gunicorn
```

### 2. Configurar Base de Datos

```bash
# Conectar a MySQL
mysql -u root -p

# Ejecutar script de setup
source setup_database.sql
```

Esto crea:
- BD `comparapp_admin` con tabla de clientes
- 2 clientes de ejemplo con sus BDs

### 3. Variables de Entorno

Crear `.env`:

```bash
MYSQL_ROOT_PASSWORD=tu_password_seguro
FLASK_SECRET_KEY=tu_secret_key_random
```

### 4. Configurar DNS Wildcard

En tu proveedor de DNS (Cloudflare, Route53, etc.):

```
Type    Name                          Value
A       comparappargentina.com        123.45.67.89
A       *.comparappargentina.com      123.45.67.89
```

### 5. Obtener Certificado SSL Wildcard

```bash
# Instalar certbot
apt install certbot

# Obtener certificado wildcard (requiere validación DNS manual)
certbot certonly --manual --preferred-challenges dns \
  -d comparappargentina.com \
  -d *.comparappargentina.com

# Seguir instrucciones para agregar registro TXT en DNS
```

### 6. Iniciar Servicios

```bash
# Con Docker Compose
docker-compose up -d

# O manualmente
python3 app.py
```

---

## 🔧 Administración de Clientes

### CLI de Administración

```bash
python3 admin_cliente.py
```

**Menú de opciones:**

1. **Listar clientes**: Ver todos los clientes activos e inactivos
2. **Crear cliente**: Alta de nuevo cliente con BD automática
3. **Ver token**: Mostrar token de acceso
4. **Cambiar token**: Generar nuevo token
5. **Activar/Desactivar**: Control instantáneo de acceso
6. **Eliminar cliente**: Borra cliente y su BD (irreversible)

### Crear Cliente Nuevo

```bash
# Ejecutar script
python3 admin_cliente.py

# Seleccionar opción 2
📝 Nombre del cliente: Supermercado San Martin
🌐 Subdominio: sanmartin

# El sistema crea:
✅ Base de datos: cliente_sanmartin
✅ Tabla products
✅ Token: abc123xyz789...
✅ URL: https://sanmartin.comparappargentina.com
```

**Entregar al cliente:**
- URL de acceso
- Token de autenticación

---

## 📡 API Reference

### Autenticación

Todos los endpoints protegidos requieren:

```bash
Authorization: Bearer <token_del_cliente>
Host: <subdominio>.comparappargentina.com
```

### Endpoints Principales

#### 1. Obtener Producto

```bash
GET /api/producto/<codigo>
```

**Respuesta:**
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

#### 2. Guardar/Actualizar Producto

```bash
POST /api/producto
Content-Type: application/json

{
  "code": "7790895000010",
  "name": "Coca Cola 2.25L",
  "pricebuy": 1600,
  "pricesell": 2100,
  "margen": 30
}
```

#### 3. Eliminar Producto

```bash
DELETE /api/producto/<codigo>
```

#### 4. Listar Productos

```bash
GET /api/productos
```

#### 5. Endpoint para POS (consulta pública)

```bash
GET /api/pos/precio/<codigo>
```

**Respuesta simplificada para POS:**
```json
{
  "encontrado": true,
  "codigo": "7790895000010",
  "nombre": "Coca Cola 2L",
  "precio": 2000.00
}
```

#### 6. Info del Cliente

```bash
GET /api/info-cliente
```

---

## 🔒 Seguridad

### Implementado

✅ **HTTPS obligatorio**: Certificados SSL Let's Encrypt  
✅ **Token único por cliente**: 32 caracteres random  
✅ **Validación de subdominio**: No se puede acceder a datos de otro cliente  
✅ **Rate limiting**: Nginx limita requests por IP  
✅ **Headers de seguridad**: HSTS, X-Frame-Options, etc.  
✅ **Logs de acceso**: Auditoría opcional por cliente  

### Recomendaciones

- **Rotar tokens periódicamente** (cada 3-6 meses)
- **Monitorear logs** de `comparapp_admin.logs_acceso`
- **Backups automáticos** de cada BD de cliente
- **Firewall**: Solo puertos 80, 443, 22 abiertos
- **VPN opcional**: Para acceso administrativo

---

## 📊 Monitoreo

### Health Check

```bash
curl https://cliente.comparappargentina.com/api/health
```

Respuesta:
```json
{
  "status": "ok",
  "service": "comparapp"
}
```

### Logs

```bash
# Logs de aplicación
docker logs -f comparapp_app

# Logs de Nginx
docker logs -f comparapp_nginx

# Logs de MySQL
docker logs -f comparapp_mysql
```

### Métricas en Base de Datos

```sql
USE comparapp_admin;

-- Total de clientes
SELECT COUNT(*) FROM clientes;

-- Clientes activos
SELECT COUNT(*) FROM clientes WHERE activo = 1;

-- Accesos en última hora
SELECT cliente_id, COUNT(*) as requests
FROM logs_acceso
WHERE timestamp > NOW() - INTERVAL 1 HOUR
GROUP BY cliente_id;
```

---

## 🔄 Integración con POS

### Ejemplo: Unicenta/Chromis

Modificar script SQL de Unicenta para consultar API:

```python
import requests

def obtener_precio(codigo_barras):
    url = f"https://micliente.comparappargentina.com/api/pos/precio/{codigo_barras}"
    headers = {
        "Authorization": "Bearer mi_token_secreto"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.ok:
            data = response.json()
            if data['encontrado']:
                return data['precio']
    except:
        pass
    
    # Fallback a precio local si API falla
    return consultar_precio_local(codigo_barras)
```

---

## 🛠️ Mantenimiento

### Backup Automático

Crear script `backup.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Backup de admin
mysqldump -u root -p comparapp_admin > $BACKUP_DIR/admin_$DATE.sql

# Backup de cada cliente
mysql -u root -p -e "SHOW DATABASES LIKE 'cliente_%'" | grep cliente_ | while read db; do
    mysqldump -u root -p $db > $BACKUP_DIR/${db}_$DATE.sql
done

# Comprimir
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz $BACKUP_DIR/*.sql
rm $BACKUP_DIR/*.sql

# Subir a S3/Drive (opcional)
# rclone copy $BACKUP_DIR/backup_$DATE.tar.gz remote:comparapp-backups/
```

Agregar a cron:
```bash
crontab -e
0 3 * * * /root/backup.sh
```

### Actualización de Código

```bash
# Pull cambios
git pull origin main

# Reiniciar servicios
docker-compose restart app nginx
```

---

## 🐛 Troubleshooting

### Error: Cliente no encontrado

**Causa**: Subdominio no existe en `comparapp_admin.clientes`  
**Solución**: Verificar registro en BD o crear cliente

```sql
SELECT * FROM comparapp_admin.clientes WHERE subdominio = 'micliente';
```

### Error: Token inválido

**Causa**: Token incorrecto o cliente desactivado  
**Solución**: Regenerar token o activar cliente

```bash
python3 admin_cliente.py
# Opción 4: Cambiar token
```

### Error: Base de datos no existe

**Causa**: BD del cliente no fue creada  
**Solución**: Crearla manualmente

```sql
CREATE DATABASE cliente_nombre CHARACTER SET utf8mb4;
USE cliente_nombre;
-- Ejecutar script de tabla products
```

### Error: SSL certificate

**Causa**: Certificado expirado o no renovado  
**Solución**: Renovar con certbot

```bash
certbot renew --force-renewal
docker-compose restart nginx
```

---

## 📈 Escalabilidad

### Cuando tener más de 50 clientes:

1. **Separar BD por servidor**: Mover clientes grandes a instancias dedicadas
2. **Load Balancer**: Nginx + múltiples instancias Flask
3. **Redis para caché**: Cachear consultas frecuentes
4. **CDN**: Para archivos estáticos

### Ejemplo con Redis:

```python
import redis
r = redis.Redis(host='localhost', port=6379)

def get_producto_cached(code):
    cached = r.get(f"product:{code}")
    if cached:
        return json.loads(cached)
    
    producto = execute_client_query(...)
    r.setex(f"product:{code}", 3600, json.dumps(producto))
    return producto
```

---

## 📝 Licencia

Propietario - ComparApp Argentina

---

## 📞 Soporte

- **Email**: soporte@comparappargentina.com
- **WhatsApp**: +54 9 11 64703346
- **Documentación**: https://docs.comparappargentina.com#   E s c a n e r - P O S  
 