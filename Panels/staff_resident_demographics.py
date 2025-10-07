# Panels/staff_resident_demographics.py
import os
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from Panels.db import get_connection


class StaffResidentDemographics(QWidget):
    def __init__(self, staff_id):
        super().__init__()
        self.staff_id = staff_id

        # --- Load stylesheet ---
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        styles_dir = os.path.join(base_dir, "Styles")
        qss_path = os.path.join(styles_dir, "staff_demographics.qss")

        if os.path.exists(qss_path):
            with open(qss_path, "r") as style_file:
                self.setStyleSheet(style_file.read())
        else:
            print(f"⚠️ Could not find QSS file at {qss_path}")

        # --- Scrollable content wrapper ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("demographicsScroll")

        content = QWidget()
        content.setObjectName("demographicsContent")

        # Main layout inside the scrollable area
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(25)

        # --- Header Section ---
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Left: Titles
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)

        title = QLabel("Resident Demographics")
        title.setObjectName("headerTitle")

        subtitle = QLabel("Population Insights - Visual insights into the barangay population")
        subtitle.setObjectName("subtitle")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addWidget(title_container)
        header_layout.addStretch()

        # Right: Refresh button
        btn_refresh = QPushButton("🔄 Refresh Charts")
        btn_refresh.setFixedHeight(40)
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.clicked.connect(self.update_charts)
        header_layout.addWidget(btn_refresh)

        main_layout.addWidget(header_frame)

        # --- Statistics Cards Section ---
        self.stats_frame = QFrame()
        self.stats_frame.setObjectName("statsFrame")
        stats_layout = QHBoxLayout(self.stats_frame)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(15)

        # Cards
        self.total_residents_card = self.create_stat_card("Total Residents", "0", "All registered residents")
        self.avg_age_card = self.create_stat_card("Average Age", "0", "Mean age of population")
        self.gender_ratio_card = self.create_stat_card("Gender Ratio", "0:0", "Male:Female ratio")

        stats_layout.addWidget(self.total_residents_card)
        stats_layout.addWidget(self.avg_age_card)
        stats_layout.addWidget(self.gender_ratio_card)
        stats_layout.addStretch()

        main_layout.addWidget(self.stats_frame)

        # --- Charts Header ---
        charts_header = QLabel("Demographic Charts")
        charts_header.setObjectName("sectionHeader")
        main_layout.addWidget(charts_header)

        # --- Charts Grid ---
        self.charts_container = QWidget()
        self.charts_layout = QGridLayout(self.charts_container)
        self.charts_layout.setSpacing(20)
        self.charts_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addWidget(self.charts_container)

        # Attach scroll area
        scroll.setWidget(content)

        # Final layout (root)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(scroll)

        # Initial chart load
        self.update_charts()

    # -------------------------------------------------------------
    # Reused methods
    # -------------------------------------------------------------

    def create_stat_card(self, title, value, subtitle):
        """Create a statistics card widget"""
        card = QFrame()
        card.setObjectName("statsCard")
        card.setMinimumWidth(200)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("statsTitle")

        value_label = QLabel(value)
        value_label.setObjectName("statsValue")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("statsSubtitle")

        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        card_layout.addWidget(subtitle_label)
        card_layout.addStretch()

        return card

    def update_charts(self):
        """Clear existing charts and redraw based on DB data."""
        # Clear old charts
        while self.charts_layout.count():
            item = self.charts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Fetch residents
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT age, gender, civil_status, education_level, employment_status FROM residents")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        # If no rows found — friendly message and stop
        if not rows:
            msg = QLabel("📊 No residents found in the database.\nAdd residents to see demographic insights.")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.charts_layout.addWidget(msg, 0, 0, 1, 2)
            # update stat cards to zero
            self.total_residents_card.layout().itemAt(1).widget().setText("0")
            self.avg_age_card.layout().itemAt(1).widget().setText("0.0")
            self.gender_ratio_card.layout().itemAt(1).widget().setText("0:0")
            return

        # Prepare data (defensively convert and filter None)
        ages = []
        for r in rows:
            a = r.get("age")
            try:
                if a is not None:
                    ages.append(int(a))
            except Exception:
                # ignore badly formatted ages
                continue

        genders = [r["gender"] for r in rows if r.get("gender")]
        statuses = [r["civil_status"] for r in rows if r.get("civil_status")]
        education = [r["education_level"] for r in rows if r.get("education_level")]
        employment = [r["employment_status"] for r in rows if r.get("employment_status")]

        # Update statistics cards
        self.update_statistics(rows, ages, genders)

        # plotting styles
        plt.style.use('seaborn-v0_8')
        colors_pie = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
        colors_bar = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12']

        # --- Gender Pie Chart ---
        gender_counts = [genders.count("Male"), genders.count("Female")]
        gender_labels = ["Male", "Female"]
        # Only create pie if sum > 0
        if sum(gender_counts) > 0:
            gender_chart = self.make_chart(
                title="Gender Distribution",
                chart_func=lambda ax: ax.pie(
                    gender_counts, labels=gender_labels, autopct="%1.1f%%",
                    startangle=90, colors=['#3498db', '#e74c3c'], textprops={'fontsize': 9}
                ),
                figsize=(5, 4)
            )
            self.charts_layout.addWidget(gender_chart, 0, 0)
        else:
            placeholder = QLabel("No gender data available")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.charts_layout.addWidget(placeholder, 0, 0)

        # --- Age Group Bar Chart ---
        def age_group(age):
            if age <= 17:
                return "0–17"
            elif age <= 35:
                return "18–35"
            elif age <= 60:
                return "36–60"
            else:
                return "60+"

        age_groups = [age_group(a) for a in ages if isinstance(a, int)]
        group_labels = ["0–17", "18–35", "36–60", "60+"]
        group_counts = [age_groups.count(lbl) for lbl in group_labels]

        # Create age chart even if all zeros (bar chart will show zero height)
        age_chart = self.make_chart(
            title="Age Group Distribution",
            chart_func=lambda ax: ax.bar(group_labels, group_counts, color=colors_bar,
                                        edgecolor='white', linewidth=0.5),
            figsize=(5, 4)
        )
        ax = age_chart.figure.axes[0]
        # annotate bars safely using numeric fallback
        for i, v in enumerate(group_counts):
            numeric_v = v or 0
            ax.text(i, numeric_v + 0.1, str(int(numeric_v)), ha='center', va='bottom', fontsize=9)
        self.charts_layout.addWidget(age_chart, 0, 1)

        # --- Civil Status Pie Chart ---
        status_labels = list(filter(None, set(statuses)))
        status_counts = [statuses.count(s) for s in status_labels]
        if status_labels and sum(status_counts) > 0:
            civil_chart = self.make_chart(
                title="Civil Status Breakdown",
                chart_func=lambda ax: ax.pie(
                    status_counts, labels=status_labels, autopct="%1.1f%%",
                    colors=colors_pie[:len(status_labels)], textprops={'fontsize': 8}
                ),
                figsize=(5, 4)
            )
            self.charts_layout.addWidget(civil_chart, 1, 0)
        else:
            placeholder = QLabel("No civil status data available")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.charts_layout.addWidget(placeholder, 1, 0)

        # --- Education Bar Chart ---
        edu_labels = list(filter(None, set(education)))
        edu_counts = [education.count(e) for e in edu_labels]
        if edu_labels and sum(edu_counts) > 0:
            edu_chart = self.make_chart(
                title="Education Levels",
                chart_func=lambda ax: ax.bar(
                    edu_labels, edu_counts, color='#9b59b6', edgecolor='white', linewidth=0.5
                ),
                figsize=(5, 4)
            )
            ax = edu_chart.figure.axes[0]
            ax.tick_params(axis='x', rotation=45)
            for i, v in enumerate(edu_counts):
                numeric_v = v or 0
                ax.text(i, numeric_v + 0.1, str(int(numeric_v)), ha='center', va='bottom', fontsize=9)
            self.charts_layout.addWidget(edu_chart, 1, 1)
        else:
            placeholder = QLabel("No education data available")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.charts_layout.addWidget(placeholder, 1, 1)

    def update_statistics(self, rows, ages, genders):
        """Update the statistics cards with current data"""
        total_residents = len(rows)
        avg_age = np.mean(ages) if ages else 0.0
        male_count = genders.count("Male")
        female_count = genders.count("Female")

        # update stat cards safely
        try:
            self.total_residents_card.layout().itemAt(1).widget().setText(f"{total_residents:,}")
            self.avg_age_card.layout().itemAt(1).widget().setText(f"{avg_age:.1f}")
            self.gender_ratio_card.layout().itemAt(1).widget().setText(f"{male_count}:{female_count}")
        except Exception:
            # In case layout assumptions change, fail quietly
            pass

    def make_chart(self, title, chart_func, figsize=(5, 4)):
        """Embed matplotlib chart in a QWidget."""
        fig = Figure(figsize=figsize, facecolor='#ffffff')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#ffffff')
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        # call the provided chart draw function
        chart_func(ax)
        fig.tight_layout()
        canvas = FigureCanvas(fig)
        canvas.setMinimumHeight(300)
        return canvas
