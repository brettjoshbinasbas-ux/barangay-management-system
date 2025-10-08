import sys
import os

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit,
    QPushButton, QComboBox, QVBoxLayout, QMessageBox, QFrame, QSizePolicy
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

from Panels.db import get_connection, verify_password
from Panels.logger import log_staff_activity, log_admin_activity
from Panels.staff_dashboard import DashboardWindow
from Panels.admin_dashboard import AdminDashboard


class LoginPage(QMainWindow):
    def __init__(self):
        super().__init__()

        # --- Project Paths ---
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        styles_dir = os.path.join(base_dir, "Styles")
        images_dir = os.path.join(base_dir, "Images")

        qss_path = os.path.join(styles_dir, "login.qss")
        logo_path = os.path.join(images_dir, "BRIMS_logo.png")

        # --- Window Config ---
        self.setWindowTitle("BRIMS - Login")
        self.setMinimumSize(1200, 800)

        # --- Central Widget ---
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        # Main layout - centers everything
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Login Card Container ---
        login_card = QFrame()
        login_card.setObjectName("loginCard")
        login_card.setFixedSize(420, 680)

        # Card layout
        self.layout = QVBoxLayout(login_card)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(40, 20, 40, 40)  # ⬅️ reduced top margin
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Logo ---
        logo = QLabel()
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            logo.setMaximumHeight(150)
            logo.setPixmap(
                logo_pixmap.scaled(
                    140, 140,  # ⬅️ smaller footprint
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            print(f"⚠️ Logo not found at: {logo_path}")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layout.addWidget(logo)
        self.layout.addSpacing(10)

        # --- Title ---
        title = QLabel("BRIMS Login")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title)

        # --- Subtitle ---
        subtitle = QLabel("Barangay Resident Information Management System")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        self.layout.addWidget(subtitle)
        self.layout.addSpacing(20)

        # --- Username ---
        username_label = QLabel("Username")
        username_label.setObjectName("fieldLabel")
        self.layout.addWidget(username_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setObjectName("inputField")
        self.username_input.setMinimumHeight(45)
        self.layout.addWidget(self.username_input)
        self.layout.addSpacing(5)

        # --- Password ---
        password_label = QLabel("Password")
        password_label.setObjectName("fieldLabel")
        self.layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setObjectName("inputField")
        self.password_input.setMinimumHeight(45)
        self.layout.addWidget(self.password_input)
        self.layout.addSpacing(5)

        # --- Role ---
        role_label = QLabel("Role")
        role_label.setObjectName("fieldLabel")
        self.layout.addWidget(role_label)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["Staff", "Admin"])
        self.role_combo.setObjectName("comboBox")
        self.role_combo.setMinimumHeight(45)
        self.layout.addWidget(self.role_combo)
        self.layout.addSpacing(15)

        # --- Sign In Button ---
        login_button = QPushButton("Sign In")
        login_button.setObjectName("loginButton")
        login_button.clicked.connect(self.handle_login)
        login_button.setFixedHeight(45)
        self.layout.addWidget(login_button)

        # Add stretch to push everything up
        self.layout.addStretch()

        # Add the card to main layout
        main_layout.addWidget(login_card)

        # --- Apply Stylesheet ---
        if os.path.exists(qss_path):
            with open(qss_path, "r") as style_file:
                self.setStyleSheet(style_file.read())
        else:
            print(f"⚠️ Could not find QSS file at {qss_path}")

    def handle_login(self):
        """Handle login - NO CHANGES TO LOGIC"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_combo.currentText()

        try:
            conn = get_connection()
            cursor = conn.cursor()

            if role == "Staff":
                cursor.execute("SELECT * FROM staff WHERE username = %s", (username,))
            else:
                cursor.execute("SELECT * FROM admins WHERE username = %s", (username,))

            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user:
                if verify_password(password, user["password"]):
                    QMessageBox.information(self, "Login Success", f"Welcome {username} ({role})!")
                    self.current_user_id = user["id"]

                    if role == "Staff":
                        log_staff_activity(user["id"], "LOGIN", f"{username} logged in")
                        self.dashboard = DashboardWindow(staff_id=user["id"])
                    else:
                        log_admin_activity(user["id"], "LOGIN", f"Admin {username} logged in")
                        self.dashboard = AdminDashboard(admin_id=user["id"])

                    self.dashboard.showMaximized()
                    self.close()
                else:
                    QMessageBox.warning(self, "Login Failed", "Invalid password!")
            else:
                QMessageBox.warning(self, "Login Failed", "User not found!")

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginPage()
    window.show()
    sys.exit(app.exec())