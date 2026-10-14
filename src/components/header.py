from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
import qtawesome as qta
import db

class HeaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Título
        self.titulo = QLabel("Repositorio Digital MODERNIZACIÓN")
        self.titulo.setObjectName("titulo_app")
        layout.addWidget(self.titulo)

        layout.addStretch()

        # Seguro anti-crashes para el usuario
        try:
            usuario_db = db.obtener_usuario_actual()
            nombre_usuario = usuario_db['nombre'] if usuario_db else "Invitado"
        except Exception:
            nombre_usuario = "Invitado"

        # Botón Usuario con ícono vectorial
        self.btn_usuario = QPushButton(f" {nombre_usuario}")
        self.btn_usuario.setIcon(qta.icon('fa5s.user-circle', color='#7A1B29'))
        self.btn_usuario.setObjectName("boton_usuario")
        self.btn_usuario.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.btn_usuario)