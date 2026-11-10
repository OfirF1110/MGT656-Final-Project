# Technical Challenges and Testing Strategy

## Project scope

The proposal identifies OfferChat as the first-choice project, while the kickoff notes call the project CoffeeChat. Confirm the selected project and update this document before treating its feature scope as final.

The proposal's planned stack is Django, PostgreSQL, server-rendered HTML/CSS, small JavaScript interactions, and LLM calls through OpenRouter.

## Technical challenges

- **Account and data privacy:** Ensure users can access only their own records; cover authorization on reads and writes.
- **Reliable AI-assisted workflows:** Handle invalid, incomplete, or unavailable LLM responses without losing user input. Keep generated content reviewable and editable before saving or acting on it.
- **Relational data integrity:** Model the selected project's core records and relationships in PostgreSQL, and validate constraints and deletion behavior.
- **External service configuration:** Keep API credentials out of the repository; configure them outside source control and test AI-dependent behavior without requiring live calls.

## Testing strategy

- Write Django unit tests for model constraints, validation, and application logic.
- Write request or integration tests for authentication, authorization, core user journeys, and database behavior.
- Mock the LLM client to test successful, malformed, and failed responses deterministically.
- Run the project test suite and Django system checks before each sprint report is finalized.
- Do not commit passwords, API keys, or other secrets; use environment-based configuration for local and deployed environments.