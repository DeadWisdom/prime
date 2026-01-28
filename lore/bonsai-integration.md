# Bonsai (HelloBonsai) Programmatic Integration

researched: 2026-01-27
status: complete
tags: bonsai, invoicing, automation, browser-automation, api, zapier, playwright, vibium

## Executive Summary

HelloBonsai (hellobonsai.com) does not offer a public REST API with documented endpoints. The only official programmatic path is through Zapier, which provides trigger-only events (invoice paid, contract signed, etc.) but no actions for creating or sending invoices within Bonsai itself. For true invoice creation automation, browser automation via Playwright or Vibium is the most viable approach.

## Background

Bonsai is a business management platform for freelancers and agencies. It handles proposals, contracts, invoicing, time tracking, and CRM. The platform is primarily a GUI-driven web application at app.hellobonsai.com with no developer-facing API documentation.

The goal is to automate invoicing tasks -- specifically creating and sending invoices programmatically.

## Key Findings

### 1. No Public API

Bonsai does not publish a REST API, GraphQL API, or any developer documentation for direct programmatic access. There is no API reference, no SDKs, and no OAuth app registration.

The platform does generate an **API key** under Settings > Integrations & Data, but this key is explicitly designed for Zapier authentication, not general-purpose API access.

Bonsai's GitHub organization (github.com/HelloBonsai) contains a fork of n8n and an SSL pinning library but no public API client or documentation.

### 2. Zapier Integration (Official, Limited)

Bonsai's only official automation integration is Zapier. It provides:

**Triggers (events that flow OUT of Bonsai):**
- Contract signed / viewed
- Proposal accepted / viewed
- Invoice paid / viewed / created
- Deal updated
- Task updated
- New form response

**Actions (things you can do IN Bonsai via Zapier):**
- None documented for creating invoices or other entities within Bonsai.

This is a critical limitation: the Zapier integration is read-only in practice. You can react to Bonsai events in other tools (e.g., create an Xero invoice when a Bonsai contract is signed), but you cannot programmatically create an invoice inside Bonsai through Zapier.

### 3. No Make.com (Integromat) Integration

Bonsai does not have a native Make.com integration. The only workaround would be using Make's HTTP module with Bonsai's undocumented internal API endpoints, which carries the same risks as any reverse-engineering approach.

### 4. No Known Unofficial API Projects

No open-source projects exist that reverse-engineer Bonsai's internal API. However, tools like **Integuru** (github.com/Integuru-AI/Integuru) and **mitmproxy2swagger** could theoretically be used to capture and document Bonsai's internal HTTP endpoints by observing browser network traffic.

### 5. Browser Automation Options

Since no API exists, browser automation is the most practical path for creating and sending invoices.

#### Option A: Playwright (Recommended for reliability)

- **Mature and stable.** Microsoft-backed, 75k+ GitHub stars, massive community.
- **Python support** via `pip install playwright` and `playwright install`.
- **Handles modern SPAs well.** Auto-waiting, network interception, context isolation.
- **PDF handling.** Can intercept and validate invoice PDFs.
- **Headless operation.** Runs without a visible browser window, suitable for cron jobs or CI.
- **Well-documented.** Extensive docs, tutorials, and Stack Overflow coverage.

Typical invoice automation flow with Playwright:
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Login
    page.goto("https://app.hellobonsai.com/users/sign_in")
    page.fill('input[name="email"]', "user@example.com")
    page.fill('input[name="password"]', "password")
    page.click('button[type="submit"]')

    # Navigate to invoicing
    page.goto("https://app.hellobonsai.com/invoices/new")

    # Fill invoice fields (selectors would need inspection)
    # page.fill(...), page.click(...), etc.

    browser.close()
```

#### Option B: Vibium (Emerging, AI-native)

- **Created by Jason Huggins** (co-creator of Selenium and Appium).
- **AI-agent first design.** Built-in MCP server for Claude Code integration.
- **Python support** via `pip install vibium` (both sync and async APIs).
- **Simpler API** than Playwright for straightforward automation.
- **Self-healing locators.** Uses AI to adapt when UI elements change.
- **Current state:** v0.1.4 (January 2026), 2,500+ GitHub stars, Apache 2.0 license.

Vibium automation flow:
```python
from vibium import browser_sync as browser

