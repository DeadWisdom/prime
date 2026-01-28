# Cost Plus Drugs: Programmatic Interface & Automation Research

researched: 2026-01-28
status: complete
tags: pharmacy, automation, costplusdrugs, capecitabine, healthcare, prescription

## Executive Summary

Mark Cuban Cost Plus Drugs (MCCPDC) has **no public API** for consumer ordering. The platform is a standard web application built on Saleor (open-source eCommerce) with a custom backend. However, it offers a built-in **auto-refill feature** that may eliminate the need for custom automation entirely. Browser automation remains a viable fallback. Capecitabine (generic Xeloda) is listed on the platform in both 150mg and 500mg tablet forms at roughly $0.39/pill.

## Background

Cost Plus Drugs is a public benefit corporation founded in 2022 by Mark Cuban. It sells medications at acquisition cost + 15% markup + $5 pharmacist fee + $5.25 shipping. It does not accept insurance. The platform operates as a mail-order pharmacy shipping to all 50 US states. Their technology partner Codal rebuilt the backend on Saleor (open-source eCommerce platform) with custom authentication, auto-refill, and order processing systems.

## Key Findings

### 1. No Public API

There is no documented public REST API, GraphQL endpoint, or developer-facing programmatic ordering interface for consumers. The platform is a web application only. However, there are notable technical details:

- **Backend**: Built on **Saleor** (Python/Django-based open-source eCommerce), which natively supports GraphQL APIs. This means the frontend almost certainly communicates with a GraphQL backend, which could theoretically be reverse-engineered from browser network traffic.
- **Technology partner**: Codal performed a major backend revamp, replacing third-party dependencies and building custom auth, auto-refill, and order management systems.
- **AI integration**: Medchat.ai partnership (announced October 2025) provides AI customer care agents for pricing, order status, and delivery tracking -- suggesting some internal APIs exist for these functions.

### 2. Ordering Flow (Manual Process)

The manual ordering process is straightforward:

1. **Check availability**: Search costplusdrugs.com/medications for your drug
2. **Create account**: Register at costplusdrugs.com/create-account with email, then complete a health profile (allergies, conditions, current medications)
3. **Prescription transfer**: Give your doctor the Cost Plus Drugs pharmacy NCPDP ID: **#5755167** and the email you registered with. The doctor sends the prescription electronically via standard e-prescribing (no upload mechanism -- it must come from a provider)
4. **Confirmation email**: You receive an email (reportedly within ~20 minutes) confirming the prescription was received
5. **Place order**: Log in, pay for the medication, schedule a shipping date
6. **Shipping**: Order ships with tracking (carriers include USPS, UPS, FedEx, DHL). Typical delivery within one week
7. **Refill**: Can reorder after using ~50% of supply

**Payment**: Credit/debit card on file. No insurance accepted.

### 3. Auto-Refill Feature (Best Option for Recurring Orders)

This is likely the most important finding. Cost Plus Drugs launched an **auto-refill feature** (announced publicly mid-2025) that may solve the automation need without any custom code:

- Patients can **toggle automatic refills per eligible prescription** from their account
- The pharmacy **sends refills automatically once supply is at approximately 50%**
- Simple to enroll, easy to manage, always in the patient's control
- Announced via their official X/Twitter account: "Never miss a refill again!"
- Accessible via the **Prescription Manager** at costplusdrugs.com/prescription-manager/

**Critical question for Capecitabine**: Whether a chemotherapy drug qualifies for auto-refill is not confirmed. Specialty/chemo drugs may have different handling requirements. This should be verified directly with Cost Plus Drugs.

### 4. Browser Automation Feasibility

If auto-refill does not work for Capecitabine, browser automation is the fallback approach.

**Recommended tool**: Playwright (Python) over Selenium.
- Built-in auto-waiting eliminates race conditions
- Supports persistent browser contexts (stays logged in)
- Better anti-detection capabilities than Selenium
- Single API across Chromium, Firefox, WebKit

**Projected automation flow**:

