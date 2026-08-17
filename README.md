# ConsultBae AI Automation Assignment

A Python-based automation prototype that combines **data cleaning,
deduplication, SQLite, n8n workflow automation, a Flask API, and an audio
collection application**.

The project is divided into five tasks:

1. **Data Merge & ETL**
2. **Duplicate Detection Automation with n8n**
3. **Audio Collection & Metadata Extraction**
4. **Data Quality Analysis**
5. **Scalability Design**

The implementation focuses on building a working end-to-end prototype
using simple components that can be run locally.

---

# Architecture

```text
                    ┌──────────────────────┐
                    │   Source CSV Files   │
                    │                      │
                    │ Naukri               │
                    │ Gig Workers          │
                    │ CB Nexus             │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     Pandas ETL       │
                    │                      │
                    │ Cleaning             │
                    │ Normalization        │
                    │ Deduplication        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Master Contacts    │
                    │                      │
                    │ CSV + SQLite         │
                    └──────────┬───────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
       ┌─────────────────┐          ┌──────────────────┐
       │      n8n        │          │   Flask Audio    │
       │   Automation    │          │    Application   │
       └────────┬────────┘          └────────┬─────────┘
                │                            │
                ▼                            ▼
       ┌─────────────────┐          ┌──────────────────┐
       │ Duplicate Check │          │ Audio Processing │
       │     API         │          │                  │
       └────────┬────────┘          │ Duration         │
                │                   │ Sample Rate      │
                ▼                   │ Bitrate           │
       ┌─────────────────┐          │ Loudness          │
       │   IF Duplicate  │          └────────┬─────────┘
       └───────┬─────────┘                   │
          ┌────┴────┐                        │
          ▼         ▼                        ▼
       Duplicate   New                    SQLite
        Alert     Contact
```

---

# Tech Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Data Processing | Pandas |
| Database | SQLite |
| Backend API | Flask |
| Workflow Automation | n8n |
| Audio Processing | FFmpeg / imageio-ffmpeg |
| Frontend | HTML, CSS |
| Version Control | Git / GitHub |

SQLite was selected for the prototype because it is lightweight and does
not require a separate database server.

For a production-scale deployment, PostgreSQL would be a more suitable
database.

---

# Project Structure

```text
consultbae-automation/
│
├── audio_app/
│   ├── app.py
│   ├── templates/
│   │   └── index.html
│   ├── static/
│   │   └── style.css
│   ├── uploads/
│   └── processed/
│
├── data/
│   └── source CSV files
│
├── output/
│   ├── clean_naukri.csv
│   ├── clean_gig_workers.csv
│   ├── clean_cbnexus.csv
│   ├── master_contacts.csv
│   └── demo_contacts.csv
│
├── src/
│   ├── etl.py
│   └── db_api.py
│
├── n8n/
│   └── ConsultBae - Duplicate Contact Detection.json
│
├── consultbae.db
├── TASK4_DATA_QUALITY_REPORT.md
├── STUCK_LOG.md
├── requirements.txt
├── .gitignore
└── README.md
```

The `uploads/` and `processed/` directories are runtime directories for
the audio application and are excluded from Git.

---

# Task 1 — Data Merge & ETL

## Objective

The first task processes three source datasets and creates one normalized
master contact dataset.

The three sources do not share a common identifier, so the ETL pipeline
uses normalized contact information to identify the same person across
different systems.

## ETL Flow

```text
Naukri CSV
     │
     ├──────────────┐
     │              │
Gig Workers CSV     ├──► Pandas Cleaning
     │              │
CB Nexus CSV ───────┘
                    │
                    ▼
              Normalization
                    │
                    ▼
             Duplicate Matching
                    │
                    ▼
             Master Contacts
                    │
              ┌─────┴─────┐
              ▼           ▼
       master_contacts   SQLite
           .csv
```

## Data Normalization

The ETL process handles:

- Email normalization
- Phone normalization
- Name normalization
- Missing or empty values
- Different source schemas
- Cross-source duplicate detection
- Source tracking
- Identity-key generation

The normalized contact structure contains fields such as:

```text
name
email
phone
city
skills
source
identity_key
```

The identity key is based on normalized contact information:

```text
email|phone
```

This allows records from different sources to be compared even when there
is no shared source ID.

