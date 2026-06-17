import os
from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QLineEdit, QCheckBox,
    QComboBox, QGroupBox, QMenu, QAction, QMenuBar, QApplication,
    QTableWidget
)
from PyQt5.QtGui import (
    QIcon, QPixmap, QFont
)
from PyQt5.QtCore import (
    Qt, QSize
)


class MangoButton(QPushButton):
    def __init__(self, text, iconpath , parent=None, icon_path=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)

        icon_path = os.path.join(os.getcwd(), iconpath)
        icon_path = icon_path.replace("\\", "/")
        # Set icon
        self.setIcon(QIcon(QPixmap(icon_path)))
        self.setIconSize(QSize(40,40))  # adjust size as needed
        # Mango skin gradient: light green → yellow → orange
        self.setStyleSheet("""
            QPushButton {
                padding: 5px 8px;
                border-radius: 4px;
                border: 1px solid #FFCA28;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                border: 1px solid #90EE90;  /* bright yellow border on hover */
            }
            QPushButton:pressed {

                border: 1px solid #BF360C;
                padding-top: 7px;
                padding-bottom: 4px;
            }
            QPushButton:disabled {
                border: 1px solid #AAAAAA;
                color: #A0A0A0;
            }
        """)


class MangoLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Enter text here...")
        # Default style
        self.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 2px solid #ccc;
                border-radius: 4px;
                border-bottom: 2px solid #ccc;
                background-color: #fff8e1;  /* light mango-ish background */
            }

            QLineEdit:focus {
                border: 2px solid #ccc;  /* keep general border subtle */
                border-bottom: 2px solid #FFB74D;  /* mango-orange glow on bottom */
                background-color: #fffde7;  /* slightly lighter when focused */
            }

            QLineEdit:disabled {
                background-color: #f0f0f0;
                color: #a0a0a0;
                border-bottom: 2px solid #ccc;
            }
        """)

class MangoGroupBox(QGroupBox):
    def __init__(self, title="", *args, **kwargs):
        super().__init__(title, *args, **kwargs)
        # Adjusted static mango gradient border style
        self.setStyleSheet("""
        """)


class MangoMainWindow(QMainWindow):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.setWindowTitle("Mango Bites")
        #self.resize(1400, 800)
