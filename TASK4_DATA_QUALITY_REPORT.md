# Task 4 — Data Quality Report

While working with the three source CSV files, I found that the data was
not in exactly the same format across all three systems. Before merging
everything, I cleaned and normalized the contact information so that the
same person could be identified reliably across different sources.

## What I found and how I handled it

| Problem I found | What I did |
|---|---|
| **The same person can appear in multiple sources** | I used normalized email and phone values to identify matching contacts and created an `identity_key` using `email\|phone`. |
| **Email values were not always in a consistent format** | I removed unnecessary whitespace and converted emails to lowercase before comparing them. |
| **Phone numbers could have different formatting** | I normalized phone values before using them for duplicate matching. |
| **The three files had different structures** | I mapped the source-specific columns into one common contact structure before combining the data. |
| **Some fields can be empty or missing** | I handled missing values during the cleaning step so that they would not stop the complete ETL process. |
| **There was no common ID between the three systems** | Instead of depending on a source-specific ID, I used normalized contact information to identify the same person across datasets. |
| **It could be difficult to know where a contact came from after merging** | I kept the original `source` value in the master dataset. |

## Common Structure

After cleaning the individual files, I converted them into a common
structure containing fields such as:

```text
name
email
phone
city
skills
source
identity_key
```

The `identity_key` is based on:

```text
email|phone
```

This gave me a consistent way to compare contacts from different systems.

## Output

The cleaned datasets are saved as:

```text
output/
├── clean_naukri.csv
├── clean_gig_workers.csv
├── clean_cbnexus.csv
└── master_contacts.csv
```

The final master data is also stored in:

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

## Final Result

The main purpose of this cleaning step was not just to make the CSVs look
consistent. It was to make the data reliable enough for the next part of
the project.

The cleaned master contacts are used by the SQLite database, which is then
used by the n8n duplicate-detection workflow.

This means the data-cleaning work in Task 1 directly supports the
automation built in Task 2.