## Generated Files

The ETL pipeline produces:

```text
output/
├── clean_naukri.csv
├── clean_gig_workers.csv
├── clean_cbnexus.csv
└── master_contacts.csv
```

The cleaned data is also stored in:

```text
consultbae.db
```

The successful ETL run produced:

```text
applicants:       41
cbnexus_contacts: 30
gig_workers:      30
master_contacts:  101
```

## Running the ETL

Activate the virtual environment:

```powershell
venv\Scripts\Activate.ps1
```

Run:

```powershell
python src/etl.py
```

---

# Task 2 — n8n Duplicate Detection Automation

## Objective

The second task connects n8n with the Python duplicate detection API.

n8n acts as the orchestration layer while the Python API handles the
database lookup.

## Workflow

```text
Incoming Contact
       │
       ▼
      n8n
       │
       ▼
Parse Contact
       │
       ▼
HTTP Request
       │
       ▼
Flask API
       │
       ▼
SQLite Duplicate Check
       │
       ▼
   Duplicate?
     /     \
   YES      NO
    │        │
    ▼        ▼
 Alert    New Contact
```

The exported workflow is available at:

```text
n8n/ConsultBae - Duplicate Contact Detection.json
```

## Duplicate Detection API

```http
POST /check-duplicate
```

Example request:

```json
{
  "email": "tanvi.gupta31@example.com",
  "phone": "9000000254"
}
```

Example response:

```json
{
  "duplicate": true,
  "matched_contact": {
    "name": "Tanvi Gupta",
    "email": "tanvi.gupta31@example.com",
    "phone": "9000000254",
    "city": "Bengaluru",
    "source": "naukri"
  }
}
```

## Workflow Branches

For an existing contact:

```text
duplicate = true
       │
       ▼
Duplicate Alert
```

For a new contact:

```text
duplicate = false
       │
       ▼
New Contact
```

Both branches were tested using separate demo contacts.

---

# Task 3 — Audio Collection Application

## Objective

The third task is a small web application for collecting worker audio
submissions.

The user provides:

- Name
- Phone number
- Audio recording

The application stores the audio and automatically extracts:

- Duration
- Sample rate
- Bitrate
- Loudness

All submissions are displayed with audio playback.

## Architecture

```text
Browser
   │
   │ Name + Phone + Audio
   ▼
Flask Application
   │
   ├──────────────► Local Audio Storage
   │
   ▼
FFmpeg
   │
   ▼
WAV Processing
   │
   ├── Duration
   ├── Sample Rate
   ├── Bitrate
   └── Loudness
   │
   ▼
SQLite
   │
   ▼
Submissions List
   │
   ▼
Audio Playback
```

## Audio Processing

Uploaded audio is converted into:

```text
Mono
16 kHz
16-bit PCM WAV
```

The application then calculates the required metadata.

A successful test produced:

```text
Duration:    248.2 sec
Sample Rate: 16.0 kHz
Bitrate:     130.43 kbps
Loudness:    -15.36 dB
```

## Database Record

Each submission stores:

```text
id
name
phone
filename
duration_seconds
sample_rate_khz
bitrate_kbps
loudness_db
created_at
```

## Running the Audio Application

From the project root:

```powershell
venv\Scripts\Activate.ps1
```

Install the required packages:

```powershell
pip install flask imageio-ffmpeg
```

Start the application:

```powershell
cd audio_app
python app.py
```

Open:

```text
http://127.0.0.1:8000
```

## Audio Submission Flow

```text
Enter Name
    │
    ▼
Enter Phone
    │
    ▼
Select Audio
    │
    ▼
Upload
    │
    ▼
Process Audio
    │
    ▼
Extract Metadata
    │
    ▼
Save SQLite Record
    │
    ▼
Display Submission
```

---

# Task 4 — Data Quality Analysis

The detailed report is available in:

```text
TASK4_DATA_QUALITY_REPORT.md
```

The three source files came from different systems, so the first step was
to make their data consistent before attempting to merge them.

## Issues Found

