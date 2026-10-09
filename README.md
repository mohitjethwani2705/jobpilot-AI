# JobPilot

AI agent that tracks your job hunt from Gmail: it finds application, assessment, interview, offer and rejection emails, logs them to Google Sheets, drafts follow-ups, and adds interviews to Google Calendar.

## Roadmap
- [ ] Week 1: Gmail OAuth, fetch job emails, Gemini classifies company / role / stage (structured JSON)
- [ ] Week 2: Write to Google Sheets, dedupe by company + role, Calendar events for interviews
- [ ] Week 3: Agent with tools (search_emails, update_sheet, draft_reply) + human approval before sending
- [ ] Week 4: MCP server, dashboard, Docker deploy, demo video

## Setup
1. Google Cloud: create a project, enable the Gmail API, create an OAuth "Desktop app" client, download it as `credentials.json` into the repo root.
2. Get a Gemini API key from https://aistudio.google.com and set `GEMINI_API_KEY`.
3. `pip install -r requirements.txt`
4. `python -m jobpilot.classify`

## Stack
Python, Gemini API, Gmail / Sheets / Calendar APIs, LangGraph (week 3), MCP (week 4), Docker.
