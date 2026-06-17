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
    QDateTimeEdit

)

from AlarmComparison.customwidgets import MangoButton, MangoLineEdit, MangoGroupBox, MangoMainWindow

from AlarmComparison.models import PandasModel,GlobalFilterProxy
from AlarmComparison.dialogs import DetailDialog
from AlarmComparison.delta import calculate_pre_post_delta, calculate_history_delta



DISPLAY_COLUMNS = [
    "Severity",
    "Alarm Time",
    "Cancel Time",
    "Alarm Number",
    "Alarm Text",
    "Supplementary Information",
    "Distinguished Name",
    "Diagnostic Info",
    "Name",
]

DISPLAY_COLUMNS_NEW = [
    "Severity",
    "Alarm Time",
    "Cancel Time",
    "Alarm Number",
    "Alarm Text",
    "Supplementary Information",
    "Distinguished Name",
    "Diagnostic Info",
    "Name",
    "History Match",
    "History Count",
]

def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return relative_path
    return os.path.join(base_path, relative_path)


class AlarmTable(QWidget):
    filterChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.df = pd.DataFrame()

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

    def restart_search_timer(self):
        self.search_timer.start()

    def apply_search(self):
        text = self.search.text()
        self.proxy.setSearch(text)
        self.filterChanged.emit()

    def load_dataframe(
            self,
            display_df,
            export_df=None,
            color=None):

        self.df = display_df.copy()

        if export_df is None:
            self.export_df = display_df.copy()
        else:
            self.export_df = export_df.copy()

        # preserve original row mapping
        self.df.index = self.export_df.index

        model = PandasModel(
            self.df,
            color
        )

        self.proxy.setSourceModel(model)

        self.table.setModel(self.proxy)

        self.table.resizeColumnsToContents()

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

        visible_indexes = []

        for row in range(self.proxy.rowCount()):
            proxy_index = self.proxy.index(row, 0)

            source_index = self.proxy.mapToSource(proxy_index)

            visible_indexes.append(
                model.df.index[source_index.row()]
            )

        export_df = self.export_df.loc[
            visible_indexes
        ]

        export_df.to_csv(
            file_name,
            index=False
        )


