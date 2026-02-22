#!/usr/bin/env python3
"""
Sistema de Gestión de Productos con Impresión WiFi Térmica
Backend Flask que imprime DIRECTAMENTE a impresora WiFi
Compatible con iOS, Android, Safari, Chrome - TODOS
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pymysql
import uuid
import os
import socket
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Optional, Any


app = Flask(__name__)
CORS(app)

# Configuración de impresora WiFi
PRINTER_CONFIG = {
    'ip': os.getenv("PRINTER_IP", "192.168.1.100"),  # IP de tu impresora
    'port': int(os.getenv("PRINTER_PORT", 9100)),     # Puerto estándar ESC/POS
    'timeout': 3
}

DB_CONFIG = {
    'host': os.getenv("DB_HOST", "mariadb"),
    'user': os.getenv("DB_USER", "unicenta"),
    'password': os.getenv("DB_PASSWORD", "unicenta123"),
    'database': os.getenv("DB_NAME", "unicentaopos"),
    'port': int(os.getenv("DB_PORT", 3306)),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

VALID_TOKENS = {
    'tk_prod_abc123def456ghi789jkl012mno345': {
        'cliente': 'tienda1',
        'nombre': 'Tienda Demo'
    }
}


def validate_token(token: str) -> bool:
    """Valida si un token es válido"""
    return token in VALID_TOKENS

def require_auth(f):
    """Decorador para rutas que requieren autenticación"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token no proporcionado'}), 401
        
        token = auth_header.replace('Bearer ', '').strip()
        
        if not validate_token(token):
            return jsonify({'error': 'Token inválido o expirado'}), 401
        
        request.cliente_info = VALID_TOKENS[token]
        return f(*args, **kwargs)
    
    return decorated_function


@contextmanager
def get_db_connection():
    """Context manager para manejar conexiones a la base de datos"""
    connection = pymysql.connect(**DB_CONFIG)
    try:
        yield connection
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        connection.close()

def execute_query(query: str, params: tuple = None, fetch_one: bool = False) -> Any:
    """Ejecuta una consulta SQL y retorna los resultados"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone() if fetch_one else cursor.fetchall()

def execute_update(query: str, params: tuple = None) -> bool:
    """Ejecuta una consulta de actualización (INSERT, UPDATE, DELETE)"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
            conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error en execute_update: {str(e)}")
        return False

# ============================================
# SISTEMA DE IMPRESIÓN WIFI/RED
# ============================================

class ESCPOSCommands:
    """Comandos ESC/POS para impresoras térmicas"""
    
    INIT = b'\x1b\x40'
    LINE_FEED = b'\x0a'
    CUT_PAPER = b'\x1d\x56\x41\x00'
    
    ALIGN_LEFT = b'\x1b\x61\x00'
    ALIGN_CENTER = b'\x1b\x61\x01'
    ALIGN_RIGHT = b'\x1b\x61\x02'
    
    TEXT_NORMAL = b'\x1d\x21\x00'
    TEXT_DOUBLE_HEIGHT = b'\x1d\x21\x01'
    TEXT_DOUBLE_WIDTH = b'\x1d\x21\x10'
    TEXT_DOUBLE_BOTH = b'\x1d\x21\x11'
    TEXT_LARGE = b'\x1d\x21\x22'
    
    BOLD_ON = b'\x1b\x45\x01'
    BOLD_OFF = b'\x1b\x45\x00'
    
    BARCODE_HEIGHT = b'\x1d\x68\x50'
    BARCODE_WIDTH = b'\x1d\x77\x02'
    BARCODE_TEXT_BELOW = b'\x1d\x48\x02'
    BARCODE_EAN13 = b'\x1d\x6b\x43'


def enviar_a_impresora(comandos: bytes) -> tuple:
    """
    Envía comandos ESC/POS a impresora WiFi
    Retorna (success: bool, message: str)
    """
    try:
        # Crear socket TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(PRINTER_CONFIG['timeout'])
        
        # Conectar a impresora
        sock.connect((PRINTER_CONFIG['ip'], PRINTER_CONFIG['port']))
        
        # Enviar comandos
        sock.sendall(comandos)
        
        # Cerrar conexión
        sock.close()
        
        return True, "Impresión exitosa"
        
    except socket.timeout:
        return False, "Timeout: No se pudo conectar a la impresora"
    except socket.error as e:
        return False, f"Error de conexión: {str(e)}"
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"


