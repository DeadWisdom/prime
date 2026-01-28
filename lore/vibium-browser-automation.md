# Vibium: AI-Native Browser Automation

researched: 2026-01-28
status: complete
tags: browser-automation, ai-agents, mcp, testing, selenium, playwright, webdriver-bidi

## Executive Summary

Vibium is an AI-native browser automation tool created by Jason Huggins, the original creator of Selenium and Appium. It ships as a single ~10MB Go binary that handles browser lifecycle, WebDriver BiDi protocol, and exposes a built-in MCP server, enabling AI agents like Claude Code to drive a browser with zero configuration. It is open source (Apache-2.0), still early-stage (v0.1.x as of January 2026), and positions itself as the successor to Selenium for the AI era.

## Background

### Creator and Lineage

Jason Huggins created Selenium in 2004, co-founded Sauce Labs, and created Appium in 2012. Vibium is his next project, following the same trajectory: build foundational, open-source browser automation infrastructure for the current era. His framing is explicit: "Whatever we did with Selenium for the web, whatever we did with Appium for mobile, we are doing with AI."

### Why Vibium Exists

Existing browser automation tools (Selenium, Playwright, Puppeteer) were designed for human developers writing deterministic test scripts. AI agents have different needs:

- Clean stdio interfaces rather than complex programmatic APIs
- Zero-configuration setup (no manual browser management)
- Standards-based protocols that are not controlled by a single corporation
- Intelligent fallback when elements are not found, rather than hard failures

Vibium was purpose-built to address these gaps.

## Key Findings

### What It Is

Vibium is browser automation infrastructure, not a testing framework per se. At its core is a component called the "Clicker" -- a single Go-based binary (~10MB) with four responsibilities:

1. **Browser Management** -- Detects, downloads (if needed), and launches Chrome with BiDi protocol enabled
2. **BiDi Proxy** -- Operates as a WebSocket server (default port 9515) routing commands to the browser and events back to clients
3. **MCP Server** -- Exposes a stdio interface compatible with the Model Context Protocol for AI agent integration
4. **Auto-Wait and Screenshots** -- Built-in polling to wait for elements, plus viewport screenshot capture

### How It Works

**Installation:**
- JavaScript/Node.js: `npm install vibium`
- Python: `pip install vibium` (client still under development)
- The npm package automatically installs only the platform-specific binary needed

**AI Agent Integration (MCP):**
The primary interface for AI agents. Once registered with Claude Code or another MCP client, the agent gets access to these browser tools:
- `browser_launch` -- Start a browser session
- `browser_navigate` -- Go to a URL
- `browser_click` -- Click an element
- `browser_type` -- Type text into an element
- `browser_screenshot` -- Capture the viewport
- `browser_find` -- Locate elements on the page
- `browser_quit` -- End the session

An AI agent can be instructed in natural language (e.g., "Go to example.com and click the first link") and Vibium translates this into BiDi protocol commands.

**Programmatic API (JavaScript/TypeScript):**
For developers who prefer direct control, the JS/TS client connects to the Clicker's WebSocket interface on port 9515, bypassing the MCP layer. Both async and sync APIs are available.

**Protocol:**
Built entirely on WebDriver BiDi, a WebSocket-based standard that replaces the older HTTP-based WebDriver protocol. This provides faster communication and bidirectional event streaming. Notably, this is a W3C standard, not a proprietary protocol controlled by a single browser vendor.

### AI Integration Features

- **Built-in MCP Server** -- First-class, not bolted on. This is the primary interface for AI agents.
- **Intelligent Fallback** -- Instead of failing with "element not found," Vibium can ask an AI for help finding alternative paths to accomplish the same action.
- **Vibium Atlas** -- A visual interface that maps an application as nodes (pages) and edges (actions), similar to a navigation map. This can be used for intelligent test generation. Demonstrated at a Chicago event in September 2024.
- **Self-Healing Tests** -- AI-powered dynamic locator repair when page structures change.
- **Plain English Scripting** -- Enables writing tests in natural language, lowering the barrier for non-programmers.

### Pricing and Licensing

- **Open source** under the Apache-2.0 license
- No paid tiers have been announced
- Jason Huggins has stated there will always be an on-prem/local version of the entire stack
- The project follows the same open-source-first model as Selenium and Appium

### Maturity and Community

- **Very early stage.** The GitHub repository was published in early January 2026.
- **Version 0.1.4** on PyPI as of January 19, 2026. Placeholder-level functionality in some areas.
- **Python client is still planned**, not fully functional yet.
- The project had a Hacker News Show HN launch that generated discussion.
- Community, third-party libraries, and real-world case studies are sparse.
- Documentation exists in the GitHub repo under `docs/`, including tutorials and update logs.
- **Not production-ready** for critical workflows. Suitable for experimentation and early adoption.

## Comparison to Alternatives

### Vibium vs Playwright

