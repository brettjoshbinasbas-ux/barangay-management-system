# admin_dashboard.py
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QMessageBox, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont

from Panels.db import get_connection
from admin_worker_management import AdminWorkerManagement
from staff_infographics import StaffInfographics
from admin_reports import AdminReports
from Panels.admin_requests import AdminRequests
from Panels.admin_residents import AdminResidents
from admin_StaffActivityHistory import StaffActivityHistory
from admin_AdminActivityHistory import AdminActivityHistory


class AdminDashboard(QMainWindow):
    def __init__(self, admin_id):
        super().__init__()
        self.admin_id = admin_id
        self._refresh_pending = False  # ⬅️ ADDED: Prevent multiple rapid refreshes

        # --- Project Paths ---
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        styles_dir = os.path.join(base_dir, "Styles")
        images_dir = os.path.join(base_dir, "Images")

        qss_path = os.path.join(styles_dir, "admin_dashboard.qss")
        logo_path = os.path.join(images_dir, "BRIMS_logo.png")

        self.logo_path = logo_path

        if os.path.exists(qss_path):
            with open(qss_path, "r") as style_file:
                self.setStyleSheet(style_file.read())
        else:
            print(f"⚠️ Could not find QSS file at {qss_path}")

        self.setWindowTitle("BRIMS - Admin Panel")
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

        # Initialize pages with signal connections
        self.initialize_pages()

        # Start with Dashboard
        self.pages.setCurrentIndex(0)

        # Load dashboard data
        QTimer.singleShot(100, self.refresh_dashboard)  # ⬅️ ADDED: Delayed initial load

    def initialize_pages(self):
        """Initialize all pages with safe signal connections"""
        # Page 0: Dashboard Content
        self.dashboard_content = self.create_dashboard_content()
        self.pages.addWidget(self.dashboard_content)

        # Page 1: Worker Management
        self.worker_management_panel = AdminWorkerManagement(admin_id=self.admin_id)
        self.pages.addWidget(self.worker_management_panel)

        # Page 2: Residents Management
        self.residents_panel = AdminResidents(admin_id=self.admin_id)
        self.pages.addWidget(self.residents_panel)

        # Page 3: Requests Management
        self.requests_panel = AdminRequests(admin_id=self.admin_id)
        self.pages.addWidget(self.requests_panel)

        # ✅ ADD THESE TWO NEW PAGES:
        # Page 4: Staff Activities
        self.staff_activities_panel = StaffActivityHistory(admin_id=self.admin_id)
        self.pages.addWidget(self.staff_activities_panel)

        # Page 5: Admin Activities
        self.admin_activities_panel = AdminActivityHistory(admin_id=self.admin_id)
        self.pages.addWidget(self.admin_activities_panel)

        # Page 6: Reports & Analytics (Admin) - ✅ CHANGED from 4 to 6
        self.reports_panel = AdminReports()
        self.pages.addWidget(self.reports_panel)

        # Page 7: Staff Infographics - ✅ CHANGED from 5 to 7
        self.infographics_panel = StaffInfographics()
        self.pages.addWidget(self.infographics_panel)

        # ✅ ADDED: Auto-refresh signal connections
        self.worker_management_panel.workers_changed.connect(self.safe_refresh_dashboard)
        self.residents_panel.residents_changed.connect(self.safe_refresh_dashboard)
        self.requests_panel.requests_changed.connect(self.safe_refresh_dashboard)

    def safe_refresh_dashboard(self):
        """Safely refresh dashboard with debouncing"""
        if self._refresh_pending:
            return

        self._refresh_pending = True
        QTimer.singleShot(200, self._execute_dashboard_refresh)

    def _execute_dashboard_refresh(self):
        """Execute the actual refresh after delay"""
        try:
            self.refresh_dashboard()
        except Exception as e:
            print(f"Error refreshing admin dashboard: {e}")
        finally:
            self._refresh_pending = False

    # -------------------------
    # DB Helpers
    # -------------------------
    def get_user_info(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM admins WHERE id=%s", (self.admin_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            return {"username": user["username"], "role": "Admin"}
        else:
            return {"username": "Unknown", "role": "Admin"}

    def get_metrics(self):
        conn = get_connection()
        cursor = conn.cursor()

        # Total documents processed today
        cursor.execute("SELECT COUNT(*) AS total FROM requests WHERE DATE(created_at) = CURDATE()")
        processed = cursor.fetchone()["total"] or 0

        # Total residents added today
        cursor.execute("SELECT COUNT(*) AS total FROM residents WHERE DATE(created_at) = CURDATE()")
        residents_added = cursor.fetchone()["total"] or 0

        cursor.close()
        conn.close()
        return processed, residents_added

    def get_recent_activities(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT 'Staff' AS role, sa.action_type, sa.description, sa.created_at, s.username
            FROM staff_activity sa
            JOIN staff s ON sa.staff_id = s.id

            UNION ALL

            SELECT 'Admin' AS role, aa.action_type, aa.description, aa.created_at, a.username
            FROM admin_activity aa
            JOIN admins a ON aa.admin_id = a.id

            ORDER BY created_at DESC
            LIMIT 5
        """)
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

        # Logo + Title Container (existing code remains the same)
        logo_container = QWidget()
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(20, 0, 20, 20)
        logo_layout.setSpacing(12)

        # Logo Image (existing code remains the same)
        logo_image = QLabel()
        if os.path.exists(self.logo_path):
            pix = QPixmap(self.logo_path)
            scaled = pix.scaledToWidth(56, Qt.TransformationMode.SmoothTransformation)
            logo_image.setPixmap(scaled)
            logo_image.setMaximumSize(scaled.size())
        else:
            logo_image.setText("🏛️")
            logo_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_image.setFixedSize(48, 48)

        # Text Container (existing code remains the same)
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        logo_label = QLabel("BRIMS")
        logo_label.setObjectName("logoLabel")

        subtitle = QLabel("Admin Panel")
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
        btn_worker_management = self.create_nav_button("👤", "Worker Management")
        btn_residents = self.create_nav_button("👥", "Residents")
        btn_requests = self.create_nav_button("📄", "Requests")

        # ✅ ADD THESE TWO NEW BUTTONS RIGHT HERE:
        btn_staff_activities = self.create_nav_button("📋", "Staff Activities")
        btn_admin_activities = self.create_nav_button("📝", "Admin Activities")

        btn_reports_admin = self.create_nav_button("📉", "Reports (Admin)")
        btn_reports_staff = self.create_nav_button("📊", "Infographics (Staff View)")

        # Collect for styling / highlight management
        self.sidebar_buttons = [
            btn_dashboard, btn_worker_management, btn_residents,
            btn_requests, btn_staff_activities, btn_admin_activities,  # ✅ ADD NEW BUTTONS
            btn_reports_admin, btn_reports_staff
        ]

        # Connections (with highlighting)
        btn_dashboard.clicked.connect(
            lambda: (
                self.pages.setCurrentIndex(0), self.set_active_button(btn_dashboard), self.safe_refresh_dashboard())
        )
        btn_worker_management.clicked.connect(
            lambda: (self.pages.setCurrentIndex(1), self.set_active_button(btn_worker_management))
        )
        btn_residents.clicked.connect(
            lambda: (
                self.pages.setCurrentIndex(2),
                self.set_active_button(btn_residents),
                self.residents_panel.load_residents()
            )
        )
        btn_requests.clicked.connect(
            lambda: (self.pages.setCurrentIndex(3), self.set_active_button(btn_requests))
        )

        # ✅ ADD THESE NEW CONNECTIONS:
        btn_staff_activities.clicked.connect(
            lambda: (self.pages.setCurrentIndex(4), self.set_active_button(btn_staff_activities))
        )
        btn_admin_activities.clicked.connect(
            lambda: (self.pages.setCurrentIndex(5), self.set_active_button(btn_admin_activities))
        )

        btn_reports_admin.clicked.connect(
            lambda: (self.pages.setCurrentIndex(6), self.set_active_button(btn_reports_admin))  # ✅ CHANGED from 4 to 6
        )
        btn_reports_staff.clicked.connect(
            lambda: (self.pages.setCurrentIndex(7), self.set_active_button(btn_reports_staff))  # ✅ CHANGED from 5 to 7
        )

        # Add nav widgets
        layout.addWidget(btn_dashboard)
        layout.addWidget(btn_worker_management)
        layout.addWidget(btn_residents)
        layout.addWidget(btn_requests)

        # ✅ ADD NEW BUTTONS TO LAYOUT:
        layout.addWidget(btn_staff_activities)
        layout.addWidget(btn_admin_activities)

        layout.addWidget(btn_reports_admin)
        layout.addWidget(btn_reports_staff)

        layout.addStretch()

        # Logout button at bottom (existing code remains the same)
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
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignLeft)

        header_layout.addStretch()

        # User badge
        user = self.get_user_info()
        username = user.get("username", "Unknown")
        initials = "".join(part[:1] for part in username.split()[:2]).upper() or "AD"

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
        user_role = QLabel(user.get("role", "Admin"))
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

        # Get total residents for the main metric
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM residents")
        total_residents = cursor.fetchone()["total"] or 0
        cursor.close()
        conn.close()

        self.total_residents_card = self.create_metric_card(
            "Total Residents",
            f"{total_residents:,}",
            "👥",
            "#3B82F6"
        )
        self.processed_card = self.create_metric_card(
            "Documents Today",
            str(processed),
            "📄",
            "#10B981"
        )
        self.residents_card = self.create_metric_card(
            "New Residents Today",
            str(residents_added),
            "➕",
            "#8B5CF6"
        )

        # Store label references for updates
        self.total_residents_value = self.total_residents_card.findChild(QLabel, "metricValue")
        self.processed_value = self.processed_card.findChild(QLabel, "metricValue")
        self.residents_added_value = self.residents_card.findChild(QLabel, "metricValue")

        metrics_row.addWidget(self.total_residents_card)
        metrics_row.addWidget(self.processed_card)
        metrics_row.addWidget(self.residents_card)
        metrics_row.addStretch()

        content_layout.addLayout(metrics_row)

        # Bottom Section (Recent Activities + System Overview)
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(20)

        # Recent Activities Card
        self.activities_card = self.create_activities_card()
        bottom_row.addWidget(self.activities_card, 2)

        # System Overview Card
        self.overview_card = self.create_overview_card(processed, residents_added)
        bottom_row.addWidget(self.overview_card, 1)

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
            # ✅ IMPROVED: Include timestamp like staff version
            created_time = log['created_at'].strftime("%b %d, %Y · %I:%M %p") if log['created_at'] else "N/A"
            activity_item = self.create_activity_item(
                log['description'],
                log['action_type'].lower(),
                f"{log['username'] or log['role']} · {created_time}"  # ✅ ADDED timestamp
            )
            self.activities_layout.addWidget(activity_item)

        card_layout.addWidget(self.activities_container)
        card_layout.addStretch()

        return card

    def create_activity_item(self, description, tag_type, user_info):
        """Create a single activity item with bullet and tag"""
        item = QFrame()
        item.setObjectName("activityItem")

        item_layout = QHBoxLayout(item)
        item_layout.setContentsMargins(10, 12, 10, 12)
        item_layout.setSpacing(12)

        # Purple bullet
        bullet = QLabel("●")
        bullet.setObjectName("activityBullet")
        bullet.setFixedWidth(15)

        # Description text
        desc_widget = QWidget()
        desc_layout = QVBoxLayout(desc_widget)
        desc_layout.setContentsMargins(0, 0, 0, 0)
        desc_layout.setSpacing(2)

        title_label = QLabel(description)
        title_label.setObjectName("activityTitle")

        name_label = QLabel(user_info)  # Now includes timestamp
        name_label.setObjectName("activityName")

        desc_layout.addWidget(title_label)
        desc_layout.addWidget(name_label)

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

    def create_overview_card(self, processed, residents_added):
        """Create System Overview card"""
        card = QFrame()
        card.setObjectName("sectionCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(25, 25, 25, 25)
        card_layout.setSpacing(15)

        # Header
        header = QLabel("System Overview")
        header.setObjectName("cardTitle")
        card_layout.addWidget(header)

        subtitle = QLabel("Key performance indicators for today")
        subtitle.setObjectName("cardSubtitle")
        card_layout.addWidget(subtitle)

        card_layout.addSpacing(10)

        # Status items
        self.status_item = self.create_status_item("🟢", "System Status", "Active")
        self.processed_item = self.create_status_item("📄", "Documents Processed", f"{processed} total")
        self.added_item = self.create_status_item("👤", "New Registrations", f"{residents_added} today")

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
            from Panels.login import LoginPage  # ✅ FIXED: Correct import path
            self.close()
            self.login_page = LoginPage()
            self.login_page.show()

    def refresh_dashboard(self):
        """Refresh metrics and recent activities dynamically."""
        processed, residents_added = self.get_metrics()

        # Get total residents
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM residents")
        total_residents = cursor.fetchone()["total"] or 0
        cursor.close()
        conn.close()

        # Update top card labels
        if hasattr(self, "total_residents_value") and self.total_residents_value:
            self.total_residents_value.setText(f"{total_residents:,}")
        if hasattr(self, "processed_value") and self.processed_value:
            self.processed_value.setText(str(processed))
        if hasattr(self, "residents_added_value") and self.residents_added_value:
            self.residents_added_value.setText(str(residents_added))

        # Update overview card values
        overview_items = self.overview_card.findChildren(QFrame, "statusItem")
        if len(overview_items) >= 3:
            processed_value = overview_items[1].findChild(QLabel, "statusValue")
            if processed_value:
                processed_value.setText(f"{processed} total")

            added_value = overview_items[2].findChild(QLabel, "statusValue")
            if added_value:
                added_value.setText(f"{residents_added} today")

        # Update activities
        logs = self.get_recent_activities()
        # Clear old widgets
        for i in reversed(range(self.activities_layout.count())):
            item = self.activities_layout.itemAt(i).widget()
            if item:
                item.deleteLater()

        # Add new activities
        for log in logs:
            created_time = log['created_at'].strftime("%b %d, %Y · %I:%M %p") if log['created_at'] else "N/A"
            activity_item = self.create_activity_item(
                log['description'],
                log['action_type'].lower(),
                f"{log['username'] or log['role']} · {created_time}"  # ✅ INCLUDES timestamp
            )
            self.activities_layout.addWidget(activity_item)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdminDashboard(admin_id=1)
    window.showMaximized()
    sys.exit(app.exec())