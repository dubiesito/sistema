from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
                               QTableWidgetItem, QPushButton, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt
import qtawesome as qta
import db


class ArchivadosModal(QDialog):
    def __init__(self, usuario_id, parent=None):
        super().__init__(parent)
        self.usuario_id = usuario_id
        self.docs = []
        self.setWindowTitle("Documentos archivados (solo administrador)")
        self.resize(950, 500)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Documentos archivados"))

        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(
            ["Expediente", "Título", "Archivado el", "Archivado por", "Motivo"])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabla)

        caja = QHBoxLayout()
        caja.addStretch()
        self.btn_restaurar = QPushButton(" Restaurar")
        self.btn_restaurar.setIcon(qta.icon('fa5s.undo', color='#16A34A'))
        self.btn_restaurar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_restaurar.clicked.connect(self.restaurar)
        caja.addWidget(self.btn_restaurar)
        layout.addLayout(caja)

        self.cargar()

    def cargar(self):
        self.docs = db.obtener_documentos_archivados(self.usuario_id)
        self.tabla.setRowCount(0)
        for i, d in enumerate(self.docs):
            self.tabla.insertRow(i)
            valores = [d['nro_doc'], d['titulo'], d['fecha_archivado'], d['archivado_por'], d['motivo']]
            for col, valor in enumerate(valores):
                self.tabla.setItem(i, col, QTableWidgetItem(str(valor or "")))

    def _seleccionado(self):
        fila = self.tabla.currentRow()
        if fila < 0 or fila >= len(self.docs):
            QMessageBox.information(self, "Aviso", "Seleccione un documento de la lista.")
            return None
        return self.docs[fila]

    def restaurar(self):
        doc = self._seleccionado()
        if not doc:
            return
        exito, mensaje = db.restaurar_documento(doc['id'], self.usuario_id)
        if exito:
            QMessageBox.information(self, "Restaurar", mensaje)
            self.cargar()
        else:
            QMessageBox.warning(self, "Restaurar", mensaje)