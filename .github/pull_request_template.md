Closes #

## What the AI agent produced
<!-- Two or three lines: which files and features it wrote. -->

## What we changed or rejected, and why
<!-- What you fixed, rewrote or threw away. Write "nothing" if true. -->

## How to test
<!-- Steps a teammate follows to see it work, locally and on staging. -->

## Checklist
- [ ] Every acceptance criterion in the issue is met
- [ ] `python manage.py test` passes; no test calls a real external service
- [ ] Queries are scoped to the logged-in user; other users' data returns 404
- [ ] UI follows `docs/design/ui-guidelines.md`; screenshots at desktop and phone width attached
- [ ] Works without JavaScript where the page has forms
- [ ] No secrets, passwords or keys in the diff
- [ ] Verified on staging after merge (A/B page still has one button)
