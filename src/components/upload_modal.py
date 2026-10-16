import os
import shutil
import re
import qtawesome as qta
from pdf2image import convert_from_path

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
                               QLineEdit, QComboBox, QPushButton, QTextEdit,
                               QFileDialog, QMessageBox, QDateEdit, QScrollArea, QFrame, QWidget)
from PySide6.QtCore import Qt, QDate, Signal, QRegularExpression, QVariantAnimation
from PySide6.QtGui import QFontMetrics, QRegularExpressionValidator, QColor, QPixmap, QImage
from PIL import Image
from datetime import datetime
import db

class UploadModal(QDialog):
    solicitado_redirigir_actualizacion = Signal(dict)

    def __init__(self, parent=None, usuario_id=None):
        super().__init__(parent)

        self.usuario_id = usuario_id
        
        self.setWindowTitle("SUBIR NUEVO DOCUMENTO - VISTA DIVIDIDA")
        self.resize(1200, 650)  # Ampliamos para el Split-View
        self.ruta_archivo_seleccionado = None

        self._aplicar_estilos()

        # Layout Principal Horizontal (Contenedor Split-View)
        layout_split = QHBoxLayout(self)
        layout_split.setContentsMargins(20, 20, 20, 20)
        layout_split.setSpacing(20)

        # =========================================================
        # SECCIÓN IZQUIERDA: VISOR DE PREVISUALIZACIÓN DE PDF (45%)
        # =========================================================
        box_visor_pdf = QVBoxLayout()
        
        lbl_titulo_preview = QLabel("Previsualización del Documento")
        lbl_titulo_preview.setObjectName("lbl_titulo_modal")
        lbl_titulo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box_visor_pdf.addWidget(lbl_titulo_preview)

        # Área con scroll para la imagen del PDF
        self.scroll_pdf = QScrollArea()
        self.scroll_pdf.setWidgetResizable(True)
        self.scroll_pdf.setStyleSheet("border: 2px solid #CBD5E1; border-radius: 8px; background-color: #64748B;")

        self.lbl_preview_img = QLabel("Seleccione un archivo PDF para previsualizar la primera página aquí...")
        self.lbl_preview_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview_img.setWordWrap(True)
        self.lbl_preview_img.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: bold; padding: 20px;")
        
        self.scroll_pdf.setWidget(self.lbl_preview_img)
        box_visor_pdf.addWidget(self.scroll_pdf)

        layout_split.addLayout(box_visor_pdf, stretch=45)

        # Divisor visual
        linea_divisora = QFrame()
        linea_divisora.setFrameShape(QFrame.Shape.VLine)
        linea_divisora.setStyleSheet("color: #CBD5E1;")
        layout_split.addWidget(linea_divisora)

        # =========================================================
        # SECCIÓN DERECHA: FORMULARIO DE DATOS (55%)
        # =========================================================
        container_formulario = QWidget()
        layout_formulario = QVBoxLayout(container_formulario)
        layout_formulario.setContentsMargins(0, 0, 0, 0)
        layout_formulario.setSpacing(15)

        lbl_titulo_form = QLabel("Datos Extraídos (Edición Manual)")
        lbl_titulo_form.setObjectName("lbl_titulo_modal")
        lbl_titulo_form.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_formulario.addWidget(lbl_titulo_form)

        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(15)
        grid_layout.setVerticalSpacing(12)

        # Selección de Archivo
        box_archivo = QVBoxLayout()
        self.btn_seleccionar_pdf = QPushButton(" Seleccionar archivo PDF")
        self.btn_seleccionar_pdf.setIcon(qta.icon('fa5s.file-pdf', color='#DC2626'))
        self.btn_seleccionar_pdf.clicked.connect(self._seleccionar_archivo)
        
        self.lbl_nombre_archivo = QLabel("Ningún archivo seleccionado")
        self.lbl_nombre_archivo.setStyleSheet("color: #475569; font-size: 11px; font-style: italic;")
        box_archivo.addWidget(self.lbl_nombre_archivo)
        box_archivo.addWidget(self.btn_seleccionar_pdf)
        grid_layout.addLayout(box_archivo, 0, 0)

        # Resolución
        box_res = QVBoxLayout()
        box_res.addWidget(QLabel("Nro. de Resolución:"))
        self.input_resolucion = QLineEdit()
        self.input_resolucion.setPlaceholderText("Ej. R-123-2026-UNSAAC")
        box_res.addWidget(self.input_resolucion)
        grid_layout.addLayout(box_res, 0, 1)

        # Título
        box_titulo = QVBoxLayout()
        box_titulo.addWidget(QLabel("Título del Documento:"))
        self.input_titulo = QTextEdit()
        self.input_titulo.setPlaceholderText("Ingrese aquí la descripción o título completo...")
        self.input_titulo.setMaximumHeight(60) # Lo hacemos un poco más chato para que entre la sumilla
        box_titulo.addWidget(self.input_titulo)
        grid_layout.addLayout(box_titulo, 1, 0, 1, 2)

        # -------- NUEVO CAMPO: SUMILLA OCR --------
        box_sumilla = QVBoxLayout()
        box_sumilla.addWidget(QLabel("Sumilla (Extracto Artículo Primero):"))
        self.input_sumilla = QTextEdit()
        self.input_sumilla.setPlaceholderText("El texto se extraerá aquí automáticamente tras seleccionar el PDF...")
        self.input_sumilla.setMaximumHeight(80) 
        box_sumilla.addWidget(self.input_sumilla)
        grid_layout.addLayout(box_sumilla, 2, 0, 1, 2)
        # ------------------------------------------

        # Tipo
        box_tipo = QVBoxLayout()
        box_tipo.addWidget(QLabel("Tipo de documento:"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["--- Seleccione Tipo ---", "Aprobar", "Acumular", "Crear", "Modificar", "Resolución", "Encargar", "Disponer", "Establecer", "Proponer", "Concluir"])
        box_tipo.addWidget(self.combo_tipo)
        grid_layout.addLayout(box_tipo, 3, 0)

        # Expediente
        box_exp = QVBoxLayout()
        box_exp.addWidget(QLabel("Nro. de Expediente:"))
        self.input_expediente = QLineEdit()
        self.input_expediente.setPlaceholderText("Ej. 26054132")
        box_exp.addWidget(self.input_expediente)
        grid_layout.addLayout(box_exp, 3, 1)

        # Órgano
        box_organo = QVBoxLayout()
        box_organo.addWidget(QLabel("Órgano de procedencia:"))
        self.combo_organo = QComboBox()
        self._cargar_organos()
        box_organo.addWidget(self.combo_organo)
        grid_layout.addLayout(box_organo, 4, 0)

        # Oficio
        box_oficio = QVBoxLayout()
        box_oficio.addWidget(QLabel("Nro. de Oficio:"))
        self.input_oficio = QLineEdit()
        self.input_oficio.setPlaceholderText("Ej. 282-2026-VRIN-UNSAAC")
        box_oficio.addWidget(self.input_oficio)
        grid_layout.addLayout(box_oficio, 4, 1)

        # Fecha
        box_fecha = QVBoxLayout()
        box_fecha.addWidget(QLabel("Fecha de Emisión:"))
        self.input_fecha_emision = QDateEdit()
        self.input_fecha_emision.setCalendarPopup(True)
        self.input_fecha_emision.setSpecialValueText("Seleccione fecha manual")
        self.input_fecha_emision.setDate(QDate.currentDate())
        box_fecha.addWidget(self.input_fecha_emision)
        grid_layout.addLayout(box_fecha, 5, 0, 1, 2)

        layout_formulario.addLayout(grid_layout)
        layout_formulario.addSpacing(10)

        # Botón Subir
        self.btn_guardar = QPushButton(" Subir documento")
        self.btn_guardar.setIcon(qta.icon('fa5s.cloud-upload-alt', color='#FFFFFF'))
        self.btn_guardar.setObjectName("btn_guardar_modal")
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.setMinimumHeight(45)
        self.btn_guardar.clicked.connect(self._procesar_subida)
        
        layout_formulario.addWidget(self.btn_guardar)

        layout_split.addWidget(container_formulario, stretch=55)

        self._aplicar_candados()

    def _renderizar_preview_pdf(self, ruta_pdf):
        """Muestra las páginas 1 y 2 completas, encajadas al ancho para mantener el zoom y scrollear"""
        try:
            from pdf_extractor import RUTA_POPPLER
            from PIL import Image  
            
            # Traemos las 2 primeras hojas enteras (sin recortes)
            images = convert_from_path(ruta_pdf, first_page=1, last_page=2, poppler_path=RUTA_POPPLER)
            
            if not images:
                return

            # Si el documento tiene solo 1 página, mostramos esa. Si tiene 2, las unimos.
            if len(images) == 1:
                img_final = images[0]
            else:
                img1 = images[0]
                img2 = images[1]
                
                # Unimos ambas páginas completas con una franja separadora
                separador_px = 30
                ancho_lienzo = max(img1.width, img2.width)
                alto_lienzo = img1.height + img2.height + separador_px
                
                img_final = Image.new('RGB', (ancho_lienzo, alto_lienzo), color='#94A3B8') 
                img_final.paste(img1, (0, 0))
                img_final.paste(img2, (0, img1.height + separador_px))

            # Preparamos la imagen gigante para la interfaz
            img_final = img_final.convert("RGBA")
            data = img_final.tobytes("raw", "RGBA")
            qimg = QImage(data, img_final.size[0], img_final.size[1], QImage.Format.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimg)
            
            # MAGIA: Al escalar al ancho de 500px, el texto queda GRANDE automáticamente.
            # El alto sobrante simplemente activará la barra de scroll vertical.
            pixmap_escalado = pixmap.scaledToWidth(650, Qt.TransformationMode.SmoothTransformation)
            self.lbl_preview_img.setPixmap(pixmap_escalado)
            self.lbl_preview_img.adjustSize()
            
        except Exception as e:
            self.lbl_preview_img.setText(f"No se pudo cargar la vista previa del PDF:\n{e}")

    def _animar_campo_vacio(self, widget, texto_placeholder=""):
        if isinstance(widget, (QLineEdit, QTextEdit)):
            widget.setPlaceholderText(texto_placeholder)
        
        anim = QVariantAnimation(widget)
        anim.setDuration(1000)
        anim.setStartValue(QColor("#FFFFFF"))
        anim.setKeyValueAt(0.5, QColor("#FECACA"))
        anim.setEndValue(QColor("#FFFFFF"))
        anim.setLoopCount(3) 
        
        def cambiar_color(color):
            widget.setStyleSheet(f"""
                background-color: {color.name()}; 
                border: 2px solid #EF4444; 
                border-radius: 6px; 
                padding: 6px 8px;
                font-size: 12px;
                color: #0F172A;
            """)
            
        anim.valueChanged.connect(cambiar_color)
        anim.finished.connect(lambda: widget.setStyleSheet(""))
        setattr(widget, 'animacion_actual', anim)
        anim.start()

    def _aplicar_candados(self):
        rx_exp = QRegularExpression(r"^\d{8}$")
        self.input_expediente.setValidator(QRegularExpressionValidator(rx_exp, self))

        rx_res = QRegularExpression(r"^(AU|CU|R|VRAC|VRIN|CF|D)-\d{3,4}-\d{4}-UNSAAC$")
        rx_res.setPatternOptions(QRegularExpression.PatternOption.CaseInsensitiveOption)
        self.input_resolucion.setValidator(QRegularExpressionValidator(rx_res, self))
        self.input_resolucion.textEdited.connect(self._forzar_mayus_res)

        rx_ofi = QRegularExpression(r"^(\d{3}-\d{4}-[A-Z]{1,4}-UNSAAC|\d{3}-[A-Z]{1,4}[/-]UNSAAC-\d{4})$")
        rx_ofi.setPatternOptions(QRegularExpression.PatternOption.CaseInsensitiveOption)
        self.input_oficio.setValidator(QRegularExpressionValidator(rx_ofi, self))
        self.input_oficio.textEdited.connect(self._forzar_mayus_ofi)

    def _forzar_mayus_res(self, text):
        pos = self.input_resolucion.cursorPosition()
        self.input_resolucion.setText(text.upper())
        self.input_resolucion.setCursorPosition(pos)

    def _forzar_mayus_ofi(self, text):
        pos = self.input_oficio.cursorPosition()
        self.input_oficio.setText(text.upper())
        self.input_oficio.setCursorPosition(pos)

    def _aplicar_estilos(self):
        self.setStyleSheet("""
            QDialog { background-color: #F8FAFC; }
            QLabel { 
                color: #1E293B; font-weight: bold; font-size: 12px; background: transparent; margin-bottom: 2px;
            }
            QLabel#lbl_titulo_modal { font-size: 16px; font-weight: 900; color: #7A1B29; letter-spacing: 0.5px; }
            QLineEdit, QComboBox, QTextEdit, QDateEdit {
                background-color: #FFFFFF; color: #0F172A; border: 1.5px solid #CBD5E1; border-radius: 6px; padding: 6px 8px; font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateEdit:focus {
                border: 2px solid #7A1B29; background-color: #FFFFFF;
            }
            QPushButton {
                background-color: #FFFFFF; color: #334155; border: 1px solid #CBD5E1; border-radius: 6px; padding: 8px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background-color: #F1F5F9; border: 1px solid #94A3B8; }
            QPushButton#btn_guardar_modal {
                background-color: #7A1B29; color: #FFFFFF; font-weight: 900; font-size: 13px; border: none; border-radius: 6px; padding: 10px;
            }
            QPushButton#btn_guardar_modal:hover { background-color: #5A121E; }
            
            /* -------- NUEVO: ESTILO PARA LAS ALERTAS (QMessageBox) -------- */
            QMessageBox {
                background-color: #1E293B; /* Azul oscuro casi negro */
                border: 2px solid #334155;
            }
            QMessageBox QLabel {
                color: #FFFFFF; /* Texto blanco puro */
                font-size: 13px;
                font-weight: normal;
            }
            QMessageBox QPushButton {
                background-color: #3B82F6; /* Botón azul brillante */
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 6px 20px;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #2563EB; /* Botón azul más oscuro al pasar el mouse */
            }
        """)

    def _cargar_organos(self):
        try:
            self.combo_organo.addItem("--- Seleccione Órgano ---", None)
            organos = db.obtener_organos_activos()
            for org in organos:
                self.combo_organo.addItem(org["nombre"], org["id"])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo cargar la lista de órganos:\n{e}")

    def _actualizar_label_archivo(self, nombre_archivo: str):
        metrics = QFontMetrics(self.lbl_nombre_archivo.font())
        texto_truncado = metrics.elidedText(nombre_archivo, Qt.TextElideMode.ElideMiddle, 200)
        self.lbl_nombre_archivo.setText(texto_truncado)
        self.lbl_nombre_archivo.setToolTip(nombre_archivo)
        self.lbl_nombre_archivo.setStyleSheet("color: #7A1B29; font-weight: bold; font-size: 11px;")

    def _seleccionar_archivo(self):
        ruta_archivo, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Documento PDF", "", "Archivos PDF (*.pdf)"
        )
        
        if ruta_archivo:
            self.ruta_archivo_seleccionado = ruta_archivo
            nombre_archivo = os.path.basename(ruta_archivo)
            self._actualizar_label_archivo(nombre_archivo)
            
            # 1. Mostrar vista previa del PDF inmediatamente
            self._renderizar_preview_pdf(ruta_archivo)
            
            # 2. Iniciar extracción por IA
            self.btn_seleccionar_pdf.setText(" Analizando...")
            self.btn_seleccionar_pdf.setIcon(qta.icon('fa5s.brain', color='#3B82F6')) 
            self.btn_seleccionar_pdf.setEnabled(False)
            
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents() 
            
            try:
                from pdf_extractor import extraer_datos_inteligentes_pdf
                datos_extraidos = extraer_datos_inteligentes_pdf(ruta_archivo)
                
                if datos_extraidos:
                    if datos_extraidos.get("expediente"): 
                        self.input_expediente.setText(datos_extraidos["expediente"])
                    else:
                        self.input_expediente.clear()
                        self._animar_campo_vacio(self.input_expediente, "Ingrese 00000000 si no tiene")

                    if datos_extraidos.get("resolucion"): 
                        self.input_resolucion.setText(datos_extraidos["resolucion"])
                    else:
                        self.input_resolucion.clear()
                        self._animar_campo_vacio(self.input_resolucion, "Falta rellenar manual")

                    if datos_extraidos.get("oficio"): 
                        self.input_oficio.setText(datos_extraidos["oficio"])
                    else:
                        self.input_oficio.clear()
                        self._animar_campo_vacio(self.input_oficio, "Opcional (Dejar en blanco si no hay)")

                    if datos_extraidos.get("titulo"): 
                        self.input_titulo.setPlainText(datos_extraidos["titulo"])
                    else:
                        self.input_titulo.clear()
                        self._animar_campo_vacio(self.input_titulo, "Revisar y copiar el título manualmente")

                    # -------- NUEVO: LLENAR SUMILLA OCR --------
                    if datos_extraidos.get("asunto_ocr"):
                        self.input_sumilla.setPlainText(datos_extraidos["asunto_ocr"])
                    else:
                        self.input_sumilla.clear()
                        self.input_sumilla.setPlaceholderText("No se detectó el texto del Artículo Primero automáticamente.")
                    # -------------------------------------------

                    if datos_extraidos.get("fecha"): 
                        self.input_fecha_emision.setDate(datos_extraidos["fecha"])
                    else:
                        self.input_fecha_emision.setDate(self.input_fecha_emision.minimumDate())

                    if datos_extraidos.get("tipo"):
                        idx_tipo = self.combo_tipo.findText(datos_extraidos["tipo"])
                        if idx_tipo >= 0: 
                            self.combo_tipo.setCurrentIndex(idx_tipo)
                        else:
                            self.combo_tipo.setCurrentIndex(0)
                            self._animar_campo_vacio(self.combo_tipo)
                    else:
                        self.combo_tipo.setCurrentIndex(0)

                    if datos_extraidos.get("sigla_organo"):
                        dic_org = {"AU": "Asamblea Universitaria", "CU": "Consejo Universitario", "R": "Rectorado", "VRAC": "Vicerrectorado Académico", "VRIN": "Vicerrectorado de Investigación", "CF": "Consejo de Facultad", "D": "Decanato"}
                        nombre_organo = dic_org.get(datos_extraidos["sigla_organo"])
                        if nombre_organo:
                            idx_org = self.combo_organo.findText(nombre_organo)
                            if idx_org >= 0: 
                                self.combo_organo.setCurrentIndex(idx_org)
                        else:
                            self.combo_organo.setCurrentIndex(0)
                    else:
                        self.combo_organo.setCurrentIndex(0)
                            
            except Exception as e:
                print(f"Error en la extracción OCR: {e}")
            finally:
                self.btn_seleccionar_pdf.setText(" Seleccionar archivo PDF")
                self.btn_seleccionar_pdf.setIcon(qta.icon('fa5s.file-pdf', color='#DC2626'))
                self.btn_seleccionar_pdf.setEnabled(True)

    def _procesar_subida(self):
        if self.combo_tipo.currentIndex() == 0:
            QMessageBox.warning(self, "Validación", "¡Alto! Debe seleccionar el 'Tipo de documento' manualmente.")
            self.combo_tipo.setFocus()
            return

        if self.combo_organo.currentData() is None:
            QMessageBox.warning(self, "Validación", "¡Alto! Debe seleccionar el 'Órgano de procedencia' manualmente.")
            self.combo_organo.setFocus()
            return

        if self.input_fecha_emision.date() == self.input_fecha_emision.minimumDate():
            QMessageBox.warning(self, "Validación", "¡Alto! Debe ingresar una 'Fecha de Emisión' válida antes de subir el documento.")
            self.input_fecha_emision.setFocus()
            return

        if not self.input_expediente.hasAcceptableInput():
            QMessageBox.warning(self, "Validación", "El Nro. de Expediente debe tener exactamente 8 números.")
            self.input_expediente.setFocus()
            return

        if not self.input_resolucion.hasAcceptableInput():
            QMessageBox.warning(self, "Validación", "El Nro. de Resolución es inválido.\nFormatos aceptados: R-1091-2026-UNSAAC, etc.")
            self.input_resolucion.setFocus()
            return

        oficio = self.input_oficio.text().strip()
        if oficio and not self.input_oficio.hasAcceptableInput():
            QMessageBox.warning(self, "Validación", "El Nro. de Oficio es inválido.\nEjemplos permitidos:\n282-2026-VRIN-UNSAAC\n298-OPU/UNSAAC-2008")
            self.input_oficio.setFocus()
            return

        titulo = self.input_titulo.toPlainText().strip().upper()
        if len(titulo.split()) < 5:
            QMessageBox.warning(self, "Validación", "El Título es muy corto. Ingrese al menos 5 palabras.")
            self.input_titulo.setFocus()
            return

        nro_expediente_ingresado = self.input_expediente.text().strip()
        
        if nro_expediente_ingresado:
            import db
            doc_existente = db.obtener_documento_por_expediente(nro_expediente_ingresado)
            
            if doc_existente:
                QMessageBox.information(
                    self, 
                    "Expediente Existente", 
                    f"El expediente Nro '{nro_expediente_ingresado}' ya cuenta con un registro previo.\n\n"
                    "El sistema cambiará al modo de actualización de versión."
                )
                self.solicitado_redirigir_actualizacion.emit(doc_existente)
                self.reject() 
                return   
                 
            archivado = db.obtener_archivado_por_expediente(nro_expediente_ingresado)
            if archivado:
                QMessageBox.information(
                    self, "Expediente archivado",
                    f"El expediente {nro_expediente_ingresado} tiene un registro archivado "
                    f"(ID {archivado['id']}).\n\n"
                    "El nuevo documento se registrará por separado y su PDF llevará "
                    "un sufijo de reingreso en la carpeta de red."
                )
        if not self.ruta_archivo_seleccionado:
            QMessageBox.warning(self, "Error", "Debe seleccionar un archivo PDF.")
            return

        if not os.path.exists(self.ruta_archivo_seleccionado):
            QMessageBox.warning(self, "Error", "El archivo ya no existe. Vuelva a seleccionarlo.")
            return

        resolucion = self.input_resolucion.text().strip().upper()
        expediente = self.input_expediente.text().strip().upper()
        tipo_doc = self.combo_tipo.currentText().strip()
        nombre_organo = self.combo_organo.currentText().strip()
        sumilla_texto = self.input_sumilla.toPlainText().strip() # <-- CAPTURAMOS LA SUMILLA

        datos = {
            "tipo": tipo_doc,
            "resolucion": resolucion,
            "expediente": expediente,
            "oficio": oficio.upper(),
            "titulo": titulo,
            "organo_id": self.combo_organo.currentData(),
            "fecha_emision": self.input_fecha_emision.date().toString("yyyy-MM-dd"),
            "asunto_ocr": sumilla_texto # <-- LO ENVIAMOS AL DICCIONARIO
        }
        
        self.btn_guardar.setEnabled(False)
        self.btn_guardar.setText(" Subiendo...")

        try:
            res_limpia = resolucion.replace("/", "-").replace("\\", "-")
            exp_limpio = expediente.replace("/", "-").replace("\\", "-")
            titulo_limpio = re.sub(r'[\\/*?:"<>|]', "", titulo)
            
            if len(titulo_limpio) > 150:
                titulo_limpio = titulo_limpio[:150] + "..."
            
            nombre_destino = f"{res_limpia}-{exp_limpio}-{titulo_limpio}.pdf"

            carpeta_limpia = nombre_organo.upper()
            carpeta_limpia = carpeta_limpia.replace("Á","A").replace("É","E").replace("Í","I").replace("Ó","O").replace("Ú","U")
            
            BASE_RED = r"G:\Mi unidad\Resoluciones_Modernizacion"
            RUTA_CARPETA_RED = os.path.join(BASE_RED, carpeta_limpia)
            ruta_destino = os.path.join(RUTA_CARPETA_RED, nombre_destino)
            
            os.makedirs(RUTA_CARPETA_RED, exist_ok=True)
            shutil.copy2(self.ruta_archivo_seleccionado, ruta_destino)

            exito, mensaje_error = db.insertar_documento(datos, ruta_destino, self.usuario_id)

            if exito:
                QMessageBox.information(self, "Éxito", f"Documento subido correctamente a:\n{carpeta_limpia}")
                self.accept()
            else:
                if os.path.exists(ruta_destino):
                    os.remove(ruta_destino)
                QMessageBox.critical(self, "Error en Base de Datos", f"No se pudo guardar:\n{mensaje_error}")
        
        except Exception as e:
            QMessageBox.critical(self, "Error de sistema", f"No se pudo completar:\n{e}")
            
        finally:
            self.btn_guardar.setEnabled(True)
            self.btn_guardar.setText(" Subir documento")


def _ruta_sin_colision(ruta):
    """Si el PDF ya existe en la carpeta de red, agrega un sufijo de reingreso.
    Nunca sobrescribe un archivo existente (evita pérdida de documentos archivados)."""
    if not os.path.exists(ruta):
        return ruta
    base, ext = os.path.splitext(ruta)
    sufijo = datetime.now().strftime("_REINGRESO_%Y%m%d_%H%M%S")
    candidata = f"{base}{sufijo}{ext}"
    contador = 2
    while os.path.exists(candidata):
        candidata = f"{base}{sufijo}_{contador}{ext}"
        contador += 1
    return candidata