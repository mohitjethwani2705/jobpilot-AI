"""JobPilot Week 1: fetch job emails from Gmail and classify them with Gemini."""
import os, json, base64
from enum import Enum
from pydantic import BaseModel
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google import genai

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
QUERY = ('newer_than:30d ("application" OR "interview" OR "assessment" '
         'OR "applying" OR "shortlisted" OR "unfortunately" OR "offer")')


class Stage(str, Enum):
    applied = "applied"
    assessment = "assessment"
    interview = "interview"
    offer = "offer"
    rejected = "rejected"
    not_job = "not_job"


class JobEmail(BaseModel):
    company: str
    role: str
    stage: Stage
    next_step: str


def gmail_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def get_body(payload):
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode(errors="ignore")
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" or part.get("parts"):
            text = get_body(part)
            if text:
                return text
    return ""


def fetch_emails(svc, limit=25):
    res = svc.users().messages().list(userId="me", q=QUERY, maxResults=limit).execute()
    emails = []
    for m in res.get("messages", []):
        msg = svc.users().messages().get(userId="me", id=m["id"], format="full").execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        emails.append({
            "id": m["id"],
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "body": get_body(msg["payload"])[:3000],
        })
    return emails


def classify(client, email):
    prompt = (
        "You track a job seeker's applications. Read this email and extract the "
        "company, role, hiring stage and the candidate's next step. If it is not "
        "about a job application, use stage not_job.\n\n"
        f"From: {email['from']}\nSubject: {email['subject']}\n\n{email['body']}"
    )
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"response_mime_type": "application/json", "response_schema": JobEmail},
    )
    return resp.parsed


def main():
    svc = gmail_service()
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    results = []
    for email in fetch_emails(svc):
        job = classify(client, email)
        if job and job.stage != Stage.not_job:
            row = {**job.model_dump(mode="json"), "date": email["date"], "email_id": email["id"]}
            results.append(row)
            print(f"{row['company']:<20} {row['role']:<30} {row['stage']:<11} {row['next_step']}")
    with open("applications.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved {len(results)} job emails to applications.json")


if __name__ == "__main__":
    main()
