# staff_dashboard.py  (refactored UI improvements — DB and logic unchanged)
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QMessageBox, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont

from Panels.db import get_connection
from staff_resident_profiles import StaffResidentProfiles
from staff_requests import StaffRequests
from staff_infographics import StaffInfographics
from staff_resident_demographics import StaffResidentDemographics


class DashboardWindow(QMainWindow):
    def __init__(self, staff_id):
        super().__init__()
        self.staff_id = staff_id
        self._refresh_pending = False  # Prevent multiple rapid refreshes

        # --- Project Paths ---
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        styles_dir = os.path.join(base_dir, "Styles")
        images_dir = os.path.join(base_dir, "Images")

        qss_path = os.path.join(styles_dir, "staff_dashboard.qss")
        logo_path = os.path.join(images_dir, "BRIMS_logo.png")

        self.logo_path = logo_path

        if os.path.exists(qss_path):
            with open(qss_path, "r") as style_file:
                self.setStyleSheet(style_file.read())
        else:
            print(f"⚠️ Could not find QSS file at {qss_path}")

        self.setWindowTitle("BRIMS - Barangay Management System")
        self.setGeometry(100, 100, 1400, 800)

        # Central widget
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        # Main layout: Sidebar + Content
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)

        # StackedWidget for swapping pages
        self.pages = QStackedWidget()
        self.pages.setObjectName("contentArea")
        self.pages.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.pages)

        # Initialize pages
        self.initialize_pages()

        # Start with Dashboard
        self.pages.setCurrentIndex(0)

    def initialize_pages(self):
        """Initialize all pages with safe signal connections"""
        # Page 0: Dashboard Content
        self.dashboard_content = self.create_dashboard_content()
        self.pages.addWidget(self.dashboard_content)

        # Page 1: Resident Profiles
        self.resident_profiles = StaffResidentProfiles(self.staff_id)
        self.pages.addWidget(self.resident_profiles)

        # Page 2: Requests
        self.requests_panel = StaffRequests(self.staff_id)
        self.pages.addWidget(self.requests_panel)

        # Page 3: Resident Demographics
        self.demographics_panel = StaffResidentDemographics(self.staff_id)
        self.pages.addWidget(self.demographics_panel)

        # Page 4: Infographics
        self.infographics_panel = StaffInfographics(self.staff_id)
        self.pages.addWidget(self.infographics_panel)

        # Safe signal connections with debouncing
        self.resident_profiles.residents_changed.connect(self.safe_handle_residents_changed)
        self.requests_panel.requests_changed.connect(self.safe_handle_requests_changed)
        self.resident_profiles.residents_changed.connect(self.infographics_panel.safe_refresh_data)
        self.requests_panel.requests_changed.connect(self.infographics_panel.safe_refresh_data)

    # -------------------------
    # DB Helpers (no changes)
    # -------------------------
    def get_user_info(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username, role FROM staff WHERE id=%s", (self.staff_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            return {"username": user["username"], "role": user["role"]}
        else:
            return {"username": "Unknown", "role": "Staff"}

    def get_metrics(self):
        conn = get_connection()
        cursor = conn.cursor()

        # Docs processed today (staff_activity filtering kept same)
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM staff_activity
            WHERE staff_id=%s AND DATE(created_at)=CURDATE() 
              AND action_type LIKE '%%REQUEST%%'
        """, (self.staff_id,))
        processed = cursor.fetchone()["total"] or 0

        # Residents added today
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM staff_activity
            WHERE staff_id=%s AND DATE(created_at)=CURDATE() 
              AND action_type='ADD_RESIDENT'
        """, (self.staff_id,))
        residents_added = cursor.fetchone()["total"] or 0

        cursor.close()
        conn.close()
        return processed, residents_added

    def get_recent_activities(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT action_type, description, created_at
            FROM staff_activity
            WHERE staff_id=%s
            ORDER BY created_at DESC
            LIMIT 5
        """, (self.staff_id,))
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        return logs

    # -------------------------
    # UI Builders
    # -------------------------
    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(260)

        layout = QVBoxLayout(sidebar)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 20, 0, 20)

        # Logo + Title Container
        logo_container = QWidget()
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(20, 0, 20, 20)
        logo_layout.setSpacing(12)

        # Logo Image (scale safely, don't force crop)
        logo_image = QLabel()
        if os.path.exists(self.logo_path):
            pix = QPixmap(self.logo_path)
            # scale preserving aspect ratio, but allow layout to size it (avoid fixed cropping)
            scaled = pix.scaledToWidth(56, Qt.TransformationMode.SmoothTransformation)
            logo_image.setPixmap(scaled)
            logo_image.setMaximumSize(scaled.size())
        else:
            # fallback emoji or small placeholder
            logo_image.setText("🏛️")
            logo_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_image.setFixedSize(48, 48)

        # Text Container
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        logo_label = QLabel("BRIMS")
        logo_label.setObjectName("logoLabel")

        subtitle = QLabel("Barangay Management")
        subtitle.setObjectName("subtitleLabel")

        text_layout.addWidget(logo_label)
        text_layout.addWidget(subtitle)

        logo_layout.addWidget(logo_image)
        logo_layout.addWidget(text_container)
        logo_layout.addStretch()

        layout.addWidget(logo_container)
        layout.addSpacing(10)

        # Navigation Buttons
        btn_dashboard = self.create_nav_button("🏠", "Dashboard")
        btn_residents = self.create_nav_button("👤", "Resident Profiles")
        btn_requests = self.create_nav_button("📄", "Requests")
        btn_demographics = self.create_nav_button("📈", "Resident Demographics")
        btn_infographics = self.create_nav_button("📊", "Infographics")

        # Collect for styling / highlight management
        self.sidebar_buttons = [
            btn_dashboard, btn_residents, btn_requests, btn_demographics, btn_infographics
        ]

        # Connections (with highlighting)
        btn_dashboard.clicked.connect(lambda: (self.pages.setCurrentIndex(0), self.set_active_button(btn_dashboard)))
        btn_residents.clicked.connect(lambda: (self.pages.setCurrentIndex(1), self.set_active_button(btn_residents)))
        btn_requests.clicked.connect(lambda: (self.pages.setCurrentIndex(2), self.set_active_button(btn_requests)))
        btn_demographics.clicked.connect(lambda: (self.pages.setCurrentIndex(3), self.set_active_button(btn_demographics)))
        btn_infographics.clicked.connect(lambda: (self.pages.setCurrentIndex(4), self.set_active_button(btn_infographics)))

        # Add nav widgets
        layout.addWidget(btn_dashboard)
        layout.addWidget(btn_residents)
        layout.addWidget(btn_requests)
        layout.addWidget(btn_demographics)
        layout.addWidget(btn_infographics)

        layout.addStretch()

        # Logout button at bottom
        btn_logout = QPushButton("🚪  Logout")
        btn_logout.setObjectName("logoutButton")
        btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_logout.setMinimumHeight(44)
        btn_logout.clicked.connect(self.logout)
        layout.addWidget(btn_logout)

        # Default highlight Dashboard
        self.set_active_button(btn_dashboard)

        return sidebar

    def create_nav_button(self, icon, text):
        """Create a navigation button with icon and text"""
        btn = QPushButton(f"{icon}  {text}")
        btn.setObjectName("navButton")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(44)
        # allow stylesheet to highlight by property 'active'
        btn.setProperty("active", False)
        return btn

    def create_dashboard_content(self):
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("dashboardScroll")

        content = QWidget()
        content.setObjectName("dashboardContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(25)

        # Header (Title + User Info)
        header = QFrame()
        header.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("Dashboard")
        title_label.setObjectName("pageTitle")
        # optional font sizing for title to be visible
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignLeft)

        header_layout.addStretch()

        # User badge (dynamic initials from username)
        user = self.get_user_info()
        username = user.get("username", "Unknown")
        initials = "".join(part[:1] for part in username.split()[:2]).upper() or "UK"

        user_badge = QFrame()
        user_badge.setObjectName("userBadge")
        user_badge_layout = QHBoxLayout(user_badge)
        user_badge_layout.setContentsMargins(15, 10, 15, 10)
        user_badge_layout.setSpacing(10)

        user_icon = QLabel(initials)
        user_icon.setObjectName("userIcon")
        user_icon.setFixedSize(40, 40)
        user_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        user_info = QWidget()
        user_info_layout = QVBoxLayout(user_info)
        user_info_layout.setContentsMargins(0, 0, 0, 0)
        user_info_layout.setSpacing(0)

        user_name = QLabel(f"{username}")
        user_name.setObjectName("userName")
        user_role = QLabel(user.get("role", "Staff"))
        user_role.setObjectName("userRole")

        user_info_layout.addWidget(user_name)
        user_info_layout.addWidget(user_role)

        user_badge_layout.addWidget(user_icon)
        user_badge_layout.addWidget(user_info)

        header_layout.addWidget(user_badge)

        content_layout.addWidget(header)

        # Metrics Cards Row
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(20)

        processed, residents_added = self.get_metrics()
        self.processed_card = self.create_metric_card(
            "My Processed Today",
            str(processed),
            "✓",
            "#10B981"
        )
        self.residents_card = self.create_metric_card(
            "Residents Added",
            str(residents_added),
            "👥",
            "#3B82F6"
        )

        # store label references for updates
        self.processed_value = self.processed_card.findChild(QLabel, "metricValue")
        self.residents_added_value = self.residents_card.findChild(QLabel, "metricValue")

        metrics_row.addWidget(self.processed_card)
        metrics_row.addWidget(self.residents_card)
        metrics_row.addStretch()

        content_layout.addLayout(metrics_row)

        # Bottom Section (Recent Activities + Today's Progress)
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(20)

        # Recent Activities Card
        self.activities_card = self.create_activities_card()
        bottom_row.addWidget(self.activities_card, 2)

        # Today's Progress Card
        self.progress_card = self.create_progress_card(processed, residents_added)
        bottom_row.addWidget(self.progress_card, 1)

        content_layout.addLayout(bottom_row)
        content_layout.addStretch()

        scroll.setWidget(content)
        return scroll

    def create_metric_card(self, title, value, icon, color):
        """Create a metric card with left accent and icon"""
        card = QFrame()
        card.setObjectName("metricCard")
        card.setProperty("borderColor", color)
        card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # Text section
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setObjectName("metricTitle")

        value_label = QLabel(value)
        value_label.setObjectName("metricValue")

        text_layout.addWidget(title_label)
        text_layout.addWidget(value_label)

        # Icon badge
        icon_label = QLabel(icon)
        icon_label.setObjectName("metricIcon")
        icon_label.setStyleSheet(f"background-color: {color}; color: white; font-size: 16px; border-radius: 18px;")
        icon_label.setFixedSize(38, 38)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(text_widget)
        card_layout.addStretch()
        card_layout.addWidget(icon_label)

        return card

    def create_activities_card(self):
        """Create Recent Activities card"""
        card = QFrame()
        card.setObjectName("sectionCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(25, 25, 25, 25)
        card_layout.setSpacing(15)

        # Header
        header = QLabel("Recent Activities")
        header.setObjectName("cardTitle")
        card_layout.addWidget(header)

        subtitle = QLabel("Latest updates in the barangay system")
        subtitle.setObjectName("cardSubtitle")
        card_layout.addWidget(subtitle)

        # Activities list container
        self.activities_container = QWidget()
        self.activities_layout = QVBoxLayout(self.activities_container)
        self.activities_layout.setContentsMargins(0, 10, 0, 0)
        self.activities_layout.setSpacing(15)

        activities = self.get_recent_activities()
        for log in activities:
            # ✅ Now we also pass created_at
            created_time = log['created_at'].strftime("%b %d, %Y · %I:%M %p") if log['created_at'] else "N/A"
            activity_item = self.create_activity_item(
                log['description'],
                log['action_type'].lower(),
                created_time
            )
            self.activities_layout.addWidget(activity_item)

        card_layout.addWidget(self.activities_container)
        card_layout.addStretch()

        return card

    def create_activity_item(self, description, tag_type, created_time):
        """Create a single activity item with bullet, tag, and timestamp"""
        item = QFrame()
        item.setObjectName("activityItem")

        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(10, 12, 10, 12)
        item_layout.setSpacing(12)

        # Purple bullet
        bullet = QLabel("●")
        bullet.setObjectName("activityBullet")
        bullet.setFixedWidth(15)

        # Description text block
        desc_widget = QWidget()
        desc_layout = QVBoxLayout(desc_widget)
        desc_layout.setContentsMargins(0, 0, 0, 0)
        desc_layout.setSpacing(2)

        # Parse description title
        parts = description.split(" - ", 1) if " - " in description else [description, ""]
        title_label = QLabel(parts[0])
        title_label.setObjectName("activityTitle")
        desc_layout.addWidget(title_label)

        if len(parts) > 1 and parts[1].strip():
            name_label = QLabel(parts[1])
            name_label.setObjectName("activityName")
            desc_layout.addWidget(name_label)

        # ✅ Add date label (created_at)
        date_label = QLabel(created_time)
        date_label.setObjectName("activityDate")
        date_label.setStyleSheet("color: #94A3B8; font-size: 10px;")
        desc_layout.addWidget(date_label)

        # Tag badge
        tag_label = QLabel(tag_type.replace("_", " "))
        tag_label.setObjectName(f"activityTag_{tag_type}")
        tag_label.setProperty("tagType", tag_type)
        tag_label.setFixedHeight(22)

        item_layout.addWidget(bullet)
        item_layout.addWidget(desc_widget)
        item_layout.addStretch()
        item_layout.addWidget(tag_label)

        return item

    def create_progress_card(self, processed, residents_added):
        """Create Today's Progress card"""
        card = QFrame()
        card.setObjectName("sectionCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(25, 25, 25, 25)
        card_layout.setSpacing(15)

        # Header
        header = QLabel("Today's Progress")
        header.setObjectName("cardTitle")
        card_layout.addWidget(header)

        subtitle = QLabel("Your daily performance metrics")
        subtitle.setObjectName("cardSubtitle")
        card_layout.addWidget(subtitle)

        card_layout.addSpacing(10)

        # Status items
        self.status_item = self.create_status_item("🟢", "Work Status", "Active")
        self.processed_item = self.create_status_item("📄", "Processed Today", f"{processed} docs")
        self.added_item = self.create_status_item("👥", "Residents Added", f"{residents_added} today")

        card_layout.addWidget(self.status_item)
        card_layout.addWidget(self.processed_item)
        card_layout.addWidget(self.added_item)
        card_layout.addStretch()

        return card

    def create_status_item(self, icon, label, value):
        """Create a status item row"""
        item = QFrame()
        item.setObjectName("statusItem")

        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(15, 12, 15, 12)
        item_layout.setSpacing(12)

        icon_label = QLabel(icon)
        icon_label.setFixedWidth(20)

        text_label = QLabel(label)
        text_label.setObjectName("statusLabel")

        value_label = QLabel(value)
        value_label.setObjectName("statusValue")

        item_layout.addWidget(icon_label)
        item_layout.addWidget(text_label)
        item_layout.addStretch()
        item_layout.addWidget(value_label)

        return item

    def set_active_button(self, active_button):
        """Reset all sidebar buttons, then highlight the active one."""
        for btn in self.sidebar_buttons:
            btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        active_button.setProperty("active", True)
        active_button.style().unpolish(active_button)
        active_button.style().polish(active_button)

    def logout(self):
        reply = QMessageBox.question(
            self,
            "Confirm Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            from Panels.login import LoginPage
            self.close()
            self.login_page = LoginPage()
            self.login_page.show()

    def safe_handle_residents_changed(self):
        """Safely handle residents changed signal with debouncing"""
        if self._refresh_pending:
            return

        self._refresh_pending = True
        QTimer.singleShot(200, self._execute_residents_refresh)

    def _execute_residents_refresh(self):
        """Execute the actual refresh after delay"""
        try:
            # Only refresh if we're on a relevant page
            current_index = self.pages.currentIndex()
            if current_index == 0:  # Dashboard
                self.refresh_dashboard()
            elif current_index == 3:  # Demographics
                self.demographics_panel.update_charts()
            elif current_index == 4:  # Infographics
                self.infographics_panel.refresh_data()

            # Always refresh dashboard metrics
            self.refresh_dashboard_metrics()

        except Exception as e:
            print(f"Error during residents refresh: {e}")
        finally:
            self._refresh_pending = False

    def safe_handle_requests_changed(self):
        """Safely handle requests changed signal with debouncing"""
        QTimer.singleShot(200, self._execute_requests_refresh)

    def _execute_requests_refresh(self):
        """Execute the actual requests refresh after delay"""
        try:
            current_index = self.pages.currentIndex()
            if current_index == 0:  # Dashboard
                self.refresh_dashboard()
            elif current_index == 4:  # Infographics
                self.infographics_panel.refresh_data()

            self.refresh_dashboard_metrics()

        except Exception as e:
            print(f"Error during requests refresh: {e}")

    def refresh_dashboard_metrics(self):
        """Refresh only the metric numbers without rebuilding UI"""
        try:
            processed, residents_added = self.get_metrics()

            # Update top card labels
            if hasattr(self, "processed_value") and self.processed_value:
                self.processed_value.setText(str(processed))
            if hasattr(self, "residents_added_value") and self.residents_added_value:
                self.residents_added_value.setText(str(residents_added))

            # Update progress card values
            progress_items = self.progress_card.findChildren(QFrame, "statusItem")
            if len(progress_items) >= 3:
                processed_value = progress_items[1].findChild(QLabel, "statusValue")
                if processed_value:
                    processed_value.setText(f"{processed} docs")

                added_value = progress_items[2].findChild(QLabel, "statusValue")
                if added_value:
                    added_value.setText(f"{residents_added} today")

            # Update activities
            self.refresh_activities_list()

        except Exception as e:
            print(f"Error refreshing dashboard metrics: {e}")

    def refresh_activities_list(self):
        """Refresh only the activities list"""
        try:
            logs = self.get_recent_activities()

            # Clear old widgets safely
            for i in reversed(range(self.activities_layout.count())):
                item = self.activities_layout.itemAt(i)
                if item and item.widget():
                    item.widget().deleteLater()

            # Add new activities
            for log in logs:
                created_time = log['created_at'].strftime("%b %d, %Y · %I:%M %p") if log['created_at'] else "N/A"
                activity_item = self.create_activity_item(
                    log['description'],
                    log['action_type'].lower(),
                    created_time  # ✅ Now including created_time
                )
                self.activities_layout.addWidget(activity_item)

        except Exception as e:
            print(f"Error refreshing activities: {e}")

    def refresh_dashboard(self):
        """Refresh the entire dashboard (use sparingly)"""
        try:
            current_index = self.pages.currentIndex()
            if current_index == 0:  # Only refresh if we're on dashboard
                self.refresh_dashboard_metrics()
        except Exception as e:
            print(f"Error in refresh_dashboard: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashboardWindow(staff_id=1)
    window.showMaximized()
    sys.exit(app.exec())

