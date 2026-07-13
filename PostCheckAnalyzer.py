# ======================== Imports ========================

"""
Version: 1.7.13
Last Updated: 14/07/2026
Author: Tapon Paul
Git Branch: V2
Git Commit: V2 full and final
"""

import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QStackedWidget,
)

from ui.customwidgets import (
    MangoMainWindow,
)

from global_functions.helper_functions import resource_path
from ui.alarm_ui import AlarmAnalyzerWidget
from ui.help_ui import HelpWidget
from ui.config_ui import ConfigAnalyzerWidget
from ui.customUIs import (
    CSVMergerDialog,
)


class MainWindow(MangoMainWindow):
    def __init__(self):
        super().__init__()
        self.container = QStackedWidget()
        self.setCentralWidget(self.container)
        self.alarm_analyzer = None
        self.config_analyzer = None
        self.help_analyzer = None
        self.create_menu()

    def show_alarm_analyzer(self):
        if self.alarm_analyzer is None:
            self.alarm_analyzer = AlarmAnalyzerWidget(self.statusBar())
            self.container.addWidget(self.alarm_analyzer)
        self.container.setCurrentWidget(self.alarm_analyzer)
        self.alarm_analyzer.show_input_tab()

    def show_config_analyzer(self):
        if self.config_analyzer is None:
            self.config_analyzer = ConfigAnalyzerWidget()
            self.container.addWidget(self.config_analyzer)
        self.container.setCurrentWidget(self.config_analyzer)

    def show_help(self):
        if self.help_analyzer is None:
            self.help_analyzer = HelpWidget()
            self.container.addWidget(self.help_analyzer)
        self.container.setCurrentWidget(self.help_analyzer)

    def create_menu(self):
        menubar = self.menuBar()
        # -------------------------
        # ALARM MENU
        # -------------------------
        analyzer_menu = menubar.addMenu("&Alarm")
        config_menu = menubar.addMenu("&Configuration")
        browse_action = analyzer_menu.addAction(
            "A&larm analyzer"
        )

        browse_action.setIcon(
            QIcon(resource_path("resources/icon/search.png"))
        )

        browse_action.triggered.connect(
            self.show_alarm_analyzer
        )
        mergefile_action = analyzer_menu.addAction(
            "&Merge alarms"
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
            QIcon(resource_path("resources/icon/EXIT.png"))
        )
        exit_action.triggered.connect(
            self.close
        )
        # -------------------------
        # CONFIG MENU
        # -------------------------
        browse_action = config_menu.addAction(
            "Browse Input Files"
        )
        browse_action.setIcon(
            QIcon(resource_path("resources/icon/search.png"))
        )
        browse_action.triggered.connect(
            self.show_config_analyzer
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
            self.show_help
        )

    def load_csv_merger_ui(self):
        dlg = CSVMergerDialog()
        dlg.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("resources/icon/PostCheckAnalyzer.ico")))
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