def generar_etiqueta_producto(producto: Dict) -> bytes:
    """
    Genera comandos ESC/POS para imprimir etiqueta de producto
    Optimizado para impresoras de 58mm
    """
    cmd = bytearray()
    
    # Inicializar
    cmd.extend(ESCPOSCommands.INIT)
    
    # Título centrado
    cmd.extend(ESCPOSCommands.ALIGN_CENTER)
    cmd.extend(ESCPOSCommands.TEXT_NORMAL)
    cmd.extend(ESCPOSCommands.BOLD_ON)
    cmd.extend("ETIQUETA DE PRECIO\n".encode('utf-8'))
    cmd.extend(ESCPOSCommands.BOLD_OFF)
    cmd.extend(ESCPOSCommands.LINE_FEED)
    
    # Nombre del producto
    nombre = producto.get('name', 'Sin nombre')[:28]
    cmd.extend(ESCPOSCommands.ALIGN_LEFT)
    cmd.extend(ESCPOSCommands.TEXT_NORMAL)
    cmd.extend(f"{nombre}\n".encode('utf-8'))
    cmd.extend(ESCPOSCommands.LINE_FEED)
    
    # Precio grande
    precio = float(producto.get('pricesell', 0))
    cmd.extend(ESCPOSCommands.ALIGN_CENTER)
    cmd.extend(ESCPOSCommands.TEXT_LARGE)
    cmd.extend(ESCPOSCommands.BOLD_ON)
    cmd.extend(f"$ {precio:,.2f}\n".encode('utf-8'))
    cmd.extend(ESCPOSCommands.BOLD_OFF)
    cmd.extend(ESCPOSCommands.TEXT_NORMAL)
    cmd.extend(ESCPOSCommands.LINE_FEED)
    
    # Código de barras
    codigo = producto.get('code', '')
    if codigo and len(codigo) in [12, 13]:
        cmd.extend(ESCPOSCommands.ALIGN_CENTER)
        cmd.extend(ESCPOSCommands.BARCODE_HEIGHT)
        cmd.extend(ESCPOSCommands.BARCODE_WIDTH)
        cmd.extend(ESCPOSCommands.BARCODE_TEXT_BELOW)
        
        if len(codigo) == 12:
            codigo = '0' + codigo
        
        cmd.extend(ESCPOSCommands.BARCODE_EAN13)
        cmd.extend(bytes([len(codigo)]))
        cmd.extend(codigo.encode('ascii'))
        cmd.extend(ESCPOSCommands.LINE_FEED)
    else:
        cmd.extend(ESCPOSCommands.ALIGN_CENTER)
        cmd.extend(f"COD: {codigo}\n".encode('utf-8'))
    
    cmd.extend(ESCPOSCommands.LINE_FEED)
    
    # Fecha
    cmd.extend(ESCPOSCommands.ALIGN_CENTER)
    cmd.extend(ESCPOSCommands.TEXT_NORMAL)
    fecha = datetime.now().strftime('%d/%m/%Y %H:%M')
    cmd.extend(f"{fecha}\n".encode('utf-8'))
    
    # Saltos y corte
    cmd.extend(ESCPOSCommands.LINE_FEED * 3)
    cmd.extend(ESCPOSCommands.CUT_PAPER)
    
    return bytes(cmd)


# ============================================
# RUTAS DE IMPRESIÓN
# ============================================

