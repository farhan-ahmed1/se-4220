# Ames Classifieds (SE 4220 Project 5)

A small Craigslist-style classified ads website for Ames, Iowa, deployed on
Google Cloud Platform. See [`ASSIGNMENT.md`](ASSIGNMENT.md) for the project
brief and [`docs/architecture.md`](docs/architecture.md) for the technical
report and architecture diagrams.

## Stack at a glance

- **Flask** (Python 3.12) + **Jinja2** + **Bootstrap 5** for the web app
- **Cloud SQL MySQL** for users / sections / categories / listings
- **Google Cloud Storage** for listing photos
- **App Engine Standard** for hosting

## Local development

1. From this directory, set up a virtualenv and install deps:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy the env template and fill in values:

   ```bash
   cp .env.example .env
   # edit .env -- DB host/user/password, GCS bucket, etc.
   ```

3. Apply the schema and seed initial data:

   ```bash
   mysql -h $DB_HOSTNAME -u $DB_USERNAME -p $DB_NAME < schema.sql
   python seed.py
   ```

4. Run the app:

   ```bash
   python main.py
   # open http://localhost:8080
   ```

   Demo login: `admin` / `Password55`.

## Deploying to App Engine

1. Make sure you have the `gcloud` CLI installed and authenticated.

2. Edit `app.yaml` and replace the `REPLACE_WITH_*` env vars with real
   values (Cloud SQL public IP / DB user / DB password / Flask secret).

3. Deploy:

   ```bash
   gcloud app deploy app.yaml
   gcloud app browse
   ```

App Engine's default service account picks up GCS credentials
automatically — no `gcp-key.json` needed in production.

## What you'll need to set up in GCP

The application code is written; these are the manual cloud-side steps the
instructor will need before / during the demo:

- A Cloud SQL MySQL instance with a database named `classifieds_db`. (You
  can reuse the photogallery instance from Chapter 6 — just create a new
  database in it.)
- A SQL user with read/write on `classifieds_db`.
- A GCS bucket (default name: `se4220-classifieds-bucket`) configured for
  public reads on uploaded objects (for example, by enabling
  *uniform bucket-level access* and granting `allUsers` the
  *Storage Object Viewer* role).
- The Cloud SQL instance must accept connections from App Engine
  (Authorized networks `0.0.0.0/0` is fine for a demo, or use the Cloud
  SQL Auth Proxy for stricter access).
- For local development, a service account JSON with GCS write access
  saved as `gcp-key.json` (or any path you set in
  `GOOGLE_APPLICATION_CREDENTIALS`).

Everything else (schema, seed data, web app, deployment config) is in
this directory.

## File map

| File | Purpose |
|------|---------|
| `app.py` | Flask routes |
| `config.py` | 25 categories + per-category attribute schemas |
| `db.py` | Tiny MySQL helper |
| `gcs.py` | GCS upload helper |
| `main.py` | App Engine entrypoint (`from app import app`) |
| `seed.py` | Populates 5 sections / 25 categories / 75 listings |
| `schema.sql` | DDL |
| `app.yaml` | App Engine config |
| `templates/` | Jinja templates |
| `static/style.css` | Layout polish on top of Bootstrap |
| `docs/architecture.md` | System architecture + technical report |
| `ASSIGNMENT.md` | Original project brief |
