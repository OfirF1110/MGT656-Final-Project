# Sprint 2 report

**Sprint goal:** Put production live with its own database, ship our first product stories through reviewed pull requests, and start the AI feature.

**What shipped:** All four stories, each through a reviewed pull request.

- Contact management ([#10](https://github.com/OfirF1110/MGT656-Final-Project/issues/10)) and demo contacts in the seed ([#25](https://github.com/OfirF1110/MGT656-Final-Project/issues/25)): pull requests [#28](https://github.com/OfirF1110/MGT656-Final-Project/pull/28) and [#29](https://github.com/OfirF1110/MGT656-Final-Project/pull/29), with review fixes [#30](https://github.com/OfirF1110/MGT656-Final-Project/pull/30) and [#31](https://github.com/OfirF1110/MGT656-Final-Project/pull/31).
- AI summary of meeting notes, first slice ([#24](https://github.com/OfirF1110/MGT656-Final-Project/issues/24)): pull requests [#33](https://github.com/OfirF1110/MGT656-Final-Project/pull/33) and [#34](https://github.com/OfirF1110/MGT656-Final-Project/pull/34).
- Production environment with its own database ([#23](https://github.com/OfirF1110/MGT656-Final-Project/issues/23)): pull request [#32](https://github.com/OfirF1110/MGT656-Final-Project/pull/32).

**What works on staging now:** https://offerchat-staging.onrender.com and production at https://offerchat-production.onrender.com, both deployed from `main`, each with its own Neon Postgres database.

- Contacts: add, edit, delete and search, with six relationship stages. Users see only their own contacts, and the seed gives each grader account eight samples.
- `/summaries/`: paste meeting notes and get a two to three sentence summary. The server calls the model through OpenRouter, and nothing is saved.
- All 137 tests pass. Known issue: one production summary hit the model's output limit and showed a safe error. It has not recurred, and we added logging to find the cause.

**Working with our agents:** Mocked tests gave us false confidence. Codex's summary code passed every mocked test, but the first real calls on staging returned only one summary item, ran out of output length, or added stray text. We changed our rule: an AI story needs a few real calls with made-up notes on staging before merge, and failures log only an error category, never the notes.

**Backlog changes for next sprint:** Backlog cleanup ([#26](https://github.com/OfirF1110/MGT656-Final-Project/issues/26)) and the `technical.md` update ([#27](https://github.com/OfirF1110/MGT656-Final-Project/issues/27)) carry over. We closed [#16](https://github.com/OfirF1110/MGT656-Final-Project/issues/16), which overlapped with #10. For Sprint 3 we plan the rest of the AI story ([#11](https://github.com/OfirF1110/MGT656-Final-Project/issues/11): follow-up suggestions and saved notes), the follow-up task list ([#12](https://github.com/OfirF1110/MGT656-Final-Project/issues/12)), and finding the cause of the cut-off summary.