@app.route('/api/imprimir/etiqueta', methods=['POST'])
@require_auth
def imprimir_etiqueta():
    """
    Imprime etiqueta directamente en impresora WiFi
    
    Body JSON:
    {
        "codigo": "7790001234567"  // Buscar por código
    }
    O:
    {
        "producto": {
            "name": "Coca Cola 2.25L",
            "code": "7790001234567",
            "pricesell": 1250.50
        }
    }
    """
    try:
        data = request.json
        
        # Opción 1: Buscar producto por código
        if data.get('codigo'):
            query = """
                SELECT code, name, pricesell, codetype
                FROM products 
                WHERE code = %s
                LIMIT 1
            """
            producto = execute_query(query, (data['codigo'],), fetch_one=True)
            
            if not producto:
                return jsonify({
                    'success': False, 
                    'error': 'Producto no encontrado'
                }), 404
        
        # Opción 2: Datos directos
        elif data.get('producto'):
            producto = data['producto']
        else:
            return jsonify({
                'success': False,
                'error': 'Debe proporcionar código o datos del producto'
            }), 400
        
        # Generar comandos
        comandos = generar_etiqueta_producto(producto)
        
        # IMPRIMIR DIRECTAMENTE
        success, mensaje = enviar_a_impresora(comandos)
        
        if success:
            return jsonify({
                'success': True,
                'mensaje': mensaje,
                'producto': {
                    'name': producto.get('name'),
                    'code': producto.get('code'),
                    'pricesell': float(producto.get('pricesell', 0))
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': mensaje
            }), 500
        
    except Exception as e:
        print(f"❌ Error en imprimir_etiqueta: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/imprimir/lote', methods=['POST'])
@require_auth
def imprimir_lote():
    """
    Imprime múltiples etiquetas
    
    Body JSON:
    {
        "codigos": ["7790001234567", "7790001234568"]
    }
    """
    try:
        data = request.json
        codigos = data.get('codigos', [])
        
        if not codigos:
            return jsonify({
                'success': False,
                'error': 'Debe proporcionar al menos un código'
            }), 400
        
        # Buscar productos
        placeholders = ','.join(['%s'] * len(codigos))
        query = f"""
            SELECT code, name, pricesell, codetype
            FROM products 
            WHERE code IN ({placeholders})
        """
        productos = execute_query(query, tuple(codigos))
        
        if not productos:
            return jsonify({
                'success': False,
                'error': 'No se encontraron productos'
            }), 404
        
        # Generar todas las etiquetas
        comandos_total = bytearray()
        for producto in productos:
            comandos_total.extend(generar_etiqueta_producto(producto))
        
        # Imprimir todo
        success, mensaje = enviar_a_impresora(bytes(comandos_total))
        
        if success:
            return jsonify({
                'success': True,
                'mensaje': f'{len(productos)} etiquetas impresas',
                'cantidad': len(productos)
            })
        else:
            return jsonify({
                'success': False,
                'error': mensaje
            }), 500
        
    except Exception as e:
        print(f"❌ Error en imprimir_lote: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/imprimir/test', methods=['GET'])
@require_auth
def test_impresora():
    """Test de conexión con la impresora"""
    try:
        # Página de prueba simple
        cmd = bytearray()
        cmd.extend(ESCPOSCommands.INIT)
        cmd.extend(ESCPOSCommands.ALIGN_CENTER)
        cmd.extend(ESCPOSCommands.TEXT_DOUBLE_BOTH)
        cmd.extend("TEST OK\n".encode('utf-8'))
        cmd.extend(ESCPOSCommands.TEXT_NORMAL)
        cmd.extend(ESCPOSCommands.LINE_FEED)
        cmd.extend(f"IP: {PRINTER_CONFIG['ip']}\n".encode('utf-8'))
        cmd.extend(f"{datetime.now().strftime('%d/%m/%Y %H:%M')}\n".encode('utf-8'))
        cmd.extend(ESCPOSCommands.LINE_FEED * 3)
        cmd.extend(ESCPOSCommands.CUT_PAPER)
        
        success, mensaje = enviar_a_impresora(bytes(cmd))
        
        return jsonify({
            'success': success,
            'mensaje': mensaje,
            'impresora': {
                'ip': PRINTER_CONFIG['ip'],
                'port': PRINTER_CONFIG['port']
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/imprimir/config', methods=['GET', 'POST'])
@require_auth
def configurar_impresora():
    """Obtener o actualizar configuración de impresora"""
    if request.method == 'GET':
        return jsonify({
            'ip': PRINTER_CONFIG['ip'],
            'port': PRINTER_CONFIG['port'],
            'timeout': PRINTER_CONFIG['timeout']
        })
    else:
        data = request.json
        if data.get('ip'):
            PRINTER_CONFIG['ip'] = data['ip']
        if data.get('port'):
            PRINTER_CONFIG['port'] = int(data['port'])
        
        return jsonify({
            'success': True,
            'mensaje': 'Configuración actualizada',
            'config': PRINTER_CONFIG
        })


# ============================================
# RUTAS EXISTENTES
# ============================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    try:
        version_query = 'SELECT VERSION() as version'
        result = execute_query(version_query, fetch_one=True)
        db_status = 'connected'
        db_version = result['version']
    except Exception as e:
        db_status = 'disconnected'
        db_version = str(e)
    
    # Test impresora
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect((PRINTER_CONFIG['ip'], PRINTER_CONFIG['port']))
        sock.close()
        printer_status = 'connected'
    except:
        printer_status = 'disconnected'
    
    return jsonify({
        'status': 'ok',
        'database': db_status,
        'db_version': db_version,
        'printer': printer_status,
        'printer_ip': PRINTER_CONFIG['ip'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/productos', methods=['GET'])
@require_auth
def listar_productos():
    try:
        query = """
            SELECT id, reference, code, codetype, name, pricebuy, 
                   pricesell, stockunits, category, supplier
            FROM products 
            ORDER BY name ASC
            LIMIT 1000
        """
        productos = execute_query(query)
        
        return jsonify({
            'success': True,
            'productos': [{
                'id': p['id'],
                'code': p['code'],
                'codetype': p['codetype'],
                'reference': p['reference'],
                'name': p['name'],
                'pricebuy': float(p['pricebuy']) if p['pricebuy'] else 0,
                'pricesell': float(p['pricesell']) if p['pricesell'] else 0,
                'stockunits': float(p['stockunits']) if p['stockunits'] else 0,
                'category': p['category'],
                'supplier': p['supplier']
            } for p in productos]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/producto/<codigo>', methods=['GET'])
@require_auth
def obtener_producto(codigo: str):
    try:
        query = """
            SELECT id, reference, code, codetype, name, pricebuy, pricesell, 
                   category, taxcat, stockunits, supplier, texttip, warranty
            FROM products 
            WHERE code = %s OR reference = %s
            LIMIT 1
        """
        producto = execute_query(query, (codigo, codigo), fetch_one=True)
        
        if producto:
            return jsonify({
                'encontrado': True,
                'producto': {
                    'id': producto['id'],
                    'code': producto['code'],
                    'codetype': producto['codetype'],
                    'reference': producto['reference'],
                    'name': producto['name'],
                    'pricebuy': float(producto['pricebuy']) if producto['pricebuy'] else 0,
                    'pricesell': float(producto['pricesell']) if producto['pricesell'] else 0,
                    'stockunits': float(producto['stockunits']) if producto['stockunits'] else 0
                }
            })
        else:
            return jsonify({'encontrado': False}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/producto', methods=['POST'])
@require_auth
def guardar_producto():
    try:
        data = request.json
        
        if not data.get('code') or not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'Código y nombre son obligatorios'
            }), 400
        
        pricebuy = float(data.get('pricebuy', 0))
        margen = float(data.get('margen', 0))
        
        if margen > 0:
            pricesell = round(pricebuy * (1 + margen / 100), 2)
        else:
            pricesell = float(data.get('pricesell', 0))
        
        reference = data.get('reference', '').strip() or data['code']
        
        check_query = 'SELECT id FROM products WHERE code = %s'
        existe = execute_query(check_query, (data['code'],), fetch_one=True)
        
        if existe:
            update_query = """
                UPDATE products 
                SET reference=%s, name=%s, pricebuy=%s, pricesell=%s
                WHERE code=%s
            """
            params = (reference, data['name'], pricebuy, pricesell, data['code'])
        else:
            new_id = str(uuid.uuid4())
            update_query = """
                INSERT INTO products 
                (id, reference, code, name, pricebuy, pricesell)
                VALUES (%s,%s,%s,%s,%s,%s)
            """
            params = (new_id, reference, data['code'], data['name'], pricebuy, pricesell)
        
        success = execute_update(update_query, params)
        
        if success:
            return jsonify({'success': True, 'pricesell': pricesell})
        else:
            return jsonify({'success': False, 'error': 'Error al guardar'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/producto/<codigo>', methods=['DELETE'])
@require_auth
def eliminar_producto(codigo: str):
    try:
        query = 'DELETE FROM products WHERE code = %s'
        success = execute_update(query, (codigo,))
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/categorias', methods=['GET'])
@require_auth
def obtener_categorias():
    try:
        query = 'SELECT id, name FROM categories ORDER BY name'
        categorias = execute_query(query)
        if categorias:
            return jsonify([{'id': c['id'], 'name': c['name']} for c in categorias])
        else:
            return jsonify([
                {'id': '000', 'name': 'General'},
                {'id': '001', 'name': 'Alimentos'},
                {'id': '002', 'name': 'Bebidas'}
            ])
    except:
        return jsonify([{'id': '000', 'name': 'General'}])

# ============================================
# INICIALIZACIÓN
# ============================================

def print_startup_info():
    print("=" * 70)
    print("🚀 SISTEMA DE GESTIÓN - IMPRESIÓN WIFI UNIVERSAL")
    print("=" * 70)
    print(f"📍 Base de datos: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"🖨️  Impresora WiFi: {PRINTER_CONFIG['ip']}:{PRINTER_CONFIG['port']}")
    
    try:
        count_query = 'SELECT COUNT(*) as total FROM products'
        result = execute_query(count_query, fetch_one=True)
        print(f"✅ BD: {result['total']} productos")
    except Exception as e:
        print(f"❌ BD: Error de conexión")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect((PRINTER_CONFIG['ip'], PRINTER_CONFIG['port']))
        sock.close()
        print(f"✅ Impresora: Conectada")
    except:
        print(f"⚠️  Impresora: No conectada (configúrala después)")
    
    print("=" * 70)
    print("🌐 Servidor: http://0.0.0.0:5000")
    print("📱 Compatible: iOS, Android, Chrome, Safari - TODOS")
    print("=" * 70)

if __name__ == '__main__':
    print_startup_info()
    app.run(debug=False, host='0.0.0.0', port=5000)