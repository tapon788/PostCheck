from PyQt5.QtWidgets import (
    QDialog,
    QTextEdit,
    QVBoxLayout
)


from PyQt5.QtWidgets import QDialog, QTextEdit, QVBoxLayout

from PyQt5.QtWidgets import QDialog, QTextEdit, QVBoxLayout


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