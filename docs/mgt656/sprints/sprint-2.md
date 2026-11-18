# Sprint 2 report

**Sprint goal:** Put production live with its own database, ship our first product stories through reviewed pull requests, and start the AI feature.

**What shipped:** Four stories, each through a reviewed pull request.

- Contact management with relationship stages ([#10](https://github.com/OfirF1110/MGT656-Final-Project/issues/10)): pull request [#28](https://github.com/OfirF1110/MGT656-Final-Project/pull/28), plus review fix [#30](https://github.com/OfirF1110/MGT656-Final-Project/pull/30).
- Demo contacts in the seed ([#25](https://github.com/OfirF1110/MGT656-Final-Project/issues/25)): pull request [#29](https://github.com/OfirF1110/MGT656-Final-Project/pull/29), plus review fix [#31](https://github.com/OfirF1110/MGT656-Final-Project/pull/31).
- AI summary of meeting notes, first slice ([#24](https://github.com/OfirF1110/MGT656-Final-Project/issues/24)): pull request [#33](https://github.com/OfirF1110/MGT656-Final-Project/pull/33), plus failure logging in [#34](https://github.com/OfirF1110/MGT656-Final-Project/pull/34).
- Production environment with its own database ([#23](https://github.com/OfirF1110/MGT656-Final-Project/issues/23)): pull request [#32](https://github.com/OfirF1110/MGT656-Final-Project/pull/32).

**What works on staging now:** [Staging](https://offerchat-staging.onrender.com) and [production](https://offerchat-production.onrender.com) both run `main`, each with its own Neon Postgres database.

- Contacts: add, edit, delete and search contacts, each with one of six relationship stages. Users see only their own contacts.
- The seed gives each grader account eight sample contacts and is safe to rerun.
- `/summaries/`: paste meeting notes and get a two to three sentence summary. The server calls the model through OpenRouter, and nothing is saved.
- All 137 tests pass, with the model mocked.
- Known issue: one production summary request hit the model's output limit and showed a safe error with the notes kept. It has not happened again, and we added logging to find the cause.

**Working with our agents:** Mocked tests gave us false confidence on the AI feature. Codex's summary code passed every mocked test, but the first real calls on staging returned only one summary item, ran out of output length, or added stray text. We changed how we work: an AI story now needs a few real calls with made-up notes on staging before merge, the model must answer in a strict format that the server checks, and failures log only an error category, never the notes.

**Backlog changes for next sprint:** For Sprint 3 we plan the rest of the AI story ([#11](https://github.com/OfirF1110/MGT656-Final-Project/issues/11): follow-up suggestions and saved notes) as new sub-issues, the follow-up task list ([#12](https://github.com/OfirF1110/MGT656-Final-Project/issues/12)), and finding the cause of the cut-off summary. Backlog cleanup ([#26](https://github.com/OfirF1110/MGT656-Final-Project/issues/26)) and the `technical.md` update ([#27](https://github.com/OfirF1110/MGT656-Final-Project/issues/27)) carry over. We closed [#16](https://github.com/OfirF1110/MGT656-Final-Project/issues/16), which overlapped with #10. The other stories stay in the backlog without a sprint.
