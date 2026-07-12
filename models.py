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
                    return QIcon(resource_path("resources/icon/resolved.png"))


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

        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

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
        self.column_filters = {}

    def setSearch(self, text):
        self.search_text = text.strip().lower()
        self.invalidateFilter()

    def setColumnFilter(self, column, text):
        text = text.strip().lower()

        if text:
            self.column_filters[column] = text
        else:
            self.column_filters.pop(column, None)

        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()

        if model is None:
            return True

        if self.search_text:

            # Combine all column values for this row
            row_values = []

            for column in range(model.columnCount()):
                index = model.index(
                    source_row,
                    column,
                    source_parent
                )

                value = str(
                    model.data(index, Qt.DisplayRole) or ""
                ).lower()

                row_values.append(value)

            # Treat the whole row as searchable text
            row_text = " ".join(row_values)

            # Split: abc | def | !xyz
            terms = [
                term.strip()
                for term in self.search_text.split("|")
                if term.strip()
            ]

            positive_terms = [
                term
                for term in terms
                if not term.startswith("!")
            ]

            negative_terms = [
                term[1:].strip()
                for term in terms
                if term.startswith("!") and len(term) > 1
            ]

            # Reject if ANY excluded term exists anywhere in the row
            if any(
                    term in row_text
                    for term in negative_terms
            ):
                return False

            # If positive terms exist, at least ONE must exist
            if positive_terms and not any(
                    term in row_text
                    for term in positive_terms
            ):
                return False


        # --------------------------------
        # Per-column filters
        # --------------------------------

    # Per-column filters
        for column, filter_text in self.column_filters.items():

            index = model.index(
                source_row,
                column,
                source_parent
            )

            value = str(
                model.data(index, Qt.DisplayRole) or ""
            ).lower()

            # Split by | and remove surrounding spaces
            terms = [
                term.strip()
                for term in filter_text.split("|")
                if term.strip()
            ]

            positive_terms = [
                term
                for term in terms
                if not term.startswith("!")
            ]

            negative_terms = [
                term[1:].strip()
                for term in terms
                if term.startswith("!") and len(term) > 1
            ]

            # Exclude if ANY negative term matches
            if any(term in value for term in negative_terms):
                return False

            # If positive terms exist, at least ONE must match
            if positive_terms and not any(
                    term in value for term in positive_terms
            ):
                return False

        return True


    def sort(self, column, order):
        super().sort(column, order)