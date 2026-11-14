# OfferChat UI guidelines

Read this before building any page. To see every component rendered, log in as a staff user and open
`/styleguide/`. Styles live in `static/css/theme.css`; small behaviors in `static/js/app.js`.

## Principles

1. **Laptop first, phone complete.** Design for a 1280–1440px screen, then make sure every action works at
   390px and 820px wide. Phones are a course requirement, not an afterthought.
2. **One primary action per page.** Everything else is a quiet button, a text button, or a link.
3. **Every action answers.** Saves and deletes show a toast; htmx requests dim what they're updating;
   failures say what happened and what to do.
4. **Works without JS.** Build the plain form or link first. htmx only swaps parts of the page.
5. **Calm by default.** One accent color for actions. Stage tints only on stage pills, avatar tints only on avatars.
   Depth comes from one soft elevation token (`--oc-elev-1`) instead of borders; menus use `--oc-shadow-pop`.

These borrow from Material Design / MUI (8px grid, clear hierarchy, feedback, 44–48px touch targets,
visible focus, labels above fields). We don't use MUI itself: it's a React library.

## Tokens

| Token | Value | Use |
|---|---|---|
| `--oc-ink` | `#131A2A` | Sidebar, phone top bar, toasts |
| `--oc-canvas` | `#F5F6F8` | Page background |
| `--oc-surface` | `#FFFFFF` | Panels, tables, cards |
| `--oc-line` | `#E2E5EA` | Borders |
| `--oc-text` / `--oc-muted` | `#1A2130` / `#5D6677` | Body / secondary text |
| `--oc-accent` | `#4C5BD4` | Primary buttons, links, focus |
| `--oc-elev-1` | ring + two soft shadows | Panels, tables, cards (replaces borders) |
| `--oc-danger` | `#B3261E` | Destructive actions, errors |

- Type: Geist 400/500/600. Page title 24px/600, body 14px, meta 13px. Dates use `.tnum` (tabular numbers).
- Spacing: multiples of 4px. Radius: 7px for controls, 10px for panels and cards.
- Don't add new colors or font sizes; extend the tokens in `theme.css` if you truly need one.

## Layout

Three tiers. The shell switches at **1024px**; components switch at the widths below.

| Width | Shell | Components |
|---|---|---|
| ≥ 1024px | Dark 232px sidebar | Table rows; header Edit/Delete; popover menus; detail page two columns from 1200px |
| 768–1023px (tablets) | Sticky top bar + bottom tab bar (Contacts · Add · Account) | Table rows; Edit in top bar, Edit/Delete at page end; sticky form actions; detail two columns from 900px |
| < 768px (phones) | Same as tablets | Rows become cards; stage menu becomes a bottom sheet; fields stack under 600px |

Patterns we reuse from our other apps (zhiji, headsup, intake, yale-radar):
- `viewport-fit=cover` and `env(safe-area-inset-*)` on every fixed bar (top bar, tab bar, sheets).
- Bottom tab bar on touch layouts, with a round accent **Add** in the middle for the main action.
- The tab bar slides away while a text field has focus (`body.kbd-open`, set in `app.js`).
- The form's Save/Cancel bar sticks above the tab bar, within thumb reach.
- Menus become bottom sheets on phones: grip, `88dvh` max, `overscroll-behavior: contain`, tap outside to close.
- `@media (pointer: coarse)`: 44px targets and 16px inputs. `@media (hover: none)`: no hover-only UI.
- Overflow safety: `overflow-x: clip`, `minmax(0, 1fr)` columns, `overflow-wrap: anywhere` on names and notes.
- No CSS container queries on page wrappers: they make `position: fixed` children (sheets) position inside the wrapper.

- Logged-in pages extend `templates/app.html`.
- Public pages (login, landing, the A/B page) extend `templates/base.html`, which has **no navigation**.
  Never add buttons there: the A/B page must contain exactly one `<button>`.
- Page header: `.page-head` with `.page-title`, optional `.page-meta`, and `.page-actions` on the right.
  Below 1024px, `.page-actions` in the header is often hidden; put a quick action in `{% block page_actions %}`
  (top bar, right) and repeat important actions at the end of the page (see `.detail-mobile-actions`).
- Content blocks: `.panel` with an `h2.panel-title`.

## Components

| Component | Where | Notes |
|---|---|---|
| Form field | `templates/components/_field.html` | `{% include 'components/_field.html' with field=form.x optional=True %}`. Label above, help text, error below with `aria-describedby`. Use `css="form-select"` for selects. |
| Buttons | Bootstrap `.btn` + `.btn-primary`, `.btn-quiet`, `.btn-danger-quiet`, `.btn-danger`, `.btn-text` | Verb first: "Add contact", "Save changes", "Delete contact". |
| Stage pill | `<span class="stage-pill stage-pill--{{ contact.stage }}">{{ contact.get_stage_display }}</span>` | Soft pill + dot, one tint per stage (gray, amber, blue, violet, green, light gray). The label is always the text. |
| Avatar | `{% load contacts_ui %}{% avatar contact.name %}` (`"lg"` for 52px) | Initials on a stable tint chosen from the name (crc32, six tones). Decorative (`aria-hidden`). |
| Row quick actions | `.row-actions` in `contacts/_row.html` | Own last column; appear on hover or keyboard focus on devices with a mouse (`any-hover`), hidden on touch and phones. Each link has an `aria-label`. |
| Stage menu | `contacts/_stage_menu.html` | Needs `contact`, `stage_menu`, `menu_context` (`row`/`panel`), `next_url`. |
| Contact row/card | `contacts/_row.html` | Table row on desktop, card on phones (CSS only). List supports `?sort=updated|name|last_contact`. |
| Tag | `<span class="tag">finance</span>` | Lowercase. |
| Empty state | `.empty-state` with `.empty-icon`, `.empty-title`, `.empty-body`, one button | An invitation, not an apology. |
| Toast | Django `messages.success(...)` on redirects; `HX-Trigger: {"toast": "..."}` for htmx; `OfferChat.toast(msg, "error")` in JS | Short, past tense: "Contact added", "Stage updated". |
| Delete confirmation | `contacts/confirm_delete.html` | Name the thing, say what else goes, GET shows, POST deletes. |

## Writing

- Sentence case everywhere. No "please", no exclamation marks, no "successfully".
- Keep one verb through a flow: button "Add contact" → toast "Contact added".
- Errors say what's wrong and how to fix it: "Enter a name", "Enter a LinkedIn profile link, like linkedin.com/in/yourname".
- Empty states name the space and offer the next action.

## Accessibility checklist

- Every input has a visible `<label>`; icon-only buttons have `aria-label`.
- Focus is visible (accent outline). Don't remove outlines.
- Status is never color-only (stage icons always have text).
- Touch targets ≥ 44px on phones; inputs ≥ 16px font on phones (prevents iOS zoom).
- Respect `prefers-reduced-motion` (already handled in `theme.css`).

## Add a new page in 5 steps

1. Create a view with `@login_required`, scope every query to `request.user`, and pass `nav_active`.
2. Template: `{% extends 'app.html' %}`, set `{% block title %}`, build with `.page-head` and `.panel`.
3. Add a nav link in `templates/components/_nav.html` (only for features that work end to end).
4. Use the components above; check `/styleguide/` before inventing a new one.
5. Write tests (including another user getting 404), then check the page at 1440px, 820px and 390px wide,
   with nothing scrolling sideways and nothing hidden behind the tab bar.
