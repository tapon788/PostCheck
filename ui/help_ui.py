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