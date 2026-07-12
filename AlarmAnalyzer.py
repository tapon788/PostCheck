# ======================== Imports ========================
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QStackedWidget,
    QMessageBox,
)

from AlarmComparison.customwidgets import (
    MangoMainWindow,
)

from AlarmComparison.customUIs import CSVMergerDialog
from AlarmComparison.helper_functions import resource_path
from customUIs import AlarmAnalyzerWidget, ConfigAnalyzerWidget

class MainWindow(MangoMainWindow):

    def __init__(self):
        super().__init__()

        self.container = QStackedWidget()
        self.setCentralWidget(self.container)
        self.alarm_analyzer = None
        self.config_analyzer = None

        self.create_menu()

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

    def show_alarm_analyzer(self):
        if self.alarm_analyzer is None:
            self.alarm_analyzer = AlarmAnalyzerWidget(self.statusBar())
            self.container.addWidget(self.alarm_analyzer)
            print("CREATED:", id(self.alarm_analyzer))

        print("SHOWING:", id(self.alarm_analyzer))
        self.container.setCurrentWidget(self.alarm_analyzer)
        self.alarm_analyzer.show_input_tab()


    def show_config_analyzer(self):
        if self.config_analyzer is None:
            self.config_analyzer = ConfigAnalyzerWidget()
            self.container.addWidget(self.config_analyzer)
        self.container.setCurrentWidget(self.config_analyzer)

    def create_menu(self):

        menubar = self.menuBar()

        # -------------------------
        # ANALYZER MENU
        # -------------------------
        analyzer_menu = menubar.addMenu("&Alarm Analyzer")
        config_menu = menubar.addMenu("&Configuration Analyzer")

        browse_action = analyzer_menu.addAction(
            "Browse Input Files"
        )

        browse_action.setIcon(
            QIcon(resource_path("resources/icon/search.png"))
        )

        browse_action.triggered.connect(
            self.show_alarm_analyzer
        )


        browse_action = config_menu.addAction(
            "Browse Input Files"
        )

        browse_action.setIcon(
            QIcon(resource_path("resources/icon/browse.png"))
        )

        browse_action.triggered.connect(
            self.show_config_analyzer
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
            QIcon(resource_path("resources/icon/EXIT.png"))
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


    def load_csv_merger_ui(self):

        dlg = CSVMergerDialog()

        dlg.exec_()


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