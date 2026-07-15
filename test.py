from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QSizePolicy,
)
import sys

from global_functions.helper_functions import resource_path

class FeatureCard(QFrame):
    clicked = pyqtSignal()

    def __init__(
        self,
        icon,
        title,
        description,
        bullet_points=None,
        parent=None
    ):
        super().__init__(parent)

        self.setObjectName("FeatureCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(300, 300)

        self.normal_shadow = QGraphicsDropShadowEffect(self)
        self.normal_shadow.setBlurRadius(18)
        self.normal_shadow.setOffset(0, 4)
        self.normal_shadow.setColor(Qt.gray)
        self.setGraphicsEffect(self.normal_shadow)

        # -------------------------
        # Main layout
        # -------------------------
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Icon
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setPixmap(
            QIcon(icon).pixmap(QSize(56, 56))
        )

        # Title
        self.title_label = QLabel(title)
        self.title_label.setObjectName("CardTitle")
        self.title_label.setAlignment(Qt.AlignCenter)

        # Description
        self.description_label = QLabel(description)
        self.description_label.setObjectName("CardDescription")
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)

        # Bullet points
        if bullet_points:
            bullet_container = QWidget()
            bullet_layout = QVBoxLayout(bullet_container)
            bullet_layout.setContentsMargins(10, 8, 10, 0)
            bullet_layout.setSpacing(6)

            for text in bullet_points:
                bullet = QLabel(f"•  {text}")
                bullet.setObjectName("BulletText")
                bullet.setWordWrap(True)
                bullet_layout.addWidget(bullet)

            layout.addWidget(bullet_container)

        layout.addStretch()

        self.setStyleSheet("""
            QFrame#FeatureCard {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
            }

            QLabel#CardTitle {
                color: #1e293b;
                font-size: 18px;
                font-weight: 600;
            }

            QLabel#CardDescription {
                color: #64748b;
                font-size: 13px;
            }

            QLabel#BulletText {
                color: #475569;
                font-size: 13px;
            }
        """)

    def enterEvent(self, event):
        self.normal_shadow.setBlurRadius(35)
        self.normal_shadow.setOffset(0, 6)
        self.normal_shadow.setColor(Qt.cyan)

        self.setStyleSheet("""
            QFrame#FeatureCard {
                background-color: white;
                border: 2px solid #38bdf8;
                border-radius: 16px;
            }

            QLabel#CardTitle {
                color: #0284c7;
                font-size: 18px;
                font-weight: 600;
            }

            QLabel#CardDescription {
                color: #64748b;
                font-size: 13px;
            }

            QLabel#BulletText {
                color: #475569;
                font-size: 13px;
            }
        """)

        super().enterEvent(event)

    def leaveEvent(self, event):
        self.normal_shadow.setBlurRadius(18)
        self.normal_shadow.setOffset(0, 4)
        self.normal_shadow.setColor(Qt.gray)

        self.setStyleSheet("""
            QFrame#FeatureCard {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
            }

            QLabel#CardTitle {
                color: #1e293b;
                font-size: 18px;
                font-weight: 600;
            }

            QLabel#CardDescription {
                color: #64748b;
                font-size: 13px;
            }

            QLabel#BulletText {
                color: #475569;
                font-size: 13px;
            }
        """)

        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

        super().mousePressEvent(event)


class CardDashboard(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Feature Dashboard")
        self.resize(1100, 700)

        self.cards = []

        # Main layout centers everything
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)

        main_layout.addStretch()

        # Horizontal centering
        center_layout = QHBoxLayout()
        center_layout.addStretch()

        self.card_grid = QGridLayout()
        self.card_grid.setHorizontalSpacing(24)
        self.card_grid.setVerticalSpacing(24)

        center_layout.addLayout(self.card_grid)
        center_layout.addStretch()

        main_layout.addLayout(center_layout)
        main_layout.addStretch()

        # Add cards
        self.add_card(
            resource_path("resources/icon/AlarmAnalyzerWidgetIcon.ico"),
            "Alarm Analyzer",
            "Analyze and compare network alarm files.",
            [
                "Compare pre and post alarms",
                "Identify new and cleared alarms",
                "Advanced filtering"
            ],
            self.open_alarm_analyzer
        )

        self.add_card(
            resource_path("resources/icon/"),
            "Configuration Analyzer",
            "Analyze network configuration changes.",
            [
                "Compare configuration files",
                "Detect parameter changes",
                "Export analysis results"
            ],
            self.open_config_analyzer
        )

        self.add_card(
            "icons/report.png",
            "Report Generator",
            "Create detailed analysis reports.",
            [
                "Generate Excel reports",
                "Export filtered results",
                "Create summaries"
            ],
            self.open_reports
        )

        self.setStyleSheet("""
            CardDashboard {
                background-color: #f4f7fb;
            }
        """)

    def add_card(
        self,
        icon,
        title,
        description,
        bullet_points,
        callback
    ):
        card = FeatureCard(
            icon=icon,
            title=title,
            description=description,
            bullet_points=bullet_points
        )

        card.clicked.connect(callback)

        index = len(self.cards)

        # 3 cards per row
        row = index // 3
        column = index % 3

        self.card_grid.addWidget(card, row, column)
        self.cards.append(card)

    def open_alarm_analyzer(self):
        print("Opening Alarm Analyzer")

    def open_config_analyzer(self):
        print("Opening Configuration Analyzer")

    def open_reports(self):
        print("Opening Report Generator")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = CardDashboard()
    window.show()

    sys.exit(app.exec_())