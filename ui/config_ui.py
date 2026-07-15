# ======================== Imports ========================


import os,sys

import pandas as pd
import json
import time
import traceback

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot


from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPlainTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QFrame,
    QGroupBox,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QLabel,
    QComboBox,
    QDialog,
    QListWidget,
    QInputDialog,
    QMessageBox
)

from ui.customwidgets import (
    MangoButton,
    MangoDateTimeEdit,
    MangoLineEdit,
    MangoGroupBox,
    MangoPlainTextEdit,
    MangoComboBox,
    MangoListWidget,
)

from PyQt5.QtGui import QIcon

from global_functions.helper_functions import (
    resource_path,
    parse_xml,
    compare,
    normalize,
    build_summary,
    write_to_excel,
)

DEFAULT_PROFILES = {
    "4G SW upgrade": [
        "LNCEL",
        "LNMME",
        "LNRELGNBCELL",
        "LNADJGNB",
        "IKEP",
        "IKEP_R",
        "IPSECP",
        "SECPOL",
        "SMOD_R",
    ],

    "5G SW upgrade": [
        "NRCELL",
        "RMOD_R",
        "LTEENB",
        "XNLINK",
        "NRADJGNB",
        "SERVEDAMF",
        "IKEP",
        "IKEP_R",
        "IPSECP",
        "SECPOL",
        "SMOD_R",
    ],
    "CB005832 Fronthaul Loop Back": [
        "NRCELL",
        "RMOD_R",
        "OAMMA",
        "OAMMD",
        "ETHAPP",
        "FEATCADM"
    ],
}

class Worker(QObject):
    log = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(
        self,
        profile_name,
        pre_xml,
        post_xml,
        output_file,
        sheet_order
    ):
        super().__init__()

        self.profile_name = profile_name
        self.pre_xml = pre_xml
        self.post_xml = post_xml
        self.output_file = output_file
        self.sheet_order = sheet_order

    @pyqtSlot()
    def run(self):
        try:
            self.log.emit(
                f"Starting {self.profile_name} comparison..."
            )

            self.log.emit(
                f"Managed objects: {', '.join(self.sheet_order)}"
            )

            self.log.emit("\nParsing PRE XML...")

            pre_data = parse_xml(
                self.pre_xml,
                allowed_classes=self.sheet_order
            )

            self.log.emit("PRE XML parsing completed.")

            self.log.emit("\nParsing POST XML...")

            post_data = parse_xml(
                self.post_xml,
                allowed_classes=self.sheet_order
            )

            self.log.emit("POST XML parsing completed.")

            self.log.emit("\nComparing data...")

            result = compare(
                pre_data,
                post_data
            )

            self.log.emit("Comparison completed.")

            self.log.emit("\nGenerating Excel report...")

            write_to_excel(
                result,
                self.output_file,
                self.sheet_order
            )

            self.log.emit(
                f"\n✓ Excel report generated successfully:\n"
                f"{self.output_file}"
            )

        except Exception:
            self.error.emit(
                traceback.format_exc()
            )

        finally:
            self.finished.emit()

class FileInputPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.profile_file = self.get_profile_file_path()

        self.profiles = self.load_profiles()

        self.init_ui()

    def init_ui(self):

        # =========================
        # Main page layout
        # =========================
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(30, 30, 30, 30)

        # Center the card horizontally
        card_row = QHBoxLayout()
        card_row.addStretch()

        # =========================
        # Card
        # =========================
        self.card = QFrame()
        self.card.setObjectName("card")
        self.card.setMinimumWidth(750)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)

        # Title
        title = QLabel("Configuration Analyzer Inputs")
        title.setStyleSheet("""
        margin:25 0;
        font-size:30px;
        
        color:#447100;
        """)
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        self.rat_combo = MangoComboBox()
        self.refresh_profile_combo()

        self.add_profile_button = MangoButton("","Add a profile", resource_path("resources/icon/add.svg"))
        self.add_profile_button.setToolTip("Add new profile")
        self.add_profile_button.setFixedWidth(35)

        self.settings_button = MangoButton("","Edit settings",resource_path("resources/icon/settings.svg"))

        self.add_profile_button.clicked.connect(
            self.add_profile
        )

        self.settings_button.clicked.connect(
            self.open_sheet_settings
        )

        profile_group = QGroupBox("Select Profile")

        profile_layout = QHBoxLayout(profile_group)

        profile_layout.addWidget(self.rat_combo, 1)
        profile_layout.addWidget(self.add_profile_button)
        profile_layout.addWidget(self.settings_button)

        card_layout.addWidget(profile_group)


        rat = self.rat_combo.currentData()
        # =========================
        # Input File 1
        # =========================
        self.file1_edit = MangoLineEdit()
        self.file1_edit.setPlaceholderText("Select first input file...")

        self.file1_button = MangoButton("Browse", "Browse Pre dump",resource_path("resources/icon/search.png"))
        self.file1_button.clicked.connect(
            lambda: self.browse_file(self.file1_edit)
        )

        file1_group = self.create_file_group(
            "Pre Dump (.xml)",
            self.file1_edit,
            self.file1_button
        )

        card_layout.addWidget(file1_group)

        # =========================
        # Input File 2
        # =========================
        self.file2_edit = MangoLineEdit()
        self.file2_edit.setPlaceholderText("Select second input file...")

        self.file2_button = MangoButton("Browse", "Browse Post dump", resource_path("resources/icon/search.png"))
        self.file2_button.clicked.connect(
            lambda: self.browse_file(self.file2_edit)
        )

        file2_group = self.create_file_group(
            "Post dump (.xml)",
            self.file2_edit,
            self.file2_button
        )

        card_layout.addWidget(file2_group)

        # =========================
        # Run button
        # =========================
        run_row = QHBoxLayout()
        run_row.addStretch()

        self.run_button = MangoButton("Run", "Click to analyze", resource_path("resources/icon/run.png"))
        self.run_button.setObjectName("runButton")
        self.run_button.setFixedWidth(140)
        self.run_button.clicked.connect(self.start_processing)
        run_row.addWidget(self.run_button)
        run_row.addStretch()

        card_layout.addLayout(run_row)

        # =========================
        # Log window
        # =========================
        # =========================
        # Log group
        # =========================
        log_group = QGroupBox("Execution Log")

        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(10, 2, 10, 10)

        self.log_output = MangoPlainTextEdit()
        self.log_output.setObjectName("logOutput")
        self.log_output.setReadOnly(True)
        # self.log_output.setPlaceholderText(
        #     "Execution logs will appear here..."
        # )
        self.log_output.setMinimumHeight(180)

        log_layout.addWidget(self.log_output)

        view_result_layout = QHBoxLayout()
        self.btn_open_result = MangoButton("", "Open result in excel",resource_path("resources/icon/open.svg"))
        self.btn_open_result_folder = MangoButton("", "Open result directory", resource_path("resources/icon/folder.svg"))
        btn_view_result = MangoButton("View Result", "View results", resource_path("resources/icon/result.png"))
        self.btn_open_result.setEnabled(False)
        self.btn_open_result_folder.setEnabled(False)
        btn_view_result.setEnabled(False)
        view_result_layout.addWidget(self.btn_open_result)
        view_result_layout.addWidget(self.btn_open_result_folder)
        view_result_layout.addWidget(btn_view_result)

        self.result_file = None
        self.output_dir = None
        self.btn_open_result.clicked.connect(self.open_result)
        self.btn_open_result_folder.clicked.connect(self.open_result_folder)
        log_layout.addLayout(view_result_layout)
        # Add the whole group box to the card
        card_layout.addWidget(log_group)


        # Add card to centered row
        card_row.addWidget(self.card)
        card_row.addStretch()

        page_layout.addStretch()
        page_layout.addLayout(card_row)
        page_layout.addStretch()

    def get_profile_file_path(self):
        # Running as PyInstaller EXE
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)

        # Running as normal Python script
        else:
            base_dir = os.path.dirname(
                os.path.abspath(__file__)
            )

        return os.path.join(
            base_dir,
            "profiles.json"
        )

    def open_result(self):
        os.startfile(self.result_file)

    def open_result_folder(self):
        os.startfile(self.output_dir)
    def add_profile(self):
        name, ok = QInputDialog.getText(
            self,
            "Add Profile",
            "Enter profile name:"
        )

        if not ok:
            return

        name = name.strip()

        if not name:
            return

        if name in self.profiles:
            QMessageBox.warning(
                self,
                "Profile Exists",
                f'Profile "{name}" already exists.'
            )
            return

        # New profile starts with an empty MO list
        self.profiles[name] = []

        self.save_profiles()
        self.refresh_profile_combo(name)

        # Immediately open its settings
        self.open_sheet_settings()
    def refresh_profile_combo(self, selected_name=None):
        if selected_name is None:
            selected_name = self.rat_combo.currentText()

        self.rat_combo.blockSignals(True)
        self.rat_combo.clear()

        self.rat_combo.addItems(
            self.profiles.keys()
        )

        if selected_name in self.profiles:
            self.rat_combo.setCurrentText(selected_name)

        self.rat_combo.blockSignals(False)

    def load_profiles(self):
        # No profiles.json yet:
        # create it from hardcoded defaults
        if not os.path.exists(self.profile_file):
            profiles = {
                name: items.copy()
                for name, items in DEFAULT_PROFILES.items()
            }

            self.save_profiles(profiles)

            return profiles

        try:
            with open(
                    self.profile_file,
                    "r",
                    encoding="utf-8"
            ) as file:
                data = json.load(file)

            if not isinstance(data, dict):
                raise ValueError(
                    "Invalid profiles.json format."
                )

            return data

        except Exception as error:
            print(
                f"Could not load profiles.json: {error}"
            )

            # Fall back to defaults
            return {
                name: items.copy()
                for name, items in DEFAULT_PROFILES.items()
            }

    def save_profiles(self, profiles=None):
        if profiles is None:
            profiles = self.profiles

        try:
            with open(
                    self.profile_file,
                    "w",
                    encoding="utf-8"
            ) as file:
                json.dump(
                    profiles,
                    file,
                    indent=4,
                    ensure_ascii=False
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Could not save profiles:\n{error}"
            )

    def open_sheet_settings(self):
        profile_name = self.rat_combo.currentText()

        if not profile_name:
            return

        dialog = SheetOrderDialog(
            rat_name=profile_name,
            items=self.profiles[profile_name],
            parent=self
        )

        # -------------------------
        # Load hardcoded defaults
        # -------------------------
        def load_defaults():
            if profile_name not in DEFAULT_PROFILES:
                QMessageBox.information(
                    dialog,
                    "No Default Available",
                    f'No default configuration exists for "{profile_name}".'
                )
                return

            dialog.list_widget.clear()
            dialog.list_widget.addItems(
                DEFAULT_PROFILES[profile_name]
            )

        # -------------------------
        # Delete current profile
        # -------------------------
        def delete_profile():
            reply = QMessageBox.question(
                dialog,
                "Delete Profile",
                f'Delete profile "{profile_name}"?',
                QMessageBox.Yes | QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                return

            del self.profiles[profile_name]

            self.save_profiles()
            self.refresh_profile_combo()

            dialog.reject()

        dialog.loadDefaultsRequested.connect(
            load_defaults
        )

        dialog.deleteRequested.connect(
            delete_profile
        )

        # -------------------------
        # Save changes
        # -------------------------
        if dialog.exec_() == QDialog.Accepted:
            self.profiles[profile_name] = (
                dialog.get_items()
            )

            self.save_profiles()

            self.append_log(
                f'{profile_name} configuration saved '
                f'({len(self.profiles[profile_name])} items).'
            )
    def create_file_group(self, title, line_edit, browse_button):
        group = MangoGroupBox(title)

        layout = QHBoxLayout(group)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(10)

        layout.addWidget(line_edit, 1)
        layout.addWidget(browse_button)

        return group

    def browse_file(self, line_edit):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*.*)"
        )

        if file_path:
            line_edit.setText(file_path)

    def start_processing(self):
        import os

        # -------------------------
        # Clear previous run log
        # -------------------------
        self.log_output.clear()

        # -------------------------
        # Get current profile
        # -------------------------
        profile_name = self.rat_combo.currentText().strip()

        if not profile_name:
            self.append_error("No profile selected.")
            return

        if profile_name not in self.profiles:
            self.append_error(
                f'Profile "{profile_name}" was not found.'
            )
            return

        # Get a copy of the current managed object list
        sheet_order = self.profiles[profile_name].copy()

        if not sheet_order:
            self.append_error(
                f'No managed objects configured for "{profile_name}".'
            )
            return

        # -------------------------
        # Get input files
        # -------------------------
        pre_xml = self.file1_edit.text().strip()
        post_xml = self.file2_edit.text().strip()

        # -------------------------
        # Validate PRE XML
        # -------------------------
        if not pre_xml:
            self.append_error(
                "Please select the PRE XML file."
            )
            return

        if not os.path.isfile(pre_xml):
            self.append_error(
                f"PRE XML file does not exist:\n{pre_xml}"
            )
            return

        # -------------------------
        # Validate POST XML
        # -------------------------
        if not post_xml:
            self.append_error(
                "Please select the POST XML file."
            )
            return

        if not os.path.isfile(post_xml):
            self.append_error(
                f"POST XML file does not exist:\n{post_xml}"
            )
            return

        # -------------------------
        # Create output file path
        # -------------------------
        input_folder = os.path.dirname(pre_xml)

        folder_name = os.path.basename(input_folder)
        self.output_dir = input_folder
        print(input_folder)
        # Make profile name safe for filename
        safe_profile_name = "".join(
            char if char.isalnum() or char in ("-", "_")
            else "_"
            for char in profile_name
        )

        output_file = os.path.join(
            input_folder,
            f"{folder_name}_{safe_profile_name}_comparison.xlsx"
        )

        self.result_file = output_file

        # -------------------------
        # Initial log information
        # -------------------------
        self.append_log(
            f"Profile: {profile_name}"
        )

        self.append_log(
            f"PRE XML: {pre_xml}"
        )

        self.append_log(
            f"POST XML: {post_xml}"
        )

        self.append_log(
            f"Output: {output_file}"
        )

        self.append_log(
            f"Managed objects: {len(sheet_order)}"
        )

        # -------------------------
        # Update UI state
        # -------------------------
        self.run_button.setEnabled(False)
        self.run_button.setText("Running...")

        # Optional: prevent configuration changes
        # while processing
        self.rat_combo.setEnabled(False)
        self.settings_button.setEnabled(False)
        self.add_profile_button.setEnabled(False)

        # -------------------------
        # Create background thread
        # -------------------------
        self.thread = QThread(self)

        # -------------------------
        # Create worker
        # -------------------------
        self.worker = Worker(
            profile_name=profile_name,
            pre_xml=pre_xml,
            post_xml=post_xml,
            output_file=output_file,
            sheet_order=sheet_order
        )

        # Move worker to background thread
        self.worker.moveToThread(self.thread)

        # -------------------------
        # Thread starts Worker
        # -------------------------
        self.thread.started.connect(
            self.worker.run
        )

        # -------------------------
        # Worker signals -> UI
        # -------------------------
        self.worker.log.connect(
            self.append_log
        )

        self.worker.error.connect(
            self.append_error
        )

        self.worker.finished.connect(
            self.processing_finished
        )

        # -------------------------
        # Cleanup
        # -------------------------
        self.worker.finished.connect(
            self.thread.quit
        )

        self.worker.finished.connect(
            self.worker.deleteLater
        )

        self.thread.finished.connect(
            self.thread.deleteLater
        )

        # -------------------------
        # Start processing
        # -------------------------
        self.thread.start()


    @pyqtSlot(str)
    def append_log(self, message):
        self.log_output.appendPlainText(message)


    @pyqtSlot(str)
    def append_error(self, message):
        self.log_output.appendPlainText("\nERROR:")
        self.log_output.appendPlainText(message)

    @pyqtSlot()
    def processing_finished(self):
        self.run_button.setEnabled(True)
        self.run_button.setText("Run")

        self.rat_combo.setEnabled(True)
        self.settings_button.setEnabled(True)
        self.add_profile_button.setEnabled(True)
        self.btn_open_result.setEnabled(True)
        self.btn_open_result_folder.setEnabled(True)


