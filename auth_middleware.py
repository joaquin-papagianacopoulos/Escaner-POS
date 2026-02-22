"""
Middleware de autenticación para ComparApp SaaS
Valida subdominios, tokens y estado de clientes
"""

from functools import wraps
from flask import request, jsonify, g
import pymysql
from contextlib import contextmanager

# ============================================
# CONFIGURACIÓN
# ============================================

ADMIN_DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '12345678',
    'database': 'comparapp_admin',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}


# ============================================
# UTILIDADES DE BASE DE DATOS
# ============================================

@contextmanager
def get_admin_connection():
    """Conexión a la BD administrativa"""
    conn = pymysql.connect(**ADMIN_DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_client_connection(db_name):
    """Conexión a la BD de un cliente específico"""
    config = ADMIN_DB_CONFIG.copy()
    config['database'] = db_name
    conn = pymysql.connect(**config)
    try:
        yield conn
    finally:
        conn.close()


# ============================================
# FUNCIONES DE AUTENTICACIÓN
# ============================================

def extraer_subdominio(host):
    """
    Extrae el subdominio del host
    Ej: cliente1.comparappargentina.com -> cliente1
    """
    if not host:
        return None
    
    # Remover puerto si existe
    host = host.split(':')[0]
    
    # Si es localhost o IP, retornar None
    if host in ['localhost', '127.0.0.1'] or host.startswith('192.168'):
        return None
    
    partes = host.split('.')
    
    # Debe tener al menos 3 partes: subdominio.dominio.tld
    if len(partes) >= 3:
        return partes[0]
    
    return None


def obtener_cliente_por_subdominio(subdominio):
    """Busca cliente por subdominio en la BD admin"""
    if not subdominio:
        return None
    
    query = """
        SELECT id, nombre, subdominio, db_name, token, activo
        FROM clientes
        WHERE subdominio = %s
        LIMIT 1
    """
    
    with get_admin_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (subdominio,))
            return cursor.fetchone()


def validar_token(cliente, token_recibido):
    """Valida que el token coincida con el del cliente"""
    if not cliente or not token_recibido:
        return False
    
    # Remover "Bearer " si existe
    if token_recibido.startswith('Bearer '):
        token_recibido = token_recibido[7:]
    
    return cliente['token'] == token_recibido


def registrar_acceso(cliente_id, endpoint, ip):
    """Registra acceso en logs (opcional)"""
    try:
        query = """
            INSERT INTO logs_acceso (cliente_id, endpoint, ip, timestamp)
            VALUES (%s, %s, %s, NOW())
        """
        with get_admin_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (cliente_id, endpoint, ip))
            conn.commit()
    except Exception as e:
        print(f"Error al registrar acceso: {e}")


# ============================================
# DECORADORES DE AUTENTICACIÓN
# ============================================

def requiere_auth(f):
    """
    Decorador que valida autenticación antes de ejecutar endpoint
    
    Uso:
        @app.route('/api/productos')
        @requiere_auth
        def listar_productos():
            # Acceso a g.cliente y g.db_name
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Extraer subdominio
        host = request.headers.get('Host', '')
        subdominio = extraer_subdominio(host)
        
        if not subdominio:
            return jsonify({
                'error': 'Subdominio no detectado',
                'mensaje': 'Accede desde tu subdominio: tucliente.comparappargentina.com'
            }), 400
        
        # 2. Buscar cliente
        cliente = obtener_cliente_por_subdominio(subdominio)
        
        if not cliente:
            return jsonify({
                'error': 'Cliente no encontrado',
                'mensaje': f'El subdominio "{subdominio}" no está registrado'
            }), 404
        
        # 3. Verificar si está activo
        if not cliente['activo']:
            return jsonify({
                'error': 'Cliente inactivo',
                'mensaje': 'Tu cuenta ha sido suspendida. Contacta a soporte.'
            }), 403
        
        # 4. Validar token
        token = request.headers.get('Authorization', '')
        
        if not validar_token(cliente, token):
            return jsonify({
                'error': 'Token inválido',
                'mensaje': 'Autenticación fallida'
            }), 401
        
        # 5. Registrar acceso (opcional)
        ip = request.remote_addr
        registrar_acceso(cliente['id'], request.path, ip)
        
        # 6. Guardar contexto en Flask g
        g.cliente = cliente
        g.db_name = cliente['db_name']
        g.cliente_id = cliente['id']
        
        # 7. Ejecutar función original
        return f(*args, **kwargs)
    
    return decorated_function


def requiere_auth_opcional(f):
    """
    Decorador para endpoints públicos que pueden usar auth
    
    Uso para endpoints públicos de consulta de precios desde POS
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        host = request.headers.get('Host', '')
        subdominio = extraer_subdominio(host)
        
        if subdominio:
            cliente = obtener_cliente_por_subdominio(subdominio)
            if cliente and cliente['activo']:
                token = request.headers.get('Authorization', '')
                if validar_token(cliente, token):
                    g.cliente = cliente
                    g.db_name = cliente['db_name']
        
        return f(*args, **kwargs)
    
    return decorated_function


# ============================================
# UTILIDADES PARA CONSULTAS
# ============================================

def execute_client_query(query, params=None, fetch_one=False):
    """
    Ejecuta query en la BD del cliente actual (desde g.db_name)
    """
    if not hasattr(g, 'db_name'):
        raise Exception("No hay cliente autenticado en el contexto")
    
    with get_client_connection(g.db_name) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone() if fetch_one else cursor.fetchall()


def execute_client_update(query, params=None):
    """
    Ejecuta UPDATE/INSERT/DELETE en la BD del cliente actual
    """
    if not hasattr(g, 'db_name'):
        raise Exception("No hay cliente autenticado en el contexto")
    
    try:
        with get_client_connection(g.db_name) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
            conn.commit()
        return True
    except Exception as e:
        print(f"Error en execute_client_update: {e}")
        return False