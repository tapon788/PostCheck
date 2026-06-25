import sys, os
import pandas as pd

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QDateTime, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTabWidget,
    QTableView,
    QMessageBox,
    QSizePolicy,
    QDateTimeEdit, QDialog, QLineEdit, QMenu, QCheckBox, QInputDialog, QComboBox,
    QHeaderView

)

from AlarmComparison.customwidgets import (
    MangoButton,
    MangoLineEdit,
    MangoGroupBox,
    MangoMainWindow,
    MangoCheckBox,
)

from AlarmComparison.models import PandasModel,GlobalFilterProxy
from AlarmComparison.dialogs import DetailDialog
from AlarmComparison.delta import calculate_pre_post_delta, calculate_history_delta
from AlarmComparison.customUIs import CSVMergerDialog
from AlarmComparison.helper_functions import resource_path

DISPLAY_COLUMNS = [
    "Severity",
    "Alarm Number",
    "Supplementary Information",
    "Distinguished Name",
    "Alarm Time",
    "Alarm Text",
    "Diagnostic Info",
    "Name",
]

DISPLAY_COLUMNS_NEW = [
    "Severity",
    "Alarm Number",
    "Supplementary Information",
    "Distinguished Name",
    "Alarm Time",
    "History Match",
    "Status",
    "Resolved",
    "Cancel Time",
    "Alarm Text",
    "Diagnostic Info",
    "Name",
    "History Count",
]




