# ======================== Imports ========================


import os

import pandas as pd

from PyQt5.QtCore import QDateTime

from PyQt5.QtWidgets import (
    QWidget,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTabWidget,
    QMessageBox,
    QSizePolicy,
    QDialog,
    QFrame
)

from global_functions.delta import (
    calculate_pre_post_delta,
    calculate_history_delta,
)

from ui.customwidgets import (
    MangoButton,
    MangoDateTimeEdit,
    MangoLineEdit,
    MangoGroupBox
)

from PyQt5.QtGui import (
    QIcon,
    QMovie,
)

from PyQt5.QtCore import (
    Qt,
    QObject,
    QThread,
    pyqtSignal,
)

from global_functions.helper_functions import (
    resource_path,
    DISPLAY_COLUMNS,
    DISPLAY_COLUMNS_NEW,
)

from ui.tablewidget import AlarmTable


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
        if not output.find(".csv") >= 0:
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
            with open(output_path, "w", encoding="utf-8") as outfile:
                for csv in csv_files:
                    file_path = os.path.join(folder, csv)
                    with open(file_path, "r", encoding="utf-8") as infile:
                        lines = infile.readlines()
                        if first_file:
                            outfile.writelines(lines)
                            first_file = False
                        else:
                            outfile.writelines(lines[1:])
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


class AnalysisWorker(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, pre_path, post_path, history_path, post_history_path, key_cols_active_delta,
                 key_cols_history_delta, status_file):
        super().__init__()
        self.pre_path = pre_path
        self.post_path = post_path
        self.history_path = history_path
        self.post_history_path = post_history_path
        self.key_cols_active_delta = key_cols_active_delta
        self.key_cols_history_delta = key_cols_history_delta
        self.status_file = status_file

    @staticmethod
    def load_csv_if_exists(path):
        path = path.strip()

        if not path:
            return pd.DataFrame()

        return pd.read_csv(
            path,
            dtype=str,
            keep_default_na=False,
            low_memory=False
        )

    def apply_status_to_dataframe(self, df):
        if df.empty:
            return df

        if not os.path.exists(self.status_file):
            df = df.copy()
            df["Status"] = ""
            df["Resolved"] = ""
            return df

        status_db = pd.read_csv(
            self.status_file,
            dtype=str,
            keep_default_na=False
        )

        if status_db.empty:
            df = df.copy()
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

        # Keep only columns that exist
        if not all(col in status_db.columns for col in status_cols):
            return df

        status_db = status_db[status_cols]

        return df.merge(
            status_db,
            on=merge_cols,
            how="left"
        )

    def run(self):
        try:
            # -----------------------------
            # 1. LOAD CSV FILES
            # -----------------------------
            pre_df = self.load_csv_if_exists(
                self.pre_path
            )

            post_df = self.load_csv_if_exists(
                self.post_path
            )

            history_df = self.load_csv_if_exists(
                self.history_path
            )

            post_history_df = self.load_csv_if_exists(
                self.post_history_path
            )

            # -----------------------------
            # 2. ACTIVE DELTA
            # -----------------------------
            new_df, cleared_df = calculate_pre_post_delta(
                pre_df,
                post_df,
                history_df,
                self.key_cols_active_delta
            )

            # -----------------------------
            # 3. HISTORY DELTA
            # -----------------------------
            hist_new_df, hist_cleared_df = (
                calculate_history_delta(
                    history_df,
                    post_history_df,
                    self.key_cols_history_delta
                )
            )

            # -----------------------------
            # 4. APPLY SAVED STATUS
            # -----------------------------
            new_df = self.apply_status_to_dataframe(
                new_df
            )

            hist_new_df = self.apply_status_to_dataframe(
                hist_new_df
            )

            # -----------------------------
            # 5. RETURN EVERYTHING
            # -----------------------------
            result = {
                "pre_df": pre_df,
                "post_df": post_df,
                "history_df": history_df,
                "post_history_df": post_history_df,

                "new_df": new_df,
                "cleared_df": cleared_df,

                "hist_new_df": hist_new_df,
                "hist_cleared_df": hist_cleared_df,
            }

            self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))


