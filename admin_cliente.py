"""
CLI de Administración de Clientes para ComparApp SaaS
Permite crear, listar, activar/desactivar y eliminar clientes
"""

import pymysql
import secrets
import sys
from datetime import datetime

# ============================================
# CONFIGURACIÓN
# ============================================

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '12345678',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

ADMIN_DB = 'comparapp_admin'


# ============================================
# FUNCIONES DE BASE DE DATOS
# ============================================

def get_connection(database=ADMIN_DB):
    """Conexión a base de datos"""
    config = DB_CONFIG.copy()
    config['database'] = database
    return pymysql.connect(**config)


def ejecutar_query(query, params=None, database=ADMIN_DB, fetch=True):
    """Ejecuta query y retorna resultados"""
    conn = get_connection(database)
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            conn.commit()
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return None if fetch else False
    finally:
        conn.close()


# ============================================
# FUNCIONES DE ADMINISTRACIÓN
# ============================================

def generar_token():
    """Genera token seguro de 32 caracteres"""
    return secrets.token_urlsafe(32)


def listar_clientes():
    """Lista todos los clientes"""
    query = """
        SELECT id, nombre, subdominio, db_name, activo, fecha_alta
        FROM clientes
        ORDER BY id
    """
    clientes = ejecutar_query(query)
    
    if not clientes:
        print("\n📋 No hay clientes registrados\n")
        return
    
    print("\n" + "=" * 100)
    print(f"{'ID':<5} {'NOMBRE':<30} {'SUBDOMINIO':<25} {'BASE DE DATOS':<25} {'ACTIVO':<10}")
    print("=" * 100)
    
    for c in clientes:
        estado = "✅ Sí" if c['activo'] else "❌ No"
        print(f"{c['id']:<5} {c['nombre']:<30} {c['subdominio']:<25} {c['db_name']:<25} {estado:<10}")
    
    print("=" * 100 + "\n")


