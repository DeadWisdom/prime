# Google Gmail and Calendar Integration

researched: 2026-01-26
status: complete
tags: google, gmail, calendar, api, oauth, python, cli, integration

## Executive Summary

Connecting to Gmail and Google Calendar programmatically requires OAuth 2.0 authentication (mandatory since September 2024). The most practical approaches are: (1) Google's official APIs with the `google-api-python-client` library, (2) simplified wrapper libraries like `simplegmail`, or (3) CLI tools like `gcalcli` and `gscli` for quick access without building a full integration.

## Background

Google deprecated "less secure app" access and now requires OAuth 2.0 for all programmatic access to Gmail and Calendar. This applies to both the REST APIs and legacy protocols (IMAP/SMTP/CalDAV). For personal use and development, you'll create OAuth credentials in Google Cloud Console; for enterprise deployment, service accounts with domain-wide delegation are available but require admin privileges and carry security considerations.

## Authentication Methods

### OAuth 2.0 (Standard Approach)

The recommended method for accessing user data. Involves:

1. **Create OAuth Client ID** in [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. **Download credentials.json** (client secrets file)
3. **User authorizes via browser** on first run
4. **Token saved locally** (typically as `token.json`) for future use

**Key libraries:**
```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

**Basic authentication flow:**
```python
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds
```

**Important limitations:**
- Apps in "Testing" mode have refresh tokens that expire after 7 days
- Limit of 100 refresh tokens per Google Account per OAuth client
- Restricted scopes require verification for public apps

### Service Accounts (Enterprise/Workspace)

For Google Workspace organizations only. Allows server-to-server access without user interaction.

1. Create service account in Cloud Console
2. Enable domain-wide delegation in Google Admin Console
3. Grant specific OAuth scopes to the service account
4. Service account impersonates users to access their data

**Use cases:** Automated systems, background processing, admin tools

**Security warning:** Domain-wide delegation grants broad access. A compromised service account can access any user's data within the granted scopes.

## Gmail Integration Options

### Option 1: Gmail API (Recommended)

The official REST API. Full-featured but requires understanding the API structure.

**Setup:**
1. Enable Gmail API in Cloud Console
2. Create OAuth credentials
3. Use `google-api-python-client`

**Example - List messages:**
```python
from googleapiclient.discovery import build

def list_messages(creds):
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', maxResults=10).execute()
    messages = results.get('messages', [])
    for msg in messages:
        message = service.users().messages().get(userId='me', id=msg['id']).execute()
        print(message['snippet'])
```

### Option 2: simplegmail Library

A Pythonic wrapper around the Gmail API. Significantly reduces boilerplate.

```bash
pip install simplegmail
```

```python
from simplegmail import Gmail

gmail = Gmail()  # Uses credentials.json in current directory
messages = gmail.get_unread_inbox()
for message in messages:
    print(f"From: {message.sender}")
    print(f"Subject: {message.subject}")
    print(f"Body: {message.plain}")
```

**Features:**
- Automatic OAuth handling (saves token to `gmail-token.json`)
- Mark read/unread, star, trash, archive
- Send messages and attachments
- Label management

### Option 3: IMAP with OAuth 2.0

Use Python's built-in `imaplib` with OAuth authentication. Useful if you need IMAP-specific features or already have IMAP-based code.

```python
import imaplib

def imap_connect(username, access_token):
    auth_string = f'user={username}\1auth=Bearer {access_token}\1\1'
    imap = imaplib.IMAP4_SSL('imap.gmail.com')
    imap.authenticate('XOAUTH2', lambda x: auth_string)
    return imap
```

**Note:** Requires the full `https://mail.google.com/` scope.

### Gmail API Scopes (Least to Most Permissive)

| Scope | Description |
|-------|-------------|
| `gmail.labels` | Create, read, update, delete labels only |
| `gmail.send` | Send messages only (no read access) |
| `gmail.readonly` | Read all messages and metadata (no write) |
| `gmail.compose` | Create, read, update, delete drafts; send messages |
| `gmail.insert` | Insert and import messages only |
| `gmail.modify` | All read/write except permanent deletion |
| `mail.google.com` | Full access including permanent deletion |

**Best practice:** Use the most restrictive scope that meets your needs. `gmail.readonly` is sufficient for reading emails.

## Calendar Integration Options

### Option 1: Google Calendar API

**Setup:**
1. Enable Google Calendar API in Cloud Console
2. Use same OAuth credentials as Gmail (add calendar scopes)

**Example - List upcoming events:**
```python
from googleapiclient.discovery import build
from datetime import datetime

def list_events(creds):
    service = build('calendar', 'v3', credentials=creds)
    now = datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        maxResults=10,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"{start}: {event['summary']}")
```

**Calendar API Scopes:**
- `calendar.readonly` - View calendars and events
- `calendar` - Full read/write access
- `calendar.events` - Read/write events only
- `calendar.events.readonly` - View events only

### Option 2: CalDAV Protocol

Google supports CalDAV, though documentation is sparse. Use the `caldav` Python library.

```bash
pip install caldav
```

**Endpoint:** `https://apidata.googleusercontent.com/caldav/v2/{calendarId}/events`

**Note:** Still requires OAuth 2.0. The old `google.com/calendar/dav` endpoint is deprecated.

## CLI Tools

### gcalcli (Google Calendar CLI)

Mature, full-featured calendar CLI.

```bash
pip install gcalcli
```

**Commands:**
```bash
gcalcli list           # List calendars
gcalcli agenda         # View upcoming events
gcalcli calw           # Weekly calendar view
gcalcli calm           # Monthly calendar view
gcalcli quick "Meeting tomorrow at 2pm"  # Quick add
```

**Setup:** Requires creating your own OAuth credentials. On first run, opens browser for authorization.

### gscli (Google Service CLI)

Covers Gmail, Calendar, and Drive with structured output (JSON/table/text).

**Gmail commands:**
```bash
gscli gmail list                    # List recent emails
gscli gmail search "is:unread"      # Search with Gmail syntax
gscli gmail read <message-id>       # Read specific email
```

**Calendar commands:**
```bash
gscli calendar list                 # List calendars
gscli calendar events               # List events
```

### gogcli

Another multi-service CLI (Gmail, Calendar, Drive, Contacts).

```bash
gog calendar events <calendarId> --today
gog calendar events <calendarId> --week
```

## Practical Recommendations

### For Quick Personal Use

1. **Calendar:** Use `gcalcli` - mature, well-documented, just works
2. **Gmail:** Use `gscli` or the `simplegmail` library

### For Script/Automation

1. Use `simplegmail` for email operations (cleaner API)
2. Use `google-api-python-client` directly for calendar
3. Store `token.json` securely (contains refresh token)

### For Production Applications

1. Use official Google APIs (`google-api-python-client`)
2. Request minimal scopes
3. Handle token refresh properly
4. Consider service accounts for server-to-server (Workspace only)
5. Apps using restricted scopes need verification for public release

## Setup Checklist

1. [ ] Create Google Cloud project at [console.cloud.google.com](https://console.cloud.google.com)
2. [ ] Enable Gmail API and/or Google Calendar API
3. [ ] Configure OAuth consent screen (Internal for Workspace, External for personal)
4. [ ] Create OAuth 2.0 Client ID (Desktop app type for CLI/scripts)
5. [ ] Download `credentials.json`
6. [ ] Install libraries: `pip install google-api-python-client google-auth-oauthlib`
7. [ ] Run authentication flow (browser opens for consent)
8. [ ] Token saved to `token.json` for future use

## Sources & Further Reading

- [Gmail API Python Quickstart](https://developers.google.com/workspace/gmail/api/quickstart/python)
- [Google Calendar API Python Quickstart](https://developers.google.com/workspace/calendar/api/quickstart/python)
- [Gmail API Scopes Reference](https://developers.google.com/workspace/gmail/api/auth/scopes)
- [OAuth 2.0 for Google APIs](https://developers.google.com/identity/protocols/oauth2)
- [simplegmail on GitHub](https://github.com/jeremyephron/simplegmail)
- [gcalcli on GitHub](https://github.com/insanum/gcalcli)
- [gscli on GitHub](https://github.com/shaharia-lab/gscli)
- [CalDAV API Guide](https://developers.google.com/workspace/calendar/caldav/v2/guide)
- [Domain-wide Delegation Guide](https://support.google.com/a/answer/162106)

## Open Questions

- **App verification:** If building a public-facing app with restricted Gmail scopes, what is the current timeline and cost for Google's security assessment?
- **Token storage:** Best practices for secure token storage in multi-user applications (likely needs a database with encryption)
- **Rate limits:** Current Gmail API quota limits for personal vs. Workspace accounts
- **pythonic-gmail:** New library (Sept 2025) worth evaluating as alternative to simplegmail
