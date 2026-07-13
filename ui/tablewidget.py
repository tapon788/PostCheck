# ======================== Imports ========================


import os
import pandas as pd

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableView,
    QMessageBox,
    QMenu,
    QHeaderView,
    QLabel

)
from PyQt5.QtGui import (
    QIcon,
    QMovie,
)
from ui.customwidgets import (
    MangoButton,
    MangoLineEdit,
    MangoCheckableComboBox,
)

from global_functions.helper_functions import resource_path

from models.models import (
    PandasModel,
    GlobalFilterProxy,
)
from ui.dialogs import DetailDialog

from ui.dialogs import StatusDialog


class AlarmTable(QWidget):
    filterChanged = pyqtSignal()
    runRequested = pyqtSignal()

    def __init__(self, filename=None, context=None):
        super().__init__()
        self.run_movie = None
        self.enable_status_tracking = False
        self.df = pd.DataFrame()
        self.filename = filename

        self.search = MangoLineEdit()
        self.search.setPlaceholderText("Global Filter ...")
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(500)
        self.search_timer.timeout.connect(self.apply_search)

        self.export_btn = MangoButton("","Export Data", resource_path("resources/icon/export.png"))
        self.export_btn.clicked.connect(self.export_csv)

        self.table = QTableView()
        self.table.setSortingEnabled(True)

        layout = QVBoxLayout()
        if context == "delta":
            self.checkable_combo_delta = MangoCheckableComboBox()
            self.checkable_combo_delta.addItems([
                "Alarm Number",
                "Supplementary Information",
                "Distinguished Name",
                "Diagnostic Info",
                "Severity",
            ])
            self.btn_run_delta = MangoButton("", "Re-calculate Delta", resource_path("resources/icon/play.ico"))
            self.btn_run_delta.clicked.connect(lambda: self.runRequested.emit())
            top_select_delta = QHBoxLayout()
            top_select_delta.addWidget(QLabel("Delta Comparison Combination"))
            top_select_delta.addWidget(self.checkable_combo_delta)

            top_select_delta.addWidget(self.btn_run_delta)
            top_select_delta.setStretch(0, 0)
            top_select_delta.setStretch(1, 1)
            top_select_delta.setStretch(2, 0)

            layout.addLayout(top_select_delta)

        top = QHBoxLayout()

        top.addWidget(self.search)
        top.addWidget(self.export_btn)

        layout.addLayout(top)

        self.column_filter_widget = QWidget()
        self.column_filter_widget.setFixedHeight(35)

        layout.addWidget(self.column_filter_widget)
        layout.addWidget(self.table)

        self.column_filter_edits = []

        self.setLayout(layout)
        self.proxy = GlobalFilterProxy()
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
            font-size: 16px;
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

        header = self.table.horizontalHeader()

        header.sectionResized.connect(
            self.update_filter_positions
        )

        header.sectionMoved.connect(
            self.update_filter_positions
        )

        self.table.horizontalScrollBar().valueChanged.connect(
            self.update_filter_positions
        )

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
        self.resize_cols("Severity", 100)
        self.resize_cols("Alarm Number", 100)
        self.resize_cols("Supplementary Information", 250)
        self.resize_cols("Distinguished Name", 300)
        self.resize_cols("Diagnostic Info", 350)
        self.resize_cols("Name", 300)
        self.resize_cols("Status", 400)
        #self.resize_cols("Resolved", 30)

        self.create_column_filters()

    def create_column_filters(self):

        for edit in self.column_filter_edits:
            edit.deleteLater()

        self.column_filter_edits.clear()

        model = self.proxy.sourceModel()

        if model is None:
            return

        for column in range(model.columnCount()):
            edit = MangoLineEdit(
                self.column_filter_widget
            )
            edit.setClearButtonEnabled(True)
            edit.textChanged.connect(
                lambda text, col=column:
                self.on_column_filter_changed(col, text)
            )

            edit.show()

            self.column_filter_edits.append(edit)

        self.update_filter_positions()

    def on_column_filter_changed(self, column, text):
        self.proxy.setColumnFilter(column, text)
        self.filterChanged.emit()
    def update_filter_positions(self, *args):

        header = self.table.horizontalHeader()

        for logical_index, edit in enumerate(
                self.column_filter_edits
        ):
            x = header.sectionViewportPosition(
                logical_index
            )

            width = header.sectionSize(
                logical_index
            )

            edit.setGeometry(
                x,
                0,
                width,
                self.column_filter_widget.height()
            )



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


    def run_delta_analysis(self,pre_df, post_df, history_df):
        pass


    def start_run_animation(self):
        if not hasattr(self, "btn_run_delta"):
            return

        self.run_movie = QMovie(
            resource_path("resources/icon/loading.gif")
        )

        if not self.run_movie.isValid():
            print("Invalid loading GIF")
            return

        self.run_movie.frameChanged.connect(
            self.update_run_button_icon
        )

        self.run_movie.start()


    def update_run_button_icon(self, frame_number):
        if self.run_movie is None:
            return

        pixmap = self.run_movie.currentPixmap()

        if not pixmap.isNull():
            self.btn_run_delta.setIcon(
                QIcon(pixmap)
            )


    def stop_run_animation(self):
        if not hasattr(self, "btn_run_delta"):
            return

        if self.run_movie is not None:
            self.run_movie.stop()
            self.run_movie = None

        self.btn_run_delta.setIcon(
            QIcon(
                resource_path(
                    "resources/icon/play.ico"
                )
            )
        )

    def create_column_filters(self):

        for edit in self.column_filter_edits:
            edit.deleteLater()

        self.column_filter_edits.clear()

        model = self.proxy.sourceModel()

        if model is None:
            return

        for column in range(model.columnCount()):

            edit = MangoLineEdit(
                self.column_filter_widget
            )

            edit.setClearButtonEnabled(True)

            # Placeholder-style filter icon
            filter_action = edit.addAction(
                QIcon(
                    resource_path(
                        "resources/icon/filter.png"
                    )
                ),
                MangoLineEdit.LeadingPosition
            )

            # Keep reference to the action
            edit.filter_action = filter_action

            edit.textChanged.connect(
                lambda text, col=column:
                    self.on_column_filter_changed(
                        col,
                        text
                    )
            )

            # Show icon only when text is empty
            edit.textChanged.connect(
                lambda text, action=filter_action:
                    action.setVisible(not bool(text))
            )

            edit.show()

            self.column_filter_edits.append(edit)

        self.update_filter_positions()