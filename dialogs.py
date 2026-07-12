

from PyQt5.QtWidgets import  QTextEdit

from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QDateTime, QTimer
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QDialog,

)

from AlarmComparison.customwidgets import (
    MangoButton,
    MangoLineEdit,
    MangoCheckBox,
)

from AlarmComparison.helper_functions import resource_path


class StatusDialog(QDialog):

    def __init__(
            self,
            status="",
            resolved=False):

        super().__init__()
        self.setWindowIcon(QIcon(resource_path(
            "resources/icon/update.ico"
        )))
        self.setWindowTitle(
            "Update Status"
        )
        self.resize(600, 200)
        layout = QVBoxLayout()

        self.status_edit = MangoLineEdit()
        self.status_edit.setText(status)

        self.resolved_chk = MangoCheckBox(
            "Resolved"
        )

        self.resolved_chk.setChecked(
            resolved
        )

        save_btn = MangoButton(
            "","Save", resource_path("resources/icon/save.ico")
        )

        save_btn.clicked.connect(
            self.accept
        )

        layout.addWidget(
            QLabel("Status")
        )

        layout.addWidget(
            self.status_edit
        )

        layout.addWidget(
            self.resolved_chk
        )

        layout.addWidget(
            save_btn, alignment=Qt.AlignHCenter
        )

        self.setLayout(layout)


class DetailDialog(QDialog):

    def __init__(self, row_data):
        super().__init__()

        self.setWindowTitle("Alarm Details")
        self.resize(900, 700)

        txt = QTextEdit()
        txt.setReadOnly(True)

        severity = str(row_data.get("Severity", "")).lower()

        severity_style = {
            "critical": {
                "bg": "#ff4d4d",
                "fg": "white"
            },
            "major": {
                "bg": "#ffa500",
                "fg": "black"
            },
            "minor": {
                "bg": "#fff176",
                "fg": "black"
            },
            "warning": {
                "bg": "#add8e6",
                "fg": "black"
            }
        }

        html = ""

        for k, v in row_data.items():

            # Default style
            bg = "white"
            fg = "black"
            size = "18px"

            # Apply severity formatting only to Severity line
            if k == "Severity":

                style = severity_style.get(severity)

                if style:
                    bg = style["bg"]
                    fg = style["fg"]
                    size = "24px"

            html += f"""
            <div style="
                background-color:{bg};
                color:{fg};
                font-size:{size};
                padding:5px;
                margin:2px;">

                <b>{k}</b>: {v}

            </div>
            """

        txt.setHtml(html)

        layout = QVBoxLayout()
        layout.addWidget(txt)

        self.setLayout(layout)