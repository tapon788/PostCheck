# ======================== Imports ========================

from PyQt5.QtCore import (
    Qt,
    QAbstractTableModel,
    QSortFilterProxyModel
)

from PyQt5.QtGui import (
    QColor,
    QIcon,
)

import pandas as pd
import numbers

from global_functions.helper_functions import resource_path

from global_functions.helper_functions import DATE_COLUMNS
class PandasModel(QAbstractTableModel):



    def __init__(self, df, color=None, table_name=None):
        super().__init__()
        self.table_name = table_name
        self.df = df.copy()   # ✅ FIX: use same attribute everywhere
        # -----------------------------------
        # Build search cache only when needed
        # -----------------------------------
        if not self.df.empty:
            self.build_search_cache()
        else:
            self.search_cache = None

        self.row_color = color

    def build_search_cache(self):
        self.search_cache = (
            self.df.fillna("")
            .astype(str)
            .agg(" ".join, axis=1)
            .str.lower()
        )
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

            if column_name == "Alarm Time":
                return str(value)

            if column_name == "Cancel Time":
                return str(value)

            if pd.isna(value):
                return ""

            # Convert NumPy scalar to native Python type
            if hasattr(value, "item"):
                value = value.item()

            return value

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
        print("PandasModel.sort() called")
        print("Column:", column)
        print("Order:", order)
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
        if col_name in DATE_COLUMNS:

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

        self.build_search_cache()

        self.layoutChanged.emit()



# import numbers
# import pandas as pd
# from PyQt5.QtCore import Qt, QSortFilterProxyModel


class GlobalFilterProxy(QSortFilterProxyModel):

    def __init__(self):
        super().__init__()

        self.search_text = ""

        self.search_positive = []
        self.search_negative = []

        # column -> {"positive":[...], "negative":[...]}
        self.column_filters = {}

    # ----------------------------------------------------
    # GLOBAL SEARCH
    # ----------------------------------------------------

    def setSearch(self, text):

        self.search_text = text.strip().lower()

        terms = [
            t.strip()
            for t in self.search_text.split("|")
            if t.strip()
        ]

        self.search_positive = [
            t for t in terms
            if not t.startswith("!")
        ]

        self.search_negative = [
            t[1:]
            for t in terms
            if t.startswith("!") and len(t) > 1
        ]

        self.invalidateFilter()

    # ----------------------------------------------------
    # COLUMN FILTER
    # ----------------------------------------------------

    def setColumnFilter(self, column, text):

        text = text.strip().lower()

        if not text:
            self.column_filters.pop(column, None)
            self.invalidateFilter()
            return

        terms = [
            t.strip()
            for t in text.split("|")
            if t.strip()
        ]

        self.column_filters[column] = {
            "positive": [
                t for t in terms
                if not t.startswith("!")
            ],
            "negative": [
                t[1:]
                for t in terms
                if t.startswith("!") and len(t) > 1
            ]
        }

        self.invalidateFilter()

    # ----------------------------------------------------
    # FILTERING
    # ----------------------------------------------------

    def filterAcceptsRow(self, source_row, source_parent):

        model = self.sourceModel()

        if model is None:
            return True

        df = model.df

        # ============================================
        # GLOBAL SEARCH
        # ============================================

        if self.search_text:

            row_text = " ".join(
                str(df.iat[source_row, c]).lower()
                for c in range(df.shape[1])
            )

            if any(
                term in row_text
                for term in self.search_negative
            ):
                return False

            if (
                self.search_positive
                and not any(
                    term in row_text
                    for term in self.search_positive
                )
            ):
                return False

        # ============================================
        # COLUMN FILTERS
        # ============================================

        for column, filters in self.column_filters.items():

            value = str(
                df.iat[source_row, column]
            ).lower()

            if any(
                term in value
                for term in filters["negative"]
            ):
                return False

            if (
                filters["positive"]
                and not any(
                    term in value
                    for term in filters["positive"]
                )
            ):
                return False

        return True

    # ----------------------------------------------------
    # SORTING
    # ----------------------------------------------------

    def sort(self, column, order):
        super().sort(column, order)

    # ----------------------------------------------------
    # SMART SORT
    # ----------------------------------------------------

    def lessThan(self, left, right):

        left_data = self.sourceModel().data(
            left,
            Qt.DisplayRole
        )

        right_data = self.sourceModel().data(
            right,
            Qt.DisplayRole
        )

        if left_data in ("", None):
            return False

        if right_data in ("", None):
            return True

        # Numeric
        if (
            isinstance(left_data, numbers.Number)
            and
            isinstance(right_data, numbers.Number)
        ):
            return left_data < right_data

        # Date
        try:
            left_dt = pd.to_datetime(
                left_data,
                errors="raise"
            )

            right_dt = pd.to_datetime(
                right_data,
                errors="raise"
            )

            return left_dt < right_dt

        except Exception:
            pass

        # Text
        return (
            str(left_data).lower()
            <
            str(right_data).lower()
        )