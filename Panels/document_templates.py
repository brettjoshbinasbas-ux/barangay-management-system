# document_templates.py

# Sample document templates
def generate_barangay_clearance(resident_name, address, purpose="Employment"):
    return f"""
BARANGAY CLEARANCE

TO WHOM IT MAY CONCERN:

This is to certify that {resident_name}, of legal age, and a bonafide resident of {address}, 
is known to this Barangay to be a person of good moral character and has no derogatory record 
in this office.

This clearance is issued upon the request of {resident_name} for {purpose.lower()} purposes.

Issued this ______ day of ____________, 20__ at Barangay ______________.

_________________________
Barangay Captain
"""


def generate_certificate_of_residency(resident_name, address, length_of_residency="5 years"):
    return f"""
CERTIFICATE OF RESIDENCY

TO WHOM IT MAY CONCERN:

This is to certify that {resident_name} is a bona fide resident of {address} 
and has been residing in this barangay for {length_of_residency}.

This certification is issued upon the request of {resident_name} for whatever 
legal purpose it may serve.

Issued this ______ day of ____________, 20__ at Barangay ______________.

_________________________
Barangay Captain
"""


def generate_barangay_id(resident_name, address, birth_date, birth_place, civil_status):
    return f"""
BARANGAY IDENTIFICATION CARD

This certifies that:

NAME: {resident_name}
ADDRESS: {address}
DATE OF BIRTH: {birth_date}
PLACE OF BIRTH: {birth_place}
CIVIL STATUS: {civil_status}

is a registered resident of Barangay ______________ and is hereby issued 
this Identification Card valid for one (1) year from date of issue.

Issued this ______ day of ____________, 20__.

_________________________
Barangay Captain

[Photo Here] [Signature of Bearer]
"""


def generate_indigency_certificate(resident_name, address, purpose="Medical Assistance"):
    return f"""
CERTIFICATE OF INDIGENCY

TO WHOM IT MAY CONCERN:

This is to certify that {resident_name}, of legal age, and a resident of {address}, 
belongs to an indigent family in this barangay.

This certification is issued upon the request of {resident_name} to avail of 
{purpose.lower()} from your office.

Issued this ______ day of ____________, 20__ at Barangay ______________.

_________________________
Barangay Captain
"""


def generate_business_permit(business_name, owner_name, business_address, business_type):
    return f"""
BARANGAY BUSINESS PERMIT

This is to certify that {business_name} owned by {owner_name} located at 
{business_address} engaged in {business_type} business has complied with 
all the requirements and is hereby granted a permit to operate.

This permit is valid for one calendar year unless sooner revoked.

Issued this ______ day of ____________, 20__ at Barangay ______________.

_________________________
Barangay Captain
"""


def generate_barangay_clearance_for_travel(resident_name, address, destination, travel_companions=""):
    companions_text = f" together with {travel_companions}" if travel_companions else ""
    return f"""
TRAVEL CLEARANCE

TO WHOM IT MAY CONCERN:

This is to certify that {resident_name}, a resident of {address}, 
is traveling to {destination}{companions_text}.

The purpose of travel is for personal/family matters.

This Barangay Clearance is issued for travel purposes.

Issued this ______ day of ____________, 20__ at Barangay ______________.

_________________________
Barangay Captain
"""


# Example usage:
if __name__ == "__main__":
    resident_name = "Juan Dela Cruz"
    address = "123 Main Street, Barangay Sample"

    print("=== BARANGAY CLEARANCE ===")
    print(generate_barangay_clearance(resident_name, address))

    print("\n=== CERTIFICATE OF RESIDENCY ===")
    print(generate_certificate_of_residency(resident_name, address, "3 years"))

    print("\n=== INDIGENCY CERTIFICATE ===")
    print(generate_indigency_certificate(resident_name, address, "Educational Assistance"))

    print("\n=== BUSINESS PERMIT ===")
    print(generate_business_permit(
        "Juan's Sari-Sari Store",
        resident_name,
        address,
        "retail grocery"
    ))

def generate_solo_parent_certificate(resident_name, address, children_names):
    children_list = ", ".join(children_names)
    return f"""
SOLO PARENT CERTIFICATION

TO WHOM IT MAY CONCERN:

This is to certify that {resident_name}, of legal age, and a resident of {address}, 
is a solo parent with dependent children named: {children_list}.

This certification is issued upon the request of {resident_name} for whatever 
legal purpose it may serve, particularly for availing benefits under the 
Solo Parents Welfare Act.

Issued this ______ day of ____________, 20__ at Barangay ______________.

_________________________
Barangay Captain
"""

def generate_first_time_jobseeker_certificate(resident_name, address):
    return f"""
CERTIFICATION FOR FIRST-TIME JOBSEEKER

TO WHOM IT MAY CONCERN:

This is to certify that {resident_name}, of legal age, and a resident of {address}, 
is a first-time jobseeker as defined under Republic Act No. 11261 (First Time 
Jobseekers Assistance Act).

This certification is issued to avail of the privileges and exemptions provided 
by the said law.

Issued this ______ day of ____________, 20__ at Barangay ______________.

_________________________
Barangay Captain
"""

def generate_cedula(resident_name, address, birth_date, civil_status, profession, income_range):
    return f"""
COMMUNITY TAX CERTIFICATE (CEDULA)

Name: {resident_name}
Address: {address}
Date of Birth: {birth_date}
Civil Status: {civil_status}
Profession/Occupation: {profession}
Gross Receipts/Earnings: {income_range}

This Community Tax Certificate is issued pursuant to the provisions of Republic Act 
No. 7160 to {resident_name} upon payment of the corresponding community tax.

Issued this ______ day of ____________, 20__ at Barangay ______________.

_________________________
Barangay Treasurer
"""