import sys
import os

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QInputDialog
from PySide6.QtGui import QIcon
from components.header import HeaderWidget
from components.search_bar import SearchBarWidget
from components.results_table import ResultsTableWidget
from components.update_modal import UpdateVersionModal
from components.upload_modal import UploadModal
from components.archivados_modal import ArchivadosModal
from PySide6.QtWidgets import QApplication, QMessageBox

import db

USUARIO_ACTIVO = None
USUARIO_ACTIVO_ID = None

class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.usuario_id = USUARIO_ACTIVO['id']
        
        self.setWindowTitle("Sistema de Gestión Documental - UNSAAC")
        self.resize(1050, 650)

        ruta_script = os.path.dirname(os.path.abspath(__file__))
        ruta_icono = os.path.join(ruta_script, "logo.ico") 
        if os.path.exists(ruta_icono):
            self.setWindowIcon(QIcon(ruta_icono))

        # Contenedor principal
        widget_central = QWidget()
        layout_principal = QVBoxLayout(widget_central)
        layout_principal.setContentsMargins(40, 30, 40, 30)
        layout_principal.setSpacing(25)
 
        # 1. Header
        self.header = HeaderWidget()
        layout_principal.addWidget(self.header)

        # 2. Barra de búsqueda
        self.search_bar = SearchBarWidget()
        layout_principal.addWidget(self.search_bar)
        
        # 3. Tabla General de Resultados
        self.tabla_resultados = ResultsTableWidget()
        self.tabla_resultados.solicitado_subir_pdf.connect(self.al_hacer_clic_subir_pdf)
        self.tabla_resultados.solicitado_ver_pdf.connect(self.al_ver_documento)
        self.tabla_resultados.solicitado_archivar.connect(self.al_archivar)
        self.tabla_resultados.solicitado_ver_archivados.connect(self.al_ver_archivados)
        
        layout_principal.addWidget(self.tabla_resultados)


        self.tabla_resultados.set_es_admin(
            bool(USUARIO_ACTIVO) and USUARIO_ACTIVO.get("rol") == db.ROL_ADMIN
        )
        
        # Conectar señales de la barra de búsqueda
        self.search_bar.texto_cambiado.connect(self.al_buscar_tiempo_real)
        self.search_bar.buscar_solicitado.connect(self.al_buscar_explicita)
        self.search_bar.filtros_cambiados.connect(self.al_cambiar_filtros)
        self.tabla_resultados.solicitado_actualizar_pdf.connect(self.abrir_modal_version)

        layout_principal.addStretch()
        
        # CARGA INICIAL DE DATOS
        self.cargar_datos_iniciales()
        
        # OBLIGATORIO: Asignar el widget central a la ventana principal
        self.setCentralWidget(widget_central)

    
    def al_archivar(self, doc):
        confirmar = QMessageBox.question(
            self, "Archivar documento",
            f"¿Archivar el expediente {doc.get('nro_doc')}?\n\n"
            "Dejará de aparecer en la tabla general. El PDF y su historial se conservan "
            "y solo el administrador podrá verlo.",
        )
        if confirmar != QMessageBox.StandardButton.Yes:
            return

        motivo, ok = QInputDialog.getText(self, "Motivo del archivado", "Indique el motivo (obligatorio):")
        if not ok or not motivo.strip():
            return

        exito, mensaje = db.archivar_documento(doc['id'], USUARIO_ACTIVO_ID, motivo)
        if exito:
            self.cargar_datos_iniciales()
        else:
            QMessageBox.warning(self, "No se pudo archivar", mensaje)

    def al_ver_archivados(self):
        from components.archivados_modal import ArchivadosModal
        ArchivadosModal(USUARIO_ACTIVO_ID, self).exec()
        self.cargar_datos_iniciales()
    
    
    def cargar_datos_iniciales(self):
        print("Conectando a SQL Server para traer documentos...")
        datos = db.obtener_documentos_tabla()
        
        if datos:
            self.tabla_resultados.mostrar_documentos(datos)
            print(f"¡Se cargaron {len(datos)} documentos con éxito!")
        else:
            print("No se encontraron documentos o hubo un error de conexión.")
       
    def al_buscar_tiempo_real(self, texto):
        filtros = self.search_bar.obtener_filtros()
        documentos_encontrados = db.buscar_documentos(texto, filtros)
        self.tabla_resultados.mostrar_documentos(documentos_encontrados)

    def al_buscar_explicita(self, texto): 
        """Se ejecuta al presionar Enter o el botón Buscar"""
        filtros = self.search_bar.obtener_filtros()
        datos = db.buscar_documentos(texto, filtros)
        self.tabla_resultados.mostrar_documentos(datos)

    def al_cambiar_filtros(self, filtros):
        """Se ejecuta cuando cambia algún filtro"""
        texto = self.search_bar.obtener_texto_busqueda()
        if texto or texto == "":
            self.al_buscar_tiempo_real(texto)

    def al_hacer_clic_subir_pdf(self, *args):
        if getattr(self, '_modal_abierto', False):
            return
            
        self._modal_abierto = True
        try:
            modal = UploadModal(self, usuario_id=self.usuario_id)
            # Conectamos la señal de redirección inteligente antes de ejecutar
            modal.solicitado_redirigir_actualizacion.connect(self.abrir_modal_version)
            
            if modal.exec() == 1: 
                print("Refrescando la tabla con el nuevo documento...")
                self.cargar_datos_iniciales()
        finally:
            self._modal_abierto = False

    def al_ver_documento(self, datos_documento):
        try:
            from components.pdf_viewer_modal import PdfViewerModal
            modal = PdfViewerModal(datos_documento, self)
            modal.exec()
        except Exception as e:
            print(f"❌ Error al intentar abrir el visor de PDF: {e}")

    def abrir_modal_version(self, datos_documento):
        modal = UpdateVersionModal(datos_documento, self)
        if modal.exec():
            # CORRECCIÓN: Actualizar la tabla sin provocar un crash
            self.cargar_datos_iniciales()

