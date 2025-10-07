import os
import csv
from datetime import datetime
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy, QMessageBox, QScrollArea
)
from PyQt6.QtGui import QColor, QFont
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

from Panels.db import get_connection
from Panels.logger import log_admin_activity


class AdminRequests(QWidget):
    requests_changed = pyqtSignal()

    def __init__(self, admin_id):
        super().__init__()
        self.admin_id = admin_id
        self.load_stylesheet()
        self.init_ui()
        self.load_requests()

    def load_stylesheet(self):
        """Load the external QSS stylesheet using standard project paths"""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            styles_dir = os.path.join(base_dir, "Styles")
            qss_path = os.path.join(styles_dir, "admin_requests.qss")

            if os.path.exists(qss_path):
                with open(qss_path, "r", encoding="utf-8") as style_file:
                    self.setStyleSheet(style_file.read())
            else:
                print(f"⚠️ QSS file not found at: {qss_path}")

        except Exception as e:
            print(f"Error loading stylesheet: {e}")

    # -----------------------------
    # UI Setup
    # -----------------------------
    def init_ui(self):
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("requestsScroll")

        content = QWidget()
        content.setObjectName("requestsContent")
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

        page_title = QLabel("Requests")
        page_title.setObjectName("pageTitle")
        title_layout.addWidget(page_title)

        header_layout.addWidget(title_container, alignment=Qt.AlignmentFlag.AlignLeft)
        header_layout.addStretch()

        # REMOVED: "+ New Request" button as requested

        layout.addWidget(header_frame)

        # --- Subtitle Section ---
        subtitle_container = QWidget()
        subtitle_layout = QVBoxLayout(subtitle_container)
        subtitle_layout.setContentsMargins(0, 0, 0, 0)
        subtitle_layout.setSpacing(5)

        main_subtitle = QLabel("Document Requests")
        main_subtitle.setObjectName("mainSubtitle")

        description = QLabel("Manage barangay requests")
        description.setObjectName("description")

        subtitle_layout.addWidget(main_subtitle)
        subtitle_layout.addWidget(description)

        layout.addWidget(subtitle_container)

        # --- Metrics Card ---
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(20)

        self.accepted_card = self.create_metric_card("Accepted", "0", "✓", "#10B981")
        metrics_row.addWidget(self.accepted_card)
        metrics_row.addStretch()

        layout.addLayout(metrics_row)

        # --- Document Requests Table Card ---
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

        list_title = QLabel("Document Requests")
        list_title.setObjectName("listTitle")

        list_subtitle = QLabel("All document requests with their current status")
        list_subtitle.setObjectName("listSubtitle")

        list_info_layout.addWidget(list_title)
        list_info_layout.addWidget(list_subtitle)

        card_header.addWidget(list_info)
        card_header.addStretch()

        # Right side - Filter and Export buttons
        filters_row = QHBoxLayout()
        filters_row.setSpacing(10)

        self.filter_box = QComboBox()
        self.filter_box.setObjectName("filterDropdown")
        self.filter_box.addItems(["All", "Pending", "In Progress", "Completed", "Rejected"])
        self.filter_box.currentTextChanged.connect(self.load_requests)
        self.filter_box.setFixedWidth(150)
        filters_row.addWidget(self.filter_box)

        btn_export_csv = QPushButton("📂 Export CSV")
        btn_export_csv.setObjectName("exportButton")
        btn_export_csv.clicked.connect(self.export_to_csv)
        filters_row.addWidget(btn_export_csv)

        btn_export_pdf = QPushButton("🧾 Export PDF")
        btn_export_pdf.setObjectName("exportButton")
        btn_export_pdf.clicked.connect(self.export_to_pdf)
        filters_row.addWidget(btn_export_pdf)

        card_header.addLayout(filters_row)

        table_layout.addLayout(card_header)

        # --- Table - FIXED: Added Completed Date column (8 total columns now) ---
        self.table = QTableWidget()
        self.table.setObjectName("requestsTable")
        self.table.setColumnCount(8)  # Changed from 7 to 8
        self.table.setHorizontalHeaderLabels([
            "Resident", "Document Type", "Purpose", "Request Date", "Status",
            "Completed Date", "Handled By", "Actions"  # Added Completed Date
        ])

        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.Stretch)  # Resident
        header.setSectionResizeMode(1, header.ResizeMode.Fixed)    # Document Type
        header.setSectionResizeMode(2, header.ResizeMode.Stretch)  # Purpose
        header.setSectionResizeMode(3, header.ResizeMode.Fixed)    # Request Date
        header.setSectionResizeMode(4, header.ResizeMode.Fixed)    # Status
        header.setSectionResizeMode(5, header.ResizeMode.Fixed)    # Completed Date - NEW
        header.setSectionResizeMode(6, header.ResizeMode.Fixed)    # Handled By
        header.setSectionResizeMode(7, header.ResizeMode.Fixed)    # Actions

        self.table.setColumnWidth(1, 250)  # Document Type
        self.table.setColumnWidth(3, 200)  # Request Date
        self.table.setColumnWidth(4, 120)  # Status
        self.table.setColumnWidth(5, 250)  # Completed Date - NEW
        self.table.setColumnWidth(6, 150)  # Handled By
        self.table.setColumnWidth(7, 150)  # Actions

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
        """Update metric card with accepted count"""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM requests WHERE status='Completed'")
        accepted_count = cursor.fetchone()["total"]

        cursor.close()
        conn.close()

        # Update card
        accepted_value = self.accepted_card.findChild(QLabel, "metricValue")
        if accepted_value:
            accepted_value.setText(str(accepted_count))

    # -----------------------------
    # Load Data - UPDATED FOR NEW COLUMNS
    # -----------------------------
    def load_requests(self):
        """Fetch requests from DB, optionally filtered."""
        conn = get_connection()
        cursor = conn.cursor()

        filter_status = self.filter_box.currentText()

        base_query = """
            SELECT r.id, res.name AS resident_name, r.document_type, r.purpose,
                   r.request_date, r.status, r.completed_date, s.username AS handled_by
            FROM requests r
            JOIN residents res ON r.resident_id = res.id
            LEFT JOIN staff s ON r.created_by = s.id
        """

        if filter_status == "All":
            cursor.execute(base_query + " ORDER BY r.request_date DESC")
        else:
            cursor.execute(base_query + " WHERE r.status=%s ORDER BY r.request_date DESC", (filter_status,))

        requests = cursor.fetchall()
        cursor.close()
        conn.close()

        # Populate table
        self.table.setRowCount(len(requests))
        for row, req in enumerate(requests):
            # Resident name with icon
            resident_widget = QWidget()
            resident_layout = QHBoxLayout(resident_widget)
            resident_layout.setContentsMargins(10, 5, 10, 5)
            resident_layout.setSpacing(8)

            person_icon = QLabel("👤")
            person_icon.setFixedWidth(20)
            resident_name = QLabel(req["resident_name"])
            resident_name.setObjectName("residentName")

            resident_layout.addWidget(person_icon)
            resident_layout.addWidget(resident_name)
            resident_layout.addStretch()

            self.table.setCellWidget(row, 0, resident_widget)

            # Document type with icon
            doc_widget = QWidget()
            doc_layout = QHBoxLayout(doc_widget)
            doc_layout.setContentsMargins(10, 5, 10, 5)
            doc_layout.setSpacing(8)

            doc_icon = QLabel("📄")
            doc_icon.setFixedWidth(20)
            doc_type = QLabel(req["document_type"])
            doc_type.setObjectName("docType")

            doc_layout.addWidget(doc_icon)
            doc_layout.addWidget(doc_type)
            doc_layout.addStretch()

            self.table.setCellWidget(row, 1, doc_widget)

            # Purpose
            purpose_item = QTableWidgetItem(req["purpose"])
            purpose_item.setFlags(purpose_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, purpose_item)

            # ✅ FIXED: Request date with proper formatting including seconds
            date_widget = QWidget()
            date_layout = QHBoxLayout(date_widget)
            date_layout.setContentsMargins(10, 5, 10, 5)
            date_layout.setSpacing(8)

            calendar_icon = QLabel("📅")
            calendar_icon.setFixedWidth(20)

            # Format request date with seconds if it's a datetime
            if req["request_date"]:
                if hasattr(req["request_date"], 'strftime'):  # It's a datetime object
                    request_date_str = req["request_date"].strftime("%Y-%m-%d %H:%M:%S")
                else:  # It's already a string
                    request_date_str = str(req["request_date"])
            else:
                request_date_str = "N/A"

            date_label = QLabel(request_date_str)
            date_label.setObjectName("dateLabel")

            date_layout.addWidget(calendar_icon)
            date_layout.addWidget(date_label)
            date_layout.addStretch()

            self.table.setCellWidget(row, 3, date_widget)

            # --- Status Column ---
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(0, 0, 0, 0)
            status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            status_label = QLabel(req["status"])
            status_label.setObjectName("statusBadge")
            status_label.setProperty("statusType", req["status"].lower().replace(" ", "_"))
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_label.setMinimumWidth(80)
            status_label.setMaximumWidth(100)

            status_layout.addWidget(status_label)
            self.table.setCellWidget(row, 4, status_widget)

            # ✅ FIXED: Completed Date with proper formatting including seconds
            completed_date_widget = QWidget()
            completed_date_layout = QHBoxLayout(completed_date_widget)
            completed_date_layout.setContentsMargins(10, 5, 10, 5)
            completed_date_layout.setSpacing(8)

            completed_icon = QLabel("✅")
            completed_icon.setFixedWidth(20)

            # Format completed date with seconds if it exists
            if req["completed_date"]:
                if hasattr(req["completed_date"], 'strftime'):  # It's a datetime object
                    completed_date_str = req["completed_date"].strftime("%Y-%m-%d %H:%M:%S")
                else:  # It's already a string
                    completed_date_str = str(req["completed_date"])
            else:
                completed_date_str = "—"

            completed_date_label = QLabel(completed_date_str)
            completed_date_label.setObjectName("dateLabel")

            completed_date_layout.addWidget(completed_icon)
            completed_date_layout.addWidget(completed_date_label)
            completed_date_layout.addStretch()

            self.table.setCellWidget(row, 5, completed_date_widget)

            # --- Handled By Column ---
            handled_by_item = QTableWidgetItem(req["handled_by"] or "—")
            handled_by_item.setFlags(handled_by_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            handled_by_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, handled_by_item)

            # --- Actions Column ---
            actions_frame = QFrame()
            actions_layout = QHBoxLayout(actions_frame)
            actions_layout.setContentsMargins(8, 5, 8, 5)
            actions_layout.setSpacing(6)
            actions_layout.addStretch()

            if req["status"] in ["Pending", "In Progress"]:
                # Approve button
                btn_approve = QPushButton("✓")
                btn_approve.setFont(QFont("Segoe UI", 12))
                btn_approve.setFixedSize(32, 25)
                btn_approve.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_approve.setToolTip("Approve request")
                btn_approve.setStyleSheet("""
                    QPushButton {
                        background-color: #D1FAE5;
                        border: 1px solid #A7F3D0;
                        border-radius: 6px;
                        color: #065F46;
                    }
                    QPushButton:hover {
                        background-color: #A7F3D0;
                    }
                """)
                btn_approve.clicked.connect(lambda _, rid=req["id"]: self.approve_request(rid))
                actions_layout.addWidget(btn_approve)

                # Reject button
                btn_reject = QPushButton("✗")
                btn_reject.setFont(QFont("Segoe UI", 12))
                btn_reject.setFixedSize(32, 25)
                btn_reject.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_reject.setToolTip("Reject request")
                btn_reject.setStyleSheet("""
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
                btn_reject.clicked.connect(lambda _, rid=req["id"]: self.reject_request(rid))
                actions_layout.addWidget(btn_reject)

            elif req["status"] == "Completed":
                # Reopen button
                btn_reopen = QPushButton("🔁")
                btn_reopen.setFont(QFont("Segoe UI", 12))
                btn_reopen.setFixedSize(32, 25)
                btn_reopen.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_reopen.setToolTip("Reopen request")
                btn_reopen.setStyleSheet("""
                    QPushButton {
                        background-color: #FEF3C7;
                        border: 1px solid #FDE68A;
                        border-radius: 6px;
                        color: #92400E;
                    }
                    QPushButton:hover {
                        background-color: #FDE68A;
                    }
                """)
                btn_reopen.clicked.connect(lambda _, rid=req["id"]: self.reopen_request(rid))
                actions_layout.addWidget(btn_reopen)

            actions_layout.addStretch()
            self.table.setCellWidget(row, 7, actions_frame)  # Changed from 6 to 7
            self.table.setRowHeight(row, 60)

        self.update_metrics()

    # -----------------------------
    # Admin Actions (NO CHANGES TO LOGIC)
    # -----------------------------
    def approve_request(self, request_id):
        reply = QMessageBox.question(
            self, "Approve Request", "Approve this request as completed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            conn = get_connection()
            cursor = conn.cursor()
            completed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "UPDATE requests SET status='Completed', completed_date=%s WHERE id=%s",
                (completed_time, request_id)
            )
            conn.commit()
            cursor.close()
            conn.close()

            log_admin_activity(self.admin_id, "APPROVE_REQUEST", f"Approved request {request_id}")
            QMessageBox.information(self, "Approved", "Request marked as completed.")
            self.load_requests()
            self.requests_changed.emit()

    def reject_request(self, request_id):
        reply = QMessageBox.question(
            self, "Reject Request", "Reject this request?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE requests SET status='Rejected' WHERE id=%s", (request_id,))
            conn.commit()
            cursor.close()
            conn.close()

            log_admin_activity(self.admin_id, "REJECT_REQUEST", f"Rejected request {request_id}")
            QMessageBox.warning(self, "Rejected", "Request has been rejected.")
            self.load_requests()
            self.requests_changed.emit()

    def reopen_request(self, request_id):
        reply = QMessageBox.question(
            self, "Reopen Request", "Reopen this request for reprocessing?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE requests SET status='In Progress', completed_date=NULL WHERE id=%s", (request_id,))
            conn.commit()
            cursor.close()
            conn.close()

            log_admin_activity(self.admin_id, "REOPEN_REQUEST", f"Reopened request {request_id}")
            QMessageBox.information(self, "Reopened", "Request set back to 'In Progress'.")
            self.load_requests()
            self.requests_changed.emit()

    # -----------------------------
    # File Handling (NO CHANGES TO LOGIC)
    # -----------------------------
    def export_to_csv(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, res.name AS resident, r.document_type, r.purpose,
                   r.request_date, r.status, r.completed_date, s.username AS handled_by
            FROM requests r
            JOIN residents res ON r.resident_id = res.id
            LEFT JOIN staff s ON r.created_by = s.id
            ORDER BY r.created_at DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        export_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(export_dir, exist_ok=True)
        filename = os.path.join(export_dir, f"requests_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Resident", "Document Type", "Purpose", "Request Date", "Status",
                "Completed Date", "Handled By"
            ])
            for row in rows:
                # ✅ FIXED: Format dates properly for CSV export
                request_date = row["request_date"]
                if request_date and hasattr(request_date, 'strftime'):
                    request_date_str = request_date.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    request_date_str = str(request_date) if request_date else ""

                completed_date = row["completed_date"]
                if completed_date and hasattr(completed_date, 'strftime'):
                    completed_date_str = completed_date.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    completed_date_str = str(completed_date) if completed_date else ""

                writer.writerow([
                    row["resident"],
                    row["document_type"],
                    row["purpose"],
                    request_date_str,
                    row["status"],
                    completed_date_str,
                    row["handled_by"] or ""
                ])

        QMessageBox.information(self, "Export Successful", f"Requests exported to:\n{filename}")
        log_admin_activity(self.admin_id, "EXPORT_REQUESTS", "Exported all requests to CSV.")

    def export_to_pdf(self):
        """Exports all requests to a PDF report (official format)."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, res.name AS resident, r.document_type, r.purpose,
                   r.request_date, r.status, r.completed_date, s.username AS handled_by
            FROM requests r
            JOIN residents res ON r.resident_id = res.id
            LEFT JOIN staff s ON r.created_by = s.id
            ORDER BY r.created_at DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        export_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(export_dir, exist_ok=True)
        filename = os.path.join(export_dir, f"requests_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

        c = canvas.Canvas(filename, pagesize=landscape(letter))
        width, height = landscape(letter)

        c.setFont("Helvetica-Bold", 16)
        c.drawString(1 * inch, height - 0.75 * inch, "Barangay Document Requests Report")

        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, height - 1.05 * inch, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        headers = ["Resident", "Document Type", "Purpose", "Request Date", "Status", "Completed Date", "Handled By"]
        x_positions = [0.5, 2.0, 3.5, 5.0, 6.5, 7.5, 8.5]
        y = height - 1.5 * inch

        c.setFont("Helvetica-Bold", 10)
        for i, h in enumerate(headers):
            c.drawString(x_positions[i] * inch, y, h)

        c.line(0.5 * inch, y - 2, 10.5 * inch, y - 2)
        y -= 0.25 * inch

        c.setFont("Helvetica", 9)
        for row in rows:
            if y < 1 * inch:
                c.showPage()
                y = height - 1 * inch
                c.setFont("Helvetica", 9)

            # ✅ FIXED: Format dates properly for PDF export
            request_date = row["request_date"]
            if request_date and hasattr(request_date, 'strftime'):
                request_date_str = request_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                request_date_str = str(request_date) if request_date else ""

            completed_date = row["completed_date"]
            if completed_date and hasattr(completed_date, 'strftime'):
                completed_date_str = completed_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                completed_date_str = str(completed_date) if completed_date else "-"

            c.drawString(x_positions[0] * inch, y, str(row["resident"]))
            c.drawString(x_positions[1] * inch, y, str(row["document_type"]))
            c.drawString(x_positions[2] * inch, y, str(row["purpose"])[:25])
            c.drawString(x_positions[3] * inch, y, request_date_str)
            c.drawString(x_positions[4] * inch, y, str(row["status"]))
            c.drawString(x_positions[5] * inch, y, completed_date_str)
            c.drawString(x_positions[6] * inch, y, str(row["handled_by"] or "-"))
            y -= 0.25 * inch

        c.save()

        QMessageBox.information(self, "Export Successful", f"PDF report generated:\n{filename}")
        log_admin_activity(self.admin_id, "EXPORT_PDF", "Exported requests report to PDF.")

    def export_to_pdf(self):
        """Exports all requests to a PDF report (official format)."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, res.name AS resident, r.document_type, r.purpose,
                   r.request_date, r.status, r.completed_date, s.username AS handled_by
            FROM requests r
            JOIN residents res ON r.resident_id = res.id
            LEFT JOIN staff s ON r.created_by = s.id
            ORDER BY r.created_at DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        export_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(export_dir, exist_ok=True)
        filename = os.path.join(export_dir, f"requests_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

        c = canvas.Canvas(filename, pagesize=landscape(letter))
        width, height = landscape(letter)

        c.setFont("Helvetica-Bold", 16)
        c.drawString(1 * inch, height - 0.75 * inch, "Barangay Document Requests Report")

        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, height - 1.05 * inch, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        headers = ["Resident", "Document Type", "Purpose", "Request Date", "Status", "Completed Date", "Handled By"]
        x_positions = [0.5, 2.0, 3.5, 5.0, 6.5, 7.5, 8.5]
        y = height - 1.5 * inch

        c.setFont("Helvetica-Bold", 10)
        for i, h in enumerate(headers):
            c.drawString(x_positions[i] * inch, y, h)

        c.line(0.5 * inch, y - 2, 10.5 * inch, y - 2)
        y -= 0.25 * inch

        c.setFont("Helvetica", 9)
        for row in rows:
            if y < 1 * inch:
                c.showPage()
                y = height - 1 * inch
                c.setFont("Helvetica", 9)
            c.drawString(x_positions[0] * inch, y, str(row["resident"]))
            c.drawString(x_positions[1] * inch, y, str(row["document_type"]))
            c.drawString(x_positions[2] * inch, y, str(row["purpose"])[:25])
            c.drawString(x_positions[3] * inch, y, str(row["request_date"]))
            c.drawString(x_positions[4] * inch, y, str(row["status"]))
            c.drawString(x_positions[5] * inch, y, str(row["completed_date"] or "-"))
            c.drawString(x_positions[6] * inch, y, str(row["handled_by"] or "-"))
            y -= 0.25 * inch

        c.save()

        QMessageBox.information(self, "Export Successful", f"PDF report generated:\n{filename}")
        log_admin_activity(self.admin_id, "EXPORT_PDF", "Exported requests report to PDF.")