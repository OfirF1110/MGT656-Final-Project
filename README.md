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