| Problem | Handling |
|---|---|
| Same person appearing across multiple sources | Used normalized email and phone values and generated an `identity_key`. |
| Inconsistent email formatting | Removed unnecessary whitespace and converted emails to lowercase. |
| Different phone formatting | Normalized phone values before matching. |
| Different source structures | Mapped each source into a common contact structure. |
| Missing or empty values | Handled them during the cleaning stage without stopping the ETL pipeline. |
| No common ID between systems | Used normalized contact information instead of relying on source-specific IDs. |
| Source information could be lost after merging | Preserved the original `source` field. |

## Common Structure

After cleaning, the sources are converted into a common structure containing
fields such as:

```text
name
email
phone
city
skills
source
identity_key
```

The identity key follows:

```text
email|phone
```

This provides a consistent way to compare contacts from different systems.

## Result

The cleaned data is available in:

```text
output/master_contacts.csv
```

and in:

```text
consultbae.db
```

The cleaned master dataset is then used by the duplicate-detection
automation in Task 2.

---

# Task 5 — Scalability Considerations

The current implementation is intentionally lightweight and designed for
local execution.

If around 5,000 workers submitted recordings over a weekend, several
components would need to change.

## Current Prototype

```text
Flask
  │
  ├── Local File Storage
  │
  └── SQLite
        │
        └── Synchronous Audio Processing
```

## Production Direction

```text
                  Workers
                     │
                     ▼
               Load Balancer
                     │
                     ▼
                  API Layer
                     │
             ┌───────┴────────┐
             │                │
             ▼                ▼
      Object Storage      PostgreSQL
             │
             ▼
            Queue
             │
             ▼
     Audio Processing Workers
             │
             ▼
       Metadata Database
```

## Storage

Local filesystem storage would not be suitable for a distributed
production system.

Audio files should be moved to object storage such as S3-compatible
storage.

The database would store the object key or URL rather than the binary
audio itself.

## Database

SQLite works well for the prototype but would become a limitation with
many concurrent writes.

Production should use PostgreSQL with:

- Connection pooling
- Proper indexes
- Transaction management
- Backups

## Audio Processing

The current application processes audio during the HTTP request.

At higher scale this could cause slow requests, timeouts and high CPU
usage.

A queue-based architecture would be more appropriate:

```text
Upload
  │
  ▼
Object Storage
  │
  ▼
Queue
  │
  ▼
Audio Processing Worker
  │
  ▼
Metadata Database
```

## Duplicate Submissions

Duplicate uploads can be handled using:

- Idempotency keys
- Submission IDs
- File hashes
- Database uniqueness constraints

## Failure Handling

Processing should use explicit states such as:

```text
UPLOADED
    ↓
PROCESSING
    ↓
COMPLETED
```

or:

```text
UPLOADED
    ↓
PROCESSING
    ↓
FAILED
```

Failed jobs can then be retried or moved to a dead-letter queue.

## Large Uploads

For larger files, the browser could upload directly to object storage
using signed URLs.

This keeps large binary transfers away from the application server.

## Cost Control

Storage and processing costs can be controlled through:

- Object-storage lifecycle policies
- Duplicate-file prevention
- Storage monitoring
- Processing monitoring
- Retention policies

---

# API Endpoints

## Duplicate Detection

```http
POST /check-duplicate
```

Checks whether a contact already exists in the master database.

Example:

```json
{
  "email": "person@example.com",
  "phone": "9000000000"
}
```

---

## Audio Application

### Home

```http
GET /
```

Displays the audio submission form and previous submissions.

### Upload

```http
POST /upload
```

Accepts:

```text
name
phone
audio
```

### Audio Playback

```http
GET /audio/<filename>
```

Serves an uploaded audio file.

### Health Check

```http
GET /health
```

Returns the application health status.

---

# Database

The project uses:

```text
consultbae.db
```

SQLite is shared by the main project components.

The database contains the normalized contact data from Task 1 and the audio
submission records from Task 3.

Audio submission records contain:

```text
id
name
phone
filename
duration_seconds
sample_rate_khz
bitrate_kbps
loudness_db
created_at
```

---

# Setup

## Requirements

- Python 3.12
- Git
- n8n

Python 3.12 was used because it provided a stable environment for the
project dependencies.

## Create Virtual Environment

From the project root:

```powershell
py -3.12 -m venv venv
```

Activate it:

```powershell
venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

If required:

```powershell
python -m pip install imageio-ffmpeg
```

---

# Running the Project

## 1. Run the ETL Pipeline

```powershell
venv\Scripts\Activate.ps1
python src/etl.py
```

This creates the cleaned CSV files and updates the SQLite database.

---

## 2. Run the Duplicate Detection API

Open another terminal:

```powershell
venv\Scripts\Activate.ps1
python src/db_api.py
```

The API runs locally at:

```text
http://127.0.0.1:5000
```

---

## 3. Run n8n

Start n8n using the installed setup.

Import:

```text
n8n/ConsultBae - Duplicate Contact Detection.json
```

The workflow communicates with the duplicate detection API.

---

## 4. Run the Audio Application

Open another terminal:

```powershell
venv\Scripts\Activate.ps1
cd audio_app
python app.py
```

Open:

```text
http://127.0.0.1:8000
```

---

# Development / Stuck Log

This project involved working with n8n and audio processing for the first
time, so I ran into several environment and integration issues during
development.

The complete debugging history is documented separately in:

**[STUCK_LOG.md](STUCK_LOG.md)**

Some of the main issues were:

### Python Environment Setup

The first virtual environment setup using Python 3.14 froze during
`ensurepip`. I switched to Python 3.12 and recreated the environment.

### Pandas Installation

Pandas appeared to be installed, but the project still reported:

```text
ModuleNotFoundError: No module named 'pandas'
```

The issue was that `pip` was installing packages outside the active
virtual environment. I fixed this by using the virtual environment's
Python directly.

### SQLite Schema Conflict

The ETL pipeline initially failed with:

```text
sqlite3.OperationalError: duplicate column name: name
```

This happened because the CB Nexus dataframe contained both `Name` and a
newly-created `name` column. I removed the duplicate source column before
writing the dataframe to SQLite.

### n8n File Access

n8n initially returned:

```text
Access to the file is not allowed
```

when trying to read a local CSV file. I investigated the local file-access
configuration and moved toward the API/webhook approach for the workflow.

### n8n Boolean Condition

The IF node initially had the duplicate value configured as Text instead
of Boolean. Changing the condition to a Boolean check fixed the warning.

### n8n Conditional Branches

At one point the duplicate alert showed:

```text
Node was not executed, the execution took a different path
```

This turned out not to be a broken node. The test contact was simply not a
duplicate, so the IF node correctly routed it through the FALSE branch.

### Dynamic n8n Values

Hardcoded email and phone values worked, while:

```text
={{ $json.email }}
={{ $json.phone }}
```

initially returned the wrong duplicate result.

I inspected the data entering the HTTP Request node and corrected the
dynamic field mapping.

### Empty CSV

The `Extract From File` node returned:

```text
No output data returned
```

The actual input CSV was `0 B`, so the problem was the empty test file
rather than the n8n node.

### Audio Processing

The audio application initially failed with:

```text
ModuleNotFoundError: No module named 'audioop'
```

I replaced the loudness calculation with an RMS calculation using
`struct` and `math`.

The next error was:

```text
ModuleNotFoundError: No module named 'imageio_ffmpeg'
```

I installed the missing dependency:

```powershell
pip install imageio-ffmpeg
```

After that, the audio application started successfully.

The full error-by-error development history is available in
**[STUCK_LOG.md](STUCK_LOG.md)**.

---

# Design Decisions

## Why SQLite?

SQLite was chosen because it is lightweight, requires no separate server,
and is sufficient for the local prototype.

## Why Flask?

Flask was sufficient for the lightweight REST API and audio application
without adding unnecessary framework complexity.

## Why n8n?

n8n is used as the workflow orchestration layer while the Python API
contains the duplicate-detection logic.

This keeps the business logic separate from the automation workflow.

## Why Local Audio Storage?

The assignment allows a local demonstration, so local storage keeps the
prototype simple.

For production, audio files should be moved to object storage.

---

# Future Improvements

For a production-ready version, I would prioritize:

- PostgreSQL instead of SQLite
- Object storage for audio files
- Background audio-processing workers
- Queue-based processing
- Retry and failure handling
- Idempotency and file hashing
- Authentication and authorization
- Upload size and file-type validation
- Structured logging
- Monitoring and metrics
- Automated tests
- CI/CD
- Horizontal scaling
