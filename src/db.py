import getpass
import pyodbc

#autenticación de windows"
SERVER = r'.\SQLEXPRESS'
DATABASE = 'BD_MODERNIZACION'
DRIVER='ODBC Driver 17 for SQL Server'

#Función para obtener la conexión a la base de datos
def obtener_conexion():
    connection_string = (
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        "Trusted_Connection=yes;"                                                                                                                                                                                                                                                                                                                           
    )
    return pyodbc.connect(connection_string)
#Funcion para obtener el usuario actual de la base de datos
def obtener_usuario_actual():
    usuario_red = getpass.getuser()

    try:
        with obtener_conexion() as conn:
            cursor = conn.cursor()
            query = """
                SELECT id, nombre_completo, usuario_red, activo
                FROM Usuario 
                WHERE usuario_red = ? AND activo = 1;
            """
            cursor.execute(query,(usuario_red))
            row =  cursor.fetchone()

            if row:
                return{
                    "id": row.id,
                    "nombre": row.nombre_completo,
                    "usuario_red":row.usuario_red,
                    "activo": row.activo,
                }
            else:
                print(f"El usuario de red '{usuario_red}' no existe o está inactivo en la base de datos.")
                return None
    except Exception as e:
        print(f"Error al constultar usuario actual: {e}")
        return None
    
def obtener_organos_activos():
    """lista de dependencias"""
    try:
        with obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre FROM Organos ORDER BY nombre;")
            rows =  cursor.fetchall()
            return [{"id": r.id, "nombre": r.nombre} for r in rows]
    except Exception as e:
        print(f"Error al obtener el órgano: {e}")
        return[]

#prueba local
if __name__ == "__main__":
    print("=== Probando el módulo de base de datos === ")

    usuario = obtener_usuario_actual()
    if usuario:
        print(f"Usuario detectado en BD: {usuario['nombre']} {usuario['usuario_red']} (Rol: {usuario['activo']})")

    organos = obtener_organos_activos()
    print(f"Órganos registrados en la BD ({len(organos)}):")
    for org in organos:
        print(f" -[{org['nombre']}")

def obtener_documentos_tabla():

    try:
        conn = obtener_conexion() 
        if not conn:
            return []
            
        cursor = conn.cursor()
        
        query = """
            SELECT 
                d.id,
                d.nro_expediente,
                d.nro_resolucion,
                dv.nro_version,
                d.tipo_documento,
                d.fecha_emision,
                d.titulo,
                dv.ruta_unc,
                o.nombre AS organo_nombre
            FROM Documento d
            INNER JOIN Documento_versiones dv ON d.id = dv.documento_id
            LEFT JOIN Organos o ON d.organo_id = o.id
            WHERE dv.es_vigente = 1 AND d.estado = 'activo'
        """
        cursor.execute(query)
        filas = cursor.fetchall()
        
        documentos = []
        for fila in filas:
            documentos.append({
                "id": fila.id,
                "nro_doc": fila.nro_expediente,
                "resolucion": fila.nro_resolucion if fila.nro_resolucion else "---",
                "version": fila.nro_version,
                "tipo": fila.tipo_documento,
                "fecha": fila.fecha_emision.strftime("%d/%m/%Y") if fila.fecha_emision else "",
                "titulo": fila.titulo,
                "ruta_pdf": fila.ruta_unc,
                "organo": fila.organo_nombre if fila.organo_nombre else "Órgano no especificado"
            })
            
        cursor.close()
        conn.close()
        return documentos
        
    except Exception as e:
        print(f"Error al obtener documentos: {e}")
        return []
    
