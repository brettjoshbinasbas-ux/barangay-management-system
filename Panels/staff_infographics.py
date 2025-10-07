import os
import matplotlib.dates as mdates
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QPushButton
)
from PyQt6.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from Panels.db import get_connection


class StaffInfographics(QWidget):
    def __init__(self, staff_id=None):
        super().__init__()
        self.staff_id = staff_id
        self._refresh_pending = False  # Prevent multiple rapid refreshes

        # --- Load stylesheet ---
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        styles_dir = os.path.join(base_dir, "Styles")
        qss_path = os.path.join(styles_dir, "staff_infographics.qss")

        if os.path.exists(qss_path):
            with open(qss_path, "r") as style_file:
                self.setStyleSheet(style_file.read())

        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("infographicsScroll")

        # Content widget
        content = QWidget()
        content.setObjectName("infographicsContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(25)

        # --- Header Section ---
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        title = QLabel("Reports & Analytics")
        title.setObjectName("titleLabel")

        subtitle = QLabel("System performance and statistical reports")
        subtitle.setObjectName("subtitleLabel")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        content_layout.addWidget(header_frame)

        refresh_btn = QPushButton("🔄 Refresh Analytics")
        refresh_btn.setObjectName("refreshButton")
        refresh_btn.setFixedHeight(40)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.safe_refresh_data)
        content_layout.addWidget(refresh_btn)

        # --- Top KPIs Section ---
        kpi_section_label = QLabel("Key Performance Indicators")
        kpi_section_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #2c3e50; 
            background-color: #ecf0f1; 
            padding: 12px 15px; 
            border-radius: 6px;
            margin: 10px 0px 5px 0px;
        """)
        content_layout.addWidget(kpi_section_label)

        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(20)

        self.total_residents = self.create_kpi_box("Total Residents", "0", "#3498db")
        self.documents_issued = self.create_kpi_box("Documents Issued", "0", "#27ae60")

        kpi_layout.addWidget(self.total_residents)
        kpi_layout.addWidget(self.documents_issued)
        kpi_layout.addStretch()

        content_layout.addLayout(kpi_layout)

        # --- Charts Section Header ---
        charts_section_label = QLabel("Analytical Charts")
        charts_section_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #2c3e50; 
            background-color: #ecf0f1; 
            padding: 12px 15px; 
            border-radius: 6px;
            margin: 20px 0px 5px 0px;
        """)
        content_layout.addWidget(charts_section_label)

        # --- Middle Section: Requests + Distribution ---
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(20)

        self.doc_requests_box = self.create_chart_box("Document Requests", "Requests over time")
        self.doc_distribution_box = self.create_chart_box("Document Type Distribution", "Document breakdown")

        middle_layout.addWidget(self.doc_requests_box)
        middle_layout.addWidget(self.doc_distribution_box)
        content_layout.addLayout(middle_layout)

        # --- Bottom Section: Demographics + Activity ---
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)

        self.demographics_box = self.create_chart_box("Resident Demographics", "Population by age group")
        self.activity_box = self.create_chart_box("Recent Activity Summary", "Top staff actions")

        bottom_layout.addWidget(self.demographics_box)
        bottom_layout.addWidget(self.activity_box)
        content_layout.addLayout(bottom_layout)

        # Add stretch to push content up
        content_layout.addStretch()

        # Set scroll content
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # ✅ Initial data load with delay to ensure UI is ready
        QTimer.singleShot(100, self.refresh_data)

    def safe_refresh_data(self):
        """Safely refresh data with debouncing"""
        if self._refresh_pending:
            return

        self._refresh_pending = True
        QTimer.singleShot(300, self._execute_refresh)

    def _execute_refresh(self):
        """Execute the actual refresh after delay"""
        try:
            self.refresh_data()
        except Exception as e:
            print(f"Error refreshing infographics: {e}")
        finally:
            self._refresh_pending = False

    # --- KPI box ---
    def create_kpi_box(self, title, value, color):
        frame = QFrame()
        frame.setObjectName("kpiBox")
        frame.setMinimumWidth(200)
        frame.setFixedHeight(120)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)

        label_title = QLabel(title)
        label_title.setObjectName("kpiTitle")

        value_label = QLabel(value)
        value_label.setObjectName("kpiValue")
        value_label.setStyleSheet(f"color: {color};")  # Dynamic color

        layout.addWidget(label_title, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        frame.value_label = value_label  # attach for later update
        return frame

    # --- Chart box ---
    def create_chart_box(self, title, subtitle):
        frame = QFrame()
        frame.setObjectName("chartBox")
        frame.setMinimumHeight(350)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)

        label_title = QLabel(title)
        label_title.setObjectName("chartTitle")

        label_sub = QLabel(subtitle)
        label_sub.setObjectName("chartSubtitle")

        layout.addWidget(label_title)
        layout.addWidget(label_sub)

        frame.layout_box = layout
        return frame

    # --- Refresh Data ---
    def refresh_data(self):
        conn = get_connection()
        cursor = conn.cursor()

        # --- KPIs ---
        cursor.execute("SELECT COUNT(*) AS total FROM residents")
        row = cursor.fetchone()
        total_residents = row["total"] if row and row["total"] is not None else 0

        cursor.execute("SELECT COUNT(*) AS total FROM requests")
        row = cursor.fetchone()
        total_docs = row["total"] if row and row["total"] is not None else 0

        self.total_residents.value_label.setText(str(total_residents))
        self.documents_issued.value_label.setText(str(total_docs))

        # Set matplotlib style for consistent charts
        plt.style.use('seaborn-v0_8')

        # --- Document Requests over time ---
        cursor.execute("""
            SELECT DATE_FORMAT(request_date, '%Y-%m') AS month, COUNT(*) AS total
            FROM requests
            GROUP BY month ORDER BY month
        """)
        req_data = cursor.fetchall()
        months = [row["month"] for row in req_data if row["month"]]
        totals = [row["total"] for row in req_data if row["total"] is not None]
        if months and totals:
            self.add_line_chart(self.doc_requests_box.layout_box, months, totals, "Requests")

        # --- Document Type Distribution ---
        cursor.execute("""
            SELECT document_type, COUNT(*) AS total
            FROM requests
            GROUP BY document_type
        """)
        type_data = cursor.fetchall()
        labels = [row["document_type"] for row in type_data if row["document_type"]]
        sizes = [row["total"] or 0 for row in type_data]
        if sizes and sum(sizes) > 0:
            self.add_pie_chart(self.doc_distribution_box.layout_box, labels, sizes)

        # --- Resident Demographics ---
        cursor.execute("""
            SELECT 
                SUM(age BETWEEN 0 AND 17) AS age_0_17,
                SUM(age BETWEEN 18 AND 35) AS age_18_35,
                SUM(age BETWEEN 36 AND 60) AS age_36_60,
                SUM(age >= 61) AS age_61_plus
            FROM residents
        """)
        age_data = cursor.fetchone() or {}
        groups = ["0-17", "18-35", "36-60", "61+"]
        values = [
            age_data.get("age_0_17") or 0,
            age_data.get("age_18_35") or 0,
            age_data.get("age_36_60") or 0,
            age_data.get("age_61_plus") or 0,
        ]
        if sum(values) > 0:
            self.add_bar_chart(self.demographics_box.layout_box, groups, values, "#3498db")
        else:
            placeholder = QLabel("No resident age data available.")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.demographics_box.layout_box.addWidget(placeholder)

        # --- Recent Activity Summary ---
        cursor.execute("""
            SELECT action_type, COUNT(*) AS total
            FROM staff_activity
            GROUP BY action_type
            ORDER BY total DESC
            LIMIT 5
        """)
        act_data = cursor.fetchall()
        actions = [row["action_type"] for row in act_data if row["action_type"]]
        counts = [row["total"] or 0 for row in act_data]
        if actions and sum(counts) > 0:
            self.add_bar_chart(self.activity_box.layout_box, actions, counts, "#e74c3c")
        else:
            placeholder = QLabel("No staff activity data available.")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.activity_box.layout_box.addWidget(placeholder)

        cursor.close()
        conn.close()

    # --- Charts ---
    def add_line_chart(self, layout, x, y, label):
        fig = Figure(figsize=(6, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.set_facecolor('#ffffff')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        try:
            x_dates = [datetime.datetime.strptime(m, "%Y-%m") for m in x]
            ax.plot(x_dates, y, marker="o", label=label, color='#3498db', linewidth=2, markersize=4)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
            fig.autofmt_xdate()
        except Exception as e:
            print("⚠️ Date parsing failed:", e)
            ax.plot(list(range(len(x))), y, marker="o", color='#3498db', linewidth=2, markersize=4)

        ax.set_xlabel("Month")
        ax.set_ylabel("Requests")
        ax.legend()
        fig.tight_layout()
        self._replace_chart(layout, canvas)

    def add_pie_chart(self, layout, labels, sizes):
        fig = Figure(figsize=(5, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.set_facecolor('#ffffff')
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
        ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90,
               colors=colors[:len(labels)], textprops={'fontsize': 9})
        ax.axis("equal")
        fig.tight_layout()
        self._replace_chart(layout, canvas)

    def add_bar_chart(self, layout, labels, values, color="#3498db"):
        fig = Figure(figsize=(6, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.set_facecolor('#ffffff')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        values_float = [float(v or 0) for v in values]
        bars = ax.bar(labels, values_float, color=color, edgecolor='white', linewidth=0.5)

        for i, v in enumerate(values_float):
            ax.text(i, v + 0.1, str(int(v)), ha='center', va='bottom', fontsize=9)

        if max(len(str(label)) for label in labels) > 10:
            ax.tick_params(axis='x', rotation=45)

        fig.tight_layout()
        self._replace_chart(layout, canvas)

    def _replace_chart(self, layout, new_canvas):
        while layout.count() > 2:  # keep title + subtitle
            old_item = layout.takeAt(2)
            if old_item.widget():
                old_item.widget().deleteLater()
        layout.addWidget(new_canvas)
