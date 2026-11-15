# Notes for AI coding agents (and new teammates)

OfferChat: a personal networking assistant for students and job seekers. MGT656 team project.
Read `README.md` for setup and `docs/design/` before changing UI or contacts.

## Stack

- Django 5.2, Python 3.12 on Render (3.12–3.13 locally), PostgreSQL (Neon) when `DATABASE_URL` is set,
  SQLite locally when `DEBUG=true` and no `DATABASE_URL`.
- Server-rendered templates, Bootstrap 5.3.8, Bootstrap Icons, htmx 2 (CDN with SRI), WhiteNoise for static files.
- LLM calls go through OpenRouter **from the server only**, never from browser JavaScript.

## Commands

```bash
python manage.py migrate
python manage.py runserver
python manage.py test          # needs DEBUG=true and SECRET_KEY set; unset DATABASE_URL for local SQLite
python manage.py makemigrations --check --dry-run
```

## Layout

| Path | What |
|---|---|
| `config/` | settings and root URLs |
| `core/` | home, health, account, styleguide, seed command |
| `abtest/` | course A/B page `/020c45f` and `/020c45f/stats` — do not change without the whole team |
| `contacts/` | contacts, tags, connections, stage rule, htmx views |
| `templates/` | `base.html` (public, no nav), `app.html` (logged-in shell), `components/` |
| `static/css/theme.css`, `static/js/app.js` | theme tokens and components; toasts and htmx error handling |
| `docs/design/` | design docs and UI guidelines |
| `docs/mgt656/` | course-graded docs (fixed structure — don't add files here) |

## Rules

1. **Privacy:** every query for user data filters by `owner=request.user`. Someone else's object is a **404**, never 403.
   Use `contacts.views.get_contact_or_404` for contacts.
2. **A/B page:** must contain exactly one `<button>` with `id="abtest"`. Public templates extending `base.html` must not add buttons.
3. **Stage changes:** call `Contact.change_stage()`; don't set `contact.stage` directly in views.
4. **No secrets in git.** Configuration comes from environment variables. Schema changes only through migrations.
5. **Tests:** every change ships with Django tests. Mock the LLM and any external service; tests never use the network.
6. **UI:** follow `docs/design/ui-guidelines.md`. Logged-in pages extend `app.html`. Pages must work without JS;
   htmx only enhances. Check 1440px, 820px and 390px widths (the shell switches at 1024px).
7. **Pull requests:** branch per issue (`<issue>-short-name`), PR says `Closes #<issue>`, a teammate reviews before merge.
   The description has three sections: what the AI agent produced, what we changed or rejected and why, how to test.
   A story is Done only after someone checks it on staging.