class AlarmAnalyzerWidget(QWidget):
    def __init__(self, status_bar):
        super().__init__()
        self.status_bar = status_bar
        layout = QVBoxLayout(self)
        # -----------------------------
        # MAIN TAB CONTROL
        # -----------------------------
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.session = "statusFile"
        # -----------------------------
        # WINDOW
        # -----------------------------
        icon_path = resource_path(
            "resources/icon/AlarmAnalyzerWidgetIcon.ico"
        )
        # -----------------------------
        # DATA
        # -----------------------------
        self.pre_df = pd.DataFrame()
        self.post_df = pd.DataFrame()
        self.history_df = pd.DataFrame()
        self.post_history_df = pd.DataFrame()
        self.history_source_path = ""
        self.history_source_df = pd.DataFrame()
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
        self.analysis_thread = None
        self.analysis_worker = None
        self.run_movie = None
        self.load_analyzer_ui()
        # -----------------------------
        # DRAG DROP
        # -----------------------------
        self.setAcceptDrops(True)

    def load_analyzer_ui(self):
        # -----------------------------
        # FILE INPUT TAB
        # -----------------------------

        self.create_input_tab()

        # -----------------------------
        # MAIN TABLES
        # -----------------------------

        self.pre_tab = AlarmTable(filename=self.session, context="pre")
        self.post_tab = AlarmTable(filename=self.session, context="post")
        self.history_tab = AlarmTable(filename=self.session, context="history")
        self.post_history_tab = AlarmTable(filename=self.session, context="post_history")

        # -----------------------------
        # DELTA TABS
        # -----------------------------

        self.new_tab = AlarmTable(filename=self.session, context="delta")
        self.cleared_tab = AlarmTable(filename=self.session, context="delta")
        self.delta_tabs = QTabWidget()
        self.delta_tabs.addTab(self.new_tab, "New")
        self.delta_tabs.addTab(self.cleared_tab, "Cleared")
        self.new_tab.runRequested.connect(self.run_analysis)
        self.cleared_tab.runRequested.connect(self.run_analysis)

        # -----------------------------
        # HISTORY DELTA TABS
        # -----------------------------

        self.hist_new_tab = AlarmTable(filename=self.session, context="delta")
        self.hist_cleared_tab = AlarmTable(filename=self.session, context="delta")
        self.history_delta_tabs = QTabWidget()
        self.history_delta_tabs.addTab(self.hist_new_tab, "New")
        self.history_delta_tabs.addTab(self.hist_cleared_tab, "Cleared")
        self.hist_new_tab.runRequested.connect(self.run_analysis)
        self.hist_cleared_tab.runRequested.connect(self.run_analysis)

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
        # self.ui_loaded = True

        self.show_input_tab()

    def show_input_tab(self):
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "Input":
                self.tabs.setCurrentIndex(i)
                return

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
        if os.path.isdir(path):
            # Folder dropped
            self.scan_alarm_folder(path)

        elif os.path.isfile(path):
            # File dropped
            self.scan_alarm_file(path)

        event.acceptProposedAction()

    def scan_alarm_folder(self, folder):
        print("SELF:", id(self))
        print("PRE_EDIT:", id(self.pre_edit))
        print("VISIBLE WIDGET:", id(self))
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
            print("TEXT=", self.pre_edit.text())

        if post_file:
            self.post_edit.setText(post_file.replace("\\", "/"))

        if pre_hist_file:
            self.hist_edit.setText(pre_hist_file.replace("\\", "/"))

        if post_hist_file:
            self.post_hist_edit.setText(post_hist_file.replace("\\", "/"))

    def scan_alarm_file(self, file_path):
        filename = os.path.basename(file_path).lower()

        if "latest" in filename:
            self.latest_hist_edit.setText(file_path)

        elif "pre" in filename:
            self.pre_edit.setText(file_path)

        elif "post" in filename:
            self.post_edit.setText(file_path)

        elif "his" in filename:
            self.hist_edit.setText(file_path)

    def create_history_analysis_tab(self):

        page = QWidget()
        layout = QVBoxLayout()

        # -----------------------------
        # FILE SELECT (NEW BROWSE UI)
        # -----------------------------
        file_layout = QHBoxLayout()

        self.history_source_edit = MangoLineEdit()
        self.history_source_edit.setPlaceholderText("Select an alarm file")

        browse_btn = MangoButton("Browse", "Browse an alarm file", resource_path("resources/icon/search.png"))

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

        self.alarm_time_from_edit = MangoDateTimeEdit()
        self.alarm_time_to_edit = MangoDateTimeEdit()

        self.alarm_time_from_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.alarm_time_to_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")

        self.alarm_time_from_edit.setDateTime(QDateTime.currentDateTime())
        self.alarm_time_to_edit.setDateTime(QDateTime.currentDateTime())

        run_btn = MangoButton("Filter", "Filter Data", resource_path("resources/icon/filter.png"))
        run_btn.clicked.connect(self.run_history_analysis)

        filter_layout.addWidget(QLabel("Alarm Time From"))
        filter_layout.addWidget(self.alarm_time_from_edit)
        filter_layout.addSpacing(80)
        filter_layout.addWidget(QLabel("Alarm Time To"))
        filter_layout.addWidget(self.alarm_time_to_edit)
        filter_layout.addSpacing(80)
        filter_layout.addWidget(run_btn)
        filter_layout.addStretch()

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

        path = self.history_source_edit.text().strip().replace("\\", "/")

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

        # if not self.ui_loaded:
        #     return None

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
        print("CREATE_INPUT_TAB CALLED")

        page = QWidget()

        # Main page layout
        outer_layout = QVBoxLayout(page)
        outer_layout.setContentsMargins(20, 20, 20, 20)

        # Form container
        form_widget = QWidget()
        form_widget.setFixedWidth(850)
        form_widget.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed
        )
        layout = QVBoxLayout(form_widget)
        layout.setSpacing(15)

        # ---------------- TITLE ----------------
        label = QLabel("Alarm Analyzer Inputs")
        label.setStyleSheet("""
        margin:25 0;
        font-size:36px;
        font-weight:bold;
        color:#447100;
        """)
        label.setAlignment(Qt.AlignCenter)

        layout.addWidget(label)
        layout.addSpacing(25)

        outer_layout.addWidget(form_widget, alignment=Qt.AlignCenter)
        outer_layout.addStretch()
        # ---------------- PRE ALARM ----------------
        pre_group = MangoGroupBox("Pre Active Alarm File")
        pre_layout = QHBoxLayout()

        self.pre_edit = MangoLineEdit()
        self.pre_edit.setPlaceholderText("Browse pre active alarms ...")

        pre_btn = MangoButton("Browse..", "Browse a file for pre alarms", resource_path("resources/icon/search.png"))
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
        post_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        post_layout = QHBoxLayout()

        self.post_edit = MangoLineEdit()
        self.post_edit.setPlaceholderText("Browse post active alarms ...")

        post_btn = MangoButton("Browse..", "Browse a file for post alarms", resource_path("resources/icon/search.png"))
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

        hist_btn = MangoButton("Browse..", "Browse a file for pre history alarms",
                               resource_path("resources/icon/search.png"))
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

        post_hist_btn = MangoButton("Browse..", "Browse a file for post history alarms",
                                    resource_path("resources/icon/search.png"))
        post_hist_btn.clicked.connect(lambda: self.browse(self.post_hist_edit))

        post_hist_layout.addWidget(self.post_hist_edit)
        post_hist_layout.addWidget(post_hist_btn)

        post_hist_group.setLayout(post_hist_layout)
        post_hist_group.setToolTip("Browse an input file that contains the history alarms after the activity"
                                   "\nFor automatic file detection in drag and drop, use keyword [latest] anywhere "
                                   "in the filename")
        layout.addWidget(post_hist_group)

        # ---------------- RUN BUTTON ----------------
        self.run_btn = MangoButton("Run", "CLick to Run", resource_path("resources/icon/run.png"))

        self.run_btn.clicked.connect(self.run_analysis)

        layout.addWidget(self.run_btn, alignment=Qt.AlignHCenter)

        self.tabs.addTab(page, "Input")

    def file_row(self, label, lineedit):

        layout = QHBoxLayout()

        btn = QPushButton("Browser")

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
        if (
                self.analysis_thread is not None
                and self.analysis_thread.isRunning()
        ):
            return

        sender = self.sender()
        self.active_run_tab = None

        # Delta button triggered analysis
        if isinstance(sender, AlarmTable):
            self.active_run_tab = sender
            self.active_run_tab.start_run_animation()

        # Main Run button triggered analysis
        else:
            self.start_run_animation()

        # Only animate clicked Delta button
        if self.active_run_tab is not None:
            self.active_run_tab.start_run_animation()

        # -----------------------------
        # GET DELTA KEY COLUMNS
        # -----------------------------
        key_cols_active_delta = (
            self.new_tab
            .checkable_combo_delta
            .checkedItems()
        )

        key_cols_history_delta = (
            self.hist_new_tab
            .checkable_combo_delta
            .checkedItems()
        )

        # -----------------------------
        # DEFAULT ACTIVE DELTA KEYS
        # -----------------------------
        if not key_cols_active_delta:
            key_cols_active_delta = [
                "Alarm Number",
                "Supplementary Information",
                "Distinguished Name",
                "Severity",
            ]

        self.new_tab.checkable_combo_delta.setCheckedItems(
            key_cols_active_delta
        )

        self.cleared_tab.checkable_combo_delta.setCheckedItems(
            key_cols_active_delta
        )

        # -----------------------------
        # DEFAULT HISTORY DELTA KEYS
        # -----------------------------
        if not key_cols_history_delta:
            key_cols_history_delta = [
                "Alarm Number",
                "Supplementary Information",
                "Distinguished Name",
                "Severity",
            ]

        self.hist_new_tab.checkable_combo_delta.setCheckedItems(
            key_cols_history_delta
        )

        self.hist_cleared_tab.checkable_combo_delta.setCheckedItems(
            key_cols_history_delta
        )

        # -----------------------------
        # READ GUI VALUES HERE
        # -----------------------------
        pre_path = self.pre_edit.text().strip()
        post_path = self.post_edit.text().strip()
        history_path = self.hist_edit.text().strip()
        post_history_path = self.post_hist_edit.text().strip()

        # -----------------------------
        # UPDATE RUN BUTTON
        # -----------------------------
        # self.run_btn.setEnabled(False)
        self.start_run_animation()

        # -----------------------------
        # CREATE THREAD
        # -----------------------------
        self.analysis_thread = QThread(self)

        # -----------------------------
        # CREATE WORKER
        # -----------------------------
        self.analysis_worker = AnalysisWorker(
            pre_path=pre_path,
            post_path=post_path,
            history_path=history_path,
            post_history_path=post_history_path,
            key_cols_active_delta=key_cols_active_delta,
            key_cols_history_delta=key_cols_history_delta,
            status_file=self.get_status_file()
        )

        # Move worker into thread
        self.analysis_worker.moveToThread(
            self.analysis_thread
        )

        # -----------------------------
        # CONNECTIONS
        # -----------------------------
        self.analysis_thread.started.connect(
            self.analysis_worker.run
        )

        self.analysis_worker.finished.connect(
            self.analysis_finished
        )

        self.analysis_worker.error.connect(
            self.analysis_error
        )

        # Stop thread after success/error
        self.analysis_worker.finished.connect(
            self.analysis_thread.quit
        )

        self.analysis_worker.error.connect(
            self.analysis_thread.quit
        )

        # Delete worker
        self.analysis_thread.finished.connect(
            self.analysis_worker.deleteLater
        )

        # Final cleanup
        self.analysis_thread.finished.connect(
            self.thread_finished
        )

        # -----------------------------
        # START
        # -----------------------------
        self.analysis_thread.start()

    def analysis_finished(self, result):

        # -----------------------------
        # STORE DATAFRAMES
        # -----------------------------
        self.pre_df = result["pre_df"]
        self.post_df = result["post_df"]
        self.history_df = result["history_df"]
        self.post_history_df = result["post_history_df"]

        new_df = result["new_df"]
        cleared_df = result["cleared_df"]

        hist_new_df = result["hist_new_df"]
        hist_cleared_df = result["hist_cleared_df"]

        # -----------------------------
        # DISPLAY HELPER
        # -----------------------------
        def safe_display(df, columns):
            if df is None or df.empty:
                return pd.DataFrame(
                    columns=columns
                )

            return df[
                [
                    col
                    for col in columns
                    if col in df.columns
                ]
            ].copy()

        # -----------------------------
        # MAIN TABLES
        # -----------------------------
        self.pre_tab.load_dataframe(
            "pre_table",
            safe_display(
                self.pre_df,
                DISPLAY_COLUMNS
            ),
            self.pre_df
        )

        self.post_tab.load_dataframe(
            "post_table",
            safe_display(
                self.post_df,
                DISPLAY_COLUMNS
            ),
            self.post_df
        )

        self.history_tab.load_dataframe(
            "history_table",
            safe_display(
                self.history_df,
                DISPLAY_COLUMNS
            ),
            self.history_df
        )

        self.post_history_tab.load_dataframe(
            "post_history",
            safe_display(
                self.post_history_df,
                DISPLAY_COLUMNS
            ),
            self.post_history_df
        )

        # -----------------------------
        # ACTIVE DELTA
        # -----------------------------
        self.new_tab.load_dataframe(
            "active_delta_new_table",
            safe_display(
                new_df,
                DISPLAY_COLUMNS_NEW
            ),
            new_df,
            "#d4ffd4"
        )

        self.new_tab.apply_saved_status()

        self.cleared_tab.load_dataframe(
            "active_delta_cleared_table",
            safe_display(
                cleared_df,
                DISPLAY_COLUMNS
            ),
            cleared_df,
            "#ffd4d4"
        )

        # -----------------------------
        # HISTORY DELTA
        # -----------------------------
        self.hist_new_tab.load_dataframe(
            "history_delta_new_table",
            safe_display(
                hist_new_df,
                DISPLAY_COLUMNS_NEW
            ),
            hist_new_df,
            "#d4ffd4"
        )

        self.hist_cleared_tab.load_dataframe(
            "history_delta_cleared_table",
            safe_display(
                hist_cleared_df,
                DISPLAY_COLUMNS
            ),
            hist_cleared_df,
            "#ffd4d4"
        )

        # -----------------------------
        # UPDATE UI
        # -----------------------------
        self.update_counts()

        self.switch_to_first_available_tab()

        QMessageBox.information(
            self,
            "Analyzer Summary",
            f"New Alarms: {len(new_df)}\n"
            f"Cleared Alarms: {len(cleared_df)}\n\n"
            f"New History Alarms: {len(hist_new_df)}\n"
            f"Cleared History Alarms: {len(hist_cleared_df)}"
        )

    def analysis_error(self, message):

        QMessageBox.critical(
            self,
            "Analysis Error",
            message
        )

    def thread_finished(self):
        # Stop main Run button animation
        self.stop_run_animation()

        # Stop the Delta button animation
        if self.active_run_tab is not None:
            self.active_run_tab.stop_run_animation()

        self.active_run_tab = None

        self.analysis_worker = None
        self.analysis_thread = None

    def start_run_animation(self):

        self.run_movie = QMovie(
            resource_path(
                "resources/icon/loading.gif"
            )
        )

        self.run_movie.frameChanged.connect(
            self.update_run_button_icon
        )

        self.run_btn.setText("Running...")
        self.run_movie.start()

    def update_run_button_icon(self):

        if self.run_movie is not None:
            self.run_btn.setIcon(
                QIcon(
                    self.run_movie.currentPixmap()
                )
            )

    def stop_run_animation(self):

        if self.run_movie is not None:
            self.run_movie.stop()
            self.run_movie = None

        self.run_btn.setText("Run")

        self.run_btn.setIcon(
            QIcon(
                resource_path(
                    "resources/icon/run.png"
                )
            )
        )

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


class ConfigAnalyzerWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        banner_label = QLabel("Coming Soon ...")
        banner_label.setAlignment(Qt.AlignCenter)
        banner_label.setStyleSheet("""
        font-size:36px;
        font-weight:bold;
        color:grey;
        """)

        layout.addWidget(banner_label)
        self.setLayout(layout)


class CollapsibleFeature(QWidget):
    def __init__(self, title, items, parent=None):
        super().__init__(parent)

        self.title = title
        self.expanded = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Category button
        self.button = QPushButton(f"▶   {self.title}")
        self.button.setObjectName("featureCategoryButton")
        self.button.setCursor(Qt.PointingHandCursor)
        self.button.clicked.connect(self.toggle)

        layout.addWidget(self.button)

        # Collapsible item container
        self.content = QWidget()
        self.content.setObjectName("featureContent")

        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(25, 4, 10, 8)
        content_layout.setSpacing(3)

        for item in items:
            label = QLabel(f"•  {item}")
            label.setObjectName("featureItem")
            label.setWordWrap(True)
            content_layout.addWidget(label)

        self.content.setVisible(False)
        layout.addWidget(self.content)

    def toggle(self):
        self.expanded = not self.expanded
        self.content.setVisible(self.expanded)

        arrow = "▼" if self.expanded else "▶"
        self.button.setText(f"{arrow}   {self.title}")


class HelpWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.features_expanded = False

        self.setStyleSheet("""
            HelpWidget {
                background-color: #f4f6f8;
                font-family: "Segoe UI";
            }

            QFrame#aboutCard {
                background-color: white;
                border: 1px solid #e2e6ea;
                border-radius: 16px;
            }

            QLabel#toolName {
                font-size: 40px;
                font-weight: 700;
                color: #1f2937;
            }

            QLabel#version {
                font-size: 20px;
                color: #6b7280;
            }

            QLabel#developerName {
                font-size: 30px;
                font-weight: 600;
                color: #111827;
            }

            QLabel#title {
                font-size: 20px;
                color: #6b7280;
            }

            QLabel#info {
                font-size: 18px;
                color: #374151;
                padding: 3px;
            }

            QPushButton#featureButton {
                text-align: left;
                background-color: #f3f4f6;
                border: none;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 16px;
                font-weight: 600;
                color: #1f2937;
            }

            QPushButton#featureButton:hover {
                background-color: #e5e7eb;
            }

            QFrame#featureContainer {
                background-color: #f9fafb;
                border-radius: 8px;
            }

            QPushButton#featureCategoryButton {
                text-align: left;
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 7px 8px;
                font-size: 16px;
                font-weight: 600;
                color: #1f2937;
            }

            QPushButton#featureCategoryButton:hover {
                background-color: #e9edf2;
            }

            QWidget#featureContent {
                background-color: transparent;
            }

            QLabel#featureItem {
                background-color: transparent;
                color: #4b5563;
                font-size: 15px;
                padding: 2px 5px;
            }
        """)

        self.build_ui()

    def build_ui(self):
        # ==================== MAIN LAYOUT ====================

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        main_layout.addStretch()

        center_layout = QHBoxLayout()
        center_layout.addStretch()

        # ==================== ABOUT CARD ====================

        self.card = QFrame()
        self.card.setObjectName("aboutCard")
        self.card.setMinimumWidth(450)
        self.card.setMaximumWidth(650)
        self.card.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Maximum
        )

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(35, 30, 35, 30)
        card_layout.setSpacing(10)

        # ==================== TOOL INFORMATION ====================

        tool_name = QLabel("PostCheck Analyzer")
        tool_name.setObjectName("toolName")
        tool_name.setAlignment(Qt.AlignCenter)

        version = QLabel("Version 1.7.13")
        version.setObjectName("version")
        version.setAlignment(Qt.AlignCenter)

        card_layout.addWidget(tool_name)
        card_layout.addWidget(version)
        card_layout.addSpacing(15)

        # ==================== DEVELOPER INFORMATION ====================

        developer_name = QLabel("Tapon Paul")
        developer_name.setObjectName("developerName")
        developer_name.setAlignment(Qt.AlignCenter)

        title = QLabel("RAN Specialist Engineer")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)

        card_layout.addWidget(developer_name)
        card_layout.addWidget(title)
        card_layout.addSpacing(15)

        # ==================== CONTACT INFORMATION ====================

        email = QLabel("✉  tapon.paul@nokia.com")
        email.setObjectName("info")
        email.setAlignment(Qt.AlignCenter)

        phone = QLabel("☎  +880 1919045275")
        phone.setObjectName("info")
        phone.setAlignment(Qt.AlignCenter)

        card_layout.addWidget(email)
        card_layout.addWidget(phone)
        card_layout.addSpacing(15)

        # ==================== MAIN FEATURES BUTTON ====================

        self.feature_button = QPushButton("▶   List of New Features")
        self.feature_button.setObjectName("featureButton")
        self.feature_button.setCursor(Qt.PointingHandCursor)
        self.feature_button.clicked.connect(self.toggle_features)

        card_layout.addWidget(self.feature_button)

        # ==================== FEATURES CONTAINER ====================

        self.feature_container = QFrame()
        self.feature_container.setObjectName("featureContainer")

        feature_layout = QVBoxLayout(self.feature_container)
        feature_layout.setContentsMargins(10, 10, 10, 10)
        feature_layout.setSpacing(4)

        features = {
            "Advanced Global Filter": [
                "Using a single text pattern",
                "Using multiple text patterns",
            ],

            "Advanced Column Filter": [
                "Using a single text pattern",
                "Using multiple text patterns",
            ],

            "Inverse Filtering": [
                "Using a single text pattern",
                "Using multiple text patterns",
            ],

            "User-Defined Delta Calculation": [
                "Default delta calculation",
                "User-defined delta calculation",
            ],

            "UI Improvements": [
                "Background processing",
            ],
        }

        # Create independently collapsible categories
        for category, items in features.items():
            feature_widget = CollapsibleFeature(
                category,
                items,
                self.feature_container
            )
            feature_layout.addWidget(feature_widget)

        self.feature_container.setVisible(False)

        card_layout.addWidget(self.feature_container)

        # ==================== CENTER CARD ====================

        center_layout.addWidget(self.card)
        center_layout.addStretch()

        main_layout.addLayout(center_layout)
        main_layout.addStretch()

    def toggle_features(self):
        self.features_expanded = not self.features_expanded

        self.feature_container.setVisible(
            self.features_expanded
        )

        arrow = "▼" if self.features_expanded else "▶"
        self.feature_button.setText(f"{arrow}   List of New Features")
