import os

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QMessageBox, QDateEdit, QLabel, QWidget, QFrame
)
from PyQt6.QtCore import QDate, Qt
from Panels.db import get_connection
import datetime


class NewRequestDialog(QDialog):
    """
    Handles creation and editing of document requests by staff.
    Integrated with 'requests' table including 'completed_date' and 'created_by'.
    """

    def __init__(self, parent=None, request_id=None):
        super().__init__(parent)
        self.request_id = request_id
        self.setWindowTitle("New Document Request" if not request_id else "Edit Request")
        self.setMinimumWidth(500)
        self.setMinimumHeight(550)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Header Section ---
        header = QFrame()
        header.setObjectName("dialogHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(25, 20, 25, 20)

        # Title and subtitle
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)

        dialog_title = QLabel("New Document Request" if not request_id else "Edit Request")
        dialog_title.setObjectName("dialogTitle")

        dialog_subtitle = QLabel(
            "Create a new document request for a resident" if not request_id else "Update the document request information")
        dialog_subtitle.setObjectName("dialogSubtitle")

        title_layout.addWidget(dialog_title)
        title_layout.addWidget(dialog_subtitle)

        header_layout.addWidget(title_container)
        header_layout.addStretch()

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeButton")
        close_btn.setFixedSize(32, 32)
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)

        main_layout.addWidget(header)

        # --- Content Section ---
        content = QWidget()
        content.setObjectName("dialogContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(25, 25, 25, 25)
        content_layout.setSpacing(20)

        form = QFormLayout()
        form.setSpacing(15)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # -------------------------------
        # INPUT FIELDS
        # -------------------------------

        # Resident Name
        resident_label = QLabel("Resident Name")
        resident_label.setObjectName("fieldLabel")
        self.resident_input = QComboBox()
        self.resident_input.setObjectName("dialogComboBox")
        self.resident_input.setFixedHeight(40)
        self.load_residents()
        form.addRow(resident_label, self.resident_input)

        # Document Type
        doc_type_label = QLabel("Document Type")
        doc_type_label.setObjectName("fieldLabel")
        self.doc_type_input = QComboBox()
        self.doc_type_input.setObjectName("dialogComboBox")
        self.doc_type_input.setFixedHeight(40)
        self.doc_type_input.addItems([
            "Select document type",
            "Barangay Clearance",
            "Certificate of Residency",
            "Barangay ID",
            "Indigency Certificate",
            "Permit"
        ])
        form.addRow(doc_type_label, self.doc_type_input)

        # Purpose
        purpose_label = QLabel("Purpose")
        purpose_label.setObjectName("fieldLabel")
        self.purpose_input = QLineEdit()
        self.purpose_input.setObjectName("dialogInput")
        self.purpose_input.setPlaceholderText("Enter purpose of the document")
        form.addRow(purpose_label, self.purpose_input)

        # Request Date
        date_label = QLabel("Request Date")
        date_label.setObjectName("fieldLabel")
        self.date_input = QDateEdit()
        self.date_input.setObjectName("dialogDateEdit")
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setFixedHeight(40)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        form.addRow(date_label, self.date_input)

        # Status
        status_label = QLabel("Status")
        status_label.setObjectName("fieldLabel")
        self.status_input = QComboBox()
        self.status_input.setObjectName("dialogComboBox")
        self.status_input.setFixedHeight(40)
        self.status_input.addItems(["Pending", "In Progress", "Completed"])

        # ✅ Hide "Completed" on create mode
        if not self.request_id:
            idx = self.status_input.findText("Completed")
            if idx >= 0:
                self.status_input.removeItem(idx)

        form.addRow(status_label, self.status_input)

        content_layout.addLayout(form)
        content_layout.addStretch()

        main_layout.addWidget(content)

        # --- Footer Section ---
        footer = QFrame()
        footer.setObjectName("dialogFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(25, 15, 25, 15)
        footer_layout.setSpacing(10)

        footer_layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        footer_layout.addWidget(cancel_btn)

        # Save button
        self.save_button = QPushButton("Create Request" if not request_id else "Save Changes")
        self.save_button.setObjectName("saveButton")
        self.save_button.setFixedHeight(40)
        self.save_button.setMinimumWidth(120)
        self.save_button.clicked.connect(self.save_request)
        footer_layout.addWidget(self.save_button)

        main_layout.addWidget(footer)

        # Load QSS
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        qss_path = os.path.join(base_dir, "Styles", "staff_request_dialog.qss")

        if os.path.exists(qss_path):
            with open(qss_path, "r") as style_file:
                self.setStyleSheet(style_file.read())
        else:
            print(f"⚠️ QSS file not found at: {qss_path}")

        # -------------------------------
        # EDIT MODE
        # -------------------------------
        if request_id:
            self.load_request_data(request_id)

    # -------------------------------
    # LOAD RESIDENTS DROPDOWN (NO CHANGES)
    # -------------------------------
    def load_residents(self):
        """Populate resident dropdown with existing residents."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM residents ORDER BY name ASC")
        residents = cursor.fetchall()
        cursor.close()
        conn.close()

        self.resident_map = {}  # name -> id
        self.resident_input.addItem("Enter resident name")  # Placeholder
        for res in residents:
            self.resident_input.addItem(res["name"])
            self.resident_map[res["name"]] = res["id"]

    # -------------------------------
    # LOAD EXISTING REQUEST (Edit) (NO CHANGES)
    # -------------------------------
    def load_request_data(self, request_id):
        """Load existing request details into the form."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM requests WHERE id=%s", (request_id,))
        req = cursor.fetchone()
        cursor.close()
        conn.close()

        if req:
            for i in range(self.resident_input.count()):
                item_text = self.resident_input.itemText(i)
                if item_text in self.resident_map and self.resident_map[item_text] == req["resident_id"]:
                    self.resident_input.setCurrentIndex(i)
                    break

            self.doc_type_input.setCurrentText(req["document_type"])
            self.purpose_input.setText(req["purpose"])

            # Safely handle request date
            try:
                qdate = QDate.fromString(str(req["request_date"]).split(" ")[0], "yyyy-MM-dd")
                self.date_input.setDate(qdate if qdate.isValid() else QDate.currentDate())
            except Exception:
                self.date_input.setDate(QDate.currentDate())

            self.status_input.setCurrentText(req["status"])

    # -------------------------------
    # SAVE NEW OR UPDATED REQUEST (NO CHANGES)
    # -------------------------------
    def save_request(self):
        resident_name = self.resident_input.currentText()

        # Validation for placeholder
        if resident_name == "Enter resident name":
            QMessageBox.warning(self, "Validation Error", "Please select a resident.")
            return

        resident_id = self.resident_map.get(resident_name)

        if not resident_id:
            QMessageBox.warning(self, "Validation Error", "Please select a valid resident.")
            return

        doc_type = self.doc_type_input.currentText()

        # Validation for placeholder
        if doc_type == "Select document type":
            QMessageBox.warning(self, "Validation Error", "Please select a document type.")
            return

        purpose = self.purpose_input.text().strip()
        # FIX: Use current datetime instead of just date from calendar
        request_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = self.status_input.currentText()

        if not purpose:
            QMessageBox.warning(self, "Validation Error", "Purpose is required.")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if self.request_id:
                # Update existing - keep the original request date, only update status-related fields
                completed_date = now if status == "Completed" else None
                cursor.execute("""
                    UPDATE requests 
                    SET resident_id=%s, document_type=%s, purpose=%s, 
                        status=%s, completed_date=%s
                    WHERE id=%s
                """, (resident_id, doc_type, purpose, status, completed_date, self.request_id))
            else:
                # Insert new (include staff ID) - use current datetime for request_date
                cursor.execute("""
                    INSERT INTO requests (resident_id, document_type, purpose, request_date, status, staff_notes, created_at, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (resident_id, doc_type, purpose, request_date, status, None, now, self.parent().staff_id))

            conn.commit()
            cursor.close()
            conn.close()

            QMessageBox.information(self, "Success", "Request saved successfully.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save request:\n{e}")