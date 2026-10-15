import os
import shutil
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QFileDialog, QMessageBox, QFrame, QComboBox,
    QScrollArea, QWidget
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QWheelEvent
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtPdf import QPdfDocument

import db

# --- CLASE ESPECIAL PARA DESACTIVAR LA RUEDA EN EL SELECTOR ---
class NoScrollComboBox(QComboBox):
    """Combobox personalizado que ignora la rueda del mouse para evitar cambios accidentales"""
    def wheelEvent(self, event: QWheelEvent):
        event.ignore() # Ignora el scroll de la rueda sobre el selector


class PdfViewerModal(QDialog):
    def __init__(self, datos_doc, parent=None):
        super().__init__(parent)
        self.datos = datos_doc
        self.historial = []
        self.ruta_pdf_actual = self.datos.get('ruta_pdf', '')
        
        self.setWindowTitle("Detalle del Documento")
        self.resize(900, 600)
        
        self._init_ui()
        self._aplicar_estilos()
        self._cargar_historial_y_pdf()

    def _init_ui(self):
        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(20)

        # --------------------------------------------------
        # LADO IZQUIERDO: Visor de PDF
        # --------------------------------------------------
        self.pdf_document = QPdfDocument(self)
        self.pdf_view = QPdfView(self)
        self.pdf_view.setDocument(self.pdf_document)
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        
        layout_principal.addWidget(self.pdf_view, stretch=3)

        # --------------------------------------------------
        # LADO DERECHO: Tarjetas de información
        # --------------------------------------------------
        layout_derecho = QVBoxLayout()
        layout_derecho.setSpacing(12)
        layout_derecho.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 1. TÍTULO PRINCIPAL (En la cima de todo)
        titulo_texto = self.datos.get('titulo', 'TÍTULO NO DISPONIBLE')
        lbl_titulo_main = QLabel(titulo_texto)
        lbl_titulo_main.setObjectName("card_titulo_main")
        lbl_titulo_main.setWordWrap(True)
        lbl_titulo_main.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout_derecho.addWidget(lbl_titulo_main)

        # -------- NUEVO: TARJETA DE SUMILLA OCR --------
        sumilla_box = QFrame()
        sumilla_box.setObjectName("card_box")
        sumilla_layout = QVBoxLayout(sumilla_box)
        sumilla_layout.setContentsMargins(10, 8, 10, 8)
        
        lbl_sumilla_title = QLabel("📌 Asunto / Sumilla (Extracto):")
        lbl_sumilla_title.setObjectName("card_title")
        lbl_sumilla_title.setStyleSheet("color: #3B82F6;") # Azul para resaltar
        
        self.scroll_sumilla = QScrollArea()
        self.scroll_sumilla.setWidgetResizable(True)
        self.scroll_sumilla.setMaximumHeight(100) # Fija la altura máxima para que no empuje todo
        self.scroll_sumilla.setStyleSheet("border: none; background: transparent;")
        
        self.lbl_sumilla = QLabel("Cargando sumilla...")
        self.lbl_sumilla.setWordWrap(True)
        self.lbl_sumilla.setObjectName("card_value")
        self.lbl_sumilla.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.scroll_sumilla.setWidget(self.lbl_sumilla)
        
        sumilla_layout.addWidget(lbl_sumilla_title)
        sumilla_layout.addWidget(self.scroll_sumilla)
        
        layout_derecho.addWidget(sumilla_box)
        # -----------------------------------------------

        # 2. Selector de Versión (Usando nuestra clase sin scroll de rueda)
        self.combo_version = NoScrollComboBox()
        self.combo_version.setObjectName("combo_version")
        self.combo_version.currentIndexChanged.connect(self._al_cambiar_version)
        layout_derecho.addWidget(self.combo_version)

        # 3. Tarjeta del Motivo de Cambio (Solo visible en V2 o con motivo)
        self.box_motivo = QFrame()
        self.box_motivo.setObjectName("card_box_motivo")
        layout_motivo = QVBoxLayout(self.box_motivo)
        layout_motivo.setContentsMargins(10, 8, 10, 8)
        
        lbl_motivo_title = QLabel("📝 Motivo de actualización")
        lbl_motivo_title.setObjectName("card_title_motivo")
        
        self.lbl_motivo_val = QLabel("Sin especificación")
        self.lbl_motivo_val.setObjectName("card_value_motivo")
        self.lbl_motivo_val.setWordWrap(True)
        
        layout_motivo.addWidget(lbl_motivo_title)
        layout_motivo.addWidget(self.lbl_motivo_val)
        
        self.box_motivo.setVisible(False)
        layout_derecho.addWidget(self.box_motivo)

        # 4. Órgano
        organo_nombre = self.datos.get('organo', 'Sin Órgano')
        lbl_organo = QLabel(organo_nombre)
        lbl_organo.setObjectName("card_info")
        lbl_organo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_derecho.addWidget(lbl_organo)

        # 5. Nro de Expediente
        exp_box = QFrame()
        exp_box.setObjectName("card_box")
        exp_layout = QVBoxLayout(exp_box)
        exp_layout.setContentsMargins(10, 8, 10, 8)
        lbl_exp_title = QLabel("Nro de expediente")
        lbl_exp_title.setObjectName("card_title")
        lbl_exp_val = QLabel(str(self.datos.get('nro_doc', '---')))
        lbl_exp_val.setObjectName("card_value")
        exp_layout.addWidget(lbl_exp_title)
        exp_layout.addWidget(lbl_exp_val)
        layout_derecho.addWidget(exp_box)

        # 6. Nro de Resolución
        res_box = QFrame()
        res_box.setObjectName("card_box")
        res_layout = QVBoxLayout(res_box)
        res_layout.setContentsMargins(10, 8, 10, 8)
        lbl_res_title = QLabel("Nro de Resolución")
        lbl_res_title.setObjectName("card_title")
        lbl_res_val = QLabel(str(self.datos.get('resolucion', '---')))
        lbl_res_val.setObjectName("card_value")
        res_layout.addWidget(lbl_res_title)
        res_layout.addWidget(lbl_res_val)
        layout_derecho.addWidget(res_box)

        layout_derecho.addStretch()

        # 7. Botón DESCARGAR PDF
        btn_descargar = QPushButton("DESCARGAR PDF")
        btn_descargar.setObjectName("btn_descargar")
        btn_descargar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_descargar.clicked.connect(self._descargar_pdf)
        layout_derecho.addWidget(btn_descargar)

        layout_principal.addLayout(layout_derecho, stretch=1)

    def _cargar_historial_y_pdf(self):
        doc_id = self.datos.get('id')
        self.historial = db.obtener_historial_versiones(doc_id)

        self.combo_version.blockSignals(True)
        self.combo_version.clear()

        if self.historial:
            for item in self.historial:
                tag = " (Vigente)" if item.get('es_vigente') else ""
                texto = f"Versión {item.get('version')}{tag}"
                self.combo_version.addItem(texto, item)
            
            self.combo_version.blockSignals(False)
            self._al_cambiar_version(0)
        else:
            v_num = self.datos.get('version', 1)
            self.combo_version.addItem(f"Versión {v_num}")
            self.combo_version.blockSignals(False)
            self.lbl_sumilla.setText("Cargando versión heredada...")
            self._cargar_pdf(self.ruta_pdf_actual)

    def _al_cambiar_version(self, index):
        if index < 0 or not self.historial:
            return

        version_info = self.historial[index]
        nro_version = version_info.get('version', 1)
        motivo = version_info.get('motivo', '').strip()
        ruta_pdf = version_info.get('ruta_pdf', '')
        
        # -------- NUEVO: CAPTURAR EL ASUNTO OCR --------
        asunto_ocr = version_info.get('asunto_ocr', '')

        self.ruta_pdf_actual = ruta_pdf

        # Mostrar motivo si existe
        if nro_version > 1 or (motivo and motivo.lower() != "versión original / sin motivo"):
            self.lbl_motivo_val.setText(motivo if motivo else "Sin motivo registrado.")
            self.box_motivo.setVisible(True)
        else:
            self.box_motivo.setVisible(False)

        # Mostrar sumilla
        if asunto_ocr and asunto_ocr.strip():
            self.lbl_sumilla.setText(asunto_ocr.strip())
            self.lbl_sumilla.setStyleSheet("color: #111111; font-size: 12px;")
        else:
            self.lbl_sumilla.setText("Sin extracto de sumilla disponible en la base de datos para este documento.")
            self.lbl_sumilla.setStyleSheet("color: #94A3B8; font-size: 11px; font-style: italic;")

        self._cargar_pdf(ruta_pdf)

    def _cargar_pdf(self, ruta_pdf):
        if ruta_pdf and os.path.exists(ruta_pdf):
            self.pdf_document.load(ruta_pdf)
        else:
            QMessageBox.warning(self, "Aviso", f"No se encontró el archivo PDF:\n{ruta_pdf}")

    def _descargar_pdf(self):
        if not self.ruta_pdf_actual or not os.path.exists(self.ruta_pdf_actual):
            QMessageBox.critical(self, "Error", "El archivo origen no existe en el almacenamiento.")
            return

        nombre_sugerido = os.path.basename(self.ruta_pdf_actual)
        ruta_destino, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF", nombre_sugerido, "Archivos PDF (*.pdf)"
        )

        if ruta_destino:
            try:
                shutil.copy2(self.ruta_pdf_actual, ruta_destino)
                
                # Actualiza la fecha de modificación al momento exacto de la descarga
                os.utime(ruta_destino, None)

                QMessageBox.information(self, "Éxito", "¡El archivo se descargó correctamente!")
                
                import subprocess
                ruta_windows = os.path.normpath(ruta_destino)
                subprocess.Popen(f'explorer /select,"{ruta_windows}"')
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo descargar: {e}")

    def _aplicar_estilos(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #d9d9d9;
            }
            QPdfView {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            /* Tarjeta del Título Principal */
            QLabel#card_titulo_main {
                background-color: #ffffff;
                color: #0F172A;
                font-weight: 900;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                border-left: 5px solid #3B82F6;
            }
            /* Selector de Versión */
            QComboBox#combo_version {
                background-color: #ffffff;
                color: #111111;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
            }
            QComboBox#combo_version::drop-down {
                border: none;
                padding-right: 10px;
            }
            QLabel#card_info {
                background-color: #ffffff;
                color: #111111;
                font-weight: bold;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
            }
            QFrame#card_box {
                background-color: #ffffff;
                border-radius: 6px;
            }
            QFrame#card_box_motivo {
                background-color: #FEF3C7;
                border: 1px solid #F59E0B;
                border-radius: 6px;
            }
            QLabel#card_title_motivo {
                color: #B45309;
                font-size: 11px;
                font-weight: bold;
            }
            QLabel#card_value_motivo {
                color: #78350F;
                font-size: 12px;
                font-weight: 500;
            }
            QLabel#card_title {
                color: #222222;
                font-size: 12px;
                font-weight: bold;
            }
            QLabel#card_value {
                color: #111111;
                font-size: 13px;
            }
            QPushButton#btn_descargar {
                background-color: #29c5f6;
                color: #000000;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 6px;
                padding: 12px;
            }
            QPushButton#btn_descargar:hover {
                background-color: #00b4ec;
            }
        """)