vibe = browser.launch()
vibe.go("https://app.hellobonsai.com/users/sign_in")
email_field = vibe.find("email input")
email_field.type("user@example.com")
# ... continue with login and invoice creation
vibe.quit()
```

Vibium's advantage is its natural-language element finding ("email input" rather than CSS selectors), which makes scripts more resilient to UI changes. Its disadvantage is relative immaturity compared to Playwright.

#### Option C: Reverse-Engineer Internal API

Using browser DevTools or mitmproxy, one could capture the HTTP requests Bonsai's frontend makes when creating an invoice, then replicate those calls with a Python HTTP client (requests/httpx). This approach:

- Requires capturing and maintaining auth tokens (session cookies or JWTs)
- Is fragile -- any backend changes break the integration silently
- May violate Bonsai's Terms of Service
- Is the fastest at runtime (no browser overhead)
- Could be partially automated with tools like mitmproxy2swagger or Integuru

### 6. Bonsai's Native Workflow Automations

Bonsai has a built-in automation system for simple event-driven actions:
- When a contract is signed, send an email
- When a proposal is accepted, send a form
- When a form is filled out, schedule a meeting
- When the first invoice of a project is paid, trigger an action

These are limited to Bonsai's own predefined actions and cannot create invoices programmatically.

## Practical Implications

### Recommended Approach: Playwright + Python Script

For automating invoice creation and sending in Bonsai, the most practical architecture is:

1. **Playwright Python script** that logs into Bonsai, navigates to invoice creation, fills in fields, and sends the invoice.
2. **Credential management** via environment variables or a secrets manager (not hardcoded).
3. **Invoice data** sourced from a JSON/CSV file, a database, or passed as script arguments.
4. **Error handling** with screenshots on failure for debugging.
5. **Scheduling** via cron, systemd timer, or a task runner.

This project would use `uv` for dependency management:
```
uv add playwright
uv run playwright install chromium
```

### When to Consider Vibium Instead

If the automation will be driven by an AI agent (e.g., Claude Code triggering invoice creation), Vibium's built-in MCP server makes it the more natural choice. Its self-healing locators also reduce maintenance burden when Bonsai updates its UI.

### When to Consider the Reverse-Engineering Path

Only if performance is critical (many invoices per minute) and you are willing to accept the maintenance burden. Use mitmproxy2swagger to document endpoints, then build a thin Python client.

### Risks Common to All Approaches

- **UI/API changes.** Bonsai can change their interface at any time, breaking automation.
- **Authentication challenges.** 2FA, CAPTCHAs, or rate limiting could block automated access.
- **Terms of Service.** Automated access may violate Bonsai's ToS. Review before proceeding.
- **Session management.** Browser sessions expire; scripts need robust login handling.

## Sources & Further Reading

- [Bonsai Help Center - Integrations](https://help.hellobonsai.com/en/collections/96956-integrations)
- [Bonsai Zapier Integration](https://zapier.com/apps/bonsai/integrations)
- [Bonsai Zapier Setup Guide](https://help.hellobonsai.com/en/articles/476830-zapier)
- [Bonsai Blog: Automate with Zapier](https://www.hellobonsai.com/blog/freelancing-zapier)
- [Bonsai GitHub Organization](https://github.com/HelloBonsai)
- [Playwright GitHub](https://github.com/microsoft/playwright)
- [Playwright Python Docs](https://playwright.dev/python/)
- [Vibium GitHub](https://github.com/VibiumDev/vibium)
- [Vibium Official Site](https://vibium.com/)
- [Integuru - AI API Reverse Engineering](https://github.com/Integuru-AI/Integuru)
- [mitmproxy2swagger](https://github.com/alufers/mitmproxy2swagger)

## Open Questions

- Does Bonsai's internal API use a predictable REST pattern that could be documented? A session with browser DevTools on the invoice creation flow would reveal this.
- Does Bonsai enforce 2FA or CAPTCHA on login? This would complicate any automation approach.
- Is Bonsai planning to release a public API? Their n8n fork on GitHub and Zapier integration suggest awareness of automation demand. Reaching out to support@hellobonsai.com may yield useful information.
- Would switching to an invoicing platform with a proper API (e.g., FreshBooks, Harvest, or Wave) be more cost-effective than maintaining browser automation against Bonsai?
