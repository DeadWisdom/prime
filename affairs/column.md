# Column

status: active
priority: critical
domain: work

## Brief

Column is a social media platform — an application-only membership club for "the most interesting, intelligent, and informationally-valuable people in the world." The monarchy has been contracted to produce a sign-up website for their users (joincolumn.com).

This is also a trial project; if successful, leads to a full-time CTO role.

Project location: `../column/signup`

**Client:** Sarah Cone <sarah@joincolumn.com> (CEO, Social Impact Capital)
**Tech contact:** Szabolcs Pasztor <szabolcs0x@gmail.com>
**Designer:** Josif Perovic <josif.perovic@gmail.com>
**Payments:** Vitalia Fedossova <vitalia@impactcap.com> (pays Wednesdays)

**Contract:** $18k fixed for functionality at discretion. 50% deposit paid Jan 14. Final payment requires W9 completion.

**Tech stack:**
- Eleventy (11ty) for static site generation
- Plain HTML + CSS
- TypeScript + Lit for interactive components
- Bun for package management and JS bundling

**Quality standard (per Sarah):**
- All user interactions must acknowledge within 100ms and resolve within 200ms
- "Luxury software" — should feel like something Hermès might have crafted
- Decision: use system fonts over brand fonts to preserve load speed

**Figma:** https://www.figma.com/design/LiFIVVcX2OFWsXpCewfQDi/New-Column?node-id=4359-2

## Functionality

The site is a "front door" for joincolumn.com:
1. User enters phone number
2. If member → redirect to app
3. If not member → application flow: ask questions, collect 3 sample posts, payment info
4. Add to waitlist table

Original spec was SMS chatbot; pivoted to web forms (cheaper, simpler).

## Matters Pending

- [ ] Package project and send to Szabolcs
- [ ] Send handoff email to Sarah — frame as "ball is in your court"
- ~~Obtain database access from Szabolcs~~ (moot — handoff)
- ~~Write serverless functions~~ (moot — handoff)
- ~~Deploy site to joincolumn.com~~ (moot — handoff)
- ~~Complete W9 for Mercury Bank~~ (intentionally not pursuing remaining payment)

## Ledger

**2026-01-29** — Sarah responded asking to package everything up for Szabolcs to implement. Decision: disengage. Too many red flags — week-long block on database access, redirection of work to their CTO, CTO trial opportunity clearly not materializing. Plan: send packaged project with handoff note framing next steps as waiting on them, then let the thread die. $8k received for substantial frontend work delivered; not pursuing the remaining $9-10k. Do not submit W9.

**2026-01-27** — Sarah asked for time accounting. Replied: roughly 30-35 hours so far. Early time on design-to-code and responsive work (where AI is weakest); architecture and deployment came together quickly. Remaining backend work expected to be fast once access is sorted.

**2026-01-26** — Sarah asking if we have everything needed to launch. Szabolcs offered to help but noted he's tight on time and suggested a temporary database. Responded with full requirements explanation. Informed Sarah live launch not realistic; committed to demo by end of day. Sarah replied: "At the very least I'll know you could have gone live if the transition issues had been worked out." Demo deployed late evening at https://column-signup.netlify.app/. Known issues: serverless functions not saving submissions, admin not available, "Prompt me" button nonfunctional, some oversized mobile images. Responsiveness and accessibility work solid.

**2026-01-23** — Domain access granted by Sarah. Weather delay (-8°F, school cancelled).

**2026-01-22** — Sarah wants to launch Monday (Jan 26). Styling work complete. Still need: database connection info, hosting/DNS access, GitHub access. Szabolcs looped in for technical handoff.

**2026-01-15** — Contract discussion: Sarah prefers fixed $18k to see how much functionality can be delivered. Established "luxury software" performance standards (100ms ack, 200ms resolve). Agreed to use system fonts for speed. Josif Perovic provided design fonts.

**2026-01-14** — Figma shared. Technical interview with Szabolcs: 60min design problem + 30min product presentation. Deposit payment sent by Vitalia.

**2026-01-13** — Sarah requested references. Szabolcs to conduct one more technical interview before full onboarding.

**2026-01-11** — Pivoted from SMS chatbot to web forms. Sarah wanted cheapest option to validate "application-only" concept. Emphasis on analytics to identify friction points.

**2026-01-09** — Contract finalized via Bonsai. Introduced to Vitalia for payments. Expense clause amended (preapproval required).

**2026-01-07** — Contract sent. Legal entity: Column, Inc. Started working.

**2026-01-06** — Sarah decided to proceed with project despite price difference ("testing the long term working relationship"). Will use own Twilio/hosting until Szabolcs vets.

**2026-01-04** — Proposed $16k for full SMS flow (~80 hours). Sarah expected ~$5k. Put on hold.

**2026-01-02** — Original spec received: beautiful landing page + SMS application flow + Stripe payment capture + admin database.

**2026-01-01** — Sarah proposed small project as trial while Szabolcs completes technical assessment. Potential full-time CTO role pending.

**2025-12-10** — Initial call with Szabolcs.

**2025-12-02** — Reintroduction call with Sarah. Column's previous product team collapsed.

**2025-11-25** — Sarah reached out again after 8 months.

**2025-03-14** — First contact. CTO role discussed but couldn't do 3-month trial period.
