"""
Gmail MCP Server.

Exposes 4 tools over stdio via the official `mcp` SDK:
    - send_email
    - search_email
    - read_email
    - reply_email

Auth: standard Google OAuth "installed app" flow.
  1. In Google Cloud Console: create a project, enable the Gmail API,
     create an OAuth Client ID of type "Desktop app", download it as
     credentials.json, and place it at the project root (or point
     GMAIL_CREDENTIALS_PATH at it).
  2. First run opens a browser to authorize; a token.json is cached
     afterwards (path controlled by GMAIL_TOKEN_PATH) so you won't be
     asked again until it expires.

Run standalone for testing:
    python servers/gmail/server.py
(Normally this is spawned automatically by main.py over stdio.)
"""

from __future__ import annotations

import base64
import os
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from mcp.server.fastmcp import FastMCP

# gmail.modify covers read + send + reply + search (no delete/settings access)
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "token.json")

mcp = FastMCP("gmail")


def _get_credentials() -> Credentials:
    creds: Credentials | None = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Gmail OAuth credentials not found at '{CREDENTIALS_PATH}'. "
                    "Download an OAuth Client ID (Desktop app) from Google Cloud "
                    "Console and place it there, or set GMAIL_CREDENTIALS_PATH."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return creds


def _service():
    return build("gmail", "v1", credentials=_get_credentials())


def _extract_body(payload: dict) -> str:
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
                return base64.urlsafe_b64decode(part["body"]["data"]).decode(
                    "utf-8", errors="replace"
                )
        for part in payload["parts"]:
            if "parts" in part:
                nested = _extract_body(part)
                if nested:
                    return nested
        return "(no plain-text body found)"

    data = payload.get("body", {}).get("data")
    if data:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    return "(empty body)"


@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """Send a new email via Gmail.

    Args:
        to: recipient email address
        subject: email subject line
        body: plain-text email body
    """
    service = _service()

    message = EmailMessage()
    message.set_content(body)
    message["To"] = to
    message["Subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()

    return f"Email sent to {to} (id: {sent.get('id')})"


@mcp.tool()
def search_email(query: str, max_results: int = 5) -> str:
    """Search Gmail using Gmail's search syntax, e.g. 'from:someone subject:invoice'
    or 'is:unread newer_than:2d'.

    Args:
        query: Gmail search query string
        max_results: maximum number of messages to return (default 5)
    """
    service = _service()
    results = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )
    messages = results.get("messages", [])

    if not messages:
        return "No messages found."

    lines = []
    for m in messages:
        msg = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=m["id"],
                format="metadata",
                metadataHeaders=["Subject", "From", "Date"],
            )
            .execute()
        )
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        lines.append(
            f"id={m['id']} | From: {headers.get('From', '?')} | "
            f"Subject: {headers.get('Subject', '(no subject)')} | "
            f"Date: {headers.get('Date', '?')}"
        )

    return "\n".join(lines)


@mcp.tool()
def read_email(message_id: str) -> str:
    """Fetch the full content of a Gmail message (sender, subject, date, body).

    Args:
        message_id: the Gmail message id, as returned by search_email
    """
    service = _service()
    msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    body = _extract_body(msg["payload"])

    return (
        f"From: {headers.get('From', '?')}\n"
        f"Subject: {headers.get('Subject', '(no subject)')}\n"
        f"Date: {headers.get('Date', '?')}\n\n"
        f"{body}"
    )


@mcp.tool()
def reply_email(message_id: str, body: str) -> str:
    """Reply to an existing Gmail message, staying in the same thread.

    Args:
        message_id: id of the message being replied to
        body: plain-text reply body
    """
    service = _service()
    original = (
        service.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="metadata",
            metadataHeaders=["Subject", "From", "Message-ID"],
        )
        .execute()
    )
    headers = {h["name"]: h["value"] for h in original["payload"]["headers"]}
    thread_id = original["threadId"]

    reply = EmailMessage()
    reply.set_content(body)
    reply["To"] = headers.get("From", "")
    subject = headers.get("Subject", "")
    reply["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"

    if headers.get("Message-ID"):
        reply["In-Reply-To"] = headers["Message-ID"]
        reply["References"] = headers["Message-ID"]

    raw = base64.urlsafe_b64encode(reply.as_bytes()).decode()
    sent = (
        service.users()
        .messages()
        .send(userId="me", body={"raw": raw, "threadId": thread_id})
        .execute()
    )

    return f"Reply sent (id: {sent.get('id')})"


if __name__ == "__main__":
    mcp.run(transport="stdio")