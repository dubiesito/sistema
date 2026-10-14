import os
import shutil

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTextEdit, QFileDialog, QMessageBox, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics

class UpdateVersionModal(QDialog):
    def __init__(self, datos_documento, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SUBIR NUEVA VERSIÓN")
        self.resize(600, 450) # Más pequeño y directo que el de subida normal
        
        # Guardamos los datos del documento que viene de la tabla o de la búsqueda
        self.datos_documento = datos_documento
        self.ruta_archivo_seleccionado = None

        self._aplicar_estilos()

        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(20)
        layout_principal.setContentsMargins(40, 30, 40, 30)

        # --- ENCABEZADO ---
        lbl_titulo_modal = QLabel("ACTUALIZAR DOCUMENTO")
        lbl_titulo_modal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_titulo_modal.setObjectName("lbl_titulo_modal")
        layout_principal.addWidget(lbl_titulo_modal)

        # --- TARJETA DE INFORMACIÓN (Solo lectura) ---
        marco_info = QFrame()
        marco_info.setObjectName("marco_info")
        layout_info = QVBoxLayout(marco_info)
        
        lbl_aviso = QLabel("Estás a punto de subir una nueva versión para:")
        lbl_aviso.setStyleSheet("color: #64748B; font-size: 12px;")
        layout_info.addWidget(lbl_aviso)

        titulo_doc = self.datos_documento.get('titulo', 'TÍTULO NO DISPONIBLE')
        expediente_doc = self.datos_documento.get('nro_doc', 'S/N')
        
        lbl_titulo_doc = QLabel(titulo_doc)
        lbl_titulo_doc.setWordWrap(True)
        lbl_titulo_doc.setStyleSheet("color: #0F172A; font-weight: bold; font-size: 14px;")
        
        lbl_expediente = QLabel(f"Expediente Nro: {expediente_doc}")
        lbl_expediente.setStyleSheet("color: #16A34A; font-weight: bold; font-size: 13px;")

        layout_info.addWidget(lbl_titulo_doc)
        layout_info.addWidget(lbl_expediente)
        layout_principal.addWidget(marco_info)

        # --- SELECCIÓN DE NUEVO ARCHIVO ---
        box_archivo = QHBoxLayout()
        self.btn_seleccionar_pdf = QPushButton("📂 Seleccionar nuevo PDF")
        self.btn_seleccionar_pdf.clicked.connect(self._seleccionar_archivo)
        
        self.lbl_nombre_archivo = QLabel("Ningún archivo...")
        self.lbl_nombre_archivo.setStyleSheet("color: #475569; font-style: italic;")
        
        box_archivo.addWidget(self.btn_seleccionar_pdf)
        box_archivo.addWidget(self.lbl_nombre_archivo)
        box_archivo.setStretch(0, 1)
        box_archivo.setStretch(1, 2)
        layout_principal.addLayout(box_archivo)

        # --- MOTIVO DE ACTUALIZACIÓN ---
        layout_principal.addWidget(QLabel("Motivo de la actualización (Obligatorio):"))
        self.input_motivo = QTextEdit()
        self.input_motivo.setPlaceholderText("Ej: Se corrigió la firma del decano, se modificó el artículo 3, etc.")
        self.input_motivo.setMaximumHeight(80)
        layout_principal.addWidget(self.input_motivo)

        layout_principal.addStretch()

        # --- BOTONES FINALES ---
        caja_botones = QHBoxLayout()
        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        
        self.btn_guardar = QPushButton("Guardar Nueva Versión")
        self.btn_guardar.setObjectName("btn_guardar_modal")
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.clicked.connect(self._procesar_actualizacion)
        
        caja_botones.addWidget(self.btn_cancelar)
        caja_botones.addWidget(self.btn_guardar)
        layout_principal.addLayout(caja_botones)

    def _aplicar_estilos(self):
        self.setStyleSheet("""
            QDialog { background-color: #E2E8F0; }
            QLabel { color: #1E293B; font-weight: bold; font-size: 13px; }
            QLabel#lbl_titulo_modal { font-size: 18px; font-weight: 900; color: #0F172A; }
            
            /* Tarjeta de información del documento */
            QFrame#marco_info {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 10px;
            }
            
            QTextEdit {
                background-color: #FFFFFF; color: #0F172A;
                border: 2px solid #CBD5E1; border-radius: 6px; padding: 8px;
            }
            QTextEdit:focus { border: 2px solid #3B82F6; background-color: #F8FAFC; }
            
            QPushButton {
                background-color: #F1F5F9; color: #334155; 
                border: 2px solid #CBD5E1; border-radius: 6px; padding: 10px; font-weight: bold;
            }
            QPushButton:hover { background-color: #E2E8F0; }
            
            QPushButton#btn_guardar_modal {
                background-color: #16A34A; color: #FFFFFF; border: none; padding: 10px 20px;
            }
            QPushButton#btn_guardar_modal:hover { background-color: #15803D; }
        """)

    def _seleccionar_archivo(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar Nuevo PDF", "", "Archivos PDF (*.pdf)")
        if ruta:
            self.ruta_archivo_seleccionado = ruta
            nombre_archivo = os.path.basename(ruta)
            metrics = QFontMetrics(self.lbl_nombre_archivo.font())
            texto_truncado = metrics.elidedText(nombre_archivo, Qt.TextElideMode.ElideMiddle, 200)
            self.lbl_nombre_archivo.setText(texto_truncado)
            self.lbl_nombre_archivo.setStyleSheet("color: #16A34A; font-weight: bold;")

    def _procesar_actualizacion(self):
        # 1. Validaciones básicas de selección
        if not self.ruta_archivo_seleccionado:
            QMessageBox.warning(self, "Error", "Debe seleccionar el nuevo archivo PDF.")
            return

        motivo = self.input_motivo.toPlainText().strip()
        if not motivo:
            QMessageBox.warning(self, "Error", "Debe ingresar el motivo de la actualización.")
            return

        import os
        import shutil
        import re
        import db

        nombre_nuevo_archivo = os.path.basename(self.ruta_archivo_seleccionado).upper()
        expediente_esperado = str(self.datos_documento.get("nro_doc", "")).upper()
        resolucion_esperada = str(self.datos_documento.get("resolucion", "")).upper()

        # Limpiamos guiones, diagonales y espacios para hacer la comparación
        exp_limpio = expediente_esperado.replace("-", "").replace(" ", "")
        res_limpia = resolucion_esperada.replace("-", "").replace("/", "").replace(" ", "")

        coincide_exp = exp_limpio and exp_limpio in nombre_nuevo_archivo.replace("-", "").replace(" ", "")
        coincide_res = res_limpia and res_limpia in nombre_nuevo_archivo.replace("-", "").replace("/", "").replace(" ", "")

        # Si el archivo seleccionado no contiene ni el expediente ni la resolución, SE RECHAZA
        if not (coincide_exp or coincide_res):
            QMessageBox.critical(
                self,
                "🚫 Documento No Válido",
                f"El archivo seleccionado:\n'   {nombre_nuevo_archivo}'\n\n"
                f"NO coincide con el Expediente N° {expediente_esperado} ni con la Res. {resolucion_esperada}.\n\n"
                "Por seguridad, la operación se ha cancelado. Seleccione el archivo PDF correcto."
            )
            return 

        self.btn_guardar.setEnabled(False)
        self.btn_guardar.setText("Guardando...")

        try:
            doc_id = self.datos_documento.get("id")
            nueva_version = db.obtener_siguiente_version(doc_id)
            
            # Formatear ruta y mantener orden en Google Drive
            ruta_original = self.datos_documento.get("ruta_pdf", "")
            carpeta_destino = os.path.dirname(ruta_original)
            nombre_base = os.path.basename(ruta_original)
            
            nombre_sin_ext, ext = os.path.splitext(nombre_base)
            nombre_limpio = re.sub(r'_V\d+$', '', nombre_sin_ext)
            
            # Nomenclatura oficial en Drive
            nuevo_nombre = f"{nombre_limpio}_V{nueva_version}{ext}"
            ruta_destino = os.path.join(carpeta_destino, nuevo_nombre)
            
            os.makedirs(carpeta_destino, exist_ok=True)
            shutil.copy2(self.ruta_archivo_seleccionado, ruta_destino)
            
            exito, mensaje = db.actualizar_version_documento(doc_id, nueva_version, ruta_destino, motivo)
            
            if exito:
                QMessageBox.information(self, "Éxito", mensaje)
                self.accept()
            else:
                if os.path.exists(ruta_destino):
                    os.remove(ruta_destino)
                QMessageBox.critical(self, "Error en Base de Datos", f"Se canceló la operación:\n{mensaje}")

        except Exception as e:
            QMessageBox.critical(self, "Error de Sistema", f"No se pudo completar:\n{e}")
            
        finally:
            self.btn_guardar.setEnabled(True)
            self.btn_guardar.setText("Guardar Versión")