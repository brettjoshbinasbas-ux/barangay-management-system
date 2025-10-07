# Panels/admin_reports.py
import sys
import os
import datetime
import matplotlib.dates as mdates
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from Panels.db import get_connection


class AdminReports(QWidget):
    def __init__(self):
        super().__init__()

        # --- Project Paths ---
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        styles_dir = os.path.join(base_dir, "Styles")
        qss_path = os.path.join(styles_dir, "admin_reports.qss")

        if os.path.exists(qss_path):
            with open(qss_path, "r") as style_file:
                self.setStyleSheet(style_file.read())

        self.setObjectName("infographicsPanel")

        # Main scroll area for better responsiveness
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("reportsScroll")

        content = QWidget()
        content.setObjectName("reportsContent")
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(25)

        # --- Header Section ---
        header_frame = QFrame()
        header_frame.setObjectName("headerSection")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        title = QLabel("Reports & Analytics")
        title.setObjectName("pageTitle")

        subtitle = QLabel("System-wide analytics and reports (Admin view)")
        subtitle.setObjectName("pageSubtitle")

        header_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(header_frame)

        # --- KPIs Section ---
        kpi_section = QFrame()
        kpi_section.setObjectName("kpiSection")
        kpi_section_layout = QVBoxLayout(kpi_section)
        kpi_section_layout.setContentsMargins(0, 0, 0, 0)
        kpi_section_layout.setSpacing(15)

        kpi_title = QLabel("Key Performance Indicators")
        kpi_title.setObjectName("sectionTitle")
        kpi_section_layout.addWidget(kpi_title)

        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(20)

        self.total_residents = self.create_kpi_box("👥 Total Residents", "0", "#8B5CF6")
        self.documents_issued = self.create_kpi_box("📄 Documents Issued", "0", "#10B981")

        kpi_layout.addWidget(self.total_residents)
        kpi_layout.addWidget(self.documents_issued)
        kpi_layout.addStretch()

        kpi_section_layout.addLayout(kpi_layout)
        main_layout.addWidget(kpi_section)

        # --- Charts Section ---
        charts_section = QFrame()
        charts_section.setObjectName("chartsSection")
        charts_layout = QVBoxLayout(charts_section)
        charts_layout.setContentsMargins(0, 0, 0, 0)
        charts_layout.setSpacing(15)

        charts_title = QLabel("Analytics Dashboard")
        charts_title.setObjectName("sectionTitle")
        charts_layout.addWidget(charts_title)

        # First row of charts
        first_chart_row = QHBoxLayout()
        first_chart_row.setSpacing(20)

        self.doc_requests_box = self.create_chart_box("📈 Document Requests", "Requests over time")
        self.doc_distribution_box = self.create_chart_box("📊 Document Distribution", "Breakdown by type")

        first_chart_row.addWidget(self.doc_requests_box, 2)
        first_chart_row.addWidget(self.doc_distribution_box, 1)
        charts_layout.addLayout(first_chart_row)

        # Second row of charts
        second_chart_row = QHBoxLayout()
        second_chart_row.setSpacing(20)

        self.demographics_box = self.create_chart_box("👨‍👩‍👧‍👦 Resident Demographics", "Population by age group")
        self.summary_box = self.create_summary_box()

        second_chart_row.addWidget(self.demographics_box, 2)
        second_chart_row.addWidget(self.summary_box, 1)
        charts_layout.addLayout(second_chart_row)

        main_layout.addWidget(charts_section)
        main_layout.addStretch()

        # Set scroll content
        scroll.setWidget(content)

        # Main layout
        final_layout = QVBoxLayout(self)
        final_layout.setContentsMargins(0, 0, 0, 0)
        final_layout.addWidget(scroll)

        # ✅ Load real data
        self.refresh_data()

    # --- KPI Box ---
    def create_kpi_box(self, title, value, color):
        frame = QFrame()
        frame.setObjectName("kpiBox")
        frame.setProperty("accentColor", color)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Title with icon
        label_title = QLabel(title)
        label_title.setObjectName("kpiTitle")

        # Value
        value_label = QLabel(value)
        value_label.setObjectName("kpiValue")

        layout.addWidget(label_title, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(value_label, alignment=Qt.AlignmentFlag.AlignLeft)

        frame.value_label = value_label
        return frame

    # --- Chart Box ---
    def create_chart_box(self, title, subtitle):
        frame = QFrame()
        frame.setObjectName("chartBox")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        label_title = QLabel(title)
        label_title.setObjectName("chartTitle")

        label_sub = QLabel(subtitle)
        label_sub.setObjectName("chartSubtitle")

        header_layout.addWidget(label_title, alignment=Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(label_sub, alignment=Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(header_widget)
        frame.layout_box = layout
        return frame

    # --- Summary Box ---
    def create_summary_box(self):
        frame = QFrame()
        frame.setObjectName("summaryBox")

        self.summary_layout = QVBoxLayout(frame)
        self.summary_layout.setContentsMargins(20, 20, 20, 20)
        self.summary_layout.setSpacing(15)

        # Header
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        title = QLabel("📋 Recent Activity")
        title.setObjectName("chartTitle")

        subtitle = QLabel("System-wide activity in the past 7 days")
        subtitle.setObjectName("chartSubtitle")

        header_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignLeft)

        self.summary_layout.addWidget(header_widget)
        return frame

    # --- Charts Helpers (NO CHANGES) ---
    def _replace_chart(self, layout, new_canvas):
        while layout.count() > 2:  # keep title + subtitle
            old_item = layout.takeAt(2)
            if old_item.widget():
                old_item.widget().deleteLater()
        layout.addWidget(new_canvas)

    def add_line_chart(self, layout, x, y, label):
        fig = Figure(figsize=(4, 3))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        try:
            x_dates = [datetime.datetime.strptime(m, "%Y-%m") for m in x]
            ax.plot(x_dates, y, marker="o", label=label)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
            fig.autofmt_xdate()
        except Exception:
            ax.plot(x, y, marker="o", label=label)

        ax.set_ylabel("Requests")
        ax.legend()
        self._replace_chart(layout, canvas)

    def add_pie_chart(self, layout, labels, sizes):
        fig = Figure(figsize=(3, 3))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
        self._replace_chart(layout, canvas)

    def add_bar_chart(self, layout, labels, values, color="#9C27B0"):
        fig = Figure(figsize=(4, 3))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.bar(labels, values, color=color)
        self._replace_chart(layout, canvas)

    # --- Refresh Data (NO CHANGES) ---
    def refresh_data(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # KPIs
            cursor.execute("SELECT COUNT(*) AS total FROM residents")
            total_residents = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM requests")
            total_docs = cursor.fetchone()["total"]

            self.total_residents.value_label.setText(str(total_residents))
            self.documents_issued.value_label.setText(str(total_docs))

            # Requests over time
            cursor.execute("""
                SELECT DATE_FORMAT(request_date, '%Y-%m') AS month, COUNT(*) AS total
                FROM requests
                GROUP BY month ORDER BY month
            """)
            req_data = cursor.fetchall()
            months = [r["month"] for r in req_data]
            totals = [r["total"] for r in req_data]
            self.add_line_chart(self.doc_requests_box.layout_box, months, totals, "Requests")

            # Document type distribution
            cursor.execute("SELECT document_type, COUNT(*) AS total FROM requests GROUP BY document_type")
            type_data = cursor.fetchall()
            labels = [r["document_type"] for r in type_data]
            sizes = [r["total"] for r in type_data]
            self.add_pie_chart(self.doc_distribution_box.layout_box, labels, sizes)

            # Age demographics
            cursor.execute("""
                SELECT 
                    SUM(age BETWEEN 0 AND 17) AS age_0_17,
                    SUM(age BETWEEN 18 AND 35) AS age_18_35,
                    SUM(age BETWEEN 36 AND 50) AS age_36_50,
                    SUM(age BETWEEN 51 AND 65) AS age_51_65,
                    SUM(age >= 66) AS age_65_plus
                FROM residents
            """)
            age_data = cursor.fetchone()
            groups = ["0-17", "18-35", "36-50", "51-65", "65+"]
            values = [age_data["age_0_17"], age_data["age_18_35"],
                      age_data["age_36_50"], age_data["age_51_65"],
                      age_data["age_65_plus"]]
            self.add_bar_chart(self.demographics_box.layout_box, groups, values)

            # Activity summary (last 7 days)
            cursor.execute("""
                SELECT 'Staff' AS role, sa.action_type, COUNT(*) AS total
                FROM staff_activity sa
                WHERE sa.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY sa.action_type
                UNION ALL
                SELECT 'Admin' AS role, aa.action_type, COUNT(*) AS total
                FROM admin_activity aa
                WHERE aa.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY aa.action_type
                ORDER BY total DESC
                LIMIT 5
            """)
            act_data = cursor.fetchall()

            # Clear old summary
            for i in reversed(range(self.summary_layout.count())):
                if i < 2:  # keep title/subtitle
                    continue
                item = self.summary_layout.itemAt(i)
                if item and item.widget():
                    item.widget().deleteLater()

            # Add new summary rows
            for act in act_data:
                row = QHBoxLayout()
                l = QLabel(f"[{act['role']}] {act['action_type']}")
                l.setObjectName("summaryLabel")
                v = QLabel(str(act["total"]))
                v.setObjectName("summaryValue")
                row.addWidget(l)
                row.addStretch()
                row.addWidget(v)
                self.summary_layout.addLayout(row)

            cursor.close()
            conn.close()

        except Exception as e:
            print(f"⚠️ Failed to refresh reports: {e}")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = AdminReports()
    window.show()
    sys.exit(app.exec())