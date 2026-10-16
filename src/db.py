import getpass
import pyodbc
import os

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
            texto_limpio = " ".join(texto.split())
            if texto_limpio:
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
    """Inserta la cabecera en Documento, su primera versión y audita en Bitacora"""
    conn = None
    try:
        conn = obtener_conexion()
        if not conn:
            return False, "No se pudo establecer conexión con SQL Server."
            
        cursor = conn.cursor()
        
        # 1. INSERTAR CABECERA
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
            datos.get('tipo'),           
            datos.get('resolucion'),     
            datos.get('expediente'),     
            datos.get('oficio'),         
            datos.get('titulo', ''),     
            datos.get('organo_id'),      
            datos.get('fecha_emision'),  
            usuario_id                   
        ))
        
        row = cursor.fetchone()
        if not row or not row[0]:
            conn.rollback()
            return False, "SQL Server no devolvió el ID insertado."
            
        nuevo_doc_id = int(row[0])
        
        # 2. INSERTAR VERSIÓN INICIAL (Agregado asunto_ocr)
        nombre_archivo = ruta_unc.split("\\")[-1]
        asunto_ocr = datos.get('asunto_ocr', '') # <-- Extraemos de datos
        
        query_version = """
            INSERT INTO Documento_versiones(
                documento_id, nro_version, ruta_unc, nombre_archivo,
                es_vigente, comentario_cambio, usuario_id, fecha_subida, asunto_ocr
            ) VALUES (?, 1, ?, ?, 1, 'Versión inicial', ?, GETDATE(), ?);
        """
        cursor.execute(query_version, (
            nuevo_doc_id,
            ruta_unc,
            nombre_archivo,
            usuario_id,
            asunto_ocr  # <-- Insertamos el asunto
        ))
        
        # 3. BITACORA
        query_bitacora = """
            INSERT INTO Bitacora (usuario_id, documento_id, accion, detalle, fecha)
            VALUES (?, ?, 'SUBIDA NUEVA', ?, GETDATE());
        """
        detalle_accion = f"Se subió el documento {datos.get('resolucion')} (Expediente: {datos.get('expediente')})"
        cursor.execute(query_bitacora, (usuario_id, nuevo_doc_id, detalle_accion))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True, "None"
        
    except Exception as e:
        if conn:
            conn.rollback() 
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
    
def actualizar_version_documento(documento_id, nueva_version, ruta_archivo, comentario="Nueva versión", asunto_ocr=""):
    """Sube una nueva versión del documento usando el número exacto y agregando asunto_ocr"""
    conn = None
    try:
        conn = obtener_conexion()
        if not conn:
            return False, "No se pudo conectar a la base de datos."
            
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE Documento_versiones 
            SET es_vigente = 0 
            WHERE documento_id = ?
        """, (documento_id,))
        
        nombre_archivo = os.path.basename(ruta_archivo)
        
        query_version = """
            INSERT INTO Documento_versiones(
                documento_id, nro_version, ruta_unc, nombre_archivo,
                es_vigente, comentario_cambio, usuario_id, fecha_subida, asunto_ocr
            ) VALUES (?, ?, ?, ?, 1, ?, 1, GETDATE(), ?);
        """
        cursor.execute(query_version, (
            documento_id,
            nueva_version,
            ruta_archivo,
            nombre_archivo,
            comentario,
            asunto_ocr 
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
            SELECT nro_version, fecha_subida, comentario_cambio, ruta_unc, es_vigente, asunto_ocr
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
                "es_vigente": f.es_vigente,
                "asunto_ocr": f.asunto_ocr if f.asunto_ocr else "" # <-- Lo leemos para el visor
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
        conn = obtener_conexion() 
        if not conn:
            return None

        cursor = conn.cursor()
        query = "SELECT id, nombre_completo, activo, rol FROM Usuario WHERE usuario_red = ?"
        cursor.execute(query, (usuario_red,))
        row = cursor.fetchone()
    
        if row:
            return {
                "id": row[0],
                "nombre_completo": row[1],
                "activo": row[2],
                "rol": row[3]
            }
        return None
    except Exception as e:
        print(f"Error verificando usuario: {e}")
        return None
    finally:
        if conn:
            conn.close()

# ==================== BORRADO LÓGICO / ARCHIVADO ====================
ESTADO_ACTIVO = 'activo'
ESTADO_INACTIVO = 'inactivo'
ROL_ADMIN = 'ADMIN'
ROL_OPERADOR = 'OPERADOR'


def _obtener_rol(cursor, usuario_id):
    cursor.execute("SELECT rol FROM Usuario WHERE id = ? AND activo = 1;", (usuario_id,))
    fila = cursor.fetchone()
    return fila[0] if fila else None


def _es_admin(cursor, usuario_id):
    return _obtener_rol(cursor, usuario_id) == ROL_ADMIN


def _registrar_bitacora(cursor, usuario_id, documento_id, accion, detalle):
    cursor.execute("""
        INSERT INTO Bitacora (usuario_id, documento_id, accion, detalle, fecha)
        VALUES (?, ?, ?, ?, GETDATE());
    """, (usuario_id, documento_id, accion, detalle))


def archivar_documento(documento_id, usuario_id, motivo):
    """Borrado lógico. Cualquier usuario activo puede archivar. No toca versiones ni el PDF."""
    motivo = (motivo or "").strip()
    if not motivo:
        return False, "Debe indicar el motivo del archivado."
    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Documento
            SET estado = ?, fecha_archivado = GETDATE(),
                usuario_archivo_id = ?, motivo_archivo = ?
            WHERE id = ? AND estado = ?;
        """, (ESTADO_INACTIVO, usuario_id, motivo, documento_id, ESTADO_ACTIVO))

        if cursor.rowcount == 0:
            conn.rollback()
            return False, "El documento no existe o ya está archivado."

        _registrar_bitacora(cursor, usuario_id, documento_id, 'ARCHIVADO', f"Motivo: {motivo}")
        conn.commit()
        return True, "Documento archivado correctamente."
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error al archivar: {e}")
        return False, str(e)
    finally:
        if conn:
            conn.close()


