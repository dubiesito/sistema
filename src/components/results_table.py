from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt, Signal
import qtawesome as qta  # NUEVO: Librería de íconos profesionales

class ResultsTableWidget(QWidget):
    # Señales para comunicación con main.py
    solicitado_subir_pdf = Signal()
    solicitado_ver_pdf = Signal(dict)
    solicitado_actualizar_pdf = Signal(dict)
    solicitado_archivar = Signal(dict)          # NUEVO
    solicitado_ver_archivados = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 0, 40, 0)
        layout_principal.setSpacing(15)

        # --------------------------------------------------
        # 1. ENCABEZADO DE LA TABLA
        # --------------------------------------------------
        caja_encabezado = QHBoxLayout()

        lbl_titulo_tabla = QLabel("Tabla general de documentos")
        lbl_titulo_tabla.setObjectName("lbl_titulo_tabla")
        caja_encabezado.addWidget(lbl_titulo_tabla)

        caja_encabezado.addStretch()

        # Botón Principal con ícono y estilo UNSAAC
        self.btn_subir = QPushButton(" Subir nuevo PDF")
        self.btn_subir.setIcon(qta.icon('fa5s.plus', color='#FFFFFF'))
        self.btn_subir.setObjectName("btn_subir_pdf")
        self.btn_subir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_subir.clicked.connect(self.solicitado_subir_pdf.emit)
        caja_encabezado.addWidget(self.btn_subir)

        self.btn_archivados = QPushButton(" Ver archivados")
        self.btn_archivados.setIcon(qta.icon('fa5s.archive', color='#9b9b9b'))
        self.btn_archivados.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_archivados.setVisible(False)   # solo se muestra si es admin
        self.btn_archivados.clicked.connect(self.solicitado_ver_archivados.emit)
        caja_encabezado.addWidget(self.btn_archivados)

        layout_principal.addLayout(caja_encabezado)

        # 2. TABLA DE RESULTADOS (6 Columnas)
        self.tabla = QTableWidget()
        self.tabla.setObjectName("tabla_documentos")
        
        # 6 Columnas: Se dividen 'Ver' y 'Editar'
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "Nº de expediente", "Tipo", "Órgano", "Título", "Ver", "Editar", "Archivar"
        ])

        # Ajustes de estiramiento de columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)          
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed) 
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)   
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(6, 75)         
        
        # Ancho fijo de 50px para cada columna de botón
        self.tabla.setColumnWidth(4, 60)
        self.tabla.setColumnWidth(5, 65)

        # Ocultar números de fila
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Quitar el borde de foco punteado feo de Windows
        self.tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout_principal.addWidget(self.tabla)
        
        # Llamamos a los estilos mágicos
        self._aplicar_estilos()

        # ==========================================
        # EXPANSIÓN Y ALTURA DE LA TABLA
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(350)
       

    def set_es_admin(self, es_admin: bool):
        self.btn_archivados.setVisible(es_admin)
 
    def _aplicar_estilos(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #F8FAFC;
            }
            QLabel#lbl_titulo_tabla {
                font-size: 20px;
                font-weight: 900;
                color: #7A1B29; /* Guinda UNSAAC */
                letter-spacing: 0.5px;
            }
            QPushButton#btn_subir_pdf {
                background-color: #7A1B29; 
                color: white; 
                border-radius: 6px; 
                padding: 10px 18px; 
                font-weight: bold; 
                font-size: 13px;
                border: none;
            }
            QPushButton#btn_subir_pdf:hover {
                background-color: #5A121E;
            }
            

            QPushButton#btn_ver_archivados {
                background-color: #475569;
                color: white;
                border-radius: 6px;
                padding: 10px 18px;
                font-weight: bold;
                font-size: 13px;
                border: none;
            }
            QPushButton#btn_ver_archivados:hover {
                background-color: #334155;
            }



            /* ESTILOS DE LA TABLA (MÁXIMO CONTRASTE) */
            QTableWidget {
                background-color: transparent; /* Mata las esquinas blancas fantasmas */
                border: 1px solid #94A3B8; 
                border-radius: 8px;
                gridline-color: #CBD5E1; 
                font-size: 13px;
                font-weight: 500; 
                color: #000000; 
            }
            
            QTableWidget::viewport {
                background-color: #FFFFFF; /* Pinta de blanco solo el interior */
                border-radius: 8px; 
            }
            
            
            QHeaderView::section {
                background-color: #E2E8F0; /* Fondo de cabecera un poco más gris */
                color: #000000; /* Texto de cabecera en negro puro */
                font-weight: 900; /* Cabecera con negrita muy fuerte */
                padding: 10px;
                border: none;
                border-bottom: 2px solid #94A3B8; /* Línea baja de la cabecera más dura */
                border-right: 1px solid #CBD5E1;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #CBD5E1;
            }
            QTableWidget::item:selected {
                background-color: #DBEAFE; /* Azul vivo al seleccionar */
                color: #000000; /* Mantiene el negro puro */
                font-weight: bold; /* Engorda la letra de la fila que elijas */
            }
        """)

    def mostrar_documentos(self, lista_documentos):
        self.tabla.setRowCount(0) 

        for row_idx, doc in enumerate(lista_documentos):
            self.tabla.insertRow(row_idx)

            # Columna 0: Expediente y Versión
            expediente = doc.get('nro_expediente') or doc.get('nro_doc', '')
            version_num = doc.get("version", 1)
            version_str = f"   [v{version_num}]" if version_num else ""
            
            item_nro = QTableWidgetItem(f"{expediente}{version_str}")
            item_nro.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(row_idx, 0, item_nro)

            # Columna 1: Tipo
            item_tipo = QTableWidgetItem(str(doc.get("tipo", "")))
            item_tipo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(row_idx, 1, item_tipo)

            # Columna 2: Órgano
            item_organo = QTableWidgetItem(str(doc.get("organo", "")))
            item_organo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(row_idx, 2, item_organo)

            # Columna 3: Título
            self.tabla.setItem(row_idx, 3, QTableWidgetItem(str(doc.get("titulo", ""))))

            btn_ver = QPushButton()
            btn_ver.setIcon(qta.icon('fa5s.eye', color='#3B82F6')) # Azul
            btn_ver.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_ver.setToolTip("Ver documento PDF")
            btn_ver.setStyleSheet("""
                QPushButton { background-color: transparent; border: none; padding: 5px; }
                QPushButton:hover { background-color: #DBEAFE; border-radius: 4px; }
            """)
            btn_ver.clicked.connect(lambda _, d=doc: self.solicitado_ver_pdf.emit(d))

            cell_ver = QWidget()
            layout_ver = QHBoxLayout(cell_ver)
            layout_ver.setContentsMargins(0, 0, 0, 0)
            layout_ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_ver.addWidget(btn_ver)
            self.tabla.setCellWidget(row_idx, 4, cell_ver)

            # --------------------------------------------------
            # Columna 5: Botón Editar (Lápiz Ámbar Vectorial)
            # --------------------------------------------------
            btn_actualizar = QPushButton()
            btn_actualizar.setIcon(qta.icon('fa5s.edit', color='#F59E0B')) # Ámbar
            btn_actualizar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_actualizar.setToolTip("Subir nueva versión")
            btn_actualizar.setStyleSheet("""
                QPushButton { background-color: transparent; border: none; padding: 5px; }
                QPushButton:hover { background-color: #FEF3C7; border-radius: 4px; }
            """)
            btn_actualizar.clicked.connect(lambda _, d=doc: self.solicitado_actualizar_pdf.emit(d))


            #columna6 el boton archivar
            btn_archivar = QPushButton(" Archivar")
            btn_archivar.setIcon(qta.icon('fa5s.archive', color='#B91C1C'))
            btn_archivar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_archivar.setToolTip("Archivar documento (borrado lógico)")
            btn_archivar.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    color: #B91C1C;
                    border: 1px solid #FCA5A5;
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover { background-color: #FEE2E2; }
            """)
            btn_archivar.clicked.connect(lambda _, d=doc: self.solicitado_archivar.emit(d))

            cell_archivar = QWidget()
            layout_archivar = QHBoxLayout(cell_archivar)
            layout_archivar.setContentsMargins(4, 4, 4, 4)
            layout_archivar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_archivar.addWidget(btn_archivar)
            self.tabla.setCellWidget(row_idx, 6, cell_archivar)

            cell_editar = QWidget()
            layout_editar = QHBoxLayout(cell_editar)
            layout_editar.setContentsMargins(0, 0, 0, 0)
            layout_editar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_editar.addWidget(btn_actualizar)
            self.tabla.setCellWidget(row_idx, 5, cell_editar)