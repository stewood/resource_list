# Homeless Resource Directory — MVP Spec

**Stack**: Django 5 + HTMX + Tailwind (optional) + DRF (optional) • SQLite (WAL) • Docker (volume-mounted DB)

---

## 1) Purpose & Scope

Build a small, internal-first web app to curate and maintain a high-quality directory of resources for people experiencing homelessness (rehab, food, shelter, benefits, legal aid, etc.). Editors add/update records, reviewers verify and publish. Every change is versioned; every action is audited. Data lives in a single SQLite database file stored on a Docker volume.

**Out of scope (MVP):** public site, SMS/IVR, geocoding, multi-tenant orgs, complex scheduling.

---

## 2) Personas & Roles

* **Editor**: create/edit resources, submit for review.
* **Reviewer**: verify, publish/unpublish, merge duplicates.
* **Admin**: manage users, taxonomies, rare hard deletes, system settings.

---

## 3) Key Use Cases (MVP)

1. Create a new resource as **Draft** with required basics.
2. Submit a resource for **Review**; reviewer verifies details and sets **Published**.
3. Edit an existing resource; the system records a new immutable **version** and an **audit** entry.
4. Search and filter the directory by category/city/state/status.
5. Import a CSV of resources; validate and stage as Drafts; export filtered results to CSV.
6. Soft-archive (no hard delete except Admin) while preserving version history.

---

## 4) Data Model (SQLite)

> Keep fields minimal but compatible with typical resource lists. Additional fields can be added later without breaking history.

### 4.1 Tables

**resource**

* `id` (PK)
* `name` (TEXT, NOT NULL)
* `category_id` (FK → taxonomy\_category, NULLABLE)
* `description` (TEXT)
* **Contact & Location**: `phone` (TEXT), `email` (TEXT), `website` (TEXT), `address1` (TEXT), `address2` (TEXT), `city` (TEXT), `state` (TEXT), `postal_code` (TEXT)
* **Ops**: `status` (TEXT CHECK in ('draft','needs\_review','published') NOT NULL DEFAULT 'draft')
* `source` (TEXT)
* `last_verified_at` (DATETIME), `last_verified_by_id` (FK → user)
* `created_at`/`updated_at` (DATETIME NOT NULL)
* `created_by_id`/`updated_by_id` (FK → user NOT NULL)
* `is_deleted` (INTEGER CHECK in (0,1) DEFAULT 0)

**taxonomy\_category**

* `id`, `name` (UNIQUE NOT NULL), `slug` (UNIQUE), `description`

**resource\_version** *(immutable snapshots)*

* `id`, `resource_id` (FK), `version_number` (INT, monotonic per resource)
* `snapshot_json` (TEXT, full resource row at save time)
* `changed_fields` (TEXT, JSON array)
* `change_type` (TEXT CHECK in ('create','update','status\_change'))
* `changed_by_id` (FK → user), `changed_at` (DATETIME NOT NULL)

**audit\_log** *(append-only)*

* `id`, `actor_id` (FK → user), `action` (TEXT e.g., 'create\_resource','update\_resource','import','publish')
* `target_table` (TEXT), `target_id` (TEXT/INT), `metadata_json` (TEXT)
* `created_at` (DATETIME NOT NULL)

**resource\_fts** *(SQLite FTS5 virtual table)*

* Indexed fields: `name, description, city, state, category_name`

### 4.2 Constraints & Indexes

* Indexes on `status`, `city`, `state`, `category_id`, `updated_at`.
* CHECK: `postal_code` 5 or 9 digits when `state` present.

---

## 5) Validation & Data Quality (MVP)

**Draft — minimum to save**

* `name` required
* At least one contact among (`phone`, `email`, `website`)

**Move → needs\_review**

* `city` & `state` present
* `description` length ≥ 20
* `source` present

**Move → published**

* `last_verified_at` within **180 days**
* `last_verified_by_id` set

**Normalization**

