import os
import re
import sqlite3
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output"
)

DATABASE_FILE = os.path.join(
    BASE_DIR,
    "consultbae.db"
)


# Create output directory if it doesn't exist

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# Input files

NAUKRI_FILE = os.path.join(
    DATA_DIR,
    "source1_naukri_applicants.csv"
)

GIG_FILE = os.path.join(
    DATA_DIR,
    "source2_gig_workers.csv"
)

CBNEXUS_FILE = os.path.join(
    DATA_DIR,
    "source3_cbnexus_contacts.csv"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_text(value):
    """
    Remove unnecessary whitespace.

    Empty values become None.
    """

    if pd.isna(value):
        return None

    value = str(value).strip()

    if value == "":
        return None

    return value


def normalize_email(value):
    """
    Normalize email addresses.
    """

    value = clean_text(value)

    if value is None:
        return None

    return value.lower()


def normalize_name(value):
    """
    Normalize person names.
    """

    value = clean_text(value)

    if value is None:
        return None

    # Replace multiple spaces with one space

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.title()


def normalize_city(value):
    """
    Normalize city names.
    """

    value = clean_text(value)

    if value is None:
        return None

    city = value.lower().strip()

    city_mapping = {

        # Pune

        "pune": "Pune",

        # Noida

        "noida": "Noida",

        # Gurgaon

        "gurgaon": "Gurgaon",
        "gurugram": "Gurgaon",

        # Delhi

        "delhi": "Delhi",
        "new delhi": "Delhi",
        "delhi ncr": "Delhi",

        # Bengaluru

        "bengaluru": "Bengaluru",
        "bangalore": "Bengaluru",

    }

    return city_mapping.get(
        city,
        value.title()
    )


def normalize_phone(value):
    """
    Normalize Indian phone numbers.

    Examples:

    +91-9000000000
    919000000000
    9000000000

    become:

    9000000000
    """

    value = clean_text(value)

    if value is None:
        return None

    # Keep only digits

    digits = re.sub(
        r"\D",
        "",
        value
    )

    # Remove Indian country code

    if (
        digits.startswith("91")
        and len(digits) == 12
    ):
        digits = digits[2:]

    return digits


def normalize_boolean(value):
    """
    Convert common Yes/No formats
    into True/False.
    """

    value = clean_text(value)

    if value is None:
        return None

    value = value.lower()

    if value in [
        "y",
        "yes",
        "true",
        "verified"
    ]:
        return True

    if value in [
        "n",
        "no",
        "false",
        "unverified"
    ]:
        return False

    return None


def normalize_ctc(value):
    """
    Convert Current CTC into annual INR.

    Example:

    417964
        -> 417964

    8.3
        -> 830000

    Assumption:

    Values below 100 represent LPA.
    """

    if pd.isna(value):
        return None

    try:

        value = float(value)

    except (
        ValueError,
        TypeError
    ):

        return None

    # Values below 100 are
    # treated as LPA.

    if value < 100:

        return value * 100000

    return value


def normalize_rate(value):
    """
    Normalize gig worker rates.

    Supported formats:

    1415/hr

    15k/month
    """

    value = clean_text(value)

    if value is None:
        return None, None

    value = value.lower().replace(
        " ",
        ""
    )

    # Hourly rate

    if value.endswith("/hr"):

        numeric = value.replace(
            "/hr",
            ""
        )

        try:

            return float(
                numeric
            ), "hour"

        except ValueError:

            return None, None

    # Monthly rate

    if value.endswith("k/month"):

        numeric = value.replace(
            "k/month",
            ""
        )

        try:

            return (
                float(numeric) * 1000,
                "month"
            )

        except ValueError:

            return None, None

    return None, None


# ============================================================
# LOAD NAUKRI DATA
# ============================================================

print()
print("=" * 60)
print("TASK 1 - ETL PIPELINE")
print("=" * 60)

print()
print("[1/6] Loading Naukri applicants...")


naukri = pd.read_csv(
    NAUKRI_FILE
)


print(
    f"Naukri rows loaded: {len(naukri)}"
)


# ------------------------------------------------------------
# Rename columns
# ------------------------------------------------------------

naukri = naukri.rename(
    columns={

        "Full Name":
            "name",

        "Email":
            "email",

        "Phone":
            "phone",

        "City":
            "city",

        "Experience (Years)":
            "experience_years",

        "Current CTC":
            "current_ctc",

        "Applied Date":
            "applied_date",

        "Skills":
            "skills",

    }
)


# ------------------------------------------------------------
# Clean columns
# ------------------------------------------------------------

naukri["name"] = (
    naukri["name"]
    .apply(normalize_name)
)

naukri["email"] = (
    naukri["email"]
    .apply(normalize_email)
)

naukri["phone"] = (
    naukri["phone"]
    .apply(normalize_phone)
)

naukri["city"] = (
    naukri["city"]
    .apply(normalize_city)
)


naukri["experience_years"] = (
    pd.to_numeric(
        naukri["experience_years"],
        errors="coerce"
    )
)


naukri["current_ctc"] = (
    naukri["current_ctc"]
    .apply(normalize_ctc)
)


naukri["applied_date"] = (
    pd.to_datetime(
        naukri["applied_date"],
        errors="coerce",
        dayfirst=True
    )
)


naukri["skills"] = (
    naukri["skills"]
    .apply(clean_text)
)


# Add source

naukri["source"] = "naukri"


# ------------------------------------------------------------
# Remove duplicate emails
# ------------------------------------------------------------

before = len(naukri)

naukri = naukri.drop_duplicates(
    subset=["email"],
    keep="first"
)

after = len(naukri)

print(
    f"Removed Naukri duplicates: "
    f"{before - after}"
)


# ============================================================
# LOAD GIG WORKERS
# ============================================================

print()
print("[2/6] Loading gig workers...")


gig = pd.read_csv(
    GIG_FILE
)


print(
    f"Original gig rows: {len(gig)}"
)


# ------------------------------------------------------------
# Rename columns
# ------------------------------------------------------------

gig = gig.rename(
    columns={

        "email_id":
            "email",

        "worker_name":
            "name",

        "location":
            "city",

        "skill_tags":
            "skills",

    }
)


# ------------------------------------------------------------
# Clean columns
# ------------------------------------------------------------

gig["email"] = (
    gig["email"]
    .apply(normalize_email)
)

gig["name"] = (
    gig["name"]
    .apply(normalize_name)
)

gig["city"] = (
    gig["city"]
    .apply(normalize_city)
)

gig["skills"] = (
    gig["skills"]
    .apply(clean_text)
)

gig["status"] = (
    gig["status"]
    .apply(clean_text)
)


# ------------------------------------------------------------
# Remove invalid records
# ------------------------------------------------------------

before = len(gig)


# Email must exist

gig = gig[
    gig["email"].notna()
]


# Email must contain @

gig = gig[
    gig["email"].str.contains(
        "@",
        na=False
    )
]


after = len(gig)


print(
    f"Removed invalid gig records: "
    f"{before - after}"
)


# ------------------------------------------------------------
# Normalize status
# ------------------------------------------------------------

gig["status"] = (
    gig["status"]
    .str.lower()
)


gig["status"] = (
    gig["status"]
    .replace({

        "active":
            "Active",

        "inactive":
            "Inactive",

        "paused":
            "Paused",

    })
)


# ------------------------------------------------------------
# Normalize rate
# ------------------------------------------------------------

gig[
    [
        "rate_value",
        "rate_period"
    ]
] = gig["rate"].apply(
    lambda value:
        pd.Series(
            normalize_rate(value)
        )
)


# ------------------------------------------------------------
# Remove duplicates
# ------------------------------------------------------------

before = len(gig)

gig = gig.drop_duplicates(
    subset=["email"],
    keep="first"
)

after = len(gig)


print(
    f"Removed gig duplicates: "
    f"{before - after}"
)


gig["source"] = (
    "gig_workers"
)


# ============================================================
# LOAD CB NEXUS CONTACTS
# ============================================================

print()
print("[3/6] Loading CB Nexus contacts...")


cbnexus = pd.read_csv(
    CBNEXUS_FILE
)


print(
    f"Original CB Nexus rows: "
    f"{len(cbnexus)}"
)


# ------------------------------------------------------------
# Rename columns
# ------------------------------------------------------------

cbnexus = cbnexus.rename(
    columns={

        "Phone Number":
            "phone",

        "City":
            "city",

        "Verified":
            "verified",

        "Projects Completed":
            "projects_completed",

    }
)


# ------------------------------------------------------------
# Normalize fields
# ------------------------------------------------------------

cbnexus["name"] = (
    cbnexus["Name"]
    .apply(normalize_name)
)
cbnexus = cbnexus.drop(columns=["Name"])


cbnexus["phone"] = (
    cbnexus["phone"]
    .apply(normalize_phone)
)


cbnexus["city"] = (
    cbnexus["city"]
    .apply(normalize_city)
)


cbnexus["verified"] = (
    cbnexus["verified"]
    .apply(normalize_boolean)
)


cbnexus["projects_completed"] = (
    pd.to_numeric(
        cbnexus["projects_completed"],
        errors="coerce"
    )
)


# ------------------------------------------------------------
# Remove accidental header-like rows
# ------------------------------------------------------------

before = len(cbnexus)


cbnexus = cbnexus[
    cbnexus["name"].notna()
]


cbnexus = cbnexus[
    cbnexus["name"].str.lower()
    != "name"
]


after = len(cbnexus)


print(
    f"Removed invalid CB Nexus records: "
    f"{before - after}"
)


# ------------------------------------------------------------
# Remove duplicate phone numbers
# ------------------------------------------------------------

before = len(cbnexus)


cbnexus = cbnexus.drop_duplicates(
    subset=["phone"],
    keep="first"
)


after = len(cbnexus)


print(
    f"Removed CB Nexus duplicates: "
    f"{before - after}"
)


cbnexus["source"] = (
    "cbnexus"
)


# ============================================================
# SAVE CLEAN CSV FILES
# ============================================================

print()
print("[4/6] Saving cleaned CSV files...")


naukri.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "clean_naukri.csv"
    ),
    index=False
)


