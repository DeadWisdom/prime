#!/usr/bin/env python3
"""
Gmail Thread Search

Searches Gmail and prints the latest threads matching a query.
Requires credentials.json from Google Cloud Console.
"""

import base64
import re
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

app = typer.Typer(help="Search Gmail and display threads.")
console = Console()

# If modifying scopes, delete token.json
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Paths for credentials
SCRIPT_DIR = Path(__file__).parent
CREDENTIALS_FILE = SCRIPT_DIR / "credentials.json"
TOKEN_FILE = SCRIPT_DIR / "token.json"


def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                console.print(f"[red]Error:[/red] {CREDENTIALS_FILE} not found.")
                console.print("\nTo set up Gmail API access:")
                console.print("1. Go to https://console.cloud.google.com/")
                console.print("2. Create a project (or select existing)")
                console.print("3. Enable the Gmail API")
                console.print("4. Create OAuth 2.0 credentials (Desktop app)")
                console.print("5. Download and save as 'credentials.json' in this directory")
                raise typer.Exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def search_threads(service, query: str, max_results: int = 10, page_token: Optional[str] = None):
    """Search Gmail threads and return results."""
    params = {
        "userId": "me",
        "q": query,
        "maxResults": max_results,
    }
    if page_token:
        params["pageToken"] = page_token

    results = service.users().threads().list(**params).execute()

    return results.get("threads", []), results.get("nextPageToken")


def get_thread_details(service, thread_id: str):
    """Get full thread details including messages."""
    thread = service.users().threads().get(
        userId="me",
        id=thread_id,
        format="full"
    ).execute()

    return thread


def extract_header(headers: list, name: str) -> str:
    """Extract a header value from message headers."""
    for header in headers:
        if header["name"].lower() == name.lower():
            return header["value"]
    return ""


def get_message_body(payload: dict) -> str:
    """Extract the plain text body from a message payload."""
    # Direct body
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    # Multipart - look for text/plain
    parts = payload.get("parts", [])
    for part in parts:
        mime_type = part.get("mimeType", "")

        if mime_type == "text/plain":
            data = part.get("body", {}).get("data")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        # Nested multipart
        if mime_type.startswith("multipart/"):
            body = get_message_body(part)
            if body:
                return body

    # Fallback to text/html if no plain text
    for part in parts:
        if part.get("mimeType") == "text/html":
            data = part.get("body", {}).get("data")
            if data:
                html = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                # Strip HTML tags (basic)
                text = re.sub(r'<[^>]+>', '', html)
                text = re.sub(r'\s+', ' ', text).strip()
                return text

    return "(no text content)"


# Patterns that indicate the start of quoted reply content
REPLY_HEADER_PATTERNS = [
    r'^On [A-Z][a-z]{2}, [A-Z][a-z]{2} \d{1,2}, \d{4}',  # "On Thu, Jan 15, 2026"
    r'^On \d{1,2}/\d{1,2}/\d{2,4}',                       # "On 1/15/2026"
    r'^\d{4}-\d{2}-\d{2} .+ <.+>',                        # "2024-01-01 Person <email>"
    r'^-+\s*Original Message\s*-+',                       # "--- Original Message ---"
    r'^_{5,}',                                            # "___________" (Outlook separator)
    r'^\*From:\*',                                        # "*From:*" (bold markdown style)
    r'^>',                                                # Quoted line
]

REPLY_HEADER_RE = re.compile('|'.join(REPLY_HEADER_PATTERNS), re.MULTILINE)


def strip_reply_content(body: str) -> str:
    """Remove quoted reply content from email body."""
    # Try to find a reply header and truncate there
    match = REPLY_HEADER_RE.search(body)
    if match:
        truncated = body[:match.start()].rstrip()
        if truncated:
            return truncated

    # Fallback: strip lines starting with >
    lines = body.split('\n')
    cleaned = []
    for line in lines:
        if line.lstrip().startswith('>'):
            continue
        cleaned.append(line)

    return '\n'.join(cleaned).rstrip()


def print_thread(thread: dict):
    """Print a thread with all messages."""
    messages = thread.get("messages", [])
    if not messages:
        return

    first_msg = messages[0]
    headers = first_msg.get("payload", {}).get("headers", [])
    subject = extract_header(headers, "Subject") or "(no subject)"

    console.print(Panel(f"[bold]{subject}[/bold]", style="blue"))

    for i, msg in enumerate(messages):
        payload = msg.get("payload", {})
        headers = payload.get("headers", [])

        from_addr = extract_header(headers, "From")
        to_addr = extract_header(headers, "To")
        date = extract_header(headers, "Date")
        body = strip_reply_content(get_message_body(payload))

        console.print(f"\n[dim]{'─' * 70}[/dim]")
        console.print(f"[cyan]Message {i + 1}/{len(messages)}[/cyan]")
        console.print(f"[green]From:[/green] {from_addr}")
        console.print(f"[green]To:[/green]   {to_addr}")
        console.print(f"[green]Date:[/green] {date}")
        console.print(f"[dim]{'─' * 70}[/dim]")
        console.print(body.strip())

    console.print()


@app.command()
def search(
    query: str = typer.Argument(..., help="Gmail search query"),
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of threads to return"),
    page: int = typer.Option(1, "--page", "-p", help="Page number (1-based)"),
):
    """
    Search Gmail threads matching a query.

    Examples:

        uv run gmail_search.py "is:unread"

        uv run gmail_search.py "from:sarah@joincolumn.com" --limit 5

        uv run gmail_search.py "subject:invoice" --page 2
    """
    console.print(f"[dim]Searching Gmail for:[/dim] [bold]{query}[/bold]\n")

    service = get_gmail_service()

    # Handle pagination by fetching pages until we reach the desired one
    page_token = None
    current_page = 1

    while current_page < page:
        _, page_token = search_threads(service, query, limit, page_token)
        if not page_token:
            console.print(f"[yellow]No results on page {page}. Only {current_page} page(s) available.[/yellow]")
            raise typer.Exit(0)
        current_page += 1

    threads, next_page_token = search_threads(service, query, limit, page_token)

    if not threads:
        console.print("[yellow]No threads found matching your query.[/yellow]")
        raise typer.Exit(0)

    console.print(f"[dim]Page {page} · Showing {len(threads)} thread(s)[/dim]")
    if next_page_token:
        console.print(f"[dim]More results available (use --page {page + 1})[/dim]")
    console.print()

    for thread_summary in threads:
        thread = get_thread_details(service, thread_summary["id"])
        print_thread(thread)


if __name__ == "__main__":
    app()
