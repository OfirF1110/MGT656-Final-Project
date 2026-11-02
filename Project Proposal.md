# Project Proposal

We propose the following three ideas, ranked by preference. Our first choice is OfferChat, based on our existing HTML prototype. Each project would use Django, PostgreSQL, server-rendered HTML/CSS with small JavaScript interactions, and LLM calls through OpenRouter.

## First choice OfferChat

### Tagline

A personal networking assistant that turns professional relationships and meeting notes into useful follow-ups and recruiting opportunities.

### Major user journeys

- **As a student or job seeker,** I log in, add contacts and their companies, record how people are connected, and track each relationship from initial outreach to meeting and follow-up.

- **After a networking conversation,** I paste rough notes, review the AI summary and suggested actions, and save the meeting to the relevant contacts. I return to my task list to complete follow-ups.

- **Before a meeting or application,** I review the contact’s history, generate a preparation brief or outreach draft, and look up people I already know at the target company.

### Core features for the MVP

- **Contact management:** Private accounts; create, edit, search, and tag contacts with roles, companies, relationship stages, and last-contact dates.

- **Network view:** A contact list and simple relationship graph showing manually recorded connections.

- **Meeting history:** Log conversations, link attendees, and retain editable notes and summaries.

- **Follow-up tasks:** Review suggested actions, assign due dates, and mark tasks complete or dismissed.

- **Recruiting workspace:** Save opportunities manually and find existing contacts at the same company.

Out of scope: automated job-board crawling, LinkedIn synchronization, email or calendar integrations, and automatic message sending.

### AI feature

The LLM converts rough meeting notes into a summary, people mentioned, and concrete follow-up suggestions. It also drafts personalized outreach and meeting preparation briefs using saved contact history. Users review the output before saving tasks or using drafts.

## Second choice AI Financial Analyst

### Tagline

An AI research assistant that helps financial analysts track companies, analyze financial updates, and identify important changes.

### Major user journeys

- **As an analyst,** I log in, add public companies to a watchlist, and open a company page with the financial reports and updates I have saved.

- **When new earnings information is released,** I paste report excerpts or upload a text-based report, enter key financial metrics, and compare the latest period with previous results.

- **While researching a company,** I ask questions about saved reports, review the AI explanation alongside the relevant excerpts, and save useful analyses for later.

### Core features for the MVP

- **Company watchlist:** Add, remove, and organize companies covered by the user.

- **Company research pages:** Keep company details, uploaded reports, reporting periods, and saved analyses in one place.

- **Financial update comparison:** Compare user-entered metrics such as revenue, margins, and earnings across two periods, with percentage changes calculated by the application.

- **AI research interface:** Ask questions about selected reports and receive concise responses with references to the supplied text.

- **Saved analysis history:** Save and revisit summaries, questions, and comparisons by company and date.

Out of scope: real-time market data, automated trading, comprehensive web crawling, portfolio management, and scanned-document OCR. The MVP relies on user-supplied reports and a small set of financial metrics.

### AI feature

The LLM reads user-supplied financial reports and company updates, summarizes key information, identifies changes between reporting periods, and explains their possible implications. Answers point back to supporting report excerpts and flag missing information. The application performs numerical calculations; the LLM explains the results.

## Third choice Overlap

### Tagline

Find a time that works for everyone in a study group or team, from your phone.

### Major user journeys

- **As an organizer,** I log in and describe a meeting, such as “next Wednesday or Thursday evening, 90 minutes, group project sync.” I review the event details extracted by the AI and share a link in the group chat.

- **As a participant,** I open the link on my phone, enter my name without creating an account, and mark times as free, maybe, or busy. I can also type my availability for the AI to fill the grid, review it, and return later through a private edit link.

- **As an organizer,** I view the overlap heatmap and ranked slots, choose and confirm a time, and share the confirmation. Participants can download a calendar invitation.

- **As an admin,** I review flagged events and delete inappropriate content.

### Core features for the MVP

- **Event management:** Organizer accounts; create, edit, and delete events with candidate dates, time windows, duration, time zone, and a shareable link.

- **Mobile availability grid:** Name-only responses with free, maybe, and busy states; private links allow participants to edit their responses.

- **Overlap and ranking:** A heatmap and ranked meeting slots based on participant availability and the required duration.

- **Confirmation and calendar export:** A confirmed-time page and downloadable .ics invitation that the organizer can share.

- **AI text input:** Turn a meeting request or participant availability into editable event fields or grid selections.

Stretch goals: voice input, Google Calendar free/busy import, and web push notifications. Out of scope: recurring events and automatic meeting links.

### AI feature

The LLM extracts a title, candidate dates, time window, and duration from the organizer’s request. It also translates statements such as “free Tuesday after 5” into proposed grid selections. Users confirm the interpretation before saving. The application calculates overlap; the LLM summarizes conflicts and explains the best compromise.
