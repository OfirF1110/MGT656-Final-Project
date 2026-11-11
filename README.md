# MGT656 Final Project

A personal networking assistant that turns professional relationships and meeting notes into useful follow-ups and recruiting opportunities.

---

## Major User Journeys

1. **Build and track your network.** As a student or job seeker, I log in, add contacts and their companies, record how people are connected, and track each relationship from initial outreach to meeting and follow-up.
2. **Capture meetings and act on them.** After a networking conversation, I paste rough notes, review the AI summary and suggested actions, and save the meeting to the relevant contacts. I return to my task list to complete follow-ups.
3. **Prepare for meetings and applications.** Before a meeting or application, I review the contact's history, generate a preparation brief or outreach draft, and look up people I already know at the target company.

---

## Core Features (MVP)

| Feature | Description |
|---|---|
| **Contact management** | Private accounts. Create, edit, search, and tag contacts with roles, companies, relationship stages, and last-contact dates. |
| **Network view** | A contact list and a simple relationship graph showing manually recorded connections. |
| **Meeting history** | Log conversations, link attendees, and keep editable notes and summaries. |
| **Follow-up tasks** | Review suggested actions, assign due dates, and mark tasks complete or dismissed. |
| **Recruiting workspace** | Save opportunities manually and find existing contacts at the same company. |

### Out of Scope

- Automated job-board crawling
- LinkedIn synchronization
- Email or calendar integrations
- Automatic message sending

---

## AI Feature

The LLM:

- Converts rough meeting notes into a **summary**, a list of **people mentioned**, and concrete **follow-up suggestions**.
- Drafts **personalized outreach** and **meeting preparation briefs** using saved contact history.

> Users review all AI output before saving tasks or using drafts.

---

## Run the Django Foundation

The current implementation provides the application foundation and authentication.
The product features described above are the planned MVP, not all shipped features.

Use Python 3.12. Create a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Set configuration in your shell environment (see `.env.example` for variable names).
Django does not load `.env` files automatically. Never commit actual credentials.

- `SECRET_KEY`: a random secret; use a separate value for each environment.
- `DEBUG`: `true` for local development, `false` on staging.
- `DATABASE_URL`: the Neon Postgres connection string, including TLS options.
  Local development can use SQLite if DEBUG is true and this variable is absent.
- `ALLOWED_HOSTS`: comma-separated hostnames. Render's hostname is added automatically.
- `GRADER_ADMIN_USERNAME`, `GRADER_ADMIN_PASSWORD`: dedicated fake grader admin.
- `GRADER_MEMBER_USERNAME`, `GRADER_MEMBER_PASSWORD`: dedicated fake grader member.

After configuring the environment:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed
.\.venv\Scripts\python.exe manage.py runserver
```

Open http://127.0.0.1:8000/login/ and use a seeded account. The account page
is protected; `/health/` checks database connectivity. Logout uses a POST form.

**After any database reset, rerun migrations and `python manage.py seed`.**
Running seed again with the same credentials is safe and creates no duplicates.
It refuses to overwrite an existing same-name account with a different password.
The skeleton's demo data currently consists of the two grader accounts.
Keep their passwords in private environment settings and course submission notes.

## Automated Tests

Use a dedicated test database, never an application database with real data.
For local SQLite tests in PowerShell, preserve and temporarily unset DATABASE_URL:

```powershell
$savedDatabaseUrl = $env:DATABASE_URL
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
try {
    # Keep DEBUG=true and SECRET_KEY set in this local shell.
    .\.venv\Scripts\python.exe manage.py test
}
finally {
    $env:DATABASE_URL = $savedDatabaseUrl
    Remove-Variable savedDatabaseUrl
}
```

Tests cover successful/failed login, protected-page redirects, logout,
grader permissions, repeated seeding and seed failure handling.

## Staging Deployment

See `DEVELOPMENT.md` and `render.yaml` for the Render + Neon setup.
Build: `bash build.sh` (dependencies, static files, migrations and seed).
Start: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --access-logfile - --error-logfile -`.
Set the private environment variables before deployment, then verify both accounts
on staging. Do not mark deployment complete based only on local test results.