gig.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "clean_gig_workers.csv"
    ),
    index=False
)


cbnexus.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "clean_cbnexus.csv"
    ),
    index=False
)


print(
    "Clean CSV files saved."
)


# ============================================================
# CREATE MASTER CONTACT DATASET
# ============================================================

print()
print("[5/6] Creating master contacts...")


# ------------------------------------------------------------
# Naukri contacts
# ------------------------------------------------------------

naukri_contacts = naukri[
    [
        "name",
        "email",
        "phone",
        "city",
        "skills",
        "source"
    ]
].copy()


# ------------------------------------------------------------
# Gig contacts
# ------------------------------------------------------------

gig_contacts = gig[
    [
        "name",
        "email",
        "city",
        "skills",
        "source"
    ]
].copy()


gig_contacts["phone"] = None


gig_contacts = gig_contacts[
    [
        "name",
        "email",
        "phone",
        "city",
        "skills",
        "source"
    ]
]


# ------------------------------------------------------------
# CB Nexus contacts
# ------------------------------------------------------------

cb_contacts = cbnexus[
    [
        "name",
        "phone",
        "city",
        "source"
    ]
].copy()


cb_contacts["email"] = None

cb_contacts["skills"] = None


cb_contacts = cb_contacts[
    [
        "name",
        "email",
        "phone",
        "city",
        "skills",
        "source"
    ]
]


