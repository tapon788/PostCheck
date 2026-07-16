from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QGraphicsDropShadowEffect,
)

from global_functions.helper_functions import resource_path

from ui.alarm_ui import AlarmAnalyzerWidget
from ui.config_ui import ConfigAnalyzerWidget
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

        # Shadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(18)
        self.shadow.setOffset(0, 4)
        self.shadow.setColor(QColor(0, 0, 0, 45))
        self.setGraphicsEffect(self.shadow)

        # Main card layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Icon
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedHeight(65)

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
        self.description_label.setAlignment(Qt.AlignCenter)
        self.description_label.setWordWrap(True)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)

        # Bullet points
        if bullet_points:
            bullet_layout = QVBoxLayout()
            bullet_layout.setContentsMargins(12, 8, 12, 0)
            bullet_layout.setSpacing(7)

            for text in bullet_points:
                bullet = QLabel(f"•  {text}")
                bullet.setObjectName("BulletText")
                bullet.setWordWrap(True)
                bullet_layout.addWidget(bullet)

            layout.addLayout(bullet_layout)

        layout.addStretch()

        self.apply_normal_style()

    def apply_normal_style(self):
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

    def apply_hover_style(self):
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

    def enterEvent(self, event):
        self.shadow.setBlurRadius(35)
        self.shadow.setOffset(0, 6)
        self.shadow.setColor(QColor("#38bdf8"))

        self.apply_hover_style()

        super().enterEvent(event)

    def leaveEvent(self, event):
        self.shadow.setBlurRadius(18)
        self.shadow.setOffset(0, 4)
        self.shadow.setColor(QColor(0, 0, 0, 45))

        self.apply_normal_style()

        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

        super().mousePressEvent(event)


# ============================================================
# CARD DASHBOARD
# ============================================================




class CardDashboard(QWidget):

    # Navigation requests
    alarmRequested = pyqtSignal()
    configRequested = pyqtSignal()
    reportRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.cards = []

        # ====================================================
        # MAIN LAYOUT
        # ====================================================
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        main_layout.addStretch()

        # ====================================================
        # COMMON ICON
        # ====================================================
        self.header_icon = QLabel()
        self.header_icon.setAlignment(Qt.AlignCenter)

        self.header_icon.setPixmap(
            QIcon(
                resource_path(
                    "resources/icon/PostCheckAnalyzer.ico"
                )
            ).pixmap(QSize(72, 72))
        )

        main_layout.addWidget(
            self.header_icon,
            alignment=Qt.AlignCenter
        )

        main_layout.addSpacing(12)

        # ====================================================
        # COMMON TITLE
        # ====================================================
        self.header_title = QLabel("Post-Check Analyzer")
        self.header_title.setAlignment(Qt.AlignCenter)

        self.header_title.setStyleSheet("""
            QLabel {
                color: #1e293b;
                font-size: 30px;
                font-weight: 700;
            }
        """)

        main_layout.addWidget(
            self.header_title,
            alignment=Qt.AlignCenter
        )

        main_layout.addSpacing(35)

        # ====================================================
        # CENTERED CARD AREA
        # ====================================================
        center_layout = QHBoxLayout()

        center_layout.addStretch()

        self.card_grid = QGridLayout()
        self.card_grid.setHorizontalSpacing(24)
        self.card_grid.setVerticalSpacing(24)

        center_layout.addLayout(self.card_grid)

        center_layout.addStretch()

        main_layout.addLayout(center_layout)

        main_layout.addStretch()

        # ====================================================
        # CARDS
        # ====================================================

        self.add_card(
            icon=resource_path(
                "resources/icon/alarm.png"
            ),
            title="Alarm Analyzer",
            description=(
                "Analyze and compare network alarm files."
            ),
            bullet_points=[
                "Compare pre and post alarms",
                "Identify new and cleared alarms",
                "Advanced filtering",
                "Update status",
                "Export analysis results",
            ],
            callback=self.alarmRequested.emit
        )

        self.add_card(
            icon=resource_path(
                "resources/icon/configurator.png"
            ),
            title="Configuration Analyzer",
            description=(
                "Analyze network configuration changes."
            ),
            bullet_points=[
                "Compare pre and post config. dumps",
                "Detect parameter changes",
                "Profile based compare",
                "Export analysis results",
            ],
            callback=self.configRequested.emit
        )

        # Future Report Generator
        #
        # self.add_card(
        #     icon=resource_path(
        #         "resources/icon/report.png"
        #     ),
        #     title="Report Generator",
        #     description=(
        #         "Create detailed analysis reports."
        #     ),
        #     bullet_points=[
        #         "Generate Excel reports",
        #         "Export filtered results",
        #         "Create summaries",
        #     ],
        #     callback=self.reportRequested.emit
        # )

        # ====================================================
        # DASHBOARD STYLE
        # ====================================================
        self.setStyleSheet("""
            CardDashboard {
                background-color: #f4f7fb;
            }
        """)

    # ========================================================
    # ADD CARD
    # ========================================================
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

        columns = 3
        row, column = divmod(index, columns)

        self.card_grid.addWidget(
            card,
            row,
            column
        )

        self.cards.append(card)