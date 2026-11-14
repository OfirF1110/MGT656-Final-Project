# Design: contact management (#10) and the app shell

Status: built, awaiting team review. Owner: Leo (amused-cobra).
UI rules for every page live in [ui-guidelines.md](ui-guidelines.md).

## Why

Contacts are the base of OfferChat. Meeting notes (#11, #24), follow-up tasks (#12) and the
recruiting workspace (#13) all hang off "a contact and where the relationship stands".
#10 asks: add, edit, search and tag contacts, and always know each relationship's stage.

## Scope

In:
- Create, view, edit and delete contacts (name required; company, role, LinkedIn URL, tags, notes).
- Exactly one of six relationship stages per contact; changing it from the list or the detail page.
- Search by name, company or tag (case-insensitive, partial), combined with a stage filter.
- Delete with confirmation; the contact's connections are deleted with it.
- Contacts are private to their owner.
- The app shell (sidebar on desktop, top bar and menu on phones) used by every logged-in page.
- htmx: live search and inline stage changes, with full-page fallbacks when JS is off.

Out (separate stories): linking contacts in the UI (#16), import (#14), bulk email (#21),
target-company dashboard (#19), demo data (#25), a board view, pagination, dark mode.

Must never happen:
- The A/B page (`/020c45f`) gains a second `<button>` or changes its counting.
- Any page shows another user's contact.
- Search or stage changes stop working with JS turned off.

## Data model (`contacts/models.py`)

| Model | Fields | Notes |
|---|---|---|
| `Contact` | `owner`, `name` (120), `company`, `role`, `linkedin_url`, `notes`, `stage`, `last_contact_date`, `tags` (M2M), `created_at`, `updated_at` | Ordered by most recently updated. DB check constraint keeps `stage` to the six values. Not registered in Django admin, so admin accounts can't browse everyone's contacts. |
| `Tag` | `owner`, `name` (40, lowercase) | Unique per owner. Entered as comma-separated text; `parse_tags()` trims, lowercases and dedupes. |
| `Connection` | `owner`, `from_contact`, `to_contact`, `relationship` (`colleague`, `introduced_me`, `classmate`, `knows`) | Minimal model so deleting a contact removes its connections (cascade). No UI yet; #16 builds on it. |

Stages (`Stage` in `contacts/models.py`):

| Value | Label | Group in the stage menu |
|---|---|---|
| `to_contact` | To contact (default) | Not started |
| `awaiting_reply` | Awaiting reply | Active |
| `in_conversation` | In conversation | Active |
| `meeting_set` | Meeting set | Active |
| `met` | Met | Done |
| `inactive` | Inactive | Done |

## Rules

**Stage and last-contact date.** Every stage change goes through `Contact.change_stage(new_stage, today=None)`:
- It only acts when the stage actually changes.
- Moving into `in_conversation` or `met` sets `last_contact_date` to today (`timezone.localdate()`, New York).
- Other moves keep the date. `met → inactive → met` counts as a change and sets today again.
- It is deliberately not in `save()`: meeting logging (#11) will set `met` with the meeting's date.
- The create form may set a stage directly; picking In conversation or Met sets today.
- `last_contact_date` is read-only in forms.

**Search.** `filter_contacts()` in `contacts/views.py`: `name`, `company` or tag name `icontains` the query,
`.distinct()`, then the optional stage filter (unknown values are ignored). Accent and punctuation-insensitive
search is left to #16.

**Validation.** Name: blank or spaces only shows "Enter a name". LinkedIn: scheme optional (`linkedin.com/in/x`
becomes `https://linkedin.com/in/x`); host must be `linkedin.com` or a subdomain. Tags: each at most 40 characters.

**Privacy.** Every lookup uses `get_contact_or_404(request, pk)` (filters by `owner=request.user`).
Detail, edit, delete (GET and POST) and stage (POST) all return 404 for someone else's contact.

**Delete.** GET shows a confirmation naming the contact and how many connections go with it; only POST deletes.

## URLs (`contacts/urls.py`, namespace `contacts`)

| URL | Method | Name | htmx behavior |
|---|---|---|---|
| `/contacts/` | GET `?q=&stage=&sort=` | `list` | With `HX-Request`: returns `_results.html` only. Always `Vary: HX-Request`. History restores get the full page. |
| `/contacts/new/` | GET, POST | `create` | — |
| `/contacts/<pk>/` | GET | `detail` | — |
| `/contacts/<pk>/edit/` | GET, POST | `edit` | — |
| `/contacts/<pk>/stage/` | POST | `stage` | With `HX-Request`: returns `_row.html` (`context=row`) or `_stage_panel.html`, plus `HX-Trigger: {"toast": "Stage updated"}`. Without: redirects to a same-site `next`. Bad stage: 400. |
| `/contacts/<pk>/delete/` | GET, POST | `delete` | — |

Also: login and `/` (when logged in) land on `/contacts/`. `/styleguide/` is a staff-only page that renders every shared component.

## htmx

- htmx 2.0.11 and Bootstrap 5.3.8 JS load from jsDelivr with SRI, only in `templates/app.html`.
- CSRF: `<body hx-headers='{"X-CSRFToken": ...}'>`.
- Search input: `hx-trigger="input changed delay:300ms, search"`; stage filter: `change`; both `hx-include` the form and target `#contact-results`, pushing the URL.
- Stage menu: native `<details>` with one submit button per stage, so it works without JS. htmx posts it and swaps the row or panel.
- Failures: `static/js/app.js` shows "Couldn't save. Check your connection and try again." (or "Couldn't load results…") and leaves the page unchanged.

## Decisions

| Decision | Why |
|---|---|
| Server-rendered Django + htmx, not a JS front end | Matches the proposal's stack; htmx is on the course's technical-challenge list; everything still works without JS. |
| Bootstrap 5.3 with our own theme, not MUI | MUI is a React library and would mean a React front end. We borrow its principles (8px grid, one primary action, feedback on every action, 44px touch targets). |
| Soft stage pills with a dot (Attio/Notion style), chosen by Leo over icon rings | Easier to tell stages apart at a glance; tints are light so the table stays calm; the label is always text. |
| `change_stage()` outside `save()` | Lets meeting logging set a past date without being overwritten. |
| 404, never 403, for other users' data | Doesn't reveal that an ID exists. |
| #16 kept separate | Keeps #10 shippable this sprint; `Connection` is ready for it. |

## Testing

`contacts/tests.py` and `core/tests.py` (Django `TestCase`, no network). They cover: create, missing name,
stage changes and the date rule, partial and tag search, stage filter, escaping in search messages,
404 for other users on every URL, delete with connections, htmx fragments, CSRF via header, history restore,
the A/B page keeping exactly one button, and the staff-only styleguide.