```
1. Launch browser with persistent context (retains login cookies)
2. Navigate to costplusdrugs.com/prescription-manager/
3. If not logged in: authenticate with stored credentials
4. Locate the Capecitabine prescription
5. Click "Refill" or "Order" button
6. Confirm payment method (card on file)
7. Select shipping date
8. Confirm order
9. Capture order confirmation / tracking number
10. Send notification (email, SMS, Slack, etc.)
```

**Anti-bot considerations**:
- The site likely uses standard bot detection (Cloudflare, reCAPTCHA, etc.)
- Playwright with `playwright-stealth` plugin can bypass `navigator.webdriver` detection
- Use realistic timing, mouse movements, and avoid headless mode if detection is aggressive
- Rate limiting is unlikely to be an issue for a single order every 3 weeks

**Legal considerations**:
- The specific Terms of Service for costplusdrugs.com regarding automated access were not found in this research
- Standard pharmacy ToS typically prohibit automated access
- For personal use (not scraping/reselling), enforcement risk is minimal
- The robots.txt file should be checked before proceeding

**Scheduling**: A cron job or scheduled task running every 3 weeks could trigger the Playwright script. Alternatively, a simpler approach: monitor refill-reminder emails and trigger the script in response.

### 5. Notifications & Monitoring

Cost Plus Drugs sends **email notifications** for:
- Prescription received confirmation
- Order ready to be placed
- Order shipped (with tracking number)
- Refill reminders (when supply is running low)

**No SMS notifications** have been documented for individual consumers. Communication is primarily email-based.

**For automation monitoring**, you could:
- Set up Gmail filters + Google Apps Script to parse Cost Plus emails
- Use IMAP to programmatically monitor the inbox for shipping/tracking updates
- Forward notifications to a webhook for further processing

### 6. Existing Integrations & Partnerships

Cost Plus Drugs has no direct integrations with consumer health platforms (Apple Health, Epic MyChart, etc.), but has several relevant partnerships:

| Partner | Integration Type | Details |
|---------|-----------------|---------|
| **Alto Pharmacy** | Delivery/pickup | Team Cuban Card users can order via Alto's app with courier delivery in 12+ metro areas |
| **eNavvi** | E-prescribing | Digital prescription pad allowing doctors to prescribe directly to Cost Plus |
| **Medchat.ai** | AI customer support | AI agents for pricing, order status, delivery tracking |
| **Codal** | Technology | Backend platform, auto-refill, order management |
| **GraphiteRx** | B2B marketplace | E-commerce and procurement for healthcare providers |
| **Penn Medicine** | Health system | Direct supply of 100 common generics |
| **Humana/CenterWell** | Insurance/employer | Exploring employer drug cost reduction |
| **Wheel / Talkspace / Health Gorilla** | Virtual care | Joint partnership for telehealth prescribing |

### 7. Capecitabine Availability & Pricing

Capecitabine is listed on Cost Plus Drugs:
- **150mg tablets**: costplusdrugs.com/medications/capecitabine-150mg-tablet/
- **500mg tablets**: costplusdrugs.com/medications/capecitabine-500mg-tablet/
- **Price**: ~$23.40 for 60x 500mg tablets ($0.39/pill) -- likely the lowest US retail price
- **Comparison**: Brand Xeloda 150mg starts at ~$802.49 for 60 tablets at other pharmacies

**Supply risk**: Capecitabine has appeared on ASHP's drug shortage list. Cost Plus Drugs has previously posted advisories about stock issues. For a critical chemotherapy drug, this is a real concern and a reason to maintain a backup pharmacy relationship.

## Practical Implications

### Recommended Approach (Ordered by Preference)

1. **Try auto-refill first**: Log into Cost Plus Drugs, navigate to the Prescription Manager, and attempt to enable auto-refill for Capecitabine. If it works, this is zero-maintenance and officially supported.

2. **Email-triggered semi-automation**: If auto-refill is not available for Capecitabine, monitor refill-reminder emails. When one arrives, a Playwright script can log in and complete the order with one click/command.

3. **Scheduled full automation**: If neither of the above works, a Playwright script on a 3-week cron schedule can handle the entire flow. This is the most brittle option (site changes will break it) but is technically feasible.

