import os, sys

from PyQt5.QtWidgets import (
    QDialog,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from AlarmComparison.customwidgets import MangoLineEdit, MangoGroupBox
from AlarmComparison.helper_functions import resource_path


class CSVMergerDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )
        self.setWindowTitle("CSV Merger")
        self.resize(600, 220)
        self.setWindowIcon(QIcon(resource_path(
            "resources/icon/merge.png"
        )))

        # -----------------------------
        # Source Group
        # -----------------------------
        source_group = MangoGroupBox("Source CSV Folder")

        self.source_path = MangoLineEdit()
        self.source_path.setPlaceholderText(
            "Select folder containing CSV files"
        )

        browse_btn = QPushButton("Browse")

        browse_btn.clicked.connect(
            self.browse_folder
        )

        source_layout = QHBoxLayout()

        source_layout.addWidget(
            self.source_path
        )

        source_layout.addWidget(
            browse_btn
        )

        source_group.setLayout(
            source_layout
        )


        # -----------------------------
        # Output Group
        # -----------------------------
        output_group = MangoGroupBox("Output CSV")

        self.output_file = MangoLineEdit()
        self.output_file.setPlaceholderText(
            "Enter output file name"
        )

        merge_btn = QPushButton("Merge")

        merge_btn.clicked.connect(
            self.merge_csv
        )

        output_layout = QHBoxLayout()

        output_layout.addWidget(
            self.output_file
        )

        output_layout.addWidget(
            merge_btn
        )

        output_group.setLayout(
            output_layout
        )


        # -----------------------------
        # Main Layout
        # -----------------------------
        main_layout = QVBoxLayout()

        main_layout.addWidget(
            source_group
        )

        main_layout.addWidget(
            output_group
        )


        self.setLayout(
            main_layout
        )


    def browse_folder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select CSV Folder"
        )

        if folder:
            self.source_path.setText(folder)



    def merge_csv(self):

        folder = self.source_path.text().strip()

        if not folder:

            QMessageBox.warning(
                self,
                "Missing Path",
                "Please select source folder"
            )

            return


        output = self.output_file.text().strip()
        if not output.find(".csv")>=0:
            output = f"{output}.csv"

        if not output:

            output = "merged.csv"


        output_path = os.path.join(
            folder,
            output
        )


        csv_files = [
            f for f in os.listdir(folder)
            if f.lower().endswith(".csv")
        ]


        if not csv_files:

            QMessageBox.warning(
                self,
                "No CSV",
                "No CSV files found"
            )

            return


        try:

            first_file = True

            with open(
                output_path,
                "w",
                encoding="utf-8"
            ) as outfile:


                for csv in csv_files:

                    file_path = os.path.join(
                        folder,
                        csv
                    )


                    with open(
                        file_path,
                        "r",
                        encoding="utf-8"
                    ) as infile:


                        lines = infile.readlines()


                        if first_file:

                            outfile.writelines(lines)
                            first_file = False

                        else:

                            outfile.writelines(
                                lines[1:]
                            )


            QMessageBox.information(
                self,
                "Completed",
                f"Merged {len(csv_files)} files\n\nSaved:\n{output_path}"
            )

            self.accept()
            os.startfile(os.path.dirname(output_path))

        except Exception as e:

            QMessageBox.critical(
                self,
                "Error",
                str(e)
            )