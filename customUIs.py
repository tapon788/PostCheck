import os
import pandas as pd
from PyQt5.QtCore import Qt, QDateTime
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
    QDialog

)
from AlarmComparison.delta import calculate_pre_post_delta, calculate_history_delta
from AlarmComparison.customwidgets import (
    MangoButton,
    MangoBanner,
    MangoDateTimeEdit

)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from AlarmComparison.customwidgets import MangoLineEdit, MangoGroupBox, MangoCheckableComboBox
from AlarmComparison.helper_functions import resource_path, DISPLAY_COLUMNS, DISPLAY_COLUMNS_NEW
from datagrid import AlarmTable


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
        #self.setCentralWidget(self.tabs)
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

        self.load_analyzer_ui()
        # -----------------------------
        # DRAG DROP
        # -----------------------------
        self.setAcceptDrops(True)

    def load_analyzer_ui(self):

        print("LOAD_ANALYZER_UI CALLED")


        # if self.ui_loaded:
        #self.show_input_tab()
        #return

        # -----------------------------
        # FILE INPUT TAB
        # -----------------------------
        self.create_input_tab()

        # -----------------------------
        # MAIN TABLES
        # -----------------------------
        self.pre_tab = AlarmTable(filename=self.session, context="pre")
        self.post_tab = AlarmTable(filename=self.session, context = "post")
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

        #self.new_tab.btn_run_delta.clicked.connect(lambda: self.new_tab.run_delta_analysis(self.pre_df, self.post_df, self.history_df))

        #self.new_tab.btn_run_delta.clicked.connect(self.run_analysis)


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
        #self.ui_loaded = True

        print("TAB COUNT:", self.tabs.count())  # <-- HERE

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
        if not os.path.isdir(path):
            return

        self.scan_alarm_folder(path)

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

        self.alarm_time_from_edit = MangoDateTimeEdit()
        self.alarm_time_to_edit = MangoDateTimeEdit()

        self.alarm_time_from_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.alarm_time_to_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")

        self.alarm_time_from_edit.setDateTime(QDateTime.currentDateTime())
        self.alarm_time_to_edit.setDateTime(QDateTime.currentDateTime())

        run_btn = MangoButton("","Filter Data",resource_path("resources/icon/filter.ico"))
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


        # -----------------------------
        # SAFETY CHECKS
        # -----------------------------
        # if not self.ui_loaded:
        # QMessageBox.warning(
        #     self,
        #     "Warning",
        #     "Please select Analyzer → Browse Input Files first."
        # )
        #return

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
        # if not self.ui_loaded:
        #     QMessageBox.warning(
        #         self,
        #         "Warning",
        #         "Please select Analyzer → Browse Input Files first."
        #     )
        #     return
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
        form_widget.setFixedWidth(750)
        form_widget.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed
        )
        layout = QVBoxLayout(form_widget)
        layout.setSpacing(12)

        # ---------------- TITLE ----------------
        label = QLabel("Alarm Analyzer Inputs")
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
        post_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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
        run_btn = MangoButton("Run","CLick to Run", resource_path("resources/icon/run.png"))
        # run_btn.setFixedHeight(40)
        # run_btn.setMaximumWidth(100)
        run_btn.clicked.connect(self.run_analysis)

        layout.addWidget(run_btn, alignment=Qt.AlignHCenter)

        #page.setLayout(layout)
        #page.setMaximumWidth(600)

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
        key_cols_active_delta = self.new_tab.checkable_combo_delta.checkedItems()
        key_cols_history_delta = self.hist_new_tab.checkable_combo_delta.checkedItems()
        if not key_cols_active_delta:
            key_cols_active_delta = [
                "Alarm Number",
                "Supplementary Information",
                "Distinguished Name",
                "Severity",
            ]
        self.new_tab.checkable_combo_delta.setCheckedItems(key_cols_active_delta)
        self.cleared_tab.checkable_combo_delta.setCheckedItems(key_cols_active_delta)

        if not key_cols_history_delta:
            key_cols_history_delta = [
                "Alarm Number",
                "Supplementary Information",
                "Distinguished Name",
                "Severity",
            ]
        self.hist_new_tab.checkable_combo_delta.setCheckedItems(key_cols_history_delta)
        self.hist_cleared_tab.checkable_combo_delta.setCheckedItems(key_cols_history_delta)
        # if not self.ui_loaded:
        #     QMessageBox.warning(
        #         self,
        #         "Warning",
        #         "Please select Analyzer → Browse Input Files first."
        #     )
        #     return
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
                self.history_df,  # IMPORTANT
                key_cols_active_delta
            )

            # ----------------------------
            # 4. HISTORY DELTA (INDEPENDENT)
            # ----------------------------
            hist_new_df, hist_cleared_df = calculate_history_delta(
                self.history_df,
                self.post_history_df,
                key_cols_history_delta
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


class ConfigAnalyzerWidget(QWidget):
    def __init__(self):
        super().__init__()