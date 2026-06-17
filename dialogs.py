from PyQt5.QtWidgets import (
    QDialog,
    QTextEdit,
    QVBoxLayout
)


class DetailDialog(QDialog):

    def __init__(self, row_data):
        super().__init__()

        self.setWindowTitle("Alarm Details")
        self.resize(900, 700)

        txt = QTextEdit()
        txt.setReadOnly(True)

        lines = []

        for k, v in row_data.items():
            lines.append(f"{k}: {v}")

        txt.setPlainText("\n".join(lines))

        layout = QVBoxLayout()
        layout.addWidget(txt)

        self.setLayout(layout)