* Normalize phone to E.164-like digits; uppercase `state`
* Validate `postal_code` (##### or #####-####)
* Strip/normalize URL scheme

---

## 6) Workflows

**Lifecycle:** `Draft → Needs Review → Published` (optional: `Archived` later)

**Editing:** Editing a Published record creates a new draft-like revision or demotes to `needs_review` (implementation choice) and always records a new `resource_version`.

**Merge (later, not MVP)**: Select winner + loser; survivor keeps chosen fields; loser soft-deleted; write `change_type='merge'` with metadata.

---

## 7) History & Audit (Enforced)

* On every create/update/status change:

  * Write `resource_version` snapshot (full JSON + changed fields)
  * Write `audit_log` entry with actor, action, target, timestamp
* Immutability via SQLite triggers:

```
CREATE TRIGGER audit_no_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT,'audit_log is append-only'); END;
CREATE TRIGGER audit_no_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT,'audit_log cannot be deleted'); END;
CREATE TRIGGER version_no_update BEFORE UPDATE ON resource_version
BEGIN SELECT RAISE(ABORT,'resource_version is append-only'); END;
CREATE TRIGGER version_no_delete BEFORE DELETE ON resource_version
BEGIN SELECT RAISE(ABORT,'resource_version cannot be deleted'); END;
```

---

## 8) UI (Django + HTMX)

* **Dashboard**: counts by status; list of records “unverified > 180 days”.
* **Resource List**: search box (FTS), filters (category/city/state/status), sort by `updated_at`.
* **Resource Form**: sections (Basics, Contact, Location, Notes, Verification) with inline validation; status transition buttons.
* **History Tab**: table of versions with diff view (field-level highlights).
* **Import/Export**: upload CSV → mapping step → validation results; export current results to CSV.

---

## 9) CSV Import / Export

**Import (MVP)**

* Upload resources CSV (+ optional column-mapping CSV)
* Validate per-row (collect errors); create **Draft** records for valid rows
* Write an `audit_log` entry summarizing counts and store an error CSV for download

**Export**

* Export current filtered result set to CSV (UTF-8)

---

## 10) API (Optional in MVP)

* `GET /api/resources?q=&city=&state=&category=&status=`
* `POST /api/resources` (create Draft)
* `PATCH /api/resources/{id}`
* `POST /api/resources/{id}/submit_review`
* `POST /api/resources/{id}/publish`
* `GET /api/resources/{id}/versions`

---

## 11) SQLite Settings & Performance

* Enable **WAL** + busy timeout (e.g., 20s) on startup
* Keep write transactions short; index common filters
* FTS5 for fast search; pagination (e.g., 50/page)

---

## 12) Security & Access

* Django auth (username/password) and per-role permissions
* CSRF enabled; HTTPS in production
* Audit login attempts (basic rate limiting)
* Avoid collecting sensitive PII unnecessarily

---

## 13) Docker & Volume Strategy

**Goal:** Be able to deploy in Docker and point the app at a mounted volume that contains the SQLite DB.

* App expects DB at **`/data/db.sqlite3`**
* Docker Compose defines a named volume `resources_data` mounted at `/data`
* On container start: run migrations, enable WAL, then start Gunicorn
* To use an existing DB file, mount its host folder to `/data`

**Example compose snippet** (implementation reference):

```yaml
services:
  app:
    build: .
    ports: ["8000:8000"]
    environment:
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY:-dev}
      - DEBUG=${DEBUG:-0}
      - ALLOWED_HOSTS=*
    volumes:
      - resources_data:/data  # db.sqlite3 lives here
volumes:
  resources_data:
```

**Django settings** (DB path & options):

```python
DATABASES = {
  "default": {
    "ENGINE":"django.db.backends.sqlite3",
    "NAME": "/data/db.sqlite3",
    "OPTIONS": {"timeout": 20},
  }
}
# On startup (AppConfig.ready): set PRAGMA journal_mode=WAL, synchronous=NORMAL
```

---

## 14) Acceptance Criteria (MVP)

1. Creating a Draft without `name` fails with a clear error.
2. Submitting to **needs\_review** enforces city/state, description ≥ 20 chars, source present.
3. Publishing requires `last_verified_at` ≤ 180 days old and `last_verified_by_id`.
4. Each create/update writes a `resource_version` and an `audit_log` entry.
5. Attempting to UPDATE/DELETE a `resource_version` or `audit_log` row fails via triggers.
6. FTS search returns expected results for common queries (e.g., “shelter”, “food”).
7. CSV import creates Drafts for valid rows and produces an error report for invalid rows.
8. The app runs in Docker; the DB is created/used at `/data/db.sqlite3` on a mounted volume.

---

## 15) Future Enhancements (Post-MVP)

* Duplicate detection & Merge workflow
* Map view + distance/radius search
* Re-verification reminders at 6 months
* Public read-only site and simple API key access
* Switch to libSQL/Turso or PostgreSQL if write concurrency grows

---

## 16) Implementation Notes

* Organize Django apps: `directory` (models/views), `audit` (signals + triggers), `importer`, `api` (optional).
* Use `post_save` signals to create `resource_version` and `audit_log` entries.
* Maintain FTS5 with triggers that reflect INSERT/UPDATE/DELETE from `resource`.
* Keep a small, clean permission matrix (Editor/Reviewer/Admin) using Django groups.