# ------------------------------------------------------------
# Combine all sources
# ------------------------------------------------------------

contacts = pd.concat(
    [
        naukri_contacts,
        gig_contacts,
        cb_contacts
    ],
    ignore_index=True
)


# ------------------------------------------------------------
# Create identity key
# ------------------------------------------------------------

contacts["identity_key"] = (
    contacts["email"].fillna("")
    + "|"
    + contacts["phone"].fillna("")
)


# Remove records where
# neither email nor phone exists

contacts = contacts[
    contacts["identity_key"]
    != "|"
]


# Remove duplicate identities

contacts = contacts.drop_duplicates(
    subset=["identity_key"],
    keep="first"
)


# ------------------------------------------------------------
# Save master dataset
# ------------------------------------------------------------

contacts.to_csv(
    os.path.join(
        OUTPUT_DIR,
        "master_contacts.csv"
    ),
    index=False
)


print(
    f"Master contacts created: "
    f"{len(contacts)}"
)


# ============================================================
# CREATE SQLITE DATABASE
# ============================================================

print()
print("[6/6] Creating SQLite database...")


# Connect to SQLite

connection = sqlite3.connect(
    DATABASE_FILE
)


# ------------------------------------------------------------
# Save Naukri table
# ------------------------------------------------------------

naukri.to_sql(
    "applicants",
    connection,
    if_exists="replace",
    index=False
)


