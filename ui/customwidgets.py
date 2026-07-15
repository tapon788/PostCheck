# ======================== Imports ========================


import os
from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QLineEdit, QCheckBox, QGroupBox, QLabel,
    QComboBox, QStyledItemDelegate, QDateTimeEdit, QPlainTextEdit, QListWidget

)
from PyQt5.QtGui import (
    QIcon, QPixmap, QStandardItem, QStandardItemModel
)
from PyQt5.QtCore import (
    Qt, QSize, QEvent
)


class MangoBanner(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        font = self.font()
        font.setPointSize(16)
        font.setBold(True)
        self.setFont(font)
        self.setStyleSheet("""
            QLabel {
                color: #4a90e2;
                padding: 10px;
            }
        """)


class MangoButton(QPushButton):
    def __init__(self, btn_text:"", btn_tooltip:"",icon_path:None, parent=None):
        super().__init__(btn_text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(btn_tooltip)
        icon_path = os.path.join(os.getcwd(), icon_path)
        icon_path = icon_path.replace("\\", "/")
        # Set icon
        self.setIcon(QIcon(QPixmap(icon_path)))
        self.setIconSize(QSize(25, 25))  # adjust size as needed
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
        self.setPlaceholderText("")
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


class MangoPlainTextEdit(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
        QPlainTextEdit{
        padding: 5px;
        border: 2px solid #ccc;
        border-radius: 4px;
        background-color: #fff8e1;  /* light mango-ish background */
        font-size:8pt;
        font-family:Courier;
        }
        """)

class MangoGroupBox(QGroupBox):
    def __init__(self, title="", *args, **kwargs):
        super().__init__(title, *args, **kwargs)
        # Adjusted static mango gradient border style
        self.setStyleSheet("""
        """)


class MangoMainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("PostCheck Analyzer V1.7.13")
        # self.resize(1400, 800)


class MangoCheckBox(QCheckBox):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        # Custom mango checkbox without default tick or background
        self.setStyleSheet("""
            QCheckBox::indicator {
                border: 1px solid #FFCA28; /* mango border */
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background: white;   /* still no fill */
                border: 6px solid #FFCA28; /* solid mango box when checked */
            }
        """)


class MangoDateTimeEdit(QDateTimeEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
        QDateTimeEdit {
        background-color: #fff8dc;
        color: black;
        font-size: 16px;
        
        border: 1px solid #808080;
        border-radius: 4px;
        padding: 4px;
        }

        QDateTimeEdit::up-button,
        QDateTimeEdit::down-button {
            width: 18px;
        }

        QDateTimeEdit::drop-down {
            width: 20px;
        }
        """)


class MangoComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QComboBox {
                min-height: 35px;
                border: 2px solid #ccc;
                border-radius: 4px;
                background-color: #fff8e1;
            }
                        QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #555;
                outline: none;
                padding: 5px;
                selection-background-color: #444;
                selection-color: white;
            }

            QComboBox QAbstractItemView::item {
                min-height: 30px;
                padding: 4px 8px;
            }

            QComboBox QAbstractItemView::item:hover {
                background-color: #444;
            }

            QComboBox QAbstractItemView::item:selected {
                background-color: #555;
                color: white;
            }
            """)

class MangoCheckableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setModel(QStandardItemModel(self))
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText("Select delta comparison fields...")

        # Don't allow typing
        self.lineEdit().setFocusPolicy(Qt.NoFocus)

        # Better item height
        self.setItemDelegate(QStyledItemDelegate(self))

        # Catch mouse events in popup
        self.view().viewport().installEventFilter(self)

        # Prevent current item text from replacing our display text
        self.currentIndexChanged.connect(lambda: self.setCurrentIndex(-1))

        self.setStyleSheet("""
            QComboBox {
                min-height: 35px;
                border: 2px solid #ccc;
                border-radius: 4px;
                background-color: #fff8e1;
            }

            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #555;
                outline: none;
                padding: 5px;
                selection-background-color: #444;
                selection-color: white;
            }

            QComboBox QAbstractItemView::item {
                min-height: 30px;
                padding: 4px 8px;
            }

            QComboBox QAbstractItemView::item:hover {
                background-color: #444;
            }

            QComboBox QAbstractItemView::item:selected {
                background-color: #555;
                color: white;
            }
        """)

    def addItem(self, text):
        item = QStandardItem(text)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        item.setData(Qt.Unchecked, Qt.CheckStateRole)
        self.model().appendRow(item)

    def addItems(self, texts):
        for text in texts:
            self.addItem(text)

    def eventFilter(self, obj, event):
        if obj == self.view().viewport() and event.type() == QEvent.MouseButtonRelease:

            index = self.view().indexAt(event.pos())

            if index.isValid():
                item = self.model().itemFromIndex(index)

                if item.checkState() == Qt.Checked:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)

                self.updateText()

                # Keep popup open
                return True

        return super().eventFilter(obj, event)

    def checkedItems(self):
        result = []

        for row in range(self.model().rowCount()):
            item = self.model().item(row)
            if item.checkState() == Qt.Checked:
                result.append(item.text())

        return result

    def updateText(self):
        self.lineEdit().setText(" + ".join(self.checkedItems()))

    def setCheckedItems(self, items):
        """
        Check the items whose text appears in the given list.

        Parameters
        ----------
        items : list[str]
            List of item texts to check.
        """
        items = set(items)  # Faster lookup

        for row in range(self.model().rowCount()):
            item = self.model().item(row)

            if item.text() in items:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)

        self.updateText()

    # def hidePopup(self):
    #     if self.view().underMouse():
    #         return
    #
    #     super().hidePopup()
    #     self.updateText()


class MangoListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
        QListWidget{
        background-color: #fff8e1;
        padding: 5px;
        border: 2px solid #ccc;
        border-radius: 4px;
        border-bottom: 2px solid #ccc;
        }
        """)

