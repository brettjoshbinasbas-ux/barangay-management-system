import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame, QMessageBox, QDialog, QFormLayout,
    QLabel, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from Panels.db import get_connection, hash_password
from Panels.logger import log_admin_activity


class AdminWorkerManagement(QWidget):
    workers_changed = pyqtSignal()

    def __init__(self, admin_id=None):
        super().__init__()
        self.admin_id = admin_id

        # --- Project Paths ---
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        styles_dir = os.path.join(base_dir, "Styles")
        qss_path = os.path.join(styles_dir, "admin_worker_management.qss")

        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("workerScroll")

        content = QWidget()
        content.setObjectName("workerContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        # --- Header Section ---
        header_frame = QFrame()
        header_frame.setObjectName("headerSection")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        page_title = QLabel("Worker Management")
        page_title.setObjectName("pageTitle")
        header_layout.addWidget(page_title)

        layout.addWidget(header_frame)

        # --- Admin Panel Section ---
        admin_panel_container = QWidget()
        admin_panel_layout = QVBoxLayout(admin_panel_container)
        admin_panel_layout.setContentsMargins(0, 0, 0, 0)
        admin_panel_layout.setSpacing(10)

        main_subtitle = QLabel("Admin Panel")
        main_subtitle.setObjectName("mainSubtitle")

        description = QLabel("Manage users and system settings")
        description.setObjectName("description")

        admin_panel_layout.addWidget(main_subtitle)
        admin_panel_layout.addWidget(description)

        layout.addWidget(admin_panel_container)

        # --- User Management Badge ---
        badge_container = QFrame()
        badge_container.setObjectName("badgeContainer")
        badge_layout = QHBoxLayout(badge_container)
        badge_layout.setContentsMargins(15, 12, 15, 12)
        badge_layout.setSpacing(10)

        badge_icon = QLabel("👥")
        badge_icon.setObjectName("badgeIcon")

        badge_text = QLabel("User Management")
        badge_text.setObjectName("badgeText")

        badge_layout.addWidget(badge_icon)
        badge_layout.addWidget(badge_text)
        badge_layout.addStretch()

        layout.addWidget(badge_container)

        # --- Metrics Cards ---
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(20)

        # Total Users Card
        self.total_users_card = self.create_metric_card("Total Users", "0", "👥", "#8B5CF6")
        metrics_row.addWidget(self.total_users_card)

        # Administrators Card
        self.admin_count_card = self.create_metric_card("Administrators", "0", "🛡️", "#EF4444")
        metrics_row.addWidget(self.admin_count_card)

        # Staff Card
        self.staff_count_card = self.create_metric_card("Staff", "0", "👨‍💼", "#3B82F6")
        metrics_row.addWidget(self.staff_count_card)

        metrics_row.addStretch()

        layout.addLayout(metrics_row)

        # --- User Management Table Card ---
        table_card = QFrame()
        table_card.setObjectName("tableCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(25, 25, 25, 25)
        table_layout.setSpacing(15)

        # Card Header
        card_header = QHBoxLayout()

        # Left side - Title and subtitle
        list_info = QWidget()
        list_info_layout = QVBoxLayout(list_info)
        list_info_layout.setContentsMargins(0, 0, 0, 0)
        list_info_layout.setSpacing(2)

        list_title = QLabel("User Management")
        list_title.setObjectName("listTitle")

        list_subtitle = QLabel("Manage system users and their permissions")
        list_subtitle.setObjectName("listSubtitle")

        list_info_layout.addWidget(list_title)
        list_info_layout.addWidget(list_subtitle)

        card_header.addWidget(list_info)
        card_header.addStretch()

        # Right side - Add User Buttons
        add_buttons_layout = QHBoxLayout()
        add_buttons_layout.setSpacing(10)

        btn_add_staff = QPushButton("+ Add Staff")
        btn_add_staff.setObjectName("addButton")
        btn_add_staff.clicked.connect(lambda: self.add_user_dialog("Staff"))
        add_buttons_layout.addWidget(btn_add_staff)

        btn_add_admin = QPushButton("+ Add Admin")
        btn_add_admin.setObjectName("addAdminButton")
        btn_add_admin.clicked.connect(lambda: self.add_user_dialog("Admin"))
        add_buttons_layout.addWidget(btn_add_admin)

        card_header.addLayout(add_buttons_layout)

        table_layout.addLayout(card_header)

        # --- Filters Row ---
        filters_row = QHBoxLayout()
        filters_row.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search username or email...")
        self.search_input.setObjectName("searchBar")
        self.search_input.textChanged.connect(self.load_users)
        filters_row.addWidget(self.search_input)

        self.role_filter = QComboBox()
        self.role_filter.addItems(["All", "Staff", "Admin"])
        self.role_filter.setObjectName("roleFilter")
        self.role_filter.currentIndexChanged.connect(self.load_users)
        self.role_filter.setFixedWidth(150)
        filters_row.addWidget(self.role_filter)

        table_layout.addLayout(filters_row)

        # --- Table - UPDATED FOR ADMIN MANAGEMENT ---
        self.table = QTableWidget()
        self.table.setObjectName("usersTable")
        self.table.setColumnCount(6)  # Added Role column
        self.table.setHorizontalHeaderLabels(
            ["ID", "Username", "Email", "Role", "Status", "Actions"]
        )

        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.Fixed)  # ID
        header.setSectionResizeMode(1, header.ResizeMode.Stretch)  # Username
        header.setSectionResizeMode(2, header.ResizeMode.Stretch)  # Email
        header.setSectionResizeMode(3, header.ResizeMode.Fixed)  # Role
        header.setSectionResizeMode(4, header.ResizeMode.Fixed)  # Status
        header.setSectionResizeMode(5, header.ResizeMode.Fixed)  # Actions

        self.table.setColumnWidth(0, 80)  # ID
        self.table.setColumnWidth(3, 100)  # Role
        self.table.setColumnWidth(4, 200)  # Status
        self.table.setColumnWidth(5, 300)  # Actions (wider for more buttons)

        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(self.table.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)

        table_layout.addWidget(self.table)

        layout.addWidget(table_card)

        # Set scroll content
        scroll.setWidget(content)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # Load stylesheet
        if os.path.exists(qss_path):
            with open(qss_path, "r") as style_file:
                self.setStyleSheet(style_file.read())
        else:
            print(f"⚠️ Could not find QSS file at {qss_path}")

        # Load users initially
        self.load_users()
        self.update_metrics()

    def create_metric_card(self, title, value, icon, color):
        """Create a metric card with left border accent"""
        card = QFrame()
        card.setObjectName("metricCard")
        card.setProperty("borderColor", color)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # Text section
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("metricTitle")

        value_label = QLabel(value)
        value_label.setObjectName("metricValue")

        text_layout.addWidget(title_label)
        text_layout.addWidget(value_label)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setObjectName("metricIcon")
        icon_label.setStyleSheet(f"background-color: {color}; color: white; font-size: 20px; border-radius: 20px;")
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(text_widget)
        card_layout.addStretch()
        card_layout.addWidget(icon_label)

        return card

    def update_metrics(self):
        """Update metric cards with current counts"""
        conn = get_connection()
        cursor = conn.cursor()

        # Staff count
        cursor.execute("SELECT COUNT(*) as total FROM staff")
        staff_count = cursor.fetchone()["total"]

        # Admin count
        cursor.execute("SELECT COUNT(*) as total FROM admins")
        admin_count = cursor.fetchone()["total"]

        # Total users
        total_users = staff_count + admin_count

        cursor.close()
        conn.close()

        # Update cards
        total_value = self.total_users_card.findChild(QLabel, "metricValue")
        if total_value:
            total_value.setText(str(total_users))

        admin_value = self.admin_count_card.findChild(QLabel, "metricValue")
        if admin_value:
            admin_value.setText(str(admin_count))

        staff_value = self.staff_count_card.findChild(QLabel, "metricValue")
        if staff_value:
            staff_value.setText(str(staff_count))

    def load_users(self):
        """Load users from both staff and admins tables"""
        conn = get_connection()
        cursor = conn.cursor()

        # Get selected filter
        role_filter = self.role_filter.currentText()
        search = self.search_input.text().strip()

        users = []

        # Load staff users
        if role_filter in ["All", "Staff"]:
            staff_query = "SELECT id, username, email, 'Staff' as role, status FROM staff WHERE 1=1"
            staff_params = []

            if search:
                staff_query += " AND (username LIKE %s OR email LIKE %s)"
                staff_params.extend([f"%{search}%", f"%{search}%"])

            cursor.execute(staff_query, staff_params)
            staff_users = cursor.fetchall()
            users.extend(staff_users)

        # Load admin users
        if role_filter in ["All", "Admin"]:
            admin_query = "SELECT id, username, email, 'Admin' as role, 'active' as status FROM admins WHERE 1=1"
            admin_params = []

            if search:
                admin_query += " AND (username LIKE %s OR email LIKE %s)"
                admin_params.extend([f"%{search}%", f"%{search}%"])

            cursor.execute(admin_query, admin_params)
            admin_users = cursor.fetchall()
            users.extend(admin_users)

        self.populate_table(users)
        cursor.close()
        conn.close()

    def populate_table(self, users):
        """Populate table with users data"""
        self.table.setRowCount(len(users))

        for row, user in enumerate(users):
            # ID
            id_item = QTableWidgetItem(str(user["id"]))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, id_item)

            # Username
            username_item = QTableWidgetItem(user["username"])
            username_item.setFlags(username_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            username_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, username_item)

            # Email
            email_item = QTableWidgetItem(user["email"])
            email_item.setFlags(email_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            email_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, email_item)

            # Role Badge
            role_widget = QWidget()
            role_layout = QHBoxLayout(role_widget)
            role_layout.setContentsMargins(0, 0, 0, 0)
            role_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            role_label = QLabel(user["role"])
            role_label.setObjectName("roleBadge")
            role_label.setProperty("roleType", user["role"].lower())
            role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            role_label.setMinimumHeight(28)
            role_label.setMinimumWidth(80)
            role_layout.addWidget(role_label)

            self.table.setCellWidget(row, 3, role_widget)

            # Status Badge (only for staff, admins are always active)
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(0, 0, 0, 0)
            status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            status_text = user["status"] if user["role"] == "Staff" else "Active"
            status_label = QLabel(status_text.capitalize())
            status_label.setObjectName("statusBadge")
            status_label.setProperty("statusType", status_text.lower())
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_label.setMinimumHeight(28)
            status_label.setMinimumWidth(80)
            status_layout.addWidget(status_label)

            self.table.setCellWidget(row, 4, status_widget)

            # --- Actions Column ---
            actions = QFrame()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(8, 5, 8, 5)
            actions_layout.setSpacing(6)
            actions_layout.addStretch()

            # Edit Button
            btn_edit = QPushButton("✏️")
            btn_edit.setFont(QFont("Segoe UI", 12))
            btn_edit.setFixedSize(32, 22)
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.setToolTip("Edit user")
            btn_edit.setStyleSheet("""
                QPushButton {
                    background-color: #F1F5F9;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #E2E8F0;
                }
            """)
            btn_edit.clicked.connect(lambda _, u=user: self.edit_user_dialog(u))
            actions_layout.addWidget(btn_edit)

            # Toggle status button (only for staff)
            if user["role"] == "Staff":
                status_icon = "✅" if user["status"] == "inactive" else "⏸️"
                status_tooltip = "Activate" if user["status"] == "inactive" else "Deactivate"
                btn_toggle = QPushButton(status_icon)
                btn_toggle.setFont(QFont("Segoe UI", 12))
                btn_toggle.setFixedSize(32, 22)
                btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_toggle.setToolTip(status_tooltip)
                btn_toggle.setStyleSheet("""
                    QPushButton {
                        background-color: #F0FDF4;
                        border: 1px solid #BBF7D0;
                        border-radius: 6px;
                        color: #166534;
                    }
                    QPushButton:hover {
                        background-color: #DCFCE7;
                    }
                """)
                btn_toggle.clicked.connect(lambda _, u=user: self.toggle_status(u))
                actions_layout.addWidget(btn_toggle)

            # Delete button (prevent self-deletion)
            if not (user["role"] == "Admin" and user["id"] == self.admin_id):
                btn_delete = QPushButton("🗑️")
                btn_delete.setFont(QFont("Segoe UI", 12))
                btn_delete.setFixedSize(32, 22)
                btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_delete.setToolTip("Delete user")
                btn_delete.setStyleSheet("""
                    QPushButton {
                        background-color: #FEE2E2;
                        border: 1px solid #FECACA;
                        border-radius: 6px;
                        color: #DC2626;
                    }
                    QPushButton:hover {
                        background-color: #FECACA;
                    }
                """)
                btn_delete.clicked.connect(lambda _, uid=user["id"], uname=user["username"], role=user["role"]:
                                           self.delete_user(uid, uname, role))
                actions_layout.addWidget(btn_delete)

            actions_layout.addStretch()
            self.table.setCellWidget(row, 5, actions)
            self.table.setRowHeight(row, 60)

        self.update_metrics()

    def add_user_dialog(self, role):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Add {role}")
        dialog.setObjectName("addDialog")
        dialog.setMinimumWidth(400)

        form = QFormLayout(dialog)
        form.setSpacing(15)
        form.setContentsMargins(25, 25, 25, 25)

        username_input = QLineEdit()
        username_input.setObjectName("dialogInput")
        email_input = QLineEdit()
        email_input.setObjectName("dialogInput")
        password_input = QLineEdit()
        password_input.setObjectName("dialogInput")
        password_input.setEchoMode(QLineEdit.EchoMode.Password)

        form.addRow("Username:", username_input)
        form.addRow("Email:", email_input)
        form.addRow("Password:", password_input)

        btn_save = QPushButton(f"Add {role}")
        btn_save.setObjectName("dialogButton")
        btn_save.clicked.connect(lambda: self.save_new_user(
            username_input.text(), email_input.text(), password_input.text(), role, dialog
        ))
        form.addWidget(btn_save)

        dialog.exec()

    def save_new_user(self, username, email, password, role, dialog):
        if not username or not email or not password:
            QMessageBox.warning(self, "Error", "All fields are required.")
            return

        if "@" not in email:
            QMessageBox.warning(self, "Error", "Please enter a valid email address.")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Check if username exists in either table
            if role == "Staff":
                cursor.execute("SELECT id FROM staff WHERE username=%s", (username,))
            else:
                cursor.execute("SELECT id FROM admins WHERE username=%s", (username,))

            if cursor.fetchone():
                QMessageBox.warning(self, "Error", "Username already exists.")
                return

            hashed_pw = hash_password(password)

            if role == "Staff":
                cursor.execute(
                    "INSERT INTO staff (username, email, password, role, status) VALUES (%s, %s, %s, %s, %s)",
                    (username, email, hashed_pw, "Staff", "active")
                )
            else:
                cursor.execute(
                    "INSERT INTO admins (username, email, password, role) VALUES (%s, %s, %s, %s)",
                    (username, email, hashed_pw, "Admin")
                )

            conn.commit()
            cursor.close()
            conn.close()

            log_admin_activity(self.admin_id, f"ADD_{role.upper()}", f"Added {role.lower()} {username}")
            self.load_users()
            self.workers_changed.emit()
            dialog.accept()
            QMessageBox.information(self, "Success", f"{role} {username} added successfully.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add {role.lower()}:\n{e}")

    def edit_user_dialog(self, user):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Staff")
        dialog.setObjectName("addDialog")
        dialog.setMinimumWidth(400)

        form = QFormLayout(dialog)
        form.setSpacing(15)
        form.setContentsMargins(25, 25, 25, 25)

        email_input = QLineEdit(user["email"])
        email_input.setObjectName("dialogInput")
        password_input = QLineEdit()
        password_input.setObjectName("dialogInput")
        password_input.setPlaceholderText("Leave blank to keep current password")
        password_input.setEchoMode(QLineEdit.EchoMode.Password)

        form.addRow("Email:", email_input)
        form.addRow("New Password:", password_input)

        btn_save = QPushButton("Save Changes")
        btn_save.setObjectName("dialogButton")
        btn_save.clicked.connect(lambda: self.save_user_changes(
            user["id"], email_input.text(), password_input.text(), dialog
        ))
        form.addWidget(btn_save)

        dialog.exec()

    def save_user_changes(self, user_id, email, password, dialog):
        # ✅ ADDED: Email validation
        if not email or "@" not in email:
            QMessageBox.warning(self, "Error", "Please enter a valid email address.")
            return

        conn = get_connection()
        cursor = conn.cursor()

        if password:
            hashed_pw = hash_password(password)
            query = "UPDATE staff SET email=%s, password=%s WHERE id=%s"
            cursor.execute(query, (email, hashed_pw, user_id))
        else:
            query = "UPDATE staff SET email=%s WHERE id=%s"
            cursor.execute(query, (email, user_id))

        conn.commit()
        cursor.close()
        conn.close()

        log_admin_activity(self.admin_id, "EDIT_STAFF", f"Updated staff {user_id}")
        self.load_users()
        self.workers_changed.emit()  # ✅ ADDED: Emit signal for dashboard refresh
        dialog.accept()
        QMessageBox.information(self, "Success", "Staff updated successfully.")

    def delete_user(self, user_id, username, role):
        """Delete a user (Staff or Admin) with confirmation"""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete {role.lower()} '{username}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = get_connection()
                cursor = conn.cursor()

                if role == "Staff":
                    cursor.execute("DELETE FROM staff WHERE id=%s", (user_id,))
                    log_admin_activity(self.admin_id, "DELETE_STAFF", f"Deleted staff {username}")
                else:  # Admin
                    cursor.execute("DELETE FROM admins WHERE id=%s", (user_id,))
                    log_admin_activity(self.admin_id, "DELETE_ADMIN", f"Deleted admin {username}")

                conn.commit()
                cursor.close()
                conn.close()

                self.load_users()
                self.workers_changed.emit()
                QMessageBox.information(self, "Success", f"{role} '{username}' deleted successfully.")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete {role.lower()}:\n{e}")

    def toggle_status(self, user):
        conn = get_connection()
        cursor = conn.cursor()

        new_status = "inactive" if user["status"] == "active" else "active"
        cursor.execute("UPDATE staff SET status=%s WHERE id=%s", (new_status, user["id"]))
        conn.commit()

        cursor.close()
        conn.close()

        log_admin_activity(self.admin_id, "TOGGLE_STAFF", f"Set {user['username']} to {new_status}")
        self.load_users()
        self.workers_changed.emit()  # ✅ ADDED: Emit signal for dashboard refresh
        QMessageBox.information(self, "Success", f"Staff {user['username']} is now {new_status}.")