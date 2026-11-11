# Sprint 1 report

**Sprint goal:** Get the whole pipeline working end to end before real features: a Django app with accounts on Postgres, live on staging, with the A/B test page and a working backlog.

**What shipped:** All five stories, each through a reviewed pull request.

- App skeleton ([#1](https://github.com/OfirF1110/MGT656-Final-Project/issues/1)), login and logout ([#2](https://github.com/OfirF1110/MGT656-Final-Project/issues/2)), seed with grader accounts ([#3](https://github.com/OfirF1110/MGT656-Final-Project/issues/3)): pull request [#7](https://github.com/OfirF1110/MGT656-Final-Project/pull/7).
- A/B test page ([#4](https://github.com/OfirF1110/MGT656-Final-Project/issues/4)) and stats ([#5](https://github.com/OfirF1110/MGT656-Final-Project/issues/5)): pull request [#8](https://github.com/OfirF1110/MGT656-Final-Project/pull/8).
- [Team board](https://github.com/users/OfirF1110/projects/3) with four sprint iterations, and these docs ([#6](https://github.com/OfirF1110/MGT656-Final-Project/issues/6)).

**What works on staging now:** https://offerchat-staging.onrender.com, deployed from `main` with its own Neon Postgres database.

- Login, logout and a protected account page. Both seeded grader accounts log in.
- The A/B page at `/020c45f`: one `kudos` or `thanks` button, a stable word per visitor, one impression and at most one click each.
- `/020c45f/stats` returns live JSON with `preferred`. All 24 tests pass.

**Working with our agents:** Our agents called work done when it only worked locally. Codex's local tests passed while the database connection and the deployment were still unverified. We changed our rule: a story is done only after a person checks it on staging, and the developer verifies Neon, the grader accounts and staging before opening a pull request.

**Backlog changes for next sprint:** Nothing carries over. We plan to add: a production environment with its own database; our first product stories (manage contacts, log a meeting); a start on the AI summary of meeting notes; demo data in the seed; and a way to clear our A/B test visits before the bot run.