class AlarmTable(QWidget):
    filterChanged = pyqtSignal()

    def __init__(self, filename=None):
        super().__init__()
        self.enable_status_tracking = False
        self.df = pd.DataFrame()
        self.filename = filename
        self.search = MangoLineEdit()
        self.search.setPlaceholderText("Search...")
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(250)
        self.search_timer.timeout.connect(self.apply_search)

        self.export_btn = MangoButton("", resource_path("resources/icon/export.png"))
        self.export_btn.clicked.connect(self.export_csv)

        self.table = QTableView()
        self.table.setSortingEnabled(True)

        layout = QVBoxLayout()
        top = QHBoxLayout()
        top.addWidget(self.search)
        top.addWidget(self.export_btn)
        layout.addLayout(top)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.proxy = GlobalFilterProxy()
        self.proxy.layoutChanged.connect(self.filterChanged.emit)
        self.proxy.modelReset.connect(self.filterChanged.emit)
        self.search.textChanged.connect(self.restart_search_timer)
        self.table.doubleClicked.connect(
            self.show_details
        )
        self.table.setContextMenuPolicy(
            Qt.CustomContextMenu
        )

        self.table.customContextMenuRequested.connect(
            self.show_context_menu
        )
        # Styling only once
        self.table.verticalHeader().setDefaultSectionSize(14)
        self.table.verticalHeader().setVisible(False)
        self.table.setWordWrap(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
        QTableView {
            font-size: 14px;
        }
        """)

        self.table.horizontalHeader().setStyleSheet("""
        QHeaderView::section {
            font-size: 11px;
            font-weight: bold;
            color: white;
            background-color: #2b2b2b;
            padding: 4px;
            border: 1px solid #444;
        }
        """)

    def update_status(self, source_index):

        row = self.df.iloc[
            source_index.row()
        ]

        # -----------------------------
        # LOAD EXISTING VALUES
        # -----------------------------
        current_status = str(
            row.get("Status", "")
        )

        current_resolved = str(
            row.get("Resolved", "")
        ).lower() == "true"

        # -----------------------------
        # OPEN DIALOG WITH VALUES
        # -----------------------------
        dlg = StatusDialog()

        dlg.status_edit.setText(
            current_status
        )

        dlg.resolved_chk.setChecked(
            current_resolved
        )

        if not dlg.exec_():
            return

        status = dlg.status_edit.text()

        resolved = str(
            dlg.resolved_chk.isChecked()
        )

        key_cols = [
            "Severity",
            "Alarm Time",
            "Cancel Time",
            "Alarm Number",
            "Supplementary Information",
            "Distinguished Name",
            "Diagnostic Info"
        ]

        file = f"{self.filename}.csv"

        if os.path.exists(file):

            db = pd.read_csv(
                file,
                dtype=str,
                keep_default_na=False
            )

        else:

            db = pd.DataFrame(
                columns=[
                    "Severity",
                    "Alarm Time",
                    "Cancel Time",
                    "Alarm Number",
                    "Supplementary Information",
                    "Distinguished Name",
                    "Diagnostic Info",
                    "Status",
                    "Resolved"
                ]
            )

        # -----------------------------
        # REMOVE OLD ENTRY
        # -----------------------------

        if not db.empty:

            mask = pd.Series(
                True,
                index=db.index
            )

            for col in key_cols:
                mask &= (
                        db[col].astype(str)
                        ==
                        str(row[col])
                )

            db = db[~mask]

        # -----------------------------
        # ADD UPDATED ENTRY
        # -----------------------------

        new_row = {
            "Severity":
                row["Severity"],

            "Alarm Time":
                row["Alarm Time"],

            "Cancel Time":
                row["Cancel Time"],

            "Alarm Number":
                row["Alarm Number"],

            "Supplementary Information":
                row["Supplementary Information"],

            "Distinguished Name":
                row["Distinguished Name"],

            "Diagnostic Info":
                row["Diagnostic Info"],

            "Status":
                status,

            "Resolved":
                resolved
        }

        db = pd.concat(
            [
                db,
                pd.DataFrame([new_row])
            ],
            ignore_index=True
        )
        try:
            db.to_csv(
                file,
                index=False
            )
        except PermissionError:
            QMessageBox.warning(
                self,
                "Warning",
                f"File is open: {file}. Please close it and try again."
            )
            #print()

        # -----------------------------
        # REFRESH TABLE
        # -----------------------------

        self.apply_saved_status()

        model = self.proxy.sourceModel()

        if model:
            model.beginResetModel()

            model.df = self.df.copy()

            model.endResetModel()

        self.table.viewport().update()

    def delete_status(self, source_index):

        row = self.df.iloc[
            source_index.row()
        ]

        key_cols = [
                "Severity",
                "Alarm Time",
                "Cancel Time",
                "Alarm Number",
                "Supplementary Information",
                "Distinguished Name",
                "Diagnostic Info"
        ]

        file = f"{self.filename}.csv"

        if not os.path.exists(file):
            return

        db = pd.read_csv(
            file,
            dtype=str,
            keep_default_na=False
        )

        if db.empty:
            return

        # find matching alarm

        mask = pd.Series(
            True,
            index=db.index
        )

        for col in key_cols:
            mask &= (
                    db[col].astype(str)
                    ==
                    str(row[col])
            )

        # delete status record

        db = db[~mask]
        try:
            db.to_csv(
                file,
                index=False
            )
        except PermissionError:
            QMessageBox.warning(
                self,
                "Warning",
                f"File is open: {file}. Please close it and try again."
            )

        # reload dataframe from csv

        self.apply_saved_status()

        # refresh model

        model = self.proxy.sourceModel()

        if model:
            model.beginResetModel()

            model.df = self.df.copy()

            model.endResetModel()

        self.table.viewport().update()

    def clear_all_status(self):

        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            "Are you sure you want to clear all alarm status?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        file = f"{self.filename}.csv"

        # -----------------------------
        # CLEAR CSV
        # -----------------------------
        try:
            if os.path.exists(file):
                pd.DataFrame(
                    columns=[
                        "Severity",
                        "Alarm Time",
                        "Cancel Time",
                        "Alarm Number",
                        "Supplementary Information",
                        "Distinguished Name",
                        "Diagnostic Info",
                        "Status",
                        "Resolved"
                    ]
                ).to_csv(
                    file,
                    index=False
                )

        except PermissionError:
            QMessageBox.warning(
            self,
            "Warning",
            f"File is open: {file}. Please close it and try again."
            )
            return
        # -----------------------------
        # CLEAR TABLE DATA
        # -----------------------------
        if "Status" in self.df.columns:
            self.df["Status"] = ""

        if "Resolved" in self.df.columns:
            self.df["Resolved"] = ""

        # -----------------------------
        # REFRESH TABLE
        # -----------------------------
        model = self.proxy.sourceModel()

        if model:
            model.beginResetModel()
            model.df = self.df.copy()
            model.endResetModel()

        self.table.viewport().update()

    def open_status_file(self):
        filename = f"{self.filename}.csv"
        try:
            os.startfile(filename)
        except FileNotFoundError:
            QMessageBox.warning(
                self,
                "Warning",
                f"{filename} Does not exit. Try to create it using update status"
            )

    def apply_saved_status(self):

        if not self.enable_status_tracking:
            return
        file = f"{self.filename}.csv"

        key_cols = [
            "Supplementary Information",
            "Distinguished Name",
            "Diagnostic Info"
        ]

        # make sure columns exist
        for col in key_cols + ["Status", "Resolved"]:

            if col not in self.df.columns:
                self.df[col] = ""

        # ALWAYS clear existing values first
        self.df["Status"] = ""
        self.df["Resolved"] = ""

        if not os.path.exists(file):
            return

        db = pd.read_csv(
            file,
            dtype=str,
            keep_default_na=False
        )

        if db.empty:
            return

        # create lookup dictionary

        status_lookup = {}

        for _, row in db.iterrows():
            key = tuple(
                str(row[col])
                for col in key_cols
            )

            status_lookup[key] = {

                "Status":
                    row.get("Status", ""),

                "Resolved":
                    row.get("Resolved", "")
            }

        # apply saved values

        for idx, row in self.df.iterrows():

            key = tuple(
                str(row[col])
                for col in key_cols
            )

            if key in status_lookup:
                self.df.at[
                    idx,
                    "Status"
                ] = status_lookup[key]["Status"]

                self.df.at[
                    idx,
                    "Resolved"
                ] = status_lookup[key]["Resolved"]

    def show_context_menu(self, pos):
        if not self.enable_status_tracking:
            return
        index = self.table.indexAt(pos)

        if not index.isValid():
            return

        source_index = self.proxy.mapToSource(index)

        col_name = self.df.columns[
            source_index.column()
        ]

        if col_name != "Status":
            return

        menu = QMenu(self)

        update_action = menu.addAction(
            "Update Status"
        )

        update_action.setIcon(QIcon(resource_path('resources/icon/update.ico')))
        open_status_action = menu.addAction(
            "Open Status DB"
        )
        open_status_action.setIcon(QIcon(resource_path('resources/icon/open.ico')))
        clear_all_status_action = menu.addAction(
            "Clear All Status"
        )
        clear_all_status_action.setIcon(QIcon(resource_path('resources/icon/trash.ico')))


        action = menu.exec_(
            self.table.viewport().mapToGlobal(pos)
        )

        if action == update_action:
            self.update_status(source_index)


        elif action == clear_all_status_action:
            self.clear_all_status()

        elif action == open_status_action:
            self.open_status_file()

    def restart_search_timer(self):
        self.search_timer.start()

    def apply_search(self):
        text = self.search.text()
        self.proxy.setSearch(text)
        self.filterChanged.emit()

    def load_dataframe(self,tablename, display_df,export_df=None, color=None):

        self.df = display_df.copy()
        self.apply_saved_status()

        model = PandasModel(
            self.df,
            color,
            table_name=tablename
        )

        self.proxy.setSourceModel(model)

        self.table.setModel(self.proxy)

        self.table.resizeColumnsToContents()
        self.resize_cols("Severity", 30)
        self.resize_cols("Alarm Number", 85)
        self.resize_cols("Supplementary Information", 250)
        self.resize_cols("Status", 400)
        #self.resize_cols("Resolved", 30)


    def show_details(self, index):

        source_index = self.proxy.mapToSource(index)

        model = self.proxy.sourceModel()

        data = model.df.iloc[
            source_index.row()
        ].to_dict()

        dlg = DetailDialog(data)

        dlg.exec_()

    def export_csv(self):

        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            "",
            "CSV Files (*.csv)"
        )

        if not file_name:
            return

        model = self.proxy.sourceModel()

        rows = []

        for row in range(self.proxy.rowCount()):
            proxy_index = self.proxy.index(row, 0)

            source_index = self.proxy.mapToSource(proxy_index)

            rows.append(
                model.df.iloc[source_index.row()]
            )

        export_df = pd.DataFrame(rows)

        export_df.to_csv(
            file_name,
            index=False
        )

    def resize_cols(self, headername, width):
        header = self.table.horizontalHeader()
        header_name = headername
        model = self.table.model()

        for col in range(model.columnCount()):
            if model.headerData(col, Qt.Horizontal) == header_name:
                self.table.setColumnWidth(col, width)
                header.setSectionResizeMode(col, QHeaderView.Interactive)
                break

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
            "", resource_path("resources/icon/save.ico")
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

class MainWindow(MangoMainWindow):

    def __init__(self):
        super().__init__()
        self.session = "statusFile"
        # -----------------------------
        # WINDOW
        # -----------------------------
        icon_path = resource_path(
            "resources/icon/delta.ico"
        )

        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("PostCheck Analyzer")

        # -----------------------------
        # DATA
        # -----------------------------
        self.pre_df = pd.DataFrame()
        self.post_df = pd.DataFrame()
        self.history_df = pd.DataFrame()
        self.post_history_df = pd.DataFrame()
        self.history_source_path = ""
        self.history_source_df = pd.DataFrame()
        # -----------------------------
        # UI STATE
        # -----------------------------
        self.ui_loaded = False

        # -----------------------------
        # MAIN TAB CONTROL
        # -----------------------------
        self.tabs = QTabWidget()


        self.setCentralWidget(self.tabs)


        self.tabs.setStyleSheet("""
        QTabBar::tab {
            background: #2b2b2b;
            color: white;
            padding: 6px;
            border: 1px solid #444;
            min-width: 120px;
        }
        QTabBar::tab:hover{
            background:#4a90e2;
            color:black;
            font-weight: bold;
        }
        QTabBar::tab:selected {
            background: #4a90e2;
            color: white;
            font-weight: bold;
        }

        QTabWidget::pane {
            border: 1px solid #444;
        }
        """)
        # -----------------------------
        # STATUS BAR
        # -----------------------------
        self.status_bar = self.statusBar()

        self.status_bar.showMessage(
            "Analyzer → Browse Input Files"
        )

        # -----------------------------
        # MENU
        # -----------------------------
        self.create_menu()

        # -----------------------------
        # DRAG DROP
        # -----------------------------
        self.setAcceptDrops(True)



    def load_analyzer_ui(self):


        if self.ui_loaded:
            self.show_input_tab()
            return

        # -----------------------------
        # FILE INPUT TAB
        # -----------------------------
        self.create_input_tab()

        # -----------------------------
        # MAIN TABLES
        # -----------------------------
        self.pre_tab = AlarmTable(filename=self.session)
        self.post_tab = AlarmTable(filename=self.session)
        self.history_tab = AlarmTable(filename=self.session)
        self.post_history_tab = AlarmTable(filename=self.session)

        # -----------------------------
        # DELTA TABS
        # -----------------------------
        self.new_tab = AlarmTable(filename=self.session)
        self.cleared_tab = AlarmTable(filename=self.session)

        self.delta_tabs = QTabWidget()
        self.delta_tabs.addTab(self.new_tab, "New")
        self.delta_tabs.addTab(self.cleared_tab, "Cleared")

        # -----------------------------
        # HISTORY DELTA TABS
        # -----------------------------
        self.hist_new_tab = AlarmTable(filename=self.session)
        self.hist_cleared_tab = AlarmTable(filename=self.session)

        self.history_delta_tabs = QTabWidget()
        self.history_delta_tabs.addTab(self.hist_new_tab, "New")
        self.history_delta_tabs.addTab(self.hist_cleared_tab, "Cleared")



        # -----------------------------
        # ADD TABS IN REQUIRED ORDER
        # -----------------------------
        self.tabs.addTab(self.pre_tab, "Pre (Active)")
        self.tabs.addTab(self.post_tab, "Post (Active)")
        self.tabs.addTab(self.delta_tabs, "Delta (Active)")
        self.tabs.addTab(self.history_tab, "Pre (History)")
        self.tabs.addTab(self.post_history_tab, "Post (History)")
        self.tabs.addTab(self.history_delta_tabs, "Delta (History)")
        # -----------------------------
        # HISTORY FILTER TAB
        # -----------------------------
        self.history_filter_tab = AlarmTable(filename=self.session)

        self.create_history_analysis_tab()

        # -----------------------------
        # STATUS TRACKING
        # -----------------------------
        self.pre_tab.enable_status_tracking = False
        self.post_tab.enable_status_tracking = False
        self.history_tab.enable_status_tracking = False
        self.post_history_tab.enable_status_tracking = False

        self.new_tab.enable_status_tracking = True

        self.cleared_tab.enable_status_tracking = False
        self.hist_new_tab.enable_status_tracking = True
        self.hist_cleared_tab.enable_status_tracking = False

        # History Analysis table
        self.history_filter_tab.enable_status_tracking = False
        # -----------------------------
        # SIGNALS
        # -----------------------------
        self.tabs.currentChanged.connect(self.update_counts)
        self.delta_tabs.currentChanged.connect(self.update_counts)
        self.history_delta_tabs.currentChanged.connect(self.update_counts)

        for tab in (
                self.pre_tab,
                self.post_tab,
                self.history_tab,
                self.post_history_tab,
                self.new_tab,
                self.cleared_tab,
                self.hist_new_tab,
                self.hist_cleared_tab,
                self.history_filter_tab,
        ):
            tab.filterChanged.connect(self.update_counts)

        # -----------------------------
        # STATE
        # -----------------------------
        self.ui_loaded = True



        self.show_input_tab()

    def load_csv_merger_ui(self):

        dlg = CSVMergerDialog()

        dlg.exec_()


    def create_menu(self):

        menubar = self.menuBar()

        # -------------------------
        # ANALYZER MENU
        # -------------------------
        analyzer_menu = menubar.addMenu("&Alarm Analyzer")

        browse_action = analyzer_menu.addAction(
            "Browse Input Files"
        )

        browse_action.setIcon(
            QIcon(resource_path("resources/icon/browsefiles.png"))
        )

        browse_action.triggered.connect(
            self.load_analyzer_ui
        )

        mergefile_action = analyzer_menu.addAction(
            "Merge Alarm Files"
        )

        mergefile_action.setIcon(
            QIcon(resource_path("resources/icon/merge.png"))
        )

        mergefile_action.triggered.connect(
            self.load_csv_merger_ui
        )


        analyzer_menu.addSeparator()

        exit_action = analyzer_menu.addAction(
            "Exit"
        )

        exit_action.setIcon(
            QIcon(resource_path("resources/icon/exitapp.png"))
        )
        exit_action.triggered.connect(
            self.close
        )


        # -------------------------
        # HELP MENU
        # -------------------------
        help_menu = menubar.addMenu("&Help")

        about_action = help_menu.addAction(
            "About"
        )
        about_action.setIcon(
            QIcon(resource_path("resources/icon/about.png"))
        )
        about_action.triggered.connect(
            self.show_about
        )

    def show_input_tab(self):

        for i in range(self.tabs.count()):

            if self.tabs.tabText(i) == "Input":
                self.tabs.setCurrentIndex(i)
                return

    def show_about(self):

        QMessageBox.about(
            self,
            "About PostCheck Analyzer",
            """
            <h3>PostCheck Analyzer</h3>

            <p><b>Version:</b> 1.0</p>

            <p>
            <b>Developed By:</b><br>
            Tapon Paul
            </p>

            <p>
            <b>Email:</b><br>
            tapon.paul@nokia.com
            </p>

            <p>
            <b>Phone:</b><br>
            +8801919045275
            </p>

            <p>
            RAN Specialist Engineer<br>
            Nokia
            </p>
            """
        )

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return
        path = urls[0].toLocalFile()
        if not os.path.isdir(path):
            return

        self.scan_alarm_folder(path)

    def scan_alarm_folder(self, folder):

        pre_file = None
        post_file = None
        pre_hist_file = None
        post_hist_file = None

        for file_name in os.listdir(folder):

            full_path = os.path.join(folder, file_name)

            if not os.path.isfile(full_path):
                continue

            name = file_name.lower()

            if pre_file is None and "pre" in name:
                pre_file = full_path

            elif post_file is None and "post" in name:
                post_file = full_path

            elif pre_hist_file is None and "his" in name:
                pre_hist_file = full_path

            elif post_hist_file is None and "latest" in name:
                post_hist_file = full_path

        # -----------------------------
        # ALWAYS RESET FIRST (IMPORTANT)
        # -----------------------------
        self.pre_edit.clear()
        self.post_edit.clear()
        self.hist_edit.clear()
        self.post_hist_edit.clear()
        if pre_file:
            self.pre_edit.setText(pre_file.replace("\\", "/"))

        if post_file:
            self.post_edit.setText(post_file.replace("\\", "/"))

        if pre_hist_file:
            self.hist_edit.setText(pre_hist_file.replace("\\", "/"))

        if post_hist_file:
            self.post_hist_edit.setText(post_hist_file.replace("\\", "/"))

    def create_history_analysis_tab(self):

        page = QWidget()
        layout = QVBoxLayout()

        # -----------------------------
        # FILE SELECT (NEW BROWSE UI)
        # -----------------------------
        file_layout = QHBoxLayout()

        self.history_source_edit = MangoLineEdit()
        self.history_source_edit.setPlaceholderText("Select History Source File")

        browse_btn = QPushButton("Browse")

        browse_btn.clicked.connect(
            self.browse_history_source_file
        )

        file_layout.addWidget(QLabel("Source File"))
        file_layout.addWidget(self.history_source_edit)
        file_layout.addWidget(browse_btn)

        layout.addLayout(file_layout)

        # -----------------------------
        # TIME FILTER
        # -----------------------------
        filter_layout = QHBoxLayout()

        self.alarm_time_from_edit = QDateTimeEdit()
        self.alarm_time_to_edit = QDateTimeEdit()

        self.alarm_time_from_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.alarm_time_to_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")

        self.alarm_time_from_edit.setDateTime(QDateTime.currentDateTime())
        self.alarm_time_to_edit.setDateTime(QDateTime.currentDateTime())

        run_btn = QPushButton("Filter History Alarms")
        run_btn.clicked.connect(self.run_history_analysis)

        filter_layout.addWidget(QLabel("Alarm Time From"))
        filter_layout.addWidget(self.alarm_time_from_edit)
        filter_layout.addWidget(QLabel("Alarm Time To"))
        filter_layout.addWidget(self.alarm_time_to_edit)
        filter_layout.addWidget(run_btn)

        layout.addLayout(filter_layout)

        # -----------------------------
        # TABLE
        # -----------------------------
        layout.addWidget(self.history_filter_tab)

        page.setLayout(layout)

        self.tabs.addTab(page, "Filter By Time")

    def browse_history_source_file(self):

        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select History Source CSV",
            "",
            "CSV Files (*.csv)"
        )

        if file_name:
            self.history_source_path = file_name
            self.history_source_edit.setText(file_name)

    def run_history_analysis(self):

        # -----------------------------
        # SAFETY CHECKS
        # -----------------------------
        if not self.ui_loaded:
            QMessageBox.warning(
                self,
                "Warning",
                "Please select Analyzer → Browse Input Files first."
            )
            return

        path = self.history_source_edit.text().strip().replace("\\","/")

        if not path:
            QMessageBox.warning(
                self,
                "Warning",
                "Please select a history file"
            )
            return

        # -----------------------------
        # LOAD DATA
        # -----------------------------
        history = self.load_csv_if_exists(path)

        if history.empty:
            QMessageBox.warning(
                self,
                "Warning",
                "History file is empty or invalid"
            )
            return

        print("RAW ROWS:", len(history))

        # -----------------------------
        # CHECK COLUMN
        # -----------------------------
        if "Alarm Time" not in history.columns:
            QMessageBox.warning(
                self,
                "Error",
                "'Alarm Time' column not found"
            )
            return

        # -----------------------------
        # DATETIME CONVERSION (SAFE)
        # -----------------------------
        history["Alarm Time"] = pd.to_datetime(
            history["Alarm Time"],
            errors="coerce",
            utc=True
        )

        print("NaT COUNT:", history["Alarm Time"].isna().sum())

        # remove invalid rows
        history = history.dropna(subset=["Alarm Time"])

        print("AFTER PARSE ROWS:", len(history))

        # -----------------------------
        # TIME FILTER
        # -----------------------------
        alarm_from = self.alarm_time_from_edit.dateTime().toPyDateTime()
        alarm_to = self.alarm_time_to_edit.dateTime().toPyDateTime()

        # convert UI time to UTC for consistency
        alarm_from = pd.to_datetime(alarm_from, utc=True)
        alarm_to = pd.to_datetime(alarm_to, utc=True)

        result = history[
            (history["Alarm Time"] >= alarm_from) &
            (history["Alarm Time"] <= alarm_to)
            ]

        print("AFTER FILTER ROWS:", len(result))

        # -----------------------------
        # DISPLAY PREPARATION
        # -----------------------------
        display_df = result[
            [c for c in DISPLAY_COLUMNS if c in result.columns]
        ].copy()

        # -----------------------------
        # LOAD INTO TABLE
        # -----------------------------
        self.history_filter_tab.load_dataframe(
            "history_filter",
            display_df,
            result,
            "#fff2cc"
        )

        # -----------------------------
        # UPDATE UI
        # -----------------------------
        self.update_counts()

    def get_current_alarm_table(self):

        if not self.ui_loaded:
            return None

        widget = self.tabs.currentWidget()

        if isinstance(widget, AlarmTable):
            return widget

        if hasattr(self, "delta_tabs"):

            if widget == self.delta_tabs:
                return self.delta_tabs.currentWidget()

        if hasattr(self, "history_delta_tabs"):

            if widget == self.history_delta_tabs:
                return self.history_delta_tabs.currentWidget()

        table = widget.findChild(
            AlarmTable
        )

        if table:
            return table

        return None

    def update_counts(self):
        if not self.ui_loaded:
            QMessageBox.warning(
                self,
                "Warning",
                "Please select Analyzer → Browse Input Files first."
            )
            return
        pre_count = len(self.pre_tab.df)
        post_count = len(self.post_tab.df)
        history_count = len(self.history_tab.df)
        post_history_count = len(self.post_history_tab.df)

        new_count = len(self.new_tab.df)
        cleared_count = len(self.cleared_tab.df)

        current_table = self.get_current_alarm_table()

        current_text = ""

        if current_table is not None:
            model = current_table.proxy.sourceModel()

            if model is None:
                total_rows = 0
                visible_rows = 0
            else:
                total_rows = model.rowCount()
                visible_rows = current_table.proxy.rowCount()

            current_text = (
                f" | Current Matrix: "
                f"{visible_rows}/{total_rows} rows"
            )

        self.status_bar.showMessage(
            f"Pre Active: {pre_count}  |  "
            f"Post Active: {post_count}  |  "
            f"Newly Active: {new_count}  |  "
            f"Post Cleared: {cleared_count} | "
            f"Pre History: {history_count}  |  "
            f"Post History: {post_history_count}  |  "
            
            f"{current_text}"
        )

    def create_input_tab(self):

        page = QWidget()
        layout = QVBoxLayout()

        # ---------------- PRE ALARM ----------------
        pre_group = MangoGroupBox("Pre Active Alarm File")
        pre_layout = QHBoxLayout()

        self.pre_edit = MangoLineEdit()
        self.pre_edit.setPlaceholderText("Browse pre active alarms ...")

        pre_btn = QPushButton("Browse")
        pre_btn.clicked.connect(lambda: self.browse(self.pre_edit))

        pre_layout.addWidget(self.pre_edit)
        pre_layout.addWidget(pre_btn)

        pre_group.setLayout(pre_layout)
        pre_group.setToolTip("Browse an input file that contains the active alarms before the activity"
                              "\nFor automatic file detection in drag and drop, use keyword [pre] anywhere "
                              "in the filename")
        layout.addWidget(pre_group)

        # ---------------- POST ALARM ----------------
        post_group = MangoGroupBox("Post Active Alarm File")
        pre_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        post_layout = QHBoxLayout()

        self.post_edit = MangoLineEdit()
        self.post_edit.setPlaceholderText("Browse post active alarms ...")

        post_btn = QPushButton("Browse")
        post_btn.clicked.connect(lambda: self.browse(self.post_edit))

        post_layout.addWidget(self.post_edit)
        post_layout.addWidget(post_btn)

        post_group.setLayout(post_layout)
        post_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        post_group.setToolTip("Browse an input file that contains the active alarms after the activity"
                              "\nFor automatic file detection in drag and drop, use keyword [post] anywhere "
                              "in the filename")

        layout.addWidget(post_group)

        # ---------------- HISTORY ALARM ----------------
        hist_group = MangoGroupBox("Pre History Alarm File")
        hist_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        hist_layout = QHBoxLayout()

        self.hist_edit = MangoLineEdit()
        self.hist_edit.setPlaceholderText("Browse pre history alarms ...")

        hist_btn = QPushButton("Browse")
        hist_btn.clicked.connect(lambda: self.browse(self.hist_edit))

        hist_layout.addWidget(self.hist_edit)
        hist_layout.addWidget(hist_btn)

        hist_group.setLayout(hist_layout)
        hist_group.setToolTip("Browse an input file that contains the history alarms before the activity"
                              "\nFor automatic file detection in drag and drop, use keyword [his] anywhere "
                              "in the filename")
        layout.addWidget(hist_group)


        # ---------------- POST HISTORY ALARM ----------------
        post_hist_group = MangoGroupBox("Post History Alarm File")
        post_hist_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        post_hist_layout = QHBoxLayout()

        self.post_hist_edit = MangoLineEdit()
        self.post_hist_edit.setPlaceholderText("Browse post history alarms ...")

        post_hist_btn = QPushButton("Browse")
        post_hist_btn.clicked.connect(lambda: self.browse(self.post_hist_edit))

        post_hist_layout.addWidget(self.post_hist_edit)
        post_hist_layout.addWidget(post_hist_btn)

        post_hist_group.setLayout(post_hist_layout)
        post_hist_group.setToolTip("Browse an input file that contains the history alarms after the activity"
                              "\nFor automatic file detection in drag and drop, use keyword [latest] anywhere "
                              "in the filename")
        layout.addWidget(post_hist_group)

        # ---------------- RUN BUTTON ----------------
        run_btn = MangoButton("", resource_path("resources/icon/run.png"))
        # run_btn.setFixedHeight(40)
        # run_btn.setMaximumWidth(100)
        run_btn.clicked.connect(self.run_analysis)

        layout.addWidget(run_btn, alignment=Qt.AlignHCenter)

        page.setLayout(layout)

        self.tabs.addTab(page, "Input")

    def file_row(self, label, lineedit):

        layout = QHBoxLayout()

        btn = QPushButton("Browse")

        btn.clicked.connect(
            lambda: self.browse(lineedit)
        )

        layout.addWidget(QLabel(label))
        layout.addWidget(lineedit)
        layout.addWidget(btn)

        return layout

    def browse(self, edit):

        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV",
            "",
            "CSV Files (*.csv)"
        )

        if file_name:
            edit.setText(file_name)

    def load_csv(self, path):

        return pd.read_csv(
            path,
            dtype=str,
            keep_default_na=False,
            low_memory=False
        )

    def load_csv_if_exists(self, path):

        path = path.strip()

        if not path:
            return pd.DataFrame()

        return pd.read_csv(
            path,
            dtype=str,
            keep_default_na=False,
            low_memory=False
        )

    def get_status_file(self):

        return f"{self.session}.csv"

    def load_status_db(self):

        file = self.get_status_file()

        if not os.path.exists(file):
            return pd.DataFrame(
                columns=[
                    "Supplementary Information",
                    "Distinguished Name",
                    "Diagnostic Info",
                    "Status",
                    "Resolved"
                ]
            )

        return pd.read_csv(
            file,
            dtype=str,
            keep_default_na=False
        )

    def save_status_db(self, df):

        df.to_csv(
            self.get_status_file(),
            index=False
        )

    def apply_status_to_dataframe(self, df):

        if df.empty:
            return df

        status_db = self.load_status_db()

        if status_db.empty:
            df["Status"] = ""
            df["Resolved"] = ""
            return df

        merge_cols = [
            "Supplementary Information",
            "Distinguished Name",
            "Diagnostic Info"
        ]
        status_cols = merge_cols + [
            "Status",
            "Resolved"
        ]
        status_db = status_db[status_cols]

        return df.merge(
            status_db,
            on=merge_cols,
            how="left"
        )
    def run_analysis(self):
        x=1
        if not self.ui_loaded:
            QMessageBox.warning(
                self,
                "Warning",
                "Please select Analyzer → Browse Input Files first."
            )
            return
        try:
            # ----------------------------
            # 1. LOAD FILES (SAFE)
            # ----------------------------



            self.pre_df = self.load_csv_if_exists(self.pre_edit.text())
            self.post_df = self.load_csv_if_exists(self.post_edit.text())
            self.history_df = self.load_csv_if_exists(self.hist_edit.text())
            self.post_history_df = self.load_csv_if_exists(self.post_hist_edit.text())

            # ----------------------------
            # HELPER
            # ----------------------------
            def safe_display(df, columns):
                if df is None or df.empty:
                    return pd.DataFrame(columns=columns)
                return df[[c for c in columns if c in df.columns]]

            # ----------------------------
            # 2. LOAD MAIN TABLES
            # ----------------------------
            self.pre_tab.load_dataframe(
                "pre_table",
                safe_display(self.pre_df, DISPLAY_COLUMNS),
                self.pre_df,

            )

            self.post_tab.load_dataframe(
                "post_table",
                safe_display(self.post_df, DISPLAY_COLUMNS),
                self.post_df,

            )

            self.history_tab.load_dataframe(
                "history_table",
                safe_display(self.history_df, DISPLAY_COLUMNS),
                self.history_df,

            )
            # -----------------------------
            # POST HISTORY TABLE
            # -----------------------------
            self.post_history_tab.load_dataframe(
                "post_history",
                safe_display(self.post_history_df, DISPLAY_COLUMNS),
                self.post_history_df,

            )

            # ----------------------------
            # 3. PRE / POST DELTA
            # ----------------------------
            new_df, cleared_df = calculate_pre_post_delta(
                self.pre_df,
                self.post_df,
                self.history_df  # IMPORTANT
            )



            # ----------------------------
            # 4. HISTORY DELTA (INDEPENDENT)
            # ----------------------------
            hist_new_df, hist_cleared_df = calculate_history_delta(
                self.history_df,
                self.post_history_df
            )

            new_df = self.apply_status_to_dataframe(new_df)


            hist_new_df = self.apply_status_to_dataframe(hist_new_df)

            # ----------------------------
            # 5. LOAD DELTA TABS (PRE/POST)
            # ----------------------------

            self.new_tab.load_dataframe(
                "active_delta_new_table",
                safe_display(new_df, DISPLAY_COLUMNS_NEW),
                new_df,
                "#d4ffd4",

            )
            self.new_tab.apply_saved_status()

            self.cleared_tab.load_dataframe(
                "active_delta_cleared_table",
                safe_display(cleared_df, DISPLAY_COLUMNS),
                cleared_df,
                "#ffd4d4",

            )

            # ----------------------------
            # 6. LOAD HISTORY DELTA TABS
            # ----------------------------
            self.hist_new_tab.load_dataframe(
                "history_delta_new_table",
                safe_display(hist_new_df, DISPLAY_COLUMNS_NEW),
                hist_new_df,
                "#d4ffd4",


            )

            self.hist_cleared_tab.load_dataframe(
                "history_delta_cleared_table",
                safe_display(hist_cleared_df, DISPLAY_COLUMNS),
                hist_cleared_df,
                "#ffd4d4",

            )

            # ----------------------------
            # 7. UPDATE UI
            # ----------------------------
            self.update_counts()

            QMessageBox.information(
                self,
                "Done",
                f"New alarms: {len(new_df)}\n"
                f"Cleared alarms: {len(cleared_df)}\n\n"
                f"History New: {len(hist_new_df)}\n"
                f"History Cleared: {len(hist_cleared_df)}"
            )

            self.switch_to_first_available_tab()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


    def switch_to_first_available_tab(self):

        # Pre
        if not self.pre_df.empty:
            self.tabs.setCurrentWidget(self.pre_tab)
            return

        # Post
        if not self.post_df.empty:
            self.tabs.setCurrentWidget(self.post_tab)
            return

        # History
        if not self.history_df.empty:
            self.tabs.setCurrentWidget(self.history_tab)
            return

        # Post History
        if not self.post_history_df.empty:
            self.tabs.setCurrentWidget(self.post_history_tab)
            return
        # Delta tabs exist inside QTabWidget
        if not self.new_tab.df.empty or not self.cleared_tab.df.empty:

            # First switch to Delta parent tab
            for i in range(self.tabs.count()):
                if self.tabs.tabText(i) == "Delta":
                    self.tabs.setCurrentIndex(i)
                    break

            # Then optionally switch inner tab (New preferred)
            try:
                if not self.new_tab.df.empty:
                    self.tabs.currentWidget().setCurrentWidget(self.new_tab)
                elif not self.cleared_tab.df.empty:
                    self.tabs.currentWidget().setCurrentWidget(self.cleared_tab)
            except:
                pass

            return

        # fallback
        self.tabs.setCurrentIndex(0)

if __name__ == "__main__":

    app = QApplication(sys.argv)
    app.setStyleSheet("""
    QToolTip {
        background-color: #2b2b2b;
        color: white;
        border: 1px solid #808080;
        padding: 4px;
        font-size: 10pt;
    }
    """)
    window = MainWindow()
    window.resize(1000,800)
    window.show()

    sys.exit(app.exec_())