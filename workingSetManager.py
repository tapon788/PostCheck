import os
import sys
from collections import Counter
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
)


# ==========================================================
# Drag & Drop Text Area
# ==========================================================
class DropTextEdit(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        if not event.mimeData().hasUrls():
            return

        file_path = event.mimeData().urls()[0].toLocalFile()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.setPlainText(f.read())
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# ==========================================================
# Main Window
# ==========================================================
class WorkingSetApp(QMainWindow):

    PREFIX = "PLMN-PLMN/MRBTS-"       # <-- Change this to whatever fixed text you want

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Working Set Generator")
        self.resize(900, 700)

        self.build_ui()

    # ------------------------------------------------------

    def build_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        # --------------------------------------------------
        # Browse
        # --------------------------------------------------
        top_layout = QHBoxLayout()

        browse_btn = QPushButton("Browse File")
        browse_btn.clicked.connect(self.browse_file)

        top_layout.addWidget(browse_btn)
        top_layout.addStretch()

        layout.addLayout(top_layout)

        # --------------------------------------------------
        # Text Area
        # --------------------------------------------------
        self.text = DropTextEdit()
        self.text.setPlaceholderText(
            "Paste MRBTS here (one per line)\n\n"
            "or Drag & Drop a text file."
        )

        layout.addWidget(self.text)

        # --------------------------------------------------
        # Working Set
        # --------------------------------------------------
        work_btn = QPushButton("Make Working Set")
        work_btn.clicked.connect(self.make_working_set)

        layout.addWidget(work_btn)

        # --------------------------------------------------
        # Split Controls
        # --------------------------------------------------
        split_layout = QHBoxLayout()

        split_layout.addWidget(QLabel("Lines per file:"))

        self.lines_edit = QLineEdit()
        self.lines_edit.setFixedWidth(100)
        self.lines_edit.setText("100")

        split_layout.addWidget(self.lines_edit)

        split_btn = QPushButton("Split")
        split_btn.clicked.connect(self.split_files)

        split_layout.addWidget(split_btn)

        split_layout.addStretch()

        layout.addLayout(split_layout)

    # ------------------------------------------------------

    def browse_file(self):

        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Text File",
            "",
            "Text Files (*.txt);;All Files (*)"
        )

        if not file_name:
            return

        try:
            with open(file_name, "r", encoding="utf-8") as f:
                self.text.setPlainText(f.read())
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ------------------------------------------------------

    def get_lines(self):

        return [
            line.strip()
            for line in self.text.toPlainText().splitlines()
            if line.strip()
        ]

    # ------------------------------------------------------

    def make_working_set(self):

        lines = self.validate_input()
        if lines is None:
            return

        lines = self.check_duplicates(lines)
        if lines is None:
            return

        if not lines:
            QMessageBox.warning(self, "Warning", "No data.")
            return

        new_lines = [
            self.PREFIX + line
            for line in lines
        ]

        self.text.setPlainText("\n".join(new_lines))

        QMessageBox.information(
            self,
            "Done",
            "Working set created."
        )

    # ------------------------------------------------------

    def split_files(self):

        lines = [
            line.rstrip()
            for line in self.text.toPlainText().splitlines()
            if line.strip()
        ]

        if not lines:
            QMessageBox.warning(self, "Warning", "No data.")
            return

        try:
            chunk_size = int(self.lines_edit.text())

            if chunk_size <= 0:
                raise ValueError

        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid",
                "Please enter a valid number."
            )
            return

        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder"
        )

        if not output_dir:
            return

        total = len(lines)

        file_no = 1

        for start in range(0, total, chunk_size):

            chunk = lines[start:start + chunk_size]

            filename = os.path.join(
                output_dir,
                f"working_set_{file_no}.txt"
            )

            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(chunk))

            file_no += 1

        QMessageBox.information(
            self,
            "Completed",
            f"Created {file_no - 1} files."
        )
    def validate_input(self):
        """
        Returns a list of valid numbers if input is valid.
        Otherwise shows an error message and returns None.
        """

        lines = [
            line.strip()
            for line in self.text.toPlainText().splitlines()
            if line.strip()
        ]

        if not lines:
            QMessageBox.warning(self, "Warning", "No input found.")
            return None

        invalid = []

        for i, line in enumerate(lines, start=1):
            if not line.isdigit():
                invalid.append(f"Line {i}: {line}")

        if invalid:
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Only numbers are allowed.\n\n"
                "The following lines are invalid:\n\n"
                + "\n".join(invalid[:10]) +
                ("\n..." if len(invalid) > 10 else "")
            )
            return None

        return lines


    def check_duplicates(self, lines):
        """
        Checks for duplicate numbers.

        Returns:
            list: original lines if no duplicates or duplicates removed.
            None: if user cancels.
        """

        counter = Counter(lines)
        duplicates = {k: v for k, v in counter.items() if v > 1}

        if not duplicates:
            return lines

        msg = "Duplicate numbers were found:\n\n"

        for num, count in list(duplicates.items())[:20]:
            msg += f"{num} ({count} times)\n"

        if len(duplicates) > 20:
            msg += "\n..."

        msg += "\n\nDo you want to remove duplicate values and continue?"

        reply = QMessageBox.question(
            self,
            "Duplicate Numbers",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.No:
            return None

        # Remove duplicates while preserving order
        seen = set()
        unique_lines = []

        for line in lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)

        return unique_lines

# ==========================================================
# Main
# ==========================================================
if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = WorkingSetApp()
    window.show()

    sys.exit(app.exec_())