def crear_cliente(nombre, subdominio):
    """Crea un nuevo cliente con su base de datos"""
    
    # Validar subdominio
    if not subdominio.isalnum():
        print("❌ El subdominio solo puede contener letras y números")
        return False
    
    # Generar nombres
    db_name = f"cliente_{subdominio}"
    token = generar_token()
    
    print(f"\n🔨 Creando cliente '{nombre}'...")
    print(f"   Subdominio: {subdominio}.comparappargentina.com")
    print(f"   Base de datos: {db_name}")
    
    try:
        # 1. Crear base de datos
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.close()
        print("   ✅ Base de datos creada")
        
        # 2. Crear tabla products
        query_tabla = """
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
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        ejecutar_query(query_tabla, database=db_name, fetch=False)
        print("   ✅ Tabla products creada")
        
        # 3. Registrar cliente en admin
        query_cliente = """
            INSERT INTO clientes (nombre, subdominio, db_name, token, activo)
            VALUES (%s, %s, %s, %s, 1)
        """
        ejecutar_query(query_cliente, (nombre, subdominio, db_name, token), fetch=False)
        print("   ✅ Cliente registrado")
        
        print("\n" + "=" * 80)
        print("✅ CLIENTE CREADO EXITOSAMENTE")
        print("=" * 80)
        print(f"\n📌 URL: https://{subdominio}.comparappargentina.com")
        print(f"🔑 TOKEN: {token}")
        print("\n⚠️  GUARDA ESTE TOKEN - Es necesario para acceder al sistema\n")
        print("=" * 80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error al crear cliente: {e}\n")
        return False


def cambiar_token(cliente_id):
    """Genera nuevo token para un cliente"""
    nuevo_token = generar_token()
    
    query = "UPDATE clientes SET token = %s WHERE id = %s"
    success = ejecutar_query(query, (nuevo_token, cliente_id), fetch=False)
    
    if success:
        print(f"\n✅ Token actualizado para cliente ID {cliente_id}")
        print(f"🔑 Nuevo token: {nuevo_token}\n")
    else:
        print(f"\n❌ Error al actualizar token\n")


def activar_desactivar(cliente_id, activar=True):
    """Activa o desactiva un cliente"""
    accion = "activar" if activar else "desactivar"
    valor = 1 if activar else 0
    
    query = "UPDATE clientes SET activo = %s WHERE id = %s"
    success = ejecutar_query(query, (valor, cliente_id), fetch=False)
    
    if success:
        emoji = "✅" if activar else "❌"
        print(f"\n{emoji} Cliente ID {cliente_id} {accion}do\n")
    else:
        print(f"\n❌ Error al {accion} cliente\n")


def eliminar_cliente(cliente_id):
    """Elimina un cliente y su base de datos"""
    # Obtener info del cliente
    query = "SELECT nombre, subdominio, db_name FROM clientes WHERE id = %s"
    cliente = ejecutar_query(query, (cliente_id,))
    
    if not cliente:
        print(f"\n❌ Cliente ID {cliente_id} no encontrado\n")
        return
    
    cliente = cliente[0]
    
    print(f"\n⚠️  ADVERTENCIA: Vas a eliminar permanentemente:")
    print(f"   Cliente: {cliente['nombre']}")
    print(f"   Subdominio: {cliente['subdominio']}")
    print(f"   Base de datos: {cliente['db_name']}")
    
    confirmacion = input("\n¿Estás seguro? Escribe 'ELIMINAR' para confirmar: ")
    
    if confirmacion != 'ELIMINAR':
        print("\n❌ Operación cancelada\n")
        return
    
    try:
        # Eliminar base de datos
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS {cliente['db_name']}")
        conn.close()
        print(f"   ✅ Base de datos eliminada")
        
        # Eliminar de admin
        query = "DELETE FROM clientes WHERE id = %s"
        ejecutar_query(query, (cliente_id,), fetch=False)
        print(f"   ✅ Cliente eliminado del sistema")
        
        print("\n✅ Cliente eliminado exitosamente\n")
        
    except Exception as e:
        print(f"\n❌ Error al eliminar: {e}\n")


def ver_token(cliente_id):
    """Muestra el token de un cliente"""
    query = "SELECT nombre, token FROM clientes WHERE id = %s"
    cliente = ejecutar_query(query, (cliente_id,))
    
    if not cliente:
        print(f"\n❌ Cliente ID {cliente_id} no encontrado\n")
        return
    
    cliente = cliente[0]
    print(f"\n🔑 Token del cliente '{cliente['nombre']}':")
    print(f"   {cliente['token']}\n")


# ============================================
# MENÚ PRINCIPAL
# ============================================

def mostrar_menu():
    """Muestra menú de opciones"""
    print("\n" + "=" * 60)
    print("🏢  COMPARAPP SAAS - ADMINISTRACIÓN DE CLIENTES")
    print("=" * 60)
    print("\n1. 📋 Listar clientes")
    print("2. ➕ Crear nuevo cliente")
    print("3. 🔑 Ver token de cliente")
    print("4. 🔄 Cambiar token de cliente")
    print("5. ✅ Activar cliente")
    print("6. ❌ Desactivar cliente")
    print("7. 🗑️  Eliminar cliente")
    print("0. 🚪 Salir")
    print("\n" + "=" * 60)


def main():
    """Loop principal"""
    while True:
        mostrar_menu()
        opcion = input("\nSelecciona una opción: ").strip()
        
        if opcion == '1':
            listar_clientes()
            
        elif opcion == '2':
            nombre = input("\n📝 Nombre del cliente: ").strip()
            subdominio = input("🌐 Subdominio (solo letras/números): ").strip().lower()
            if nombre and subdominio:
                crear_cliente(nombre, subdominio)
            else:
                print("\n❌ Nombre y subdominio son obligatorios\n")
                
        elif opcion == '3':
            try:
                cliente_id = int(input("\n🔢 ID del cliente: ").strip())
                ver_token(cliente_id)
            except ValueError:
                print("\n❌ ID inválido\n")
                
        elif opcion == '4':
            try:
                cliente_id = int(input("\n🔢 ID del cliente: ").strip())
                cambiar_token(cliente_id)
            except ValueError:
                print("\n❌ ID inválido\n")
                
        elif opcion == '5':
            try:
                cliente_id = int(input("\n🔢 ID del cliente a activar: ").strip())
                activar_desactivar(cliente_id, activar=True)
            except ValueError:
                print("\n❌ ID inválido\n")
                
        elif opcion == '6':
            try:
                cliente_id = int(input("\n🔢 ID del cliente a desactivar: ").strip())
                activar_desactivar(cliente_id, activar=False)
            except ValueError:
                print("\n❌ ID inválido\n")
                
        elif opcion == '7':
            try:
                cliente_id = int(input("\n🔢 ID del cliente a eliminar: ").strip())
                eliminar_cliente(cliente_id)
            except ValueError:
                print("\n❌ ID inválido\n")
                
        elif opcion == '0':
            print("\n👋 ¡Hasta luego!\n")
            sys.exit(0)
            
        else:
            print("\n❌ Opción inválida\n")
        
        input("\nPresiona Enter para continuar...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego!\n")
        sys.exit(0)