4. **Alto Pharmacy app** (if in a supported metro): Alto offers automated refills and courier delivery through the Team Cuban Card partnership. Their app may provide a smoother experience for recurring orders.

### Implementation Sketch (Playwright, if needed)

```python
# capecitabine_refill.py -- conceptual outline
from playwright.async_api import async_playwright
import asyncio

async def refill_capecitabine():
    async with async_playwright() as p:
        # Use persistent context to retain login session
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./costplus-session",
            headless=False,  # Use headed mode to avoid detection
        )
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto("https://www.costplusdrugs.com/prescription-manager/")

        # Check if login is needed
        if "login" in page.url or await page.query_selector("[data-testid='login-form']"):
            await page.fill("input[name='email']", "YOUR_EMAIL")
            await page.fill("input[name='password']", "YOUR_PASSWORD")
            await page.click("button[type='submit']")
            await page.wait_for_navigation()

        # Find and click refill for Capecitabine
        # (selectors would need to be determined from actual page inspection)
        refill_button = await page.query_selector("text=Capecitabine >> .. >> button:has-text('Refill')")
        if refill_button:
            await refill_button.click()
            # Confirm order, payment, shipping...
            # Capture confirmation number
            pass

        await context.close()

asyncio.run(refill_capecitabine())
```

**Note**: Actual selectors and flow would need to be determined by inspecting the live site. The above is a structural template only.

## Sources & Further Reading

- [Cost Plus Drugs Homepage](https://www.costplusdrugs.com/)
- [Cost Plus Drugs FAQ](https://www.costplusdrugs.com/faq/)
- [Capecitabine 500mg on Cost Plus Drugs](https://www.costplusdrugs.com/medications/capecitabine-500mg-tablet/)
- [Capecitabine 150mg on Cost Plus Drugs](https://www.costplusdrugs.com/medications/capecitabine-150mg-tablet/)
- [Codal Case Study: Cost Plus Drugs Backend Revamp](https://codal.com/our-work/costplusdrugs)
- [Auto-Refill Announcement (X/Twitter)](https://x.com/costplusdrugs/status/1925282379381534774)
- [Prescription Manager](https://www.costplusdrugs.com/prescription-manager/)
- [Alto Pharmacy Partnership](https://www.alto.com/press-releases/team-cuban-card-business-wire)
- [eNavvi Partnership (MobiHealthNews)](https://www.mobihealthnews.com/news/enavvi-mark-cuban-cost-plus-drug-company-partner-empower-physicians)
- [Medchat.ai Partnership](https://www.prnewswire.com/news-releases/mark-cuban-cost-plus-drugs-and-medchatai-deploy-ai-to-scale-affordable-medication-access-302596860.html)
- [Penn Medicine Partnership](https://www.thedp.com/article/2025/01/penn-medicine-partners-mark-cuban-prescription-drug-efficiency)
- [Contact Your Doctor page](https://www.costplusdrugs.com/contact-your-doctor/)
- [Cost Plus Drugs Wikipedia](https://en.wikipedia.org/wiki/Cost_Plus_Drugs)

## Open Questions

1. **Does Capecitabine qualify for auto-refill?** Chemotherapy drugs may be excluded. Must verify with Cost Plus Drugs directly.
2. **What does the site's robots.txt and Terms of Service say about automation?** Could not access these during research.
3. **What does the GraphQL API surface look like?** The Saleor backend almost certainly exposes a GraphQL endpoint. Inspecting browser network traffic would reveal the schema and could enable cleaner programmatic ordering than browser automation.
4. **Supply chain reliability**: How often has Capecitabine been out of stock on the platform? Is there a waitlist or notification when stock returns?
5. **Prescription renewal cadence**: Oncologists typically write prescriptions for a set number of refills. How does Cost Plus Drugs handle prescription expiry, and do they prompt the patient to request a new prescription from their doctor?
6. **Alto Pharmacy availability**: If the patient is in a supported metro area, does Alto's app provide better automation/notification features for Team Cuban Card orders?
