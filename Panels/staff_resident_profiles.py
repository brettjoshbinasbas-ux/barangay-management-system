import os
import faulthandler
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtCore import QTimer
from functools import partial

from Panels.db import get_connection
from Panels.logger import log_staff_activity
from staff_resident_dialog import ResidentDialog

faulthandler.enable()


class StaffResidentProfiles(QWidget):
    residents_changed = pyqtSignal()

    def __init__(self, staff_id):
        super().__init__()
        self.staff_id = staff_id
        self._is_loading = False  # Prevent recursive loads

        # --- Project Paths ---
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        styles_dir = os.path.join(base_dir, "Styles")
        qss_path = os.path.join(styles_dir, "staff_resident_profiles.qss")

        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("profilesScroll")

        content = QWidget()
        content.setObjectName("profilesContent")
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

        page_title = QLabel("Resident Profiles")
        page_title.setObjectName("pageTitle")
        title_layout.addWidget(page_title)

        header_layout.addWidget(title_container, alignment=Qt.AlignmentFlag.AlignLeft)
        header_layout.addStretch()

        # Right side - Add Button and Export Buttons
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(10)

        # Export CSV Button
        self.export_csv_btn = QPushButton("📂 Export CSV")
        self.export_csv_btn.setObjectName("exportCsvButton")
        self.export_csv_btn.setFixedHeight(40)
        self.export_csv_btn.clicked.connect(self.export_to_csv)
        buttons_layout.addWidget(self.export_csv_btn)

        # Export PDF Button
        self.export_pdf_btn = QPushButton("🧾 Export PDF")
        self.export_pdf_btn.setObjectName("exportPdfButton")
        self.export_pdf_btn.setFixedHeight(40)
        self.export_pdf_btn.clicked.connect(self.export_to_pdf)
        buttons_layout.addWidget(self.export_pdf_btn)

        # Add Resident Button
        self.add_button = QPushButton("+ Add New Resident")
        self.add_button.setObjectName("addButton")
        self.add_button.setFixedHeight(40)
        self.add_button.clicked.connect(self.open_add_resident_dialog)
        buttons_layout.addWidget(self.add_button)

        header_layout.addWidget(buttons_container, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(header_frame)

        # Subtitle Section
        subtitle_container = QWidget()
        subtitle_layout = QVBoxLayout(subtitle_container)
        subtitle_layout.setContentsMargins(0, 0, 0, 0)
        subtitle_layout.setSpacing(5)

        main_subtitle = QLabel("Resident Management")
        main_subtitle.setObjectName("mainSubtitle")
        description = QLabel("Manage barangay resident information")
        description.setObjectName("description")

        subtitle_layout.addWidget(main_subtitle)
        subtitle_layout.addWidget(description)
        layout.addWidget(subtitle_container)

        # --- Table Card ---
        table_card = QFrame()
        table_card.setObjectName("tableCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(25, 25, 25, 25)
        table_layout.setSpacing(15)

        # Card Header
        card_header = QHBoxLayout()

        # Left side - List title and subtitle
        list_info = QWidget()
        list_info_layout = QVBoxLayout(list_info)
        list_info_layout.setContentsMargins(0, 0, 0, 0)
        list_info_layout.setSpacing(2)

        self.list_title = QLabel("Residents List")
        self.list_title.setObjectName("listTitle")
        self.list_subtitle = QLabel("Loading...")
        self.list_subtitle.setObjectName("listSubtitle")

        list_info_layout.addWidget(self.list_title)
        list_info_layout.addWidget(self.list_subtitle)
        card_header.addWidget(list_info)
        card_header.addStretch()

        # Right side - Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search residents...")
        self.search_bar.textChanged.connect(self.safe_filter_residents)
        self.search_bar.setObjectName("searchBar")
        self.search_bar.setFixedWidth(300)
        self.search_bar.setFixedHeight(40)
        card_header.addWidget(self.search_bar)

        table_layout.addLayout(card_header)

        # Table
        self.table = QTableWidget()
        self.table.setObjectName("residentsTable")
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Name", "Age", "Gender", "Address", "Contact",
            "Civil Status", "Employment", "Education", "Residency Years", "Actions"
        ])

        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 120)
        self.table.setColumnWidth(7, 120)
        self.table.setColumnWidth(8, 130)
        self.table.setColumnWidth(9, 180)

        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(400)

        table_layout.addWidget(self.table)
        layout.addWidget(table_card)
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

        # Load residents from DB
        QTimer.singleShot(100, self.load_residents)

    def safe_filter_residents(self, text):
        """Safe filtering with debounce to prevent rapid updates"""
        if hasattr(self, '_filter_timer'):
            self._filter_timer.stop()
        self._filter_timer = QTimer()
        self._filter_timer.setSingleShot(True)
        self._filter_timer.timeout.connect(lambda: self.load_residents(text))
        self._filter_timer.start(300)  # 300ms delay

    def clear_table(self):
        """Safely clear table contents"""
        try:
            self.table.setRowCount(0)
            # Clear any existing cell widgets to prevent memory leaks
            for row in range(self.table.rowCount()):
                widget = self.table.cellWidget(row, 9)  # Actions column
                if widget:
                    widget.deleteLater()
        except Exception as e:
            print(f"Error clearing table: {e}")

    def load_residents(self, search_query=""):
        """Load residents with proper memory management"""
        if self._is_loading:
            return

        self._is_loading = True
        try:
            conn = get_connection()
            cursor = conn.cursor()

            if search_query:
                cursor.execute(
                    "SELECT * FROM residents WHERE name LIKE %s OR address LIKE %s",
                    (f"%{search_query}%", f"%{search_query}%")
                )
            else:
                cursor.execute("SELECT * FROM residents")

            residents = cursor.fetchall()
            cursor.close()
            conn.close()

            # Clear table safely
            self.clear_table()
            self.table.setRowCount(len(residents))

            for row, resident in enumerate(residents):
                # Name
                name_item = QTableWidgetItem(resident["name"])
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 0, name_item)

                # Age
                age_item = QTableWidgetItem(str(resident["age"]))
                age_item.setFlags(age_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                age_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 1, age_item)

                # Gender
                gender_item = QTableWidgetItem(resident["gender"])
                gender_item.setFlags(gender_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                gender_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 2, gender_item)

                # Address
                address_item = QTableWidgetItem(resident["address"])
                address_item.setFlags(address_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 3, address_item)

                # Contact
                contact_item = QTableWidgetItem(resident["contact_number"])
                contact_item.setFlags(contact_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 4, contact_item)

                # Civil Status
                civil_status_item = QTableWidgetItem(resident.get("civil_status", ""))
                civil_status_item.setFlags(civil_status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                civil_status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 5, civil_status_item)

                # Employment Status
                employment_item = QTableWidgetItem(resident.get("employment_status", ""))
                employment_item.setFlags(employment_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                employment_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 6, employment_item)

                # Education Level
                education_item = QTableWidgetItem(resident.get("education_level", ""))
                education_item.setFlags(education_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                education_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 7, education_item)

                # Residency Years
                residency_item = QTableWidgetItem(str(resident.get("residency_years", "")))
                residency_item.setFlags(residency_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                residency_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 8, residency_item)

                # Actions column
                actions = QWidget()
                actions_layout = QHBoxLayout(actions)
                actions_layout.setContentsMargins(5, 5, 5, 5)
                actions_layout.setSpacing(8)

                btn_edit = QPushButton("✏️")
                btn_edit.setObjectName("editButton")
                btn_edit.setFixedSize(50, 28)
                btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_edit.setToolTip("Edit resident")
                btn_edit.clicked.connect(partial(self.open_edit_resident_dialog, resident["id"]))

                btn_delete = QPushButton("🗑️")
                btn_delete.setObjectName("deleteButton")
                btn_delete.setFixedSize(50, 28)
                btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_delete.setToolTip("Delete resident")
                btn_delete.clicked.connect(partial(self.delete_resident, resident["id"]))

                actions_layout.addWidget(btn_edit)
                actions_layout.addWidget(btn_delete)
                actions_layout.addStretch()
                self.table.setCellWidget(row, 9, actions)

                # Set row height
                self.table.setRowHeight(row, 65)

            self.list_subtitle.setText(f"Total of {len(residents)} registered residents")

        except Exception as e:
            print(f"Error loading residents: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to load residents:\n{e}")
        finally:
            self._is_loading = False

    def open_add_resident_dialog(self):
        """Open add resident dialog with proper user_id"""
        try:
            dialog = ResidentDialog(self, user_id=self.staff_id)
            dialog.setModal(True)
            if dialog.exec():
                # Use delayed signal to prevent recursion
                QTimer.singleShot(100, self.delayed_refresh)
        except Exception as e:
            print(f"Error opening add dialog: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open dialog:\n{e}")

    def open_edit_resident_dialog(self, resident_id):
        """Open edit resident dialog with proper user_id"""
        try:
            dialog = ResidentDialog(self, resident_id, user_id=self.staff_id)
            dialog.setModal(True)
            if dialog.exec():
                # Use delayed signal to prevent recursion
                QTimer.singleShot(100, self.delayed_refresh)
        except Exception as e:
            print(f"Error opening edit dialog: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open dialog:\n{e}")

    def delayed_refresh(self):
        """Delayed refresh to prevent signal recursion"""
        self.load_residents()
        # Emit signal with delay to break any potential recursion
        QTimer.singleShot(50, self.residents_changed.emit)

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
        """Delete resident with confirmation and request check"""

        # Check if resident has requests
        if self.resident_has_requests(resident_id):
            QMessageBox.warning(
                self,
                "Delete Blocked",
                "This resident has active document requests.\n\n"
                "Please delete those requests first before removing the resident.",
                QMessageBox.StandardButton.Ok
            )
            return

        # If no requests, proceed with normal deletion
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this resident?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM residents WHERE id = %s", (resident_id,))
                conn.commit()
                cursor.close()
                conn.close()

                self.load_residents()
                self.residents_changed.emit()
                log_staff_activity(self.staff_id, "DELETE_RESIDENT", f"Deleted resident {resident_id}", role="Staff")

            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to delete resident:\n{e}")

    # --- CSV Export ---
    def export_to_csv(self):
        import csv
        from datetime import datetime

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM residents ORDER BY created_at DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        export_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(export_dir, exist_ok=True)
        filename = os.path.join(export_dir, f"residents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Age", "Gender", "Address", "Contact", "Civil Status", "Employment", "Education",
                             "Residency Years", "Status"])
            for r in rows:
                writer.writerow([
                    r["name"], r["age"], r["gender"], r["address"], r["contact_number"], r["civil_status"],
                    r["employment_status"], r["education_level"], r["residency_years"], r["status"]
                ])

        QMessageBox.information(self, "Export Successful", f"Residents exported to:\n{filename}")

    # --- PDF Export ---
    def export_to_pdf(self):
        from datetime import datetime
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM residents ORDER BY created_at DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        export_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(export_dir, exist_ok=True)
        filename = os.path.join(export_dir, f"residents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

        c = canvas.Canvas(filename, pagesize=landscape(letter))
        width, height = landscape(letter)

        c.setFont("Helvetica-Bold", 16)
        c.drawString(1 * inch, height - 0.75 * inch, "Barangay Resident Directory")

        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, height - 1 * inch, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        y = height - 1.5 * inch
        headers = ["Name", "Age", "Gender", "Address", "Contact", "Civil Status", "Employment", "Status"]
        x_positions = [0.5, 2.0, 2.5, 3.0, 5.5, 6.5, 7.5, 8.5]

        c.setFont("Helvetica-Bold", 10)
        for i, h in enumerate(headers):
            c.drawString(x_positions[i] * inch, y, h)

        y -= 0.25 * inch
        c.setFont("Helvetica", 8)  # Smaller font to fit more columns
        for r in rows:
            if y < 1 * inch:
                c.showPage()
                y = height - 1 * inch
                c.setFont("Helvetica", 8)
            c.drawString(x_positions[0] * inch, y, r["name"][:20])  # Truncate long names
            c.drawString(x_positions[1] * inch, y, str(r["age"]))
            c.drawString(x_positions[2] * inch, y, r["gender"])
            c.drawString(x_positions[3] * inch, y, r["address"][:25])  # Truncate address
            c.drawString(x_positions[4] * inch, y, r["contact_number"][:15])
            c.drawString(x_positions[5] * inch, y, r.get("civil_status", "")[:12])
            c.drawString(x_positions[6] * inch, y, r.get("employment_status", "")[:12])
            c.drawString(x_positions[7] * inch, y, r["status"])
            y -= 0.25 * inch

        c.save()
        QMessageBox.information(self, "Export Successful", f"PDF generated:\n{filename}")