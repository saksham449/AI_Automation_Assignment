# Development / Stuck Log

This assignment involved several tools and technologies that I had not
worked with before, especially n8n, SQLite integration through an API, and
audio processing.

Most of the issues I faced were not major logic problems. They were
mostly environment setup, dependency, configuration, and integration
issues. I documented them here because solving these issues was an
important part of completing the project.

---

## 1. Python Virtual Environment Setup Froze

While setting up the project, I initially used Python 3.14 and created the
virtual environment with:

```powershell
python -m venv venv
```

The process got stuck while running `ensurepip`. After waiting for some
time, I stopped it with `Ctrl+C` and received a `KeyboardInterrupt`
traceback.

I decided to use Python 3.12 instead because the project depended on
several third-party packages.

I recreated the environment using:

```powershell
py -3.12 -m venv venv
```

This solved the environment creation problem.

### What I learned

For projects with multiple dependencies, using a stable Python version
supported by those dependencies can avoid a lot of unnecessary setup
problems.

---

## 2. Pandas Was Installed but Python Could Not Import It

While running the ETL pipeline, Python reported:

```text
ModuleNotFoundError: No module named 'pandas'
```

This was confusing because running:

```powershell
pip install pandas
```

showed that Pandas was already installed.

The important clue was:

```text
Defaulting to user installation because normal site-packages is not writeable.
```

This meant that `pip` was installing packages outside the virtual
environment.

I fixed this by explicitly using the Python executable from the virtual
environment:

```powershell
venv\Scripts\python.exe -m pip install pandas
```

After that, the ETL script was able to import Pandas correctly.

### What I learned

Seeing `(venv)` in the terminal does not always mean that `pip` is using
the environment I expect. Checking which Python and pip executable is
actually being used is important when debugging dependency problems.

---

## 3. SQLite Schema Error — Duplicate Column Name

Near the end of the ETL pipeline, the cleaning and merging logic was
working, but SQLite failed with:

```text
sqlite3.OperationalError: duplicate column name: name
```

The problem occurred because the CB Nexus dataframe already contained a
column called:

```text
Name
```

and the ETL code created another column:

```python
cbnexus["name"] = cbnexus["Name"].apply(normalize_name)
```

SQLite treats column names such as `Name` and `name` as equivalent.

I removed the original column before writing the dataframe to SQLite:

```python
cbnexus = cbnexus.drop(columns=["Name"])
```

The database could then be created successfully.

### What I learned

Dataframe column names should be normalized before writing data to a
database, especially when the database treats identifiers
case-insensitively.

---

## 4. SQLite CLI Was Not Available

While checking whether SQLite was installed, I ran:

```powershell
sqlite3 --version
```

PowerShell returned:

```text
sqlite3 : The term 'sqlite3' is not recognized...
```

Initially I thought SQLite itself was not working.

I realized that the SQLite command-line executable was simply not
installed or available in the Windows PATH.

Since Python already provides the built-in:

```python
import sqlite3
```

I continued using SQLite directly through Python instead of spending
additional time installing the command-line utility.

### What I learned

The SQLite CLI and Python's SQLite support are separate things. The
application can use SQLite perfectly without having the `sqlite3` command
available in PowerShell.

---

## 5. n8n Was Completely New to Me

I had not used n8n before this assignment, so initially I had to spend
some time understanding how data moves between nodes and how expressions
work.

One of the first things I tried was looking for an "Execute Command" node
so that I could directly run my Python logic from n8n.

That node was not available in my setup.

Instead of trying to force Python execution from n8n, I exposed the
duplicate-checking logic through a Flask API and used an HTTP Request node
inside n8n.

The final approach became:

```text
CSV
 │
 ▼
n8n
 │
 ▼
HTTP Request
 │
 ▼
Flask API
 │
 ▼
SQLite
 │
 ▼
IF Node
```

### What I learned

n8n does not need to contain all the business logic. It can work very well
as an orchestration layer while the actual application logic remains in a
separate API.

---

## 6. n8n Could Not Access the Local File

When I initially tried to make n8n read the generated CSV directly from
the Windows filesystem, I received:

```text
Access to the file is not allowed
```

The Windows path itself was valid, but n8n was restricting access to the
local filesystem.

I also had some confusion because environment variables/configuration were
being changed in one terminal while n8n was being started from another
terminal.

After investigating the issue, I moved toward using the API/webhook
approach instead of depending on direct filesystem access.

### What I learned

When working with local automation tools, there can be a difference
between a file being accessible to Windows and being accessible to the
application process.

---

## 7. `/check-duplicate` Returned "Method Not Allowed"

While testing the duplicate detection API, I opened:

```text
http://127.0.0.1:5000/check-duplicate
```

in the browser.

The response was:

```text
Method Not Allowed
```

At first this looked like the API itself was broken.

I then realized that the endpoint was implemented as a `POST` endpoint,
while opening the URL in a browser sends a `GET` request.

