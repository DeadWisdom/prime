# Glass

status: active
priority: critical
domain: work

## Brief

Glass Imaging is a computational photography company (founded by the engineers behind iPhone Portrait Mode) specializing in AI image correction that recovers real detail from RAW sensor data without generative hallucination. B2B licensing to device manufacturers.

**Glass Studio** is a web application that allows the Glass team to run their AI image correction models directly in the browser.

Project location: `../glass/cloud-inference` (Glass Studio web app), `../glass/prism` (image processing backend)

**Tech stack:**
- FastAPI backend
- Lit + WebAwesome frontend
- Google Cloud Run for hosting
- Inferencing on RunPod with MLFlow (managed by Glass team)
- Prism: separate service for image conversion/processing (DNG → webp thumbnails, etc.)

## Situation

The app is large and complex. A previous contractor (hired off Fiverr) made a mess of things. Sole developer managing the entire application. Update needed urgently today.

## Matters Pending

- [x] Fix comparison view: pan/zoom not syncing between the two images
- [x] Fix comparison view: stale comparison image persists when navigating to a new image
- [ ] Deploy update before meeting (**meeting rescheduled to Jan 29**)
- [ ] Address SendGrid implementation review issues (14 items, 3 critical — see `.iterations/004-email-signup-sendgrid.md`)
- [x] Send invoice via Bonsai today (overdue, money needed immediately)

## Supporting Documents

- Iteration plans: `../glass/cloud-inference/.iterations/`

## Ledger

**2026-01-27** — Affair opened. Invoice sent via Bonsai. Deployed with several fixes, client satisfied for now. Significant work remains — need to tick off more todos and deploy again tomorrow.

**2026-01-28** — Comparison view sync issues resolved (pan/zoom sync and stale image). SendGrid email signup feature implemented (models, services, endpoints, templates, frontend components) with code review completed — 14 issues identified, 3 critical. Meeting rescheduled to Jan 29; deploy needed before then.
