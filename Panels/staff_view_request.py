# staff_view_request.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QTextEdit, QLabel, QFrame, QHBoxLayout
)
from PyQt6.QtCore import Qt
from Panels.db import get_connection
from Panels.document_templates import (
    generate_barangay_clearance,
    generate_certificate_of_residency,
    generate_barangay_id,
    generate_indigency_certificate,
    generate_business_permit,
    generate_barangay_clearance_for_travel,
    generate_solo_parent_certificate,
    generate_first_time_jobseeker_certificate,
    generate_cedula,
)


class ViewRequestDialog(QDialog):
    """
    Displays the generated document text and essential request metadata.
    Includes Completed Date and Status from the database.
    """

    def __init__(self, parent=None, request_id=None):
        super().__init__(parent)
        self.setWindowTitle("View Document")
        self.resize(600, 800)  # Portrait-like style

        layout = QVBoxLayout(self)

        # --- Header Section (Metadata) ---
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)

        self.lbl_title = QLabel("📄 Document Request Details")
        self.lbl_title.setObjectName("headerTitle")
        self.lbl_title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #333;")

        self.lbl_info = QLabel("")  # Will contain metadata (resident, type, status)
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setStyleSheet("font-size: 10pt; color: #555;")

        header_layout.addWidget(self.lbl_title)
        header_layout.addWidget(self.lbl_info)
        layout.addWidget(header_frame)

        # --- Document Viewer (Main Body) ---
        self.document_view = QTextEdit()
        self.document_view.setReadOnly(True)
        self.document_view.setStyleSheet("""
            QTextEdit {
                font-family: "Times New Roman";
                font-size: 14pt;
                padding: 20px;
                background: #fff;
                border: 1px solid #ccc;
            }
        """)
        layout.addWidget(self.document_view, stretch=1)

        # --- Buttons ---
        button_frame = QFrame()
        btn_layout = QHBoxLayout(button_frame)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_close)

        layout.addWidget(button_frame)

        # --- Load Content ---
        self.load_document(request_id)

    # ---------------------------------
    # Database + Template Rendering
    # ---------------------------------
    def load_document(self, request_id):
        """Load document info from DB and render it using a template."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                r.id,
                res.name AS resident_name,
                res.address,
                r.document_type,
                r.purpose,
                r.request_date,
                r.status,
                r.completed_date
            FROM requests r
            JOIN residents res ON r.resident_id = res.id
            WHERE r.id=%s
        """, (request_id,))
        req = cursor.fetchone()
        cursor.close()
        conn.close()

        if not req:
            self.document_view.setPlainText("⚠️ Request not found.")
            return

        # --- Display metadata ---
        status_color = {
            "Pending": "#d39e00",
            "In Progress": "#007bff",
            "Completed": "#28a745"
        }.get(req["status"], "#333")

        completed_text = (
            f"✅ Completed on {req['completed_date'].strftime('%b %d, %Y')}"
            if req["completed_date"] else "⏳ Not completed yet"
        )

        self.lbl_info.setText(
            f"""
            <b>Resident:</b> {req['resident_name']}<br>
            <b>Address:</b> {req['address']}<br>
            <b>Document Type:</b> {req['document_type']}<br>
            <b>Purpose:</b> {req['purpose']}<br>
            <b>Request Date:</b> {req['request_date']}<br>
            <b>Status:</b> <span style="color:{status_color}; font-weight:bold;">{req['status']}</span><br>
            <b>{completed_text}</b>
            """
        )

        # --- Generate the document body using proper template ---
        doc_type = req["document_type"]
        doc_text = self.generate_document_text(doc_type, req)

        self.document_view.setPlainText(doc_text)

    # ---------------------------------
    # Template Dispatcher
    # ---------------------------------
    def generate_document_text(self, doc_type, req):
        """Selects and calls the right generator function."""
        name, address, purpose = req["resident_name"], req["address"], req["purpose"]

        if doc_type == "Barangay Clearance":
            return generate_barangay_clearance(name, address, purpose)
        elif doc_type == "Certificate of Residency":
            return generate_certificate_of_residency(name, address, "5 years")
        elif doc_type == "Barangay ID":
            return generate_barangay_id(name, address, "01-01-1990", "Quezon City", "Single")
        elif doc_type == "Indigency Certificate":
            return generate_indigency_certificate(name, address, purpose)
        elif doc_type == "Business Permit":
            return generate_business_permit("Sample Store", name, address, "Retail")
        elif doc_type == "Travel Clearance":
            return generate_barangay_clearance_for_travel(name, address, "Manila")
        elif doc_type == "Solo Parent Certificate":
            return generate_solo_parent_certificate(name, address, ["Child A", "Child B"])
        elif doc_type == "First-time Jobseeker Certificate":
            return generate_first_time_jobseeker_certificate(name, address)
        elif doc_type == "Cedula":
            return generate_cedula(name, address, "01-01-1990", "Single", "Clerk", "₱100,000")
        else:
            return f"⚠️ No template found for document type: {doc_type}"