# ------------------------------------------------------------
# Save Gig Workers table
# ------------------------------------------------------------

gig.to_sql(
    "gig_workers",
    connection,
    if_exists="replace",
    index=False
)


# ------------------------------------------------------------
# Save CB Nexus table
# ------------------------------------------------------------

cbnexus.to_sql(
    "cbnexus_contacts",
    connection,
    if_exists="replace",
    index=False
)


# ------------------------------------------------------------
# Save Master Contacts
# ------------------------------------------------------------

contacts.to_sql(
    "master_contacts",
    connection,
    if_exists="replace",
    index=False
)


# ------------------------------------------------------------
# Create useful indexes
# ------------------------------------------------------------

cursor = connection.cursor()


cursor.execute("""
    CREATE INDEX IF NOT EXISTS
    idx_applicants_email
    ON applicants(email)
""")


cursor.execute("""
    CREATE INDEX IF NOT EXISTS
    idx_gig_workers_email
    ON gig_workers(email)
""")


cursor.execute("""
    CREATE INDEX IF NOT EXISTS
    idx_cbnexus_phone
    ON cbnexus_contacts(phone)
""")


cursor.execute("""
    CREATE INDEX IF NOT EXISTS
    idx_master_identity
    ON master_contacts(identity_key)
""")


connection.commit()


# ============================================================
# DATABASE VERIFICATION
# ============================================================

print()
print("Checking database...")


tables = pd.read_sql_query(
    """
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
    """,
    connection
)


print()
print("Tables created:")


for table in tables["name"]:

    print(
        f"  ✓ {table}"
    )


# ------------------------------------------------------------
# Row counts
# ------------------------------------------------------------

print()
print("Database row counts:")


for table in tables["name"]:

    result = pd.read_sql_query(
        f"""
        SELECT COUNT(*) AS count
        FROM "{table}"
        """,
        connection
    )

    count = result.iloc[0]["count"]

    print(
        f"  {table}: {count}"
    )


# Close database

connection.close()


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 60)
print("ETL PIPELINE COMPLETED SUCCESSFULLY")
print("=" * 60)

print()
print("Database:")
print(
    f"  ✓ {DATABASE_FILE}"
)

print()
print("Output CSV files:")

print(
    "  ✓ output/clean_naukri.csv"
)

print(
    "  ✓ output/clean_gig_workers.csv"
)

print(
    "  ✓ output/clean_cbnexus.csv"
)

print(
    "  ✓ output/master_contacts.csv"
)

print()
print("Task 1 is complete!")