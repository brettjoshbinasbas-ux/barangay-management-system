import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QComboBox
)

from Panels.db import get_connection, hash_password


class RegisterPage(QWidget):
    def __init__(self):
        super().__init__()

        # --- Project Paths ---
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        styles_dir = os.path.join(base_dir, "Styles")

        qss_path = os.path.join(styles_dir, "register.qss")

        # --- Apply Stylesheet ---
        if os.path.exists(qss_path):
            with open(qss_path, "r") as style_file:
                self.setStyleSheet(style_file.read())
        else:
            print(f"⚠️ Could not find QSS file at {qss_path}")

        self.setWindowTitle("Register Account")
        self.resize(400, 300)

        # --- Center the window on screen ---
        screen = self.screen().availableGeometry()
        window_size = self.geometry()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        self.move(x, y)

        # --- Layout ---
        layout = QVBoxLayout(self)

        self.label = QLabel("Register New Account")
        layout.addWidget(self.label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email (required)")
        layout.addWidget(self.email_input)

        self.role_select = QComboBox()
        self.role_select.setObjectName("comboBox")
        self.role_select.addItems(["Staff"])  # ✅ Staff only
        layout.addWidget(self.role_select)

        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.register_account)
        layout.addWidget(self.register_button)

    def register_account(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        email = self.email_input.text().strip()
        role = self.role_select.currentText()  # always "Staff"
        status = "active"  # ✅ default

        if not username or not password or not email:
            QMessageBox.warning(self, "Error", "All fields are required.")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # ✅ Prevent duplicates
            cursor.execute("SELECT * FROM staff WHERE username = %s", (username,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Error", "Username already exists.")
                cursor.close()
                conn.close()
                return

            # ✅ Hash password before saving
            hashed_pw = hash_password(password)

            # ✅ Insert into staff table
            cursor.execute(
                "INSERT INTO staff (username, password, role, email, status) VALUES (%s, %s, %s, %s, %s)",
                (username, hashed_pw, role, email, status)
            )
            conn.commit()

            QMessageBox.information(self, "Success", f"Staff account created for {username}.")

            cursor.close()
            conn.close()
            self.close()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Error: {e}")