class SheetOrderDialog(QDialog):
    deleteRequested = pyqtSignal()
    loadDefaultsRequested = pyqtSignal()

    def __init__(self, rat_name, items, parent=None):
        super().__init__(parent)

        self.setWindowTitle(f"{rat_name} Managed Object Settings")
        self.resize(500, 500)

        main_layout = QVBoxLayout(self)

        # -------------------------
        # List
        # -------------------------
        self.list_widget = MangoListWidget()
        self.list_widget.setSelectionMode(
            MangoListWidget.ExtendedSelection
        )
        self.list_widget.addItems(items)

        main_layout.addWidget(self.list_widget)

        # -------------------------
        # Add new item
        # -------------------------
        add_layout = QHBoxLayout()

        self.item_edit = MangoLineEdit()
        self.item_edit.setPlaceholderText(
            "Enter managed object name..."
        )

        self.add_button = MangoButton("","Add item to the list", resource_path("resources/icon/add.svg"))

        add_layout.addWidget(self.item_edit, 1)
        add_layout.addWidget(self.add_button)

        main_layout.addLayout(add_layout)

        # -------------------------
        # Bottom buttons
        # -------------------------
        button_layout = QHBoxLayout()

        self.remove_button = MangoButton("Remove Selected", "Remove selected items from the list",resource_path("resources/icon/remove.png"))
        self.load_default_button = MangoButton("", "Load default profile", resource_path("resources/icon/reload.png"))
        self.delete_profile_button = MangoButton("Delete Profile","Delete this profile",resource_path("resources/icon/trash.png" ))
        self.save_button = MangoButton("Save","Save items to profile",resource_path("resources/icon/save.png"))

        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.load_default_button)
        button_layout.addStretch()
        button_layout.addWidget(self.delete_profile_button)
        button_layout.addWidget(self.save_button)

        main_layout.addLayout(button_layout)

        # =========================
        # SIGNAL CONNECTIONS
        # =========================
        self.add_button.clicked.connect(
            self.add_item
        )

        self.item_edit.returnPressed.connect(
            self.add_item
        )

        self.remove_button.clicked.connect(
            self.remove_selected
        )

        self.load_default_button.clicked.connect(
            self.loadDefaultsRequested.emit
        )

        self.delete_profile_button.clicked.connect(
            self.deleteRequested.emit
        )

        self.save_button.clicked.connect(
            self.accept
        )

    def add_item(self):
        text = self.item_edit.text().strip().upper()

        if not text:
            return

        existing_items = [
            self.list_widget.item(i).text()
            for i in range(self.list_widget.count())
        ]

        if text not in existing_items:
            self.list_widget.addItem(text)

        self.item_edit.clear()

    def remove_selected(self):
        for item in self.list_widget.selectedItems():
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)

    def get_items(self):
        return [
            self.list_widget.item(i).text()
            for i in range(self.list_widget.count())
        ]



class ConfigAnalyzerWidget(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # =========================
        # Stacked interface
        # =========================
        self.stack = QStackedWidget()

        # Page 0 - Input page
        self.input_page = FileInputPage()

        # Page 1 - Example result page
        self.result_page = QWidget()
        result_layout = QVBoxLayout(self.result_page)

        result_label = QLabel("Result Page")
        result_label.setAlignment(Qt.AlignCenter)
        result_layout.addWidget(result_label)

        # Add pages
        self.stack.addWidget(self.input_page)
        self.stack.addWidget(self.result_page)

        main_layout.addWidget(self.stack)

        # Example:
        # Move to result page when Run is clicked
        # self.input_page.run_button.clicked.connect(
        #     lambda: self.stack.setCurrentWidget(self.result_page)
        # )
