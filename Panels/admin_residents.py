import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QComboBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal  # ⬅️ ADD pyqtSignal
from PyQt6.QtGui import QColor, QFont
from Panels.db import get_connection
from Panels.logger import log_admin_activity
from functools import partial
from datetime import datetime


class AdminResidents(QWidget):
    residents_changed = pyqtSignal()  # ⬅️ ADD THIS SIGNAL

    def __init__(self, admin_id):
        super().__init__()
        self.admin_id = admin_id
        self.load_stylesheet()
        self.init_ui()
        self.load_staff_filter()
        self.load_residents()

    def load_stylesheet(self):
        """Load the external QSS stylesheet using standard project paths"""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            styles_dir = os.path.join(base_dir, "Styles")
            qss_path = os.path.join(styles_dir, "admin_residents.qss")

            if os.path.exists(qss_path):
                with open(qss_path, "r") as style_file:
                    self.setStyleSheet(style_file.read())
            else:
                print(f"⚠️ QSS file not found at: {qss_path}")

        except Exception as e:
            print(f"Error loading stylesheet: {e}")

    def init_ui(self):
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("residentsScroll")

        content = QWidget()
        content.setObjectName("residentsContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)

        # --- Header Section ---
        header_frame = QFrame()
        header_frame.setObjectName("headerSection")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Left side - Title
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)

        page_title = QLabel("Resident Directory")
        page_title.setObjectName("pageTitle")
        title_layout.addWidget(page_title)

        header_layout.addWidget(title_container, alignment=Qt.AlignmentFlag.AlignLeft)
        header_layout.addStretch()

        # Right side - Export buttons
        export_layout = QHBoxLayout()
        export_layout.setSpacing(10)

        self.export_csv_btn = QPushButton("📂 Export CSV")
        self.export_csv_btn.setObjectName("exportButton")
        self.export_csv_btn.clicked.connect(self.export_to_csv)

        self.export_pdf_btn = QPushButton("🧾 Export PDF")
        self.export_pdf_btn.setObjectName("exportButton")
        self.export_pdf_btn.clicked.connect(self.export_to_pdf)

        export_layout.addWidget(self.export_csv_btn)
        export_layout.addWidget(self.export_pdf_btn)

        header_layout.addLayout(export_layout)

        layout.addWidget(header_frame)

        # --- Subtitle Section ---
        subtitle_container = QWidget()
        subtitle_layout = QVBoxLayout(subtitle_container)
        subtitle_layout.setContentsMargins(0, 0, 0, 0)
        subtitle_layout.setSpacing(5)

        main_subtitle = QLabel("Admin Management")
        main_subtitle.setObjectName("mainSubtitle")

        description = QLabel("View, filter, and manage all registered residents")
        description.setObjectName("description")

        subtitle_layout.addWidget(main_subtitle)
        subtitle_layout.addWidget(description)

        layout.addWidget(subtitle_container)

        # --- Resident Management Table Card ---
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

        list_title = QLabel("Resident Management")
        list_title.setObjectName("listTitle")

        list_subtitle = QLabel("View and manage resident records")
        list_subtitle.setObjectName("listSubtitle")

        list_info_layout.addWidget(list_title)
        list_info_layout.addWidget(list_subtitle)

        card_header.addWidget(list_info)
        card_header.addStretch()

        table_layout.addLayout(card_header)

        # --- Filters Row ---
        filters_row = QHBoxLayout()
        filters_row.setSpacing(10)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search residents by name or address...")
        self.search_bar.setObjectName("searchBar")
        self.search_bar.textChanged.connect(self.filter_residents)
        filters_row.addWidget(self.search_bar)

        self.staff_filter = QComboBox()
        self.staff_filter.setObjectName("staffFilter")
        self.staff_filter.addItem("All Staff")
        self.staff_filter.currentTextChanged.connect(self.filter_residents)
        self.staff_filter.setFixedWidth(200)
        filters_row.addWidget(self.staff_filter)

        table_layout.addLayout(filters_row)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setObjectName("residentsTable")
        # Updated to 11 columns to match the old version
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "Name", "Age", "Gender", "Address", "Contact", "Civil Status",
            "Employment", "Education", "Residency Years", "Added By", "Actions"
        ])

        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(1, header.ResizeMode.Fixed)    # Age
        header.setSectionResizeMode(2, header.ResizeMode.Fixed)    # Gender
        header.setSectionResizeMode(3, header.ResizeMode.Stretch)  # Address
        header.setSectionResizeMode(4, header.ResizeMode.Fixed)    # Contact
        header.setSectionResizeMode(5, header.ResizeMode.Fixed)    # Civil Status
        header.setSectionResizeMode(6, header.ResizeMode.Fixed)    # Employment
        header.setSectionResizeMode(7, header.ResizeMode.Fixed)    # Education
        header.setSectionResizeMode(8, header.ResizeMode.Fixed)    # Residency Years
        header.setSectionResizeMode(9, header.ResizeMode.Fixed)    # Added By
        header.setSectionResizeMode(10, header.ResizeMode.Fixed)   # Actions

        self.table.setColumnWidth(1, 80)   # Age
        self.table.setColumnWidth(2, 100)  # Gender
        self.table.setColumnWidth(4, 150)  # Contact
        self.table.setColumnWidth(5, 120)  # Civil Status
        self.table.setColumnWidth(6, 150)  # Employment
        self.table.setColumnWidth(7, 120)  # Education
        self.table.setColumnWidth(8, 140)  # Residency Years
        self.table.setColumnWidth(9, 150)  # Added By
        self.table.setColumnWidth(10, 120) # Actions

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

    # ---------------------------------------
    # Load staff filter dropdown (NO CHANGES)
    # ---------------------------------------
    def load_staff_filter(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM staff ORDER BY username ASC")
        staff_list = cursor.fetchall()
        cursor.close()
        conn.close()

        for s in staff_list:
            self.staff_filter.addItem(f"{s['username']} (ID: {s['id']})", s['id'])

    # ---------------------------------------
    # Load all residents (NO CHANGES TO LOGIC)
    # ---------------------------------------
    def load_residents(self, search_query="", staff_filter=None):
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT r.*, s.username AS added_by
            FROM residents r
            LEFT JOIN staff s ON r.created_by = s.id
            WHERE 1=1
        """
        params = []

        if search_query:
            query += " AND (r.name LIKE %s OR r.address LIKE %s)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])

        if staff_filter and staff_filter != "All Staff":
            query += " AND r.created_by = %s"
            params.append(staff_filter)

        query += " ORDER BY r.created_at DESC"
        cursor.execute(query, params)
        residents = cursor.fetchall()

        cursor.close()
        conn.close()

        self.populate_table(residents)

    # ---------------------------------------
    # Populate table - UPDATED FOR ALL COLUMNS
    # ---------------------------------------
    def populate_table(self, residents):
        self.table.setRowCount(len(residents))

        for row, r in enumerate(residents):
            # Name
            name_item = QTableWidgetItem(r["name"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, name_item)

            # Age with color coding for seniors
            age_item = QTableWidgetItem(str(r["age"]))
            age_item.setFlags(age_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            age_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if r["age"] >= 60:
                age_item.setForeground(QColor(231, 76, 60))  # Red for seniors
            self.table.setItem(row, 1, age_item)

            # Gender with color coding
            gender_item = QTableWidgetItem(r["gender"])
            gender_item.setFlags(gender_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            gender_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if r["gender"].lower() == "female":
                gender_item.setForeground(QColor(155, 89, 182))  # Purple
            else:
                gender_item.setForeground(QColor(52, 152, 219))  # Blue
            self.table.setItem(row, 2, gender_item)

            # Address
            address_item = QTableWidgetItem(r["address"])
            address_item.setFlags(address_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, address_item)

            # Contact
            contact_item = QTableWidgetItem(r["contact_number"])
            contact_item.setFlags(contact_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            contact_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, contact_item)

            # Civil Status
            civil_status_item = QTableWidgetItem(r["civil_status"])
            civil_status_item.setFlags(civil_status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            civil_status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, civil_status_item)

            # Employment Status
            employment_item = QTableWidgetItem(r["employment_status"])
            employment_item.setFlags(employment_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            employment_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, employment_item)

            # Education Level
            education_item = QTableWidgetItem(r["education_level"])
            education_item.setFlags(education_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            education_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 7, education_item)

            # Residency Years
            residency_item = QTableWidgetItem(str(r["residency_years"]))
            residency_item.setFlags(residency_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            residency_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 8, residency_item)

            # Added By
            added_by_item = QTableWidgetItem(r.get("added_by", "Unknown"))
            added_by_item.setFlags(added_by_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            added_by_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 9, added_by_item)

            # --- Actions - USING THE WORKING APPROACH FROM StaffRequests ---
            actions = QFrame()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(8, 5, 8, 5)  # Same as working module
            actions_layout.setSpacing(6)  # Same as working module
            actions_layout.addStretch()

            # Edit Button - using same approach as working module
            edit_btn = QPushButton("✏️")
            edit_btn.setFont(QFont("Segoe UI", 12))
            edit_btn.setFixedSize(32, 23)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.setToolTip("Edit resident")
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F1F5F9;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #E2E8F0;
                }
            """)
            edit_btn.clicked.connect(partial(self.edit_resident, r["id"]))
            actions_layout.addWidget(edit_btn)

            # Delete button - using same approach as working module
            delete_btn = QPushButton("🗑️")
            delete_btn.setFont(QFont("Segoe UI", 12))
            delete_btn.setFixedSize(32, 23)
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_btn.setToolTip("Delete resident")
            delete_btn.setStyleSheet("""
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
            delete_btn.clicked.connect(partial(self.delete_resident, r["id"]))
            actions_layout.addWidget(delete_btn)

            actions_layout.addStretch()
            self.table.setCellWidget(row, 10, actions)

            # Set row height like the working module
            self.table.setRowHeight(row, 60)

    # ---------------------------------------
    # Filtering (NO CHANGES)
    # ---------------------------------------
    def filter_residents(self):
        search = self.search_bar.text().strip()
        staff_label = self.staff_filter.currentText()

        if staff_label == "All Staff":
            staff_id = None
        else:
            staff_id = int(staff_label.split("ID: ")[1].replace(")", ""))

        self.load_residents(search_query=search, staff_filter=staff_id)

    # ---------------------------------------
    # Edit Resident (NO CHANGES)
    # ---------------------------------------
    def edit_resident(self, resident_id):
        try:
            from staff_resident_dialog import ResidentDialog
            dialog = ResidentDialog(self, resident_id=resident_id, role="Admin", user_id=self.admin_id)
            dialog.setModal(True)
            if dialog.exec():
                self.load_residents()
                self.residents_changed.emit()  # ⬅️ ADD THIS
                log_admin_activity(self.admin_id, "EDIT_RESIDENT", f"Edited resident ID {resident_id}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit resident:\n{e}")

    def resident_has_requests(self, resident_id):
        """Check if resident has any requests"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as request_count FROM requests WHERE resident_id = %s", (resident_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result["request_count"] > 0

    def delete_resident(self, resident_id):
        """Delete resident with request check"""

        # Check if resident has requests
        if self.resident_has_requests(resident_id):
            QMessageBox.warning(
                self,
                "Cannot Delete Resident",
                "This resident has active document requests.\n\n"
                "Please delete their requests first before removing the resident.",
                QMessageBox.StandardButton.Ok
            )
            return

        # If no requests, proceed with normal deletion
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to permanently delete this resident?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM residents WHERE id=%s", (resident_id,))
                conn.commit()
                cursor.close()
                conn.close()

                log_admin_activity(self.admin_id, "DELETE_RESIDENT", f"Deleted resident ID {resident_id}")
                self.load_residents()
                self.residents_changed.emit()
                QMessageBox.information(self, "Deleted", "Resident removed successfully.")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Database error:\n{e}")

    # ---------------------------------------
    # File Handling: Export CSV (NO CHANGES)
    # ---------------------------------------
    def export_to_csv(self):
        import csv
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, s.username AS added_by
            FROM residents r
            LEFT JOIN staff s ON r.created_by = s.id
            ORDER BY r.created_at DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        export_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(export_dir, exist_ok=True)
        filename = os.path.join(export_dir, f"residents_admin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Age", "Gender", "Address", "Contact", "Civil Status",
                             "Employment", "Education", "Residency Years", "Added By"])
            for r in rows:
                writer.writerow([
                    r["name"], r["age"], r["gender"], r["address"], r["contact_number"],
                    r["civil_status"], r["employment_status"], r["education_level"],
                    r["residency_years"], r.get("added_by", "Unknown")
                ])

        QMessageBox.information(self, "Export Successful", f"Residents exported to:\n{filename}")

    # ---------------------------------------
    # File Handling: Export PDF (NO CHANGES)
    # ---------------------------------------
    def export_to_pdf(self):
        from reportlab.lib.pagesizes import landscape, letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, s.username AS added_by
            FROM residents r
            LEFT JOIN staff s ON r.created_by = s.id
            ORDER BY r.created_at DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        export_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(export_dir, exist_ok=True)
        filename = os.path.join(export_dir, f"residents_admin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

        c = canvas.Canvas(filename, pagesize=landscape(letter))
        width, height = landscape(letter)

        c.setFont("Helvetica-Bold", 16)
        c.drawString(1 * inch, height - 0.75 * inch, "Barangay Residents Report (Admin Copy)")

        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, height - 1 * inch, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        y = height - 1.5 * inch
        headers = ["Name", "Gender", "Address", "Added By"]
        x_positions = [0.5, 2.5, 4.0, 7.0]

        c.setFont("Helvetica-Bold", 10)
        for i, h in enumerate(headers):
            c.drawString(x_positions[i] * inch, y, h)

        y -= 0.25 * inch
        c.setFont("Helvetica", 9)
        for r in rows:
            if y < 1 * inch:
                c.showPage()
                y = height - 1 * inch
                c.setFont("Helvetica", 9)
            c.drawString(x_positions[0] * inch, y, r["name"])
            c.drawString(x_positions[1] * inch, y, r["gender"])
            c.drawString(x_positions[2] * inch, y, r["address"][:40])
            c.drawString(x_positions[3] * inch, y, r.get("added_by", "Unknown"))
            y -= 0.25 * inch

        c.save()
        QMessageBox.information(self, "Export Successful", f"PDF generated:\n{filename}")