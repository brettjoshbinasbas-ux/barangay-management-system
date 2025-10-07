import os
from datetime import datetime

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QSizePolicy, QHeaderView, QMessageBox
)
from PyQt6.QtGui import QIcon, QFont

from Panels.db import get_connection
from Panels.logger import log_staff_activity
from Panels.staff_request_dialog import NewRequestDialog
from Panels.staff_view_request import ViewRequestDialog


class StaffRequests(QWidget):
    requests_changed = pyqtSignal()

    def __init__(self, staff_id):
        super().__init__()
        self.staff_id = staff_id
        self.init_ui()
        self.load_requests()

        # --- Load stylesheet ---
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        qss_path = os.path.join(base_dir, "Styles", "staff_requests.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as style_file:
                self.setStyleSheet(style_file.read())

    # ------------------------------
    # UI Setup
    # ------------------------------
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(25)

        # --- Page Title (Top) ---
        page_title = QLabel("Requests")
        page_title.setObjectName("pageTitle")
        page_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Normal))
        page_title.setStyleSheet("color: #1E293B;")
        layout.addWidget(page_title)

        # --- Header Section ---
        header = QFrame()
        header.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Left: Title and Subtitle
        title_layout = QVBoxLayout()
        title_layout.setSpacing(5)

        title_label = QLabel("Document Requests")
        title_label.setObjectName("titleLabel")
        title_label.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #7C3AED;")

        subtitle_label = QLabel("Manage barangay document requests")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setFont(QFont("Segoe UI", 11))
        subtitle_label.setStyleSheet("color: #64748B;")

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        header_layout.addLayout(title_layout)

        header_layout.addStretch()

        # Right: Completed Card + New Request Button
        right_layout = QHBoxLayout()
        right_layout.setSpacing(15)

        # Completed card with green left border
        self.completed_card = QFrame()
        self.completed_card.setObjectName("completedCard")
        self.completed_card.setFixedSize(200, 90)
        self.completed_card.setStyleSheet("""
            QFrame#completedCard {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-left: 4px solid #22C55E;
                border-radius: 8px;
            }
        """)

        card_layout = QVBoxLayout(self.completed_card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(5)

        completed_label = QLabel("Completed")
        completed_label.setObjectName("completedLabel")
        completed_label.setFont(QFont("Segoe UI", 11))
        completed_label.setStyleSheet("color: #64748B;")

        # Number with icon
        number_layout = QHBoxLayout()
        number_layout.setSpacing(10)

        self.completed_number = QLabel("0")
        self.completed_number.setObjectName("completedNumber")
        self.completed_number.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        self.completed_number.setStyleSheet("color: #22C55E;")

        completed_icon = QLabel("✅")
        completed_icon.setFont(QFont("Segoe UI", 24))

        number_layout.addWidget(self.completed_number)
        number_layout.addStretch()
        number_layout.addWidget(completed_icon)

        card_layout.addWidget(completed_label)
        card_layout.addLayout(number_layout)

        btn_new_request = QPushButton("+ New Request")
        btn_new_request.setObjectName("newRequestButton")
        btn_new_request.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        btn_new_request.setFixedHeight(45)
        btn_new_request.setMaximumWidth(150)
        btn_new_request.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_new_request.setStyleSheet("""
            QPushButton#newRequestButton {
                background-color: #7C3AED;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
            }
            QPushButton#newRequestButton:hover {
                background-color: #6D28D9;
            }
            QPushButton#newRequestButton:pressed {
                background-color: #5B21B6;
            }
        """)
        btn_new_request.clicked.connect(self.open_new_request_dialog)

        right_layout.addWidget(self.completed_card)
        right_layout.addWidget(btn_new_request)
        header_layout.addLayout(right_layout)

        layout.addWidget(header)

        # --- Table Section with Container ---
        table_container = QFrame()
        table_container.setObjectName("tableContainer")
        table_container.setStyleSheet("""
            QFrame#tableContainer {
                background-color: white;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
        """)
        table_container_layout = QVBoxLayout(table_container)
        table_container_layout.setContentsMargins(30, 25, 30, 25)
        table_container_layout.setSpacing(15)

        # Table header
        table_header = QLabel("Document Requests")
        table_header.setObjectName("tableHeader")
        table_header.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold))
        table_header.setStyleSheet("color: #1E293B;")
        table_container_layout.addWidget(table_header)

        table_subheader = QLabel("All document requests with their current status")
        table_subheader.setObjectName("tableSubheader")
        table_subheader.setFont(QFont("Segoe UI", 10))
        table_subheader.setStyleSheet("color: #94A3B8;")
        table_container_layout.addWidget(table_subheader)

        # Table widget
        self.table = QTableWidget()
        self.table.setObjectName("requestsTable")
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Resident", "Document Type", "Purpose", "Request Date", "Status", "Actions"]
        )

        # Table styling
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setShowGrid(False)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.setMinimumHeight(400)
        self.table.setStyleSheet("""
            QTableWidget#requestsTable {
                background-color: white;
                border: none;
                gridline-color: transparent;
            }
            QTableWidget#requestsTable::item {
                padding: 8px;
                border-bottom: 1px solid #F1F5F9;
            }
            QTableWidget#requestsTable::item:selected {
                background-color: #F8FAFC;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                color: #64748B;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #E2E8F0;
                font-weight: 600;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
        """)

        table_container_layout.addWidget(self.table)
        layout.addWidget(table_container)

    # ------------------------------
    # Load Requests
    # ------------------------------
    def load_requests(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, res.name AS resident, r.document_type, r.purpose,
                   r.request_date, r.status, r.completed_date
            FROM requests r
            JOIN residents res ON r.resident_id = res.id
            ORDER BY r.created_at DESC
        """)
        requests = cursor.fetchall()
        cursor.close()
        conn.close()


        completed_count = sum(1 for r in requests if r["status"] == "Completed")
        self.completed_number.setText(str(completed_count))

        self.table.setRowCount(len(requests))
        for row, req in enumerate(requests):
            # Format date cleanly (no time)
            if req["request_date"]:
                if isinstance(req["request_date"], str):
                    formatted_date = req["request_date"]  # Keep the full timestamp
                else:
                    formatted_date = req["request_date"].strftime("%Y-%m-%d %H:%M:%S")
            else:
                formatted_date = "N/A"

            # Table items
            items = [
                f"👤 {req['resident']}",
                f"📄 {req['document_type']}",
                req["purpose"],
                f"📅 {formatted_date}"
            ]

            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setFont(QFont("Segoe UI", 10))
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(row, col, item)

            # Status Badge
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(8, 5, 8, 5)
            status_layout.setSpacing(8)
            status_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

            if req["status"] == "Completed":
                status_label = QLabel("✅ Completed")
                status_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
                status_label.setStyleSheet("""
                    background-color: #D1FAE5;
                    color: #059669;
                    padding: 5px 12px;
                    border-radius: 12px;
                """)
                status_layout.addWidget(status_label)

                # Add completion date
                if req["completed_date"]:
                    # completion_info = QLabel(f"Completed {req['completed_date'].strftime('%m/%d/%Y')}")
                    # completion_info.setFont(QFont("Segoe UI", 9))
                    # completion_info.setStyleSheet("color: #94A3B8;")
                    # status_layout.addWidget(completion_info)
                    pass
            else:
                status_label = QLabel(req["status"])
                status_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
                status_label.setStyleSheet("""
                    background-color: #FEF3C7;
                    color: #D97706;
                    padding: 5px 12px;
                    border-radius: 12px;
                """)
                status_layout.addWidget(status_label)

            status_layout.addStretch()
            self.table.setCellWidget(row, 4, status_widget)

            # --- Actions ---
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(8, 5, 8, 5)
            actions_layout.setSpacing(6)

            # Only show "Complete" button for non-completed requests
            if req["status"] != "Completed":
                btn_complete = QPushButton("Complete")
                btn_complete.setObjectName("completeButton")
                btn_complete.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
                btn_complete.setFixedHeight(32)
                btn_complete.setMinimumWidth(90)
                btn_complete.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_complete.setStyleSheet("""
                    QPushButton#completeButton {
                        background-color: #10B981;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 0 12px;
                    }
                    QPushButton#completeButton:hover {
                        background-color: #059669;
                    }
                """)
                btn_complete.clicked.connect(lambda _, rid=req["id"]: self.mark_as_completed(rid))
                actions_layout.addWidget(btn_complete)
            else:
                # Show completion date for completed requests
                completed_label = QLabel(
                    f"Completed {req['completed_date'].strftime('%m/%d/%Y') if req['completed_date'] else ''}")
                completed_label.setFont(QFont("Segoe UI", 9))
                completed_label.setStyleSheet("color: #94A3B8;")
                actions_layout.addWidget(completed_label)

            # Additional action buttons (view, edit, delete) - hidden but functional
            # View Button (icon only for compact display)
            btn_view = QPushButton("👁️‍🗨️")
            btn_view.setObjectName("iconButton")
            btn_view.setFont(QFont("Segoe UI", 12))
            btn_view.setFixedSize(32, 32)
            btn_view.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_view.setToolTip("View Request")
            btn_view.setStyleSheet("""
                QPushButton#iconButton {
                    background-color: #F1F5F9;
                    border: 1px solid #E2E8F0;
                    border-radius: 6px;
                }
                QPushButton#iconButton:hover {
                    background-color: #E2E8F0;
                }
            """)
            btn_view.clicked.connect(lambda _, rid=req["id"]: self.open_view_request(rid))
            actions_layout.addWidget(btn_view)

            # Edit and Delete only for non-completed
            if req["status"] != "Completed":
                btn_edit = QPushButton("📰")
                btn_edit.setObjectName("iconButton")
                btn_edit.setFont(QFont("Segoe UI", 12))
                btn_edit.setFixedSize(32, 32)
                btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_edit.setToolTip("Edit Request")
                btn_edit.setStyleSheet("""
                    QPushButton#iconButton {
                        background-color: #F1F5F9;
                        border: 1px solid #E2E8F0;
                        border-radius: 6px;
                    }
                    QPushButton#iconButton:hover {
                        background-color: #E2E8F0;
                    }
                """)
                btn_edit.clicked.connect(lambda _, rid=req["id"]: self.open_edit_request(rid))
                actions_layout.addWidget(btn_edit)

                btn_delete = QPushButton("🗑️")
                btn_delete.setObjectName("iconButton")
                btn_delete.setFont(QFont("Segoe UI", 12))
                btn_delete.setFixedSize(32, 32)
                btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_delete.setToolTip("Delete Request")
                btn_delete.setStyleSheet("""
                    QPushButton#iconButton {
                        background-color: #FEE2E2;
                        border: 1px solid #FECACA;
                        border-radius: 6px;
                    }
                    QPushButton#iconButton:hover {
                        background-color: #FECACA;
                    }
                """)
                btn_delete.clicked.connect(lambda _, rid=req["id"]: self.delete_request(rid))
                actions_layout.addWidget(btn_delete)

            actions_layout.addStretch()
            self.table.setCellWidget(row, 5, actions)

            # Set row height
            self.table.setRowHeight(row, 60)

    # ------------------------------
    # CRUD + STATUS Operations
    # ------------------------------

    # --- New Request ---
    def open_new_request_dialog(self):
        dialog = NewRequestDialog(self)
        dialog.setModal(True)
        if dialog.exec():
            log_staff_activity(self.staff_id, "ADD_REQUEST", "Created a new document request", role="Staff")
            self.load_requests()
            self.requests_changed.emit()

    # --- Edit Request ---
    def open_edit_request(self, request_id):
        dialog = NewRequestDialog(self, request_id)
        dialog.setModal(True)
        if dialog.exec():
            log_staff_activity(self.staff_id, "EDIT_REQUEST", f"Edited request {request_id}", role="Staff")
            self.load_requests()
            self.requests_changed.emit()

    # --- View Request ---
    def open_view_request(self, request_id):
        dialog = ViewRequestDialog(self, request_id)
        dialog.setModal(True)
        dialog.exec()
        log_staff_activity(self.staff_id, "VIEW_REQUEST", f"Viewed request {request_id}", role="Staff")

    # --- Delete Request ---
    def delete_request(self, request_id):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this request?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM requests WHERE id=%s", (request_id,))
            conn.commit()
            cursor.close()
            conn.close()

            log_staff_activity(self.staff_id, "DELETE_REQUEST", f"Deleted request {request_id}", role="Staff")
            self.load_requests()
            self.requests_changed.emit()

    # --- Mark as Completed ---
    def mark_as_completed(self, request_id):
        """Set request status to Completed with timestamp."""
        conn = get_connection()
        cursor = conn.cursor()

        completed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE requests
            SET status='Completed', completed_date=IFNULL(completed_date, %s)
            WHERE id=%s
        """, (completed_time, request_id))
        conn.commit()
        cursor.close()
        conn.close()

        log_staff_activity(self.staff_id, "COMPLETE_REQUEST", f"Marked request {request_id} as completed", role="Staff")
        QMessageBox.information(self, "Success", "Request marked as completed!")

        self.load_requests()
        self.requests_changed.emit()