def restaurar_documento(documento_id, usuario_id):
    """Solo administrador. Impide restaurar si ya hay un activo con el mismo expediente."""
    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()

        if not _es_admin(cursor, usuario_id):
            return False, "Solo el administrador puede restaurar documentos."

        cursor.execute(
            "SELECT nro_expediente FROM Documento WHERE id = ? AND estado = ?;",
            (documento_id, ESTADO_INACTIVO))
        fila = cursor.fetchone()
        if not fila:
            return False, "El documento no está archivado."

        cursor.execute("""
            SELECT COUNT(*) FROM Documento
            WHERE UPPER(TRIM(nro_expediente)) = UPPER(TRIM(?)) AND estado = ?;
        """, (fila[0], ESTADO_ACTIVO))
        if cursor.fetchone()[0] > 0:
            return False, ("Ya existe un documento activo con ese expediente. "
                           "Archive primero el documento activo o consulte al administrador.")

        cursor.execute("UPDATE Documento SET estado = ? WHERE id = ?;", (ESTADO_ACTIVO, documento_id))
        _registrar_bitacora(cursor, usuario_id, documento_id, 'RESTAURADO', "Documento restaurado desde archivo")
        conn.commit()
        return True, "Documento restaurado correctamente."
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error al restaurar: {e}")
        return False, str(e)
    finally:
        if conn:
            conn.close()


def obtener_documentos_archivados(usuario_id):
    """Solo administrador. Devuelve lista vacía si el usuario no es admin."""
    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        if not _es_admin(cursor, usuario_id):
            return []

        cursor.execute("""
            SELECT d.id, d.nro_expediente, d.nro_resolucion, dv.nro_version,
                   d.tipo_documento, d.titulo, o.nombre AS organo_nombre,
                   dv.ruta_unc, d.fecha_archivado, d.motivo_archivo,
                   u.nombre_completo AS archivado_por
            FROM Documento d
            INNER JOIN Documento_versiones dv ON d.id = dv.documento_id AND dv.es_vigente = 1
            LEFT JOIN Organos o ON d.organo_id = o.id
            LEFT JOIN Usuario u ON d.usuario_archivo_id = u.id
            WHERE d.estado = ?
            ORDER BY d.fecha_archivado DESC;
        """, (ESTADO_INACTIVO,))
        filas = cursor.fetchall()

        return [{
            "id": f.id,
            "nro_doc": f.nro_expediente,
            "resolucion": f.nro_resolucion or "---",
            "version": f.nro_version,
            "tipo": f.tipo_documento,
            "titulo": f.titulo,
            "organo": f.organo_nombre or "Órgano no especificado",
            "ruta_pdf": f.ruta_unc,
            "fecha_archivado": f.fecha_archivado.strftime("%d/%m/%Y %H:%M") if f.fecha_archivado else "",
            "motivo": f.motivo_archivo or "",
            "archivado_por": f.archivado_por or "",
        } for f in filas]
    except Exception as e:
        print(f"Error al listar archivados: {e}")
        return []
    finally:
        if conn:
            conn.close()


def obtener_archivado_por_expediente(nro_expediente):
    """Devuelve el archivado más reciente con ese expediente, si existe (para avisar al operador)."""
    conn = None
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TOP 1 d.id, d.titulo
            FROM Documento d
            WHERE UPPER(TRIM(d.nro_expediente)) = UPPER(TRIM(?)) AND d.estado = ?
            ORDER BY d.fecha_archivado DESC;
        """, (nro_expediente, ESTADO_INACTIVO))
        fila = cursor.fetchone()
        return {"id": fila.id, "titulo": fila.titulo} if fila else None
    except Exception as e:
        print(f"Error al buscar archivado por expediente: {e}")
        return None
    finally:
        if conn:
            conn.close()