class MainWindow(MangoMainWindow):

    def __init__(self):
        super().__init__()

        # -----------------------------
        # WINDOW
        # -----------------------------
        icon_path = resource_path(
            "resources/icon/alarm.ico"
        )

        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("Alarm Analyzer")

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
        self.pre_tab = AlarmTable()
        self.post_tab = AlarmTable()
        self.history_tab = AlarmTable()
        self.post_history_tab = AlarmTable()

        # -----------------------------
        # DELTA TABS
        # -----------------------------
        self.new_tab = AlarmTable()
        self.cleared_tab = AlarmTable()

        self.delta_tabs = QTabWidget()
        self.delta_tabs.addTab(self.new_tab, "New")
        self.delta_tabs.addTab(self.cleared_tab, "Cleared")

        # -----------------------------
        # HISTORY DELTA TABS
        # -----------------------------
        self.hist_new_tab = AlarmTable()
        self.hist_cleared_tab = AlarmTable()

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
        self.history_filter_tab = AlarmTable()

        self.create_history_analysis_tab()

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

    def create_menu(self):

        menubar = self.menuBar()

        # -------------------------
        # ANALYZER MENU
        # -------------------------
        analyzer_menu = menubar.addMenu("&Analyzer")

        browse_action = analyzer_menu.addAction(
            "Browse Input Files"
        )

        browse_action.setIcon(
            QIcon(resource_path("resources/icon/browsefiles.png"))
        )

        browse_action.triggered.connect(
            self.load_analyzer_ui
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
            "About Alarm Analyzer",
            """
            <h3>Alarm Analyzer</h3>

            <p><b>Version:</b> 1.0</p>

            <p>
            <b>Developed By:</b><br>
            Tapon Paul
            </p>

            <p>
            <b>Email:</b><br>
            test.paul@test.com
            </p>

            <p>
            <b>Phone:</b><br>
            +880XXXXXXXX
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
            f"Pre: {pre_count}  |  "
            f"Post: {post_count}  |  "
            f"History: {history_count}  |  "
            f"Post History: {post_history_count}  |  "
            f"New: {new_count}  |  "
            f"Cleared: {cleared_count} "
            f"{current_text}"
        )

    def create_input_tab(self):

        page = QWidget()
        layout = QVBoxLayout()

        # ---------------- PRE ALARM ----------------
        pre_group = MangoGroupBox("Pre Alarm File")
        pre_layout = QHBoxLayout()

        self.pre_edit = MangoLineEdit()
        self.pre_edit.setPlaceholderText("Select Pre Alarm CSV")

        pre_btn = QPushButton("Browse")
        pre_btn.clicked.connect(lambda: self.browse(self.pre_edit))

        pre_layout.addWidget(self.pre_edit)
        pre_layout.addWidget(pre_btn)

        pre_group.setLayout(pre_layout)
        layout.addWidget(pre_group)

        # ---------------- POST ALARM ----------------
        post_group = MangoGroupBox("Post Alarm File")
        pre_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        post_layout = QHBoxLayout()

        self.post_edit = MangoLineEdit()
        self.post_edit.setPlaceholderText("Select Post Alarm CSV")

        post_btn = QPushButton("Browse")
        post_btn.clicked.connect(lambda: self.browse(self.post_edit))

        post_layout.addWidget(self.post_edit)
        post_layout.addWidget(post_btn)

        post_group.setLayout(post_layout)
        post_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(post_group)

        # ---------------- HISTORY ALARM ----------------
        hist_group = MangoGroupBox("History Alarm File")
        hist_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        hist_layout = QHBoxLayout()

        self.hist_edit = MangoLineEdit()
        self.hist_edit.setPlaceholderText("Select History Alarm CSV")

        hist_btn = QPushButton("Browse")
        hist_btn.clicked.connect(lambda: self.browse(self.hist_edit))

        hist_layout.addWidget(self.hist_edit)
        hist_layout.addWidget(hist_btn)

        hist_group.setLayout(hist_layout)
        layout.addWidget(hist_group)


        # ---------------- POST HISTORY ALARM ----------------
        post_hist_group = MangoGroupBox("Post History Alarm File")
        post_hist_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        post_hist_layout = QHBoxLayout()

        self.post_hist_edit = MangoLineEdit()
        self.post_hist_edit.setPlaceholderText("Select History Alarm CSV")

        post_hist_btn = QPushButton("Browse")
        post_hist_btn.clicked.connect(lambda: self.browse(self.post_hist_edit))

        post_hist_layout.addWidget(self.post_hist_edit)
        post_hist_layout.addWidget(post_hist_btn)

        post_hist_group.setLayout(post_hist_layout)
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

    def run_analysis(self):

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
                safe_display(self.pre_df, DISPLAY_COLUMNS),
                self.pre_df
            )

            self.post_tab.load_dataframe(
                safe_display(self.post_df, DISPLAY_COLUMNS),
                self.post_df
            )

            self.history_tab.load_dataframe(
                safe_display(self.history_df, DISPLAY_COLUMNS),
                self.history_df
            )
            # -----------------------------
            # POST HISTORY TABLE
            # -----------------------------
            self.post_history_tab.load_dataframe(
                safe_display(self.post_history_df, DISPLAY_COLUMNS),
                self.post_history_df
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

            # ----------------------------
            # 5. LOAD DELTA TABS (PRE/POST)
            # ----------------------------
            self.new_tab.load_dataframe(
                safe_display(new_df, DISPLAY_COLUMNS_NEW),
                new_df,
                "#d4ffd4"
            )

            self.cleared_tab.load_dataframe(
                safe_display(cleared_df, DISPLAY_COLUMNS),
                cleared_df,
                "#ffd4d4"
            )

            # ----------------------------
            # 6. LOAD HISTORY DELTA TABS
            # ----------------------------
            self.hist_new_tab.load_dataframe(
                safe_display(hist_new_df, DISPLAY_COLUMNS_NEW),
                hist_new_df,
                "#d4ffd4"
            )

            self.hist_cleared_tab.load_dataframe(
                safe_display(hist_cleared_df, DISPLAY_COLUMNS),
                hist_cleared_df,
                "#ffd4d4"
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
    print(resource_path("resources/icon/export.png"))
    app = QApplication(sys.argv)

    window = MainWindow()
    window.resize(1000,800)
    window.show()

    sys.exit(app.exec_())