def verificar_seguridad():
    global USUARIO_ACTIVO, USUARIO_ACTIVO_ID

    try:
        computadora_actual = os.getlogin()
    except Exception:
        computadora_actual = "DESCONOCIDO"

    usuario_db = db.obtener_usuario_por_red(computadora_actual)

    if not usuario_db:
        return False, f"ACCESO DENEGADO\n\nLa computadora '{computadora_actual}' no está autorizada para ingresar al Sistema de Resoluciones de la UNSAAC."

    if usuario_db['activo'] == 0:
        return False, f"ACCESO BLOQUEADO\n\nEl usuario '{usuario_db['nombre_completo']}' se encuentra inactivo."

    USUARIO_ACTIVO = usuario_db              # diccionario: id, nombre_completo, activo, rol
    USUARIO_ACTIVO_ID = usuario_db['id']     # solo el id, para auditoría
    return True, f"Bienvenido/a, {usuario_db['nombre_completo']}"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    acceso_permitido, mensaje = verificar_seguridad()
    
    if not acceso_permitido:
        msg_error = QMessageBox()
        msg_error.setIcon(QMessageBox.Icon.Critical)
        msg_error.setWindowTitle("Seguridad Institucional")
        msg_error.setText(mensaje)
        msg_error.exec()
        sys.exit() # Cierre inmediato si no tiene permiso
        
    print(mensaje) # Imprime en consola "Bienvenido/a, Administrador"
    
    ruta_script = os.path.dirname(os.path.abspath(__file__))
    ruta_icono = os.path.join(ruta_script, "logo.ico") 
    if os.path.exists(ruta_icono):
        app.setWindowIcon(QIcon(ruta_icono))
    
    # Cargar estilos QSS
    ruta_qss = os.path.join(ruta_script, "styles.qss")
    try:
        with open(ruta_qss, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"No se encontró el archivo styles.qss en {ruta_qss}")
        
 
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())