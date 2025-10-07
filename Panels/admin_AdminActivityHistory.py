import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QScrollArea, QComboBox, QDateEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont
from Panels.db import get_connection


class AdminActivityHistory(QWidget):
    def __init__(self, admin_id):
        super().__init__()
        self.admin_id = admin_id
        self.init_ui()
        self.load_activities()

        # --- Project Paths ---
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        styles_dir = os.path.join(base_dir, "Styles")

        qss_path = os.path.join(styles_dir, "admin_activity_history.qss")

        if os.path.exists(qss_path):
            with open(qss_path, "r") as style_file:
                self.setStyleSheet(style_file.read())
        else:
            print(f"⚠️ Could not find QSS file at {qss_path}")


    def init_ui(self):
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("activityScroll")

        content = QWidget()
        content.setObjectName("activityContent")
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

        page_title = QLabel("Admin Activity History")
        page_title.setObjectName("pageTitle")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        page_title.setFont(title_font)
        title_layout.addWidget(page_title)

        header_layout.addWidget(title_container, alignment=Qt.AlignmentFlag.AlignLeft)
        header_layout.addStretch()

        # Right side - Export Buttons
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

        header_layout.addWidget(buttons_container, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(header_frame)

        # --- Subtitle Section ---
        subtitle_container = QWidget()
        subtitle_layout = QVBoxLayout(subtitle_container)
        subtitle_layout.setContentsMargins(0, 0, 0, 0)
        subtitle_layout.setSpacing(5)

        main_subtitle = QLabel("Administrative Monitoring")
        main_subtitle.setObjectName("mainSubtitle")
        description = QLabel("Track all administrative activities and system changes")
        description.setObjectName("description")

        subtitle_layout.addWidget(main_subtitle)
        subtitle_layout.addWidget(description)
        layout.addWidget(subtitle_container)

        # --- Activity History Table Card ---
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

        list_title = QLabel("Admin Activity Log")
        list_title.setObjectName("listTitle")
        list_subtitle = QLabel("All administrative activities with timestamps")
        list_subtitle.setObjectName("listSubtitle")

        list_info_layout.addWidget(list_title)
        list_info_layout.addWidget(list_subtitle)
        card_header.addWidget(list_info)
        card_header.addStretch()

        table_layout.addLayout(card_header)

        # --- Filters Row ---
        filters_row = QHBoxLayout()
        filters_row.setSpacing(10)

        # Date From
        date_from_layout = QVBoxLayout()
        date_from_layout.setSpacing(5)
        date_from_label = QLabel("From Date")
        date_from_label.setObjectName("filterLabel")
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-7))  # Default: last 7 days
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.dateChanged.connect(self.load_activities)
        date_from_layout.addWidget(date_from_label)
        date_from_layout.addWidget(self.date_from)

        # Date To
        date_to_layout = QVBoxLayout()
        date_to_layout.setSpacing(5)
        date_to_label = QLabel("To Date")
        date_to_label.setObjectName("filterLabel")
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.dateChanged.connect(self.load_activities)
        date_to_layout.addWidget(date_to_label)
        date_to_layout.addWidget(self.date_to)

        # Admin Filter
        admin_filter_layout = QVBoxLayout()
        admin_filter_layout.setSpacing(5)
        admin_label = QLabel("Admin User")
        admin_label.setObjectName("filterLabel")
        self.admin_filter = QComboBox()
        self.admin_filter.addItem("All Admins")
        self.admin_filter.currentTextChanged.connect(self.load_activities)
        admin_filter_layout.addWidget(admin_label)
        admin_filter_layout.addWidget(self.admin_filter)

        # Activity Type Filter
        activity_filter_layout = QVBoxLayout()
        activity_filter_layout.setSpacing(5)
        activity_label = QLabel("Activity Type")
        activity_label.setObjectName("filterLabel")
        self.activity_filter = QComboBox()
        self.activity_filter.addItem("All Activities")
        self.activity_filter.currentTextChanged.connect(self.load_activities)
        activity_filter_layout.addWidget(activity_label)
        activity_filter_layout.addWidget(self.activity_filter)

        # Search
        search_layout = QVBoxLayout()
        search_layout.setSpacing(5)
        search_label = QLabel("Search")
        search_label.setObjectName("filterLabel")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search activities...")
        self.search_input.textChanged.connect(self.load_activities)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)

        filters_row.addLayout(date_from_layout)
        filters_row.addLayout(date_to_layout)
        filters_row.addLayout(admin_filter_layout)
        filters_row.addLayout(activity_filter_layout)
        filters_row.addLayout(search_layout)
        filters_row.addStretch()

        table_layout.addLayout(filters_row)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setObjectName("activityTable")
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "Admin User", "Activity Type", "Description", "IP Address"
        ])

        # 🔧 FIX: Set header alignment to match content
        header = self.table.horizontalHeader()
        for i in range(self.table.columnCount()):
            header_item = self.table.horizontalHeaderItem(i)
            if header_item:
                header_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.Fixed)  # Timestamp
        header.setSectionResizeMode(1, header.ResizeMode.Fixed)  # Admin User
        header.setSectionResizeMode(2, header.ResizeMode.Fixed)  # Activity Type
        header.setSectionResizeMode(3, header.ResizeMode.Stretch)  # Description
        header.setSectionResizeMode(4, header.ResizeMode.Fixed)  # IP Address

        self.table.setColumnWidth(0, 150)  # Timestamp
        self.table.setColumnWidth(1, 120)  # Admin User
        self.table.setColumnWidth(2, 150)  # Activity Type
        self.table.setColumnWidth(4, 120)  # IP Address

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

        # Load initial filters
        self.load_filters()

    def load_filters(self):
        """Load filter dropdowns"""
        conn = get_connection()
        cursor = conn.cursor()

        # Load admin users
        cursor.execute("SELECT id, username FROM admins ORDER BY username")
        admin_list = cursor.fetchall()
        for admin in admin_list:
            self.admin_filter.addItem(f"{admin['username']} (ID: {admin['id']})", admin['id'])

        # Load activity types
        cursor.execute("SELECT DISTINCT action_type FROM admin_activity ORDER BY action_type")
        activity_types = cursor.fetchall()
        for activity in activity_types:
            if activity['action_type']:
                self.activity_filter.addItem(activity['action_type'])

        cursor.close()
        conn.close()

    def load_activities(self):
        """Load admin activities with filters"""
        conn = get_connection()
        cursor = conn.cursor()

        # Build query with filters
        query = """
            SELECT aa.*, a.username 
            FROM admin_activity aa 
            LEFT JOIN admins a ON aa.admin_id = a.id 
            WHERE 1=1
        """
        params = []

        # Date filter
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        query += " AND DATE(aa.created_at) BETWEEN %s AND %s"
        params.extend([date_from, date_to])

        # Admin filter
        if self.admin_filter.currentText() != "All Admins":
            admin_id = self.admin_filter.currentData()
            query += " AND aa.admin_id = %s"
            params.append(admin_id)

        # Activity type filter
        if self.activity_filter.currentText() != "All Activities":
            activity_type = self.activity_filter.currentText()
            query += " AND aa.action_type = %s"
            params.append(activity_type)

        # Search filter
        search_text = self.search_input.text().strip()
        if search_text:
            query += " AND (a.username LIKE %s OR aa.description LIKE %s OR aa.action_type LIKE %s)"
            params.extend([f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"])

        query += " ORDER BY aa.created_at DESC"

        cursor.execute(query, params)
        activities = cursor.fetchall()

        self.populate_table(activities)
        cursor.close()
        conn.close()

    def populate_table(self, activities):
        """Populate table with activity data"""
        self.table.setRowCount(len(activities))

        for row, activity in enumerate(activities):
            # Timestamp
            timestamp_item = QTableWidgetItem(activity["created_at"].strftime("%Y-%m-%d %H:%M:%S"))
            timestamp_item.setFlags(timestamp_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, timestamp_item)

            # Admin User
            admin_item = QTableWidgetItem(activity.get("username", "Unknown"))
            admin_item.setFlags(admin_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, admin_item)

            # Activity Type
            activity_item = QTableWidgetItem(activity.get("action_type", "N/A"))
            activity_item.setFlags(activity_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, activity_item)

            # Description
            desc_item = QTableWidgetItem(activity.get("description", "N/A"))
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, desc_item)

            # IP Address (if available)
            ip_item = QTableWidgetItem(activity.get("ip_address", "N/A"))
            ip_item.setFlags(ip_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, ip_item)

            # Set row height
            self.table.setRowHeight(row, 50)

    def export_to_csv(self):
        """Export activities to CSV"""
        import csv
        from datetime import datetime

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT aa.created_at, a.username, aa.action_type, aa.description, aa.ip_address
            FROM admin_activity aa 
            LEFT JOIN admins a ON aa.admin_id = a.id 
            ORDER BY aa.created_at DESC
        """)
        activities = cursor.fetchall()
        cursor.close()
        conn.close()

        export_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(export_dir, exist_ok=True)
        filename = os.path.join(export_dir, f"admin_activities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Admin User", "Activity Type", "Description", "IP Address"])
            for activity in activities:
                writer.writerow([
                    activity["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
                    activity.get("username", "Unknown"),
                    activity.get("action_type", "N/A"),
                    activity.get("description", "N/A"),
                    activity.get("ip_address", "N/A")
                ])

        QMessageBox.information(self, "Export Successful", f"Admin activities exported to:\n{filename}")

    def export_to_pdf(self):
        """Export activities to PDF"""
        from datetime import datetime
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT aa.created_at, a.username, aa.action_type, aa.description
            FROM admin_activity aa 
            LEFT JOIN admins a ON aa.admin_id = a.id 
            ORDER BY aa.created_at DESC
            LIMIT 100  # Limit for PDF readability
        """)
        activities = cursor.fetchall()
        cursor.close()
        conn.close()

        export_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(export_dir, exist_ok=True)
        filename = os.path.join(export_dir, f"admin_activities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

        c = canvas.Canvas(filename, pagesize=landscape(letter))
        width, height = landscape(letter)

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1 * inch, height - 0.75 * inch, "Admin Activity Report")

        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, height - 1 * inch, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Headers
        y = height - 1.5 * inch
        headers = ["Timestamp", "Admin", "Activity", "Description"]
        x_positions = [0.5, 2.0, 3.0, 4.5]

        c.setFont("Helvetica-Bold", 10)
        for i, h in enumerate(headers):
            c.drawString(x_positions[i] * inch, y, h)

        # Data
        y -= 0.25 * inch
        c.setFont("Helvetica", 8)
        for activity in activities:
            if y < 1 * inch:
                c.showPage()
                y = height - 1 * inch
                c.setFont("Helvetica", 8)

            c.drawString(x_positions[0] * inch, y, activity["created_at"].strftime("%m/%d %H:%M"))
            c.drawString(x_positions[1] * inch, y, activity.get("username", "Unknown")[:12])
            c.drawString(x_positions[2] * inch, y, activity.get("action_type", "N/A")[:15])
            c.drawString(x_positions[3] * inch, y, activity.get("description", "N/A")[:40])
            y -= 0.25 * inch

        c.save()
        QMessageBox.information(self, "Export Successful", f"PDF report generated:\n{filename}")