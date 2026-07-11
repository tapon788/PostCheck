import sys
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QComboBox,
    QStyledItemDelegate,
)


class CheckableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setModel(QStandardItemModel(self))
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText("Select...")

        # Don't allow typing
        self.lineEdit().setFocusPolicy(Qt.NoFocus)

        # Better item height
        self.setItemDelegate(QStyledItemDelegate(self))

        # Catch mouse events in popup
        self.view().viewport().installEventFilter(self)

        # Prevent current item text from replacing our display text
        self.currentIndexChanged.connect(lambda: self.setCurrentIndex(-1))

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

    def hidePopup(self):
        """
        Don't close the popup after every click.
        Close only when the user clicks outside or presses Esc.
        """
        if self.view().underMouse():
            return
        super().hidePopup()

    def checkedItems(self):
        result = []

        for row in range(self.model().rowCount()):
            item = self.model().item(row)
            if item.checkState() == Qt.Checked:
                result.append(item.text())

        return result

    def updateText(self):
        self.lineEdit().setText(" + ".join(self.checkedItems()))


class Window(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.combo = CheckableComboBox()

        self.combo.addItems([
            "Critical",
            "Major",
            "Minor",
            "Warning",
            "Info",
            "Cleared",
        ])

        layout.addWidget(self.combo)


app = QApplication(sys.argv)

window = Window()
window.resize(350, 100)
window.show()

sys.exit(app.exec_())