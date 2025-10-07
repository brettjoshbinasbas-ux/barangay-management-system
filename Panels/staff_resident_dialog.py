# Panels/staff_resident_dialog.py
import os
import datetime
import traceback
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox, QSpinBox,
    QPushButton, QMessageBox, QLabel, QWidget, QFrame
)
from PyQt6.QtCore import Qt, QTimer

from Panels.db import get_connection
from Panels.logger import log_staff_activity, log_admin_activity


class ResidentDialog(QDialog):
    """Dialog for adding or editing residents with safe operations."""

    def __init__(self, parent=None, resident_id=None, role="Staff", user_id=None):
        super().__init__(parent)
        self.resident_id = resident_id
        self.role = role
        self.user_id = user_id
        self._saving = False  # Prevent duplicate saves

        self.setWindowTitle("Add New Resident" if not resident_id else "Edit Resident")
        self.setMinimumWidth(650)
        self.setMinimumHeight(900)

        # --- Main layout ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setObjectName("dialogHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(25, 20, 25, 20)

        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)

        dialog_title = QLabel("Add New Resident" if not resident_id else "Edit Resident")
        dialog_title.setObjectName("dialogTitle")

        dialog_subtitle = QLabel(
            "Enter the details of the new resident" if not resident_id else "Update the resident information"
        )
        dialog_subtitle.setObjectName("dialogSubtitle")

        title_layout.addWidget(dialog_title)
        title_layout.addWidget(dialog_subtitle)
        header_layout.addWidget(title_container)
        header_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeButton")
        close_btn.setFixedSize(32, 32)
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)
        main_layout.addWidget(header)

        # Content
        content = QWidget()
        content.setObjectName("dialogContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(25, 25, 25, 25)
        content_layout.setSpacing(20)

        # Create form
        self.setup_form(content_layout)
        main_layout.addWidget(content)

        # Footer
        footer = QFrame()
        footer.setObjectName("dialogFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(25, 15, 25, 15)
        footer_layout.setSpacing(12)

        footer_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)
        footer_layout.addWidget(cancel_btn)

        self.save_button = QPushButton("Add Resident" if not resident_id else "Save Changes")
        self.save_button.setObjectName("saveButton")
        self.save_button.clicked.connect(self.safe_save_resident)  # Use safe save
        footer_layout.addWidget(self.save_button)
        main_layout.addWidget(footer)

        # Load QSS
        self.load_styles()

        # Edit mode: load resident
        if self.resident_id:
            QTimer.singleShot(100, self.load_resident_data)  # Load after UI is ready

    def setup_form(self, content_layout):
        """Setup the form layout"""
        form = QFormLayout()
        form.setVerticalSpacing(12)
        form.setSpacing(15)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # Name
        name_label = QLabel("Full Name")
        name_label.setObjectName("fieldLabel")
        self.name_input = QLineEdit()
        self.name_input.setObjectName("dialogInput")
        self.name_input.setPlaceholderText("Enter full name")
        form.addRow(name_label, self.name_input)

        # Age & Gender
        age_gender_container = QWidget()
        age_gender_layout = QHBoxLayout(age_gender_container)
        age_gender_layout.setContentsMargins(0, 0, 0, 0)
        age_gender_layout.setSpacing(15)

        # Age
        age_widget = QWidget()
        age_widget_layout = QVBoxLayout(age_widget)
        age_widget_layout.setContentsMargins(0, 0, 0, 0)
        age_widget_layout.setSpacing(8)
        age_label = QLabel("Age")
        age_label.setObjectName("fieldLabel")
        self.age_input = QSpinBox()
        self.age_input.setObjectName("dialogSpinBox")
        self.age_input.setRange(0, 120)
        self.age_input.setFixedHeight(60)
        age_widget_layout.addWidget(age_label)
        age_widget_layout.addWidget(self.age_input)

        # Gender
        gender_widget = QWidget()
        gender_widget_layout = QVBoxLayout(gender_widget)
        gender_widget_layout.setContentsMargins(0, 0, 0, 0)
        gender_widget_layout.setSpacing(8)
        gender_label = QLabel("Gender")
        gender_label.setObjectName("fieldLabel")
        self.gender_input = QComboBox()
        self.gender_input.setObjectName("dialogComboBox")
        self.gender_input.addItems(["Select gender", "Male", "Female"])
        self.gender_input.setFixedHeight(60)
        gender_widget_layout.addWidget(gender_label)
        gender_widget_layout.addWidget(self.gender_input)

        age_gender_layout.addWidget(age_widget, 1)
        age_gender_layout.addWidget(gender_widget, 1)
        form.addRow("", age_gender_container)

        # Address
        address_label = QLabel("Address")
        address_label.setObjectName("fieldLabel")
        self.address_input = QLineEdit()
        self.address_input.setObjectName("dialogInput")
        self.address_input.setPlaceholderText("Complete address")
        form.addRow(address_label, self.address_input)

        # Civil status
        civil_label = QLabel("Civil Status")
        civil_label.setObjectName("fieldLabel")
        self.civil_input = QComboBox()
        self.civil_input.setObjectName("dialogComboBox")
        self.civil_input.addItems(["Select civil status", "Single", "Married", "Widowed", "Divorced", "Separated"])
        self.civil_input.setEditable(True)
        self.civil_input.setFixedHeight(40)
        form.addRow(civil_label, self.civil_input)

        # Contact
        contact_label = QLabel("Contact Number")
        contact_label.setObjectName("fieldLabel")
        self.contact_input = QLineEdit()
        self.contact_input.setObjectName("dialogInput")
        self.contact_input.setPlaceholderText("Contact number")
        form.addRow(contact_label, self.contact_input)

        # Employment
        employment_label = QLabel("Employment Status")
        employment_label.setObjectName("fieldLabel")
        self.employment_input = QComboBox()
        self.employment_input.setObjectName("dialogComboBox")
        self.employment_input.addItems([
            "Select employment status", "Employed", "Unemployed", "Self-employed", "Student", "Retired", "Others"
        ])
        self.employment_input.setEditable(True)
        self.employment_input.setFixedHeight(40)
        form.addRow(employment_label, self.employment_input)

        # Education
        education_label = QLabel("Education Level")
        education_label.setObjectName("fieldLabel")
        self.education_input = QComboBox()
        self.education_input.setObjectName("dialogComboBox")
        self.education_input.addItems([
            "Select education level", "No formal education", "Elementary", "High School", "College", "Vocational",
            "Postgraduate"
        ])
        self.education_input.setEditable(True)
        self.education_input.setFixedHeight(40)
        form.addRow(education_label, self.education_input)

        # Residency years
        residency_label = QLabel("Residency Years")
        residency_label.setObjectName("fieldLabel")
        self.residency_input = QSpinBox()
        self.residency_input.setObjectName("dialogSpinBox")
        self.residency_input.setRange(0, 100)
        self.residency_input.setFixedHeight(40)
        form.addRow(residency_label, self.residency_input)

        # Status
        status_label = QLabel("Status")
        status_label.setObjectName("fieldLabel")
        self.status_input = QComboBox()
        self.status_input.setObjectName("dialogComboBox")
        self.status_input.addItems(["Active", "Inactive", "Transferred"])
        self.status_input.setFixedHeight(40)
        form.addRow(status_label, self.status_input)

        content_layout.addLayout(form)
        content_layout.addStretch()

    def load_styles(self):
        """Load QSS styles"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        qss_path = os.path.join(base_dir, "Styles", "staff_resident_dialog.qss")
        if os.path.exists(qss_path):
            try:
                with open(qss_path, "r") as style_file:
                    self.setStyleSheet(style_file.read())
            except Exception as e:
                print(f"⚠️ Style loading failed: {e}")

    def load_resident_data(self):
        """Load resident data for editing"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM residents WHERE id=%s", (self.resident_id,))
            resident = cursor.fetchone()
            cursor.close()
            conn.close()

            if resident:
                self.populate_form(resident)

        except Exception as e:
            print(f"⚠️ load_resident_data failed: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to load resident data:\n{e}")

    def populate_form(self, resident):
        """Populate form with resident data"""
        # Protect against None values
        self.name_input.setText(resident.get("name") or "")
        self.age_input.setValue(int(resident.get("age") or 0))

        gender = resident.get("gender") or ""
        gender_index = self.gender_input.findText(gender)
        if gender_index >= 0:
            self.gender_input.setCurrentIndex(gender_index)

        self.address_input.setText(resident.get("address") or "")
        self.contact_input.setText(resident.get("contact_number") or "")

        civil = resident.get("civil_status") or ""
        civil_index = self.civil_input.findText(civil)
        if civil_index >= 0:
            self.civil_input.setCurrentIndex(civil_index)
        else:
            self.civil_input.setEditText(civil)

        emp = resident.get("employment_status") or ""
        emp_index = self.employment_input.findText(emp)
        if emp_index >= 0:
            self.employment_input.setCurrentIndex(emp_index)
        else:
            self.employment_input.setEditText(emp)

        edu = resident.get("education_level") or ""
        edu_index = self.education_input.findText(edu)
        if edu_index >= 0:
            self.education_input.setCurrentIndex(edu_index)
        else:
            self.education_input.setEditText(edu)

        self.residency_input.setValue(int(resident.get("residency_years") or 0))

        status = resident.get("status") or "Active"
        status_index = self.status_input.findText(status)
        if status_index >= 0:
            self.status_input.setCurrentIndex(status_index)

    def safe_save_resident(self):
        """Safe save with prevention of duplicate calls"""
        if self._saving:
            return

        self._saving = True
        self.save_button.setEnabled(False)

        try:
            self.save_resident()
        finally:
            QTimer.singleShot(1000, self.enable_save_button)  # Re-enable after 1 second

    def enable_save_button(self):
        """Re-enable save button after operation"""
        self._saving = False
        self.save_button.setEnabled(True)

    def check_duplicate_resident(self, name, contact_number):
        """Check if resident with same name or contact number already exists"""
        conn = get_connection()
        cursor = conn.cursor()

        if self.resident_id:  # For edit mode - exclude current resident
            cursor.execute("""
                SELECT id, name, contact_number FROM residents 
                WHERE (name = %s OR contact_number = %s) AND id != %s
            """, (name, contact_number, self.resident_id))
        else:  # For add mode
            cursor.execute("""
                SELECT id, name, contact_number FROM residents 
                WHERE name = %s OR contact_number = %s
            """, (name, contact_number))

        duplicates = cursor.fetchall()
        cursor.close()
        conn.close()

        return duplicates

    def save_resident(self):
        """Save resident data with duplicate checking"""
        # Get and validate form data
        name = (self.name_input.text() or "").strip()
        age = int(self.age_input.value())
        gender = (self.gender_input.currentText() or "").strip()
        address = (self.address_input.text() or "").strip()
        contact = (self.contact_input.text() or "").strip()
        civil = (self.civil_input.currentText() or "").strip()
        employment = (self.employment_input.currentText() or "").strip()
        education = (self.education_input.currentText() or "").strip()
        residency = int(self.residency_input.value())
        status = (self.status_input.currentText() or "").strip()

        # Basic validation
        if not name:
            QMessageBox.warning(self, "Validation Error", "Name is required.")
            return
        if not address:
            QMessageBox.warning(self, "Validation Error", "Address is required.")
            return
        if gender == "Select gender" or gender == "":
            QMessageBox.warning(self, "Validation Error", "Please select a gender.")
            return
        if civil == "Select civil status" or civil == "":
            QMessageBox.warning(self, "Validation Error", "Please select a civil status.")
            return

        # Check for duplicates
        duplicates = self.check_duplicate_resident(name, contact)
        if duplicates:
            duplicate_messages = []
            for dup in duplicates:
                if dup["name"] == name:
                    duplicate_messages.append(f"• Name '{name}' already exists (ID: {dup['id']})")
                if dup["contact_number"] == contact and contact:  # Only check if contact is provided
                    duplicate_messages.append(f"• Contact number '{contact}' already exists (ID: {dup['id']})")

            if duplicate_messages:
                error_msg = "Cannot save resident due to duplicates:\n\n" + "\n".join(duplicate_messages)
                QMessageBox.warning(self, "Duplicate Resident", error_msg)
                return

        # Database operations
        conn = None
        cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            if self.resident_id:
                # UPDATE
                cursor.execute("""
                    UPDATE residents
                    SET name=%s, age=%s, gender=%s, address=%s, contact_number=%s,
                        civil_status=%s, employment_status=%s, education_level=%s,
                        residency_years=%s, status=%s
                    WHERE id=%s
                """, (name, age, gender, address, contact, civil, employment, education,
                      residency, status, self.resident_id))
            else:
                # INSERT
                created_by = self.user_id if self.user_id is not None else None
                cursor.execute("""
                    INSERT INTO residents
                    (name, age, gender, address, contact_number, civil_status,
                     employment_status, education_level, residency_years,
                     created_by, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (name, age, gender, address, contact, civil, employment, education,
                      residency, created_by, status))

            conn.commit()

            # Logging
            try:
                if self.resident_id:
                    action = f"Edited resident ID {self.resident_id}"
                else:
                    inserted_id = cursor.lastrowid if cursor else None
                    action = f"Added new resident {name} (id={inserted_id})"

                if self.role == "Admin":
                    log_admin_activity(self.user_id, "EDIT_RESIDENT" if self.resident_id else "ADD_RESIDENT", action)
                else:
                    log_staff_activity(self.user_id, "EDIT_RESIDENT" if self.resident_id else "ADD_RESIDENT", action)
            except Exception as le:
                print("⚠️ Logging failed:", le)

            QMessageBox.information(self, "Success", "Resident saved successfully.")
            self.accept()  # This will close the dialog

        except Exception as e:
            print("❌ save_resident error:", e)
            traceback.print_exc()
            QMessageBox.critical(self, "Database Error", f"Failed to save resident:\n{e}")
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()