I tested the endpoint properly from PowerShell:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:5000/check-duplicate" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"email":"tanvi.gupta31@example.com","phone":"9000000254"}'
```

The API returned the expected duplicate result.

### What I learned

The HTTP method used by the client must match the method implemented by the
API.

---

## 8. n8n IF Node Had a Configuration Warning

The duplicate detection IF node initially showed a warning.

The problem was that the API returned:

```json
{
  "duplicate": true
}
```

where `true` is a Boolean value, but the IF node had been configured to
treat the value as Text.

I removed the unnecessary condition and configured the field as a
Boolean using:

```text
is true
```

The warning disappeared.

### What I learned

When working with n8n expressions, it is important to pay attention to the
actual data type, not just the displayed value.

---

## 9. TRUE Branch Initially Had No Data

The IF node initially showed no data on the TRUE branch.

I first thought that the IF node itself was incorrect.

Instead of changing the workflow immediately, I tested the Flask API
separately with a contact that I knew already existed.

The API correctly returned:

```text
duplicate: True
```

This showed that the database and API were working.

The problem was further upstream in the data being sent from n8n.

### What I learned

Testing each component independently made it much easier to identify where
the actual problem was.

---

## 10. Hardcoded Values Worked but Dynamic Values Did Not

This was one of the most confusing n8n problems.

When I hardcoded a known duplicate contact:

```json
{
  "email": "tanvi.gupta31@example.com",
  "phone": "9000000254"
}
```

the API correctly returned:

```text
duplicate: true
```

But when I changed the request to use n8n expressions:

```json
{
  "email": "={{ $json.email }}",
  "phone": "={{ $json.phone }}"
}
```

the API initially returned:

```text
duplicate: false
```

I compared the working hardcoded request with the actual input data
entering the HTTP Request node.

After correcting the dynamic field mapping and checking the incoming item,
the correct email and phone values were sent to the Flask API.

The TRUE branch then worked correctly.

### What I learned

When a hardcoded value works but an expression does not, the first thing
to inspect is the actual data entering the node.

---

## 11. Duplicate Alert Node Was Not Executed

At one point the duplicate alert node showed:

```text
Node was not executed, the execution took a different path
```

I initially thought the webhook node was broken.

After checking the execution, I realized that the test contact was actually
a new contact.

The IF node had correctly returned:

```text
duplicate: false
```

so the workflow went through the FALSE branch.

When I tested with a known duplicate contact, the TRUE branch executed and
the duplicate alert ran successfully.

### What I learned

In a conditional workflow, a node not executing does not necessarily mean
there is an error. It may simply mean that the current input followed a
different branch.

---

## 12. Test CSV Returned "No Output Data"

While creating a smaller CSV for testing the n8n workflow, the
`Extract From File` node returned:

```text
No output data returned
```

Instead of immediately changing the node configuration, I checked the
input file.

The file information showed:

```text
File Size: 0 B
```

The actual problem was that my `demo_contacts.csv` file was empty.

I recreated the test CSV with both an existing contact and a new contact.

The resulting tests were:

```text
Existing contact → duplicate = true
New contact      → duplicate = false
```

### What I learned

When a file-processing node returns no output, checking the actual input
file first can save a lot of unnecessary debugging.

---

## 13. FALSE Branch Initially Had No Output

While configuring the FALSE branch, the Edit Fields node appeared to have
no output.

The reason was that the current execution had not sent an item through
that branch.

Once I tested using a contact that returned:

```text
duplicate: false
```

the FALSE branch received data and could be configured normally.

### What I learned

Both branches of a conditional workflow need separate test inputs.

---

## 14. Audio Application Failed Because `audioop` Was Unavailable

When I started the Task 3 audio application, Python failed with:

```text
ModuleNotFoundError: No module named 'audioop'
```

I had initially used `audioop` for the loudness calculation.

Instead of adding another dependency just for this calculation, I replaced
the implementation with an RMS calculation using Python's:

```python
struct
math
```

modules.

This removed the dependency on `audioop`.

### What I learned

When a standard-library module is unavailable in the target Python
environment, understanding what the code actually needs can make it
possible to replace the dependency with a small direct implementation.

---

## 15. Audio Application Was Missing `imageio-ffmpeg`

After fixing the `audioop` problem, the next startup error was:

```text
ModuleNotFoundError: No module named 'imageio_ffmpeg'
```

This was a missing dependency in the active virtual environment.

I installed it with:

```powershell
pip install imageio-ffmpeg
```

and restarted the application.

The Flask application then started successfully.

---

## 16. Testing Audio Metadata Extraction

Audio processing was new to me, so I wanted to make sure that the
metadata was actually being extracted and stored correctly.

A successful test produced:

```text
Duration:    248.2 sec
Sample Rate: 16.0 kHz
Bitrate:     130.43 kbps
Loudness:    -15.36 dB
```

The uploaded audio was also stored and could be played back from the
submissions page.

### What I learned

For a processing pipeline, it is useful to verify both the calculated
values and the final user-facing result rather than checking only whether
the application starts.

---

# What Took the Most Time

The biggest time sinks were not the core algorithms. They were the
environment and integration issues.

The two most frustrating problems were:

1. The Python environment appearing active while packages were actually
   being installed somewhere else.
2. n8n configuration and local file-access behavior not working as
   expected.

The n8n debugging took several iterations because I initially suspected
the IF node, when the actual problem was the data being passed into the
HTTP Request node.

---

# How I Approached Debugging

The most useful approach was to break the system into smaller pieces.

For example, instead of debugging the complete n8n workflow at once, I
tested:

```text
SQLite
   ↓
Flask API
   ↓
HTTP Request
   ↓
n8n IF Node
   ↓
Webhook
```

This made it possible to determine whether a problem was coming from the
database, API, request data, or workflow configuration.

For the audio application, I followed the same approach by resolving the
startup/import errors first and then testing the actual audio-processing
output.

---

# Final Takeaway

The assignment gave me hands-on experience with tools that I had not used
before, especially n8n and audio processing.

The biggest lesson was to avoid changing multiple things at once. Testing
each layer independently and checking the actual input/output data made
the debugging process much faster.

The final solution keeps the responsibilities separated:

```text
Pandas
  → Data cleaning and ETL

SQLite
  → Persistent storage

Flask
  → API and application logic

n8n
  → Workflow orchestration

FFmpeg
  → Audio processing
```

This separation also makes the prototype easier to extend later toward a
production architecture.