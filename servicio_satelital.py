import time
import random
import database as db

def simular_barrido_satelital():
    print("🛰️ [Satélite] Iniciando conexión con el sistema orbital...")
    try:
        conn = db.obtener_conexion()
        cursor = conn.cursor()
        
        # 1. Obtener todos los potreros registrados de todos los ganaderos
        cursor.execute("SELECT id, nombre, usuario FROM potreros;")
        potreros = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not potreros:
            print("📭 [Satélite] No hay potreros registrados en Supabase aún. Esperando...")
            return

        print(f"🛰️ [Satélite] Escaneando {len(potreros)} lotes georreferenciados en Santa Cruz...")
        print("-" * 60)
        
        for p_id, nombre, usuario in potreros:
            # Simulamos una fluctuación del NDVI entre 0.15 y 0.85
            nuevo_ndvi = round(random.uniform(0.15, 0.85), 2)
            
            # Inyectamos la telemetría directamente en Supabase usando la capa de datos
            db.simular_actualizacion_satelital_global(p_id, nuevo_ndvi)
            
            print(f"   🛸 -> Estancia @{usuario.upper()} | {nombre} | Coordenadas actualizadas -> Nuevo NDVI: {nuevo_ndvi}")
            time.sleep(1) # Simula el tiempo de procesamiento por lote
            
        print("-" * 60)
        print("✅ [Satélite] Barrido completado con éxito. Datos persistidos en Supabase.")
        
    except Exception as e:
        print(f"❌ [Satélite] Error en la conexión orbital: {e}")

if __name__ == "__main__":
    # Ejecuta un barrido inmediato al arrancar
    simular_barrido_satelital()