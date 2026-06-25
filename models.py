from PyQt5.QtCore import (
    Qt,
    QAbstractTableModel,
    QSortFilterProxyModel
)

from PyQt5.QtGui import QColor, QIcon

import pandas as pd

from AlarmComparison.helper_functions import resource_path

class PandasModel(QAbstractTableModel):

    DATE_COLUMNS = {
        "Alarm Time",
        "Cancel Time",
        "Alarm Insertion Time",
        "Alarm Update Time",
        "Origin Alarm Time",
        "Origin Cancel Time",
    }

    def __init__(self, df, color=None, table_name=None):
        super().__init__()
        self.table_name = table_name
        self.df = df.copy()   # ✅ FIX: use same attribute everywhere
        self.row_color = color

    def rowCount(self, parent=None):
        return len(self.df)

    def columnCount(self, parent=None):
        return len(self.df.columns)

    def data(self, index, role):

        if not index.isValid():
            return None

        column_name = self.df.columns[index.column()]

        # -----------------------------
        # RESOLVED ICON
        # -----------------------------
        if role == Qt.DecorationRole:

            if column_name == "Resolved":

                status = str(
                    self.df.iloc[index.row()]["Resolved"]
                ).strip().lower()
                history_match = self.get_history_match_flag(index.row())

                if status == "true":
                    return QIcon(resource_path("resources/icon/resolved2.png"))


                elif status in ("false", ""):
                    if history_match == "not found":
                        return QIcon(resource_path("resources/icon/NotResolved.png"))
                    if self.table_name == "history_delta_new_table":
                        return QIcon(resource_path("resources/icon/NotResolved.png"))
        # -----------------------------
        # DISPLAY TEXT
        # -----------------------------
        if role == Qt.DisplayRole:

            if column_name == "Resolved":
                return ""

            value = self.df.iloc[index.row(), index.column()]
            if value == 'nan':
                return ""
            return str(value)

        # -----------------------------
        # BACKGROUND
        # -----------------------------
        if role == Qt.BackgroundRole:

            if column_name == "Severity":
                severity = self.get_severity(index.row())

                color_map = {
                    "critical": QColor("#ff4d4d"),
                    "major": QColor("#ffa500"),
                    "minor": QColor("#fff176"),
                    "warning": QColor("#add8e6"),
                }

                return color_map.get(severity)

            if column_name == "History Match":
                history_match = self.get_history_match_flag(index.row())

                color_map = {
                    "exists": QColor("#bdffbd"),
                    "not found": QColor("#eecdcd"),
                }

                return color_map.get(history_match)

        return None

    def get_severity(self, row):

        try:
            return str(self.df.iloc[row]["Severity"]).strip().lower()
        except:
            return ""

    def get_history_match_flag(self, row):
        try:
            return str(self.df.iloc[row]["History Match"]).strip().lower()
        except:
            return ""

    def headerData(self, section, orientation, role):

        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return self.df.columns[section]

        return section + 1

    def sort(self, column, order):

        # -------------------------
        # SAFETY CHECK (IMPORTANT)
        # -------------------------
        if self.df is None or self.df.empty or len(self.df.columns) == 0:
            return

        if column < 0 or column >= len(self.df.columns):
            return

        col_name = self.df.columns[column]

        self.layoutAboutToBeChanged.emit()

        ascending = (order == Qt.AscendingOrder)

        df = self.df.copy()

        # -------------------------
        # DATE COLUMNS
        # -------------------------
        if col_name in self.DATE_COLUMNS:

            df[col_name] = pd.to_datetime(
                df[col_name],
                errors="coerce"
            )

            df = df.sort_values(
                by=col_name,
                ascending=ascending,
                na_position="last"
            )

        else:

            try:
                df[col_name] = pd.to_numeric(df[col_name], errors="raise")
            except:
                pass

            df = df.sort_values(
                by=col_name,
                ascending=ascending,
                na_position="last"
            )

        self.df = df.reset_index(drop=True)


        self.layoutChanged.emit()


class GlobalFilterProxy(QSortFilterProxyModel):

    def __init__(self):
        super().__init__()
        self.search_text = ""

    def setSearch(self, text):
        self.search_text = text.strip().lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, row, parent):

        if not self.search_text:
            return True

        model = self.sourceModel()
        if not model:
            return False

        column_count = model.columnCount(parent)

        for col in range(column_count):

            idx = model.index(row, col, parent)
            value = model.data(idx, Qt.DisplayRole)

            if value is None:
                continue

            # convert ONCE
            value_str = str(value).lower()

            if self.search_text in value_str:
                return True

        return False
    #
    # def sort(self, column, order):
    #     source = self.sourceModel()
    #     if source:
    #         source.sort(column, order)

    def sort(self, column, order):
        super().sort(column, order)