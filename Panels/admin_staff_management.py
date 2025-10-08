import os
from PyQt6.QtWidgets import QSizePolicy, QHeaderView
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem
)
# from PyQt6.QtCore import Qt

class StaffManagementPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

        # --- Project Paths ---
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        styles_dir = os.path.join(base_dir, "Styles")

        qss_path = os.path.join(styles_dir, "admin_worker_management.qss")

        # --- Apply Stylesheet ---
        if os.path.exists(qss_path):
            with open(qss_path, "r") as style_file:
                self.setStyleSheet(style_file.read())
        else:
            print(f"⚠️ Could not find QSS file at {qss_path}")

    def init_ui(self):
        layout = QVBoxLayout(self)

        # --- Header ---
        header = QFrame()
        header_layout = QHBoxLayout(header)

        title = QLabel("Admin Panel")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Manage users and system settings")
        subtitle.setObjectName("subtitleText")

        header_texts = QVBoxLayout()
        header_texts.addWidget(title)
        header_texts.addWidget(subtitle)

        header_layout.addLayout(header_texts)
        header_layout.addStretch()

        user_label = QLabel("Admin User\nAdmin")
        user_label.setObjectName("userLabel")
        header_layout.addWidget(user_label)

        layout.addWidget(header)

        # --- Metrics (cards) ---
        metrics_frame = QFrame()
        metrics_layout = QHBoxLayout(metrics_frame)

        metrics_layout.addWidget(self.create_metric_box("Total Users", "3"))
        metrics_layout.addWidget(self.create_metric_box("Administrators", "1"))
        metrics_layout.addWidget(self.create_metric_box("Workers", "2"))

        layout.addWidget(metrics_frame)

        # --- User Management Section ---
        section_frame = QFrame()
        section_layout = QVBoxLayout(section_frame)

        top_row = QHBoxLayout()
        section_title = QLabel("User Management")
        section_title.setObjectName("sectionTitle")
        add_user_btn = QPushButton("+ Add User")
        add_user_btn.setObjectName("addUserButton")

        top_row.addWidget(section_title)
        top_row.addStretch()
        top_row.addWidget(add_user_btn)

        section_sub = QLabel("Manage system users and their permissions")
        section_sub.setObjectName("subtitleText")

        section_layout.addLayout(top_row)
        section_layout.addWidget(section_sub)

        # --- Table ---
        table = QTableWidget()
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setObjectName("userTable")
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            ["Username", "Email", "Role", "Status", "Actions"]
        )
        users = [
            ("admin", "admin@barangay.gov.ph", "Admin", "Active"),
            ("elena.castillo", "elena@barangay.gov.ph", "Worker", "Active"),
            ("roberto.flores", "roberto@barangay.gov.ph", "Worker", "Active")
        ]
        table.setRowCount(len(users))

        for row, (username, email, role, status) in enumerate(users):
            table.setItem(row, 0, QTableWidgetItem(username))
            table.setItem(row, 1, QTableWidgetItem(email))
            table.setItem(row, 2, QTableWidgetItem(role))
            table.setItem(row, 3, QTableWidgetItem(status))

            # Action Button
            delete_btn = QPushButton("🗑️")
            table.setCellWidget(row, 4, delete_btn)

        section_layout.addWidget(table)
        layout.addWidget(section_frame)

    def create_metric_box(self, title, value):
        box = QFrame()
        box.setObjectName("metricBox")
        vbox = QVBoxLayout(box)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("metricTitle")
        value_lbl = QLabel(value)
        value_lbl.setObjectName("metricValue")

        vbox.addWidget(title_lbl)
        vbox.addWidget(value_lbl)
        return box