def buscar_documentos(texto, filtros):
    """Busca documentos en SQL Server aplicando texto y filtros en tiempo real"""
    try:
        conn = obtener_conexion()
        if not conn:
            return []
            
        cursor = conn.cursor()
        
        query = """
            SELECT 
                d.id, d.nro_expediente, d.nro_resolucion, dv.nro_version,
                d.tipo_documento, d.fecha_emision, d.titulo, 
                dv.ruta_unc, o.nombre AS organo_nombre
            FROM Documento d
            INNER JOIN Documento_versiones dv ON d.id = dv.documento_id
            LEFT JOIN Organos o ON d.organo_id = o.id
            WHERE dv.es_vigente = 1 AND d.estado = 'activo'
        """
        parametros = []
        
        # 1. Filtro por Texto (LIMPIEZA INTELIGENTE DE ESPACIOS)
        if texto:
            # Esto quita espacios al inicio, al final y espacios dobles en el medio
            texto_limpio = " ".join(texto.split())
            
            if texto_limpio:
                # 3 condiciones = 3 signos de interrogación
                query += " AND (d.titulo LIKE ? OR d.nro_resolucion LIKE ? OR d.nro_expediente LIKE ?)"
                param_texto = f"%{texto_limpio}%"
                parametros.extend([param_texto, param_texto, param_texto])
            
        # 2. Filtro por Año
        anio = filtros.get("anio")
        if anio and "todo" not in str(anio).lower():
            query += " AND YEAR(d.fecha_emision) = ?"
            parametros.append(int(anio))
            
        # 3. Filtro por Mes
        mes = filtros.get("mes")
        if mes and "todo" not in str(mes).lower():
            meses_dict = {"Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6, 
                          "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12}
            mes_num = meses_dict.get(mes)
            if mes_num:
                query += " AND MONTH(d.fecha_emision) = ?"
                parametros.append(mes_num)
                
        # 4. Filtro por Tipo
        tipo = filtros.get("tipo")
        if tipo and "todo" not in str(tipo).lower():
            query += " AND d.tipo_documento = ?"
            parametros.append(tipo)
            
        # 5. Filtro por Órgano
        organo_id = filtros.get("organo")
        if organo_id and str(organo_id) != "0" and "todo" not in str(organo_id).lower(): 
            query += " AND d.organo_id = ?"
            parametros.append(organo_id)
            
        cursor.execute(query, parametros)
        filas = cursor.fetchall()
        
        documentos = []
        for fila in filas:
            documentos.append({
                "id": fila.id,
                "nro_doc": fila.nro_expediente,
                "resolucion": fila.nro_resolucion if fila.nro_resolucion else "---",
                "version": fila.nro_version,
                "tipo": fila.tipo_documento,
                "fecha": fila.fecha_emision.strftime("%d/%m/%Y") if fila.fecha_emision else "",
                "ruta_pdf": fila.ruta_unc,
                "titulo": fila.titulo, 
                "organo": fila.organo_nombre if fila.organo_nombre else "Órgano no especificado"
            })
            
        cursor.close()
        conn.close()
        return documentos
        
    except Exception as e:
        print(f"Error en búsqueda: {e}")
        return []

def insertar_documento(datos, ruta_unc, usuario_id=1):
    """Inserta la cabecera en Documento, su primera versión y audita en Bitacora usando OUTPUT para el ID"""
    conn = None
    try:
        conn = obtener_conexion()
        if not conn:
            return False, "No se pudo establecer conexión con SQL Server."
            
        cursor = conn.cursor()
        
        # ==========================================
        # 1. INSERTAR CABECERA (Tabla: Documento)
        # ==========================================
        query_doc = """
            INSERT INTO Documento(
                tipo_documento, nro_resolucion, nro_expediente, nro_oficio,
                titulo, organo_id, fecha_emision,
                estado, usuario_id, fecha_subida
            ) 
            OUTPUT inserted.id
            VALUES (?, ?, ?, ?, ?, ?, ?, 'activo', ?, GETDATE());
        """
        cursor.execute(query_doc, (
            datos.get('tipo'),           # 1. tipo_documento
            datos.get('resolucion'),     # 2. nro_resolucion
            datos.get('expediente'),     # 3. nro_expediente
            datos.get('oficio'),         # 4. nro_oficio
            datos.get('titulo', ''),     # 5. titulo
            datos.get('organo_id'),      # 6. organo_id
            datos.get('fecha_emision'),  # 7. fecha_emision
            usuario_id                   # 8. usuario_id (Dinámico)
        ))
        
        # Capturamos el ID autogenerado
        row = cursor.fetchone()
        if not row or not row[0]:
            conn.rollback()
            return False, "SQL Server no devolvió el ID insertado."
            
        nuevo_doc_id = int(row[0])
        
        # ==========================================
        # 2. INSERTAR VERSIÓN INICIAL (Tabla: Documento_versiones)
        # ==========================================
        nombre_archivo = ruta_unc.split("\\")[-1]
        query_version = """
            INSERT INTO Documento_versiones(
                documento_id, nro_version, ruta_unc, nombre_archivo,
                es_vigente, comentario_cambio, usuario_id, fecha_subida
            ) VALUES (?, 1, ?, ?, 1, 'Versión inicial', ?, GETDATE());
        """
        cursor.execute(query_version, (
            nuevo_doc_id,
            ruta_unc,
            nombre_archivo,
            usuario_id                   
        ))
        

        query_bitacora = """
            INSERT INTO Bitacora (usuario_id, documento_id, accion, detalle, fecha)
            VALUES (?, ?, 'SUBIDA NUEVA', ?, GETDATE());
        """
        detalle_accion = f"Se subió el documento {datos.get('resolucion')} (Expediente: {datos.get('expediente')})"
        
        cursor.execute(query_bitacora, (
            usuario_id,
            nuevo_doc_id,
            detalle_accion
        ))
        
        
        conn.commit() # Si llegamos aquí, los 3 inserts fueron un éxito total
        cursor.close()
        conn.close()
        return True, "None"
        
    except Exception as e:
        if conn:
            conn.rollback() # Si explota el paso 2 o 3, se deshace el paso 1 automáticamente
        print(f"Error en SQL: {e}")
        return False, str(e)

def obtener_siguiente_version(documento_id):
    try:
        conn = obtener_conexion()
        if not conn: return 2
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(nro_version) FROM Documento_versiones WHERE documento_id = ?", (documento_id,))
        row = cursor.fetchone()
        conn.close()
        
        ultima_version = row[0] if row and row[0] else 1
        return ultima_version + 1
    except Exception:
        return 2
    
def actualizar_version_documento(documento_id, nueva_version, ruta_archivo, comentario="Nueva versión"):
    """Sube una nueva versión del documento usando el número exacto"""
    conn = None
    try:
        conn = obtener_conexion()
        if not conn:
            return False, "No se pudo conectar a la base de datos."
            
        cursor = conn.cursor()
        
        # 1. Desactivar la vigencia de todas las versiones anteriores
        cursor.execute("""
            UPDATE Documento_versiones 
            SET es_vigente = 0 
            WHERE documento_id = ?
        """, (documento_id,))
        
        # 2. Extraer solo el nombre del PDF para tu columna 'nombre_archivo'
        import os
        nombre_archivo = os.path.basename(ruta_archivo)
        
        # 3. Insertar respetando estrictamente tu esquema de BD
        query_version = """
            INSERT INTO Documento_versiones(
                documento_id, nro_version, ruta_unc, nombre_archivo,
                es_vigente, comentario_cambio, usuario_id, fecha_subida
            ) VALUES (?, ?, ?, ?, 1, ?, 1, GETDATE());
        """
        cursor.execute(query_version, (
            documento_id,
            nueva_version,
            ruta_archivo,      # Esto va a la columna ruta_unc
            nombre_archivo,    # Esto va a la columna nombre_archivo
            comentario         # Esto va a la columna comentario_cambio
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True, f"¡Se actualizó con éxito a la versión {nueva_version}!"
        
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, str(e)

def obtener_historial_versiones(documento_id):
    """Devuelve todas las versiones de un documento ordenadas de la más reciente a la más antigua"""
    try:
        conn = obtener_conexion()
        if not conn: return []
        cursor = conn.cursor()
        
        query = """
            SELECT nro_version, fecha_subida, comentario_cambio, ruta_unc, es_vigente
            FROM Documento_versiones
            WHERE documento_id = ?
            ORDER BY nro_version DESC
        """
        cursor.execute(query, (documento_id,))
        filas = cursor.fetchall()
        conn.close()
        
        historial = []
        for f in filas:
            historial.append({
                "version": f.nro_version,
                "fecha": f.fecha_subida.strftime("%d/%m/%Y %H:%M") if f.fecha_subida else "",
                "motivo": f.comentario_cambio if f.comentario_cambio else "Sin motivo especificado",
                "ruta_pdf": f.ruta_unc,
                "es_vigente": f.es_vigente
            })
        return historial
    except Exception as e:
        print(f"Error al obtener historial: {e}")
        return []

def obtener_documento_por_expediente(nro_expediente):
    """Busca si ya existe un documento con este número de expediente (ignorando espacios/mayúsculas) y devuelve sus datos vigentes."""
    try:
        conn = obtener_conexion()
        if not conn: return None
        cursor = conn.cursor()
        
        # Corregimos los nombres exactos de columnas según tu tabla Documento
        query = """
            SELECT d.id, d.nro_expediente, d.titulo, d.tipo_documento, 
                   o.nombre AS organo_nombre, d.nro_resolucion, 
                   dv.ruta_unc, dv.nro_version
            FROM Documento d
            INNER JOIN Documento_versiones dv ON d.id = dv.documento_id
            LEFT JOIN Organos o ON d.organo_id = o.id
            WHERE UPPER(TRIM(d.nro_expediente)) = UPPER(TRIM(?)) AND dv.es_vigente = 1
        """
        cursor.execute(query, (nro_expediente,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row.id,
                "nro_doc": row.nro_expediente,
                "titulo": row.titulo,
                "tipo": row.tipo_documento,
                "organo": row.organo_nombre if row.organo_nombre else "Órgano no especificado",
                "resolucion": row.nro_resolucion if row.nro_resolucion else "---",
                "ruta_pdf": row.ruta_unc,
                "version": row.nro_version
            }
        return None
    except Exception as e:
        print(f"Error al buscar expediente existente: {e}")
        return None

def obtener_usuario_por_red(usuario_red):
    """Busca al usuario en la BD usando el nombre de su computadora (os.getlogin())"""
    conn = None
    try:
        # Usa el nombre exacto de tu función para conectar a la BD
        conn = obtener_conexion() 
        if not conn:
            return None

        cursor = conn.cursor()
        # Buscamos si existe el usuario_red
        query = "SELECT id, nombre_completo, activo FROM Usuario WHERE usuario_red = ?"
        cursor.execute(query, (usuario_red,))
        row = cursor.fetchone()

        if row:
            return {
                "id": row[0],
                "nombre_completo": row[1],
                "activo": row[2]
            }
        return None
    except Exception as e:
        print(f"Error verificando usuario: {e}")
        return None
    finally:
        if conn:
            conn.close()