| Aspect | Playwright | Vibium |
|---|---|---|
| **Primary audience** | Human developers writing tests | AI agents and humans |
| **Setup** | Requires code, config, browser install | Single binary, auto-downloads Chrome |
| **Protocol** | Chrome DevTools Protocol (CDP) | WebDriver BiDi (W3C standard) |
| **AI support** | None built-in; requires wrapper | MCP server built-in |
| **Self-healing** | No | Yes (AI-powered fallback) |
| **Maturity** | Production-ready, large ecosystem | Alpha/early-stage |
| **Languages** | JS, Python, Java, C# | JS (Python planned) |
| **Creator** | Microsoft | Jason Huggins (Selenium creator) |
| **Best for** | Deterministic E2E testing | AI-driven browser tasks |

**When to choose Playwright:** You need battle-tested, deterministic browser automation for CI/CD pipelines. You are writing traditional test suites. You need multi-browser support beyond Chrome. You need production reliability today.

**When to choose Vibium:** You are building AI agent workflows that need browser access. You want MCP integration without glue code. You are comfortable with early-stage software. You want to bet on the WebDriver BiDi standard.

### Other Alternatives in the Space

**Stagehand** (by Browserbase): AI web agent framework with three simple APIs (act, extract, observe). Rebuilt in v3 to use CDP directly, removing Playwright dependency. More mature than Vibium for AI agent use cases, with self-healing and context-aware token management. Best for developers building production AI automations.

**BrowserMCP**: An MCP server + Chrome extension that automates the user's existing browser (not new instances). Uses logged-in sessions and avoids bot detection. Best for connecting AI coding tools to your live browser for local tasks. Different philosophy -- uses your real browser fingerprint.

**Chrome DevTools MCP** (what you are currently using in this project's `.mcp.json`): The Playwright-based MCP server that connects to Chrome DevTools. More established but creates new browser instances rather than using existing ones.

## Practical Implications

### For AI Agent Development

Vibium is worth watching but not yet worth depending on. The built-in MCP server is its killer feature -- it removes the need for adapter layers between AI agents and browsers. However, the current MCP tools available (`browser_launch`, `browser_click`, etc.) are simpler than what Chrome DevTools MCP or Playwright MCP already offer.

### For Testing

If you are already using Playwright for testing, there is no reason to switch today. Vibium's testing story is still aspirational. The Atlas visualization and intelligent test generation features are promising but were last demonstrated as proof-of-concept.

### For This Project

The current `.mcp.json` configuration uses `chrome-devtools` for browser automation. Vibium could theoretically replace this, but given its maturity level, it would be premature. Worth revisiting in 6-12 months.

### Recommendation

- **Watch the repository** at github.com/VibiumDev/vibium
- **Do not adopt** for production workflows yet
- **Experiment** if you want to see how MCP-native browser automation feels compared to the adapter-based approach
- **Revisit** when v1.0 ships or when the Python client is fully functional

## Sources and Further Reading

- [Vibium GitHub Repository](https://github.com/VibiumDev/vibium)
- [Vibium Official Website](https://vibium.com/)
- [Getting Started Tutorial](https://github.com/VibiumDev/vibium/blob/main/docs/tutorials/getting-started.md)
- [MCP Integration Update (Day 10)](https://github.com/VibiumDev/vibium/blob/main/docs/updates/2025-12-20-day10-mcp.md)
- [Hacker News Discussion](https://news.ycombinator.com/item?id=46377597)
- [Architecture Explained (QAbash)](https://www.qabash.com/vibium-ai-native-browser-automation-architecture/)
- [Medium: Browser Automation for the AI Era](https://medium.com/womenintechnology/vibium-browser-automation-for-the-ai-era-whats-actually-being-built-53aa61aae948)
- [Medium: From Selenium to Vibium](https://japneetsachdeva.medium.com/from-selenium-to-vibium-browser-automation-for-the-ai-era-3945a4e0dfe9)
- [TestGuild: Vibium - The New Selenium](https://testguild.com/vibium-the-new-selenium/)
- [TestGuild Podcast with Jason Huggins](https://testguild.com/podcast/automation/a559-jason/)
- [PyPI: vibium](https://pypi.org/project/vibium/)
- [Stagehand (comparable tool)](https://www.stagehand.dev/)
- [BrowserMCP (comparable tool)](https://browsermcp.io/)

## Open Questions

- **GitHub star count and contributor numbers** -- Could not programmatically query the GitHub API during this research session. Worth checking directly.
- **Python client timeline** -- When will the Python client be fully functional? Currently described as "planned."
- **Vibium Atlas availability** -- The visual app-mapping tool was demonstrated in September 2024 but its current status and availability are unclear.
- **Performance benchmarks** -- No published benchmarks comparing Vibium's speed/reliability against Playwright or Selenium.
- **Multi-browser support** -- Currently appears Chrome-only. Plans for Firefox or other browsers via BiDi are unknown.
- **Commercial model** -- Huggins has committed to open source but has not announced if there will be a commercial offering (hosted service, enterprise support, etc.) similar to the Selenium/Sauce Labs pattern.
- **How Stagehand v3 compares in practice** -- Stagehand dropped its Playwright dependency and now speaks CDP directly, making it a more direct competitor to Vibium than it was previously. A head-to-head comparison would be valuable.
