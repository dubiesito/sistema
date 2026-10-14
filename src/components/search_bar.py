from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QComboBox, QRadioButton, QPushButton)
from PySide6.QtGui import QIntValidator
from PySide6.QtCore import Signal
import db


class SearchBarWidget(QWidget):
    texto_cambiado = Signal(str)
    buscar_solicitado = Signal(str)
    filtros_cambiados = Signal(dict)

    ANIO_MINIMO = 1900
    ANIO_MAXIMO = 2029

    def __init__(self, parent=None):
        super().__init__(parent)

        self._bloquear_desmarcar = False
        self._actualizando_filtros = False

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(15)

        # BARRA DE BUSQUEDA
        caja_busqueda = QHBoxLayout()
        caja_busqueda.setContentsMargins(40, 0, 40, 0)
        caja_busqueda.setSpacing(10)

        self.barra_busqueda = QLineEdit()
        self.barra_busqueda.setObjectName("barra_busqueda")
        self.barra_busqueda.setPlaceholderText(
            "Busca documentos por asunto, numero de expediente, resolucion, etc."
        )
        self.barra_busqueda.textChanged.connect(self._on_texto_cambiado)
        self.barra_busqueda.returnPressed.connect(self._ejecutar_busqueda)
        caja_busqueda.addWidget(self.barra_busqueda)

        self.btn_buscar = QPushButton("Buscar")
        self.btn_buscar.setObjectName("btn_buscar")
        self.btn_buscar.clicked.connect(self._ejecutar_busqueda)
        caja_busqueda.addWidget(self.btn_buscar)

        layout_principal.addLayout(caja_busqueda)

        # FILTROS RAPIDOS
        caja_filtros = QHBoxLayout()
        caja_filtros.setContentsMargins(40, 0, 40, 0)
        caja_filtros.setSpacing(12)

        lbl_filtros = QLabel("Filtros rapidos:")
        lbl_filtros.setObjectName("lbl_filtros_titulo")
        caja_filtros.addWidget(lbl_filtros)

        self.radio_todos = QRadioButton("Todos")
        self.radio_todos.setChecked(True)
        self.radio_todos.toggled.connect(self._reiniciar_filtros)
        caja_filtros.addWidget(self.radio_todos)

        # A) FILTRO AÑO
        self.combo_anio = QComboBox()
        self.combo_anio.setEditable(True)
        self.combo_anio.setInsertPolicy(QComboBox.NoInsert)

        anio_actual = datetime.now().year
        for anio in range(anio_actual, anio_actual - 15, -1):
            self.combo_anio.addItem(str(anio))

        line_edit_anio = self.combo_anio.lineEdit()
        line_edit_anio.setPlaceholderText("Año: Todos")
        line_edit_anio.setValidator(
            QIntValidator(self.ANIO_MINIMO, self.ANIO_MAXIMO, self)
        )
        line_edit_anio.editingFinished.connect(self._validar_anio_ingresado)

        self.combo_anio.setCurrentIndex(-1)

        caja_filtros.addWidget(self.combo_anio)

        # B) FILTRO MES
        self.combo_mes = QComboBox()
        meses = ["Mes: Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.combo_mes.addItems(meses)
        caja_filtros.addWidget(self.combo_mes)

        # C) FILTRO TIPO
        self.combo_tipo = QComboBox()
        tipos_doc = ["Tipo: Todos", "Aprobar", "Acumular", "Crear", "Encargar",
                     "Modificar", "Disponer", "Establecer"]
        self.combo_tipo.addItems(tipos_doc)
        caja_filtros.addWidget(self.combo_tipo)

        # D) FILTRO ORGANO
        self.combo_organo = QComboBox()
        self.combo_organo.addItem("Organo: Todos")
        organos = db.obtener_organos_activos()
        for org in organos:
            self.combo_organo.addItem(org["nombre"], org["id"])
        caja_filtros.addWidget(self.combo_organo)

        caja_filtros.addStretch()
        layout_principal.addLayout(caja_filtros)

        # CONECTAR SEÑALES DE FILTROS
        self.combo_anio.currentIndexChanged.connect(self._on_filtro_cambiado)
        self.combo_mes.currentIndexChanged.connect(self._on_filtro_cambiado)
        self.combo_tipo.currentIndexChanged.connect(self._on_filtro_cambiado)
        self.combo_organo.currentIndexChanged.connect(self._on_filtro_cambiado)

    def _on_texto_cambiado(self, texto):
        self.texto_cambiado.emit(texto)

    def _ejecutar_busqueda(self):
        texto = self.barra_busqueda.text()
        self.buscar_solicitado.emit(texto)

    def _validar_anio_ingresado(self):
        texto = self.combo_anio.currentText().strip()   

        # Campo vacío -> se interpreta como "Todos"
        if not texto:
            self.combo_anio.setCurrentIndex(-1)
            return

        if not texto.isdigit():
            self.combo_anio.setCurrentIndex(-1)
            return

        #ojo a estaaaaa

        anio = int(texto)
        if not (self.ANIO_MINIMO <= anio <= self.ANIO_MAXIMO):
            print(f"Año inválido: {anio}. Debe estar entre {self.ANIO_MINIMO} y {self.ANIO_MAXIMO}")
            self.combo_anio.setCurrentIndex(-1)
            return

        idx = self.combo_anio.findText(texto)
        if idx == -1:
            self.combo_anio.insertItem(0, texto)
            idx = 0
        self.combo_anio.setCurrentIndex(idx)

    def _on_filtro_cambiado(self):
        if self._actualizando_filtros:
            return

        if not self._bloquear_desmarcar:
            if self._hay_filtros_activos():
                self.radio_todos.blockSignals(True)
                self.radio_todos.setChecked(False)
                self.radio_todos.blockSignals(False)

        filtros = self._obtener_filtros_actuales()
        print(f"Filtros activos: {filtros}")
        self.filtros_cambiados.emit(filtros)

    def _hay_filtros_activos(self):
        anio_texto = self.combo_anio.currentText().strip()
        es_anio_activo = self.combo_anio.currentIndex() != -1 and anio_texto.isdigit()

        es_mes_activo = self.combo_mes.currentIndex() != 0
        es_tipo_activo = self.combo_tipo.currentIndex() != 0
        es_organo_activo = self.combo_organo.currentIndex() != 0

        return es_anio_activo or es_mes_activo or es_tipo_activo or es_organo_activo

    def _obtener_filtros_actuales(self):
        filtros = {}

        anio_texto = self.combo_anio.currentText().strip()
        if anio_texto.isdigit():
            filtros['año'] = int(anio_texto)

        if self.combo_mes.currentIndex() != 0:
            filtros['mes'] = self.combo_mes.currentIndex()
            filtros['mes_nombre'] = self.combo_mes.currentText()

        if self.combo_tipo.currentIndex() != 0:
            filtros['tipo'] = self.combo_tipo.currentText()

        if self.combo_organo.currentIndex() != 0:
            filtros['organo_id'] = self.combo_organo.currentData()
            filtros['organo_nombre'] = self.combo_organo.currentText()

        return filtros

    def _reiniciar_filtros(self, checked):
        if not checked:
            return

        self._bloquear_desmarcar = True
        self._actualizando_filtros = True

        self.combo_anio.setCurrentIndex(-1)
        self.combo_anio.lineEdit().clear()
        self.combo_mes.setCurrentIndex(0)
        self.combo_tipo.setCurrentIndex(0)
        self.combo_organo.setCurrentIndex(0)

        self._actualizando_filtros = False
        self._bloquear_desmarcar = False

        print("Filtros reiniciados a 'Todos'")
        self.filtros_cambiados.emit({})

    def obtener_filtros(self):
        return self._obtener_filtros_actuales()

    def obtener_texto_busqueda(self):
        return self.barra_busqueda.text()

    def limpiar_todo(self):
        self.barra_busqueda.clear()
        self.radio_todos.setChecked(True)

    def obtener_texto_busqueda(self):
        return self.barra_busqueda.text().strip()

    def obtener_filtros(self):
        return {
            "anio": self.combo_anio.currentText(),
            "mes": self.combo_mes.currentText(),
            "tipo": self.combo_tipo.currentText(),
            "organo": self.combo_organo.currentData() # currentData jala el ID numérico, ¡clave!
        }
 