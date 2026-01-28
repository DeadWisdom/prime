# Web Awesome Component Library

researched: 2025-01-26
status: complete
tags: web-components, ui-library, css, design-tokens, frontend

## Executive Summary

Web Awesome is a modern web component library providing 50+ customizable components built on web standards. It works with any framework or vanilla JavaScript, offers a comprehensive design token system, and includes layout utilities for responsive design.

## Background

Web Awesome provides pre-built, accessible UI components as web components. Components are customizable via CSS custom properties (design tokens) and work without framework dependencies. The library emphasizes consistency through design tokens and provides both CDN and npm installation options.

## Key Findings

### Installation

**CDN (Recommended):**
```html
<script src="https://kit.webawesome.com/YOUR_PROJECT_ID.js"></script>
```

**npm:**
```bash
npm install @awesome.me/webawesome
```

```javascript
import '@awesome.me/webawesome/dist/styles/themes/default.css';
import '@awesome.me/webawesome/dist/components/button/button.js';
```

### Quick Start

```html
<wa-button variant="brand">Click Me</wa-button>

<wa-input label="Name" placeholder="Enter your name"></wa-input>

<wa-card>
  <h3 slot="header">Card Title</h3>
  Content goes here
  <wa-button slot="footer">Action</wa-button>
</wa-card>
```

### Design Tokens

**Space tokens** (scaled by `--wa-space-scale`):

| Token | Default | ~Pixels |
|-------|---------|---------|
| `--wa-space-3xs` | 0.125rem | 2px |
| `--wa-space-2xs` | 0.25rem | 4px |
| `--wa-space-xs` | 0.5rem | 8px |
| `--wa-space-s` | 0.75rem | 12px |
| `--wa-space-m` | 1rem | 16px |
| `--wa-space-l` | 1.5rem | 24px |
| `--wa-space-xl` | 2rem | 32px |
| `--wa-space-2xl` | 2.5rem | 40px |
| `--wa-space-3xl` | 3rem | 48px |

**Color scales** (10 hues x 11 tints):
```css
--wa-color-{hue}-{tint}
/* hues: red, orange, yellow, green, cyan, blue, indigo, purple, pink, gray */
/* tints: 0 (black) to 100 (white) */
```

**Semantic colors:**
```css
--wa-color-{group}-{role}-{attention}
/* groups: brand, neutral, success, warning, danger */
/* roles: fill, border, on */
/* attention: quiet, normal, loud */
```

**Foundational colors:**
- `--wa-color-surface-raised` / `default` / `lowered` - Background layers
- `--wa-color-text-normal` / `quiet` / `link` - Text colors
- `--wa-color-shadow`, `--wa-color-focus` - Effects

**Form control tokens:**
```css
--wa-form-control-background-color
--wa-form-control-border-color
--wa-form-control-border-radius
--wa-form-control-height
--wa-form-control-padding-inline
```

### Layout Utilities

**Stack** - Vertical flow:
```html
<div class="wa-stack">
  <div>Item 1</div>
  <div>Item 2</div>
</div>
```

**Grid** - Auto-wrapping columns:
```html
<div class="wa-grid" style="--min-column-size: 200px;">
  <wa-card>...</wa-card>
  <wa-card>...</wa-card>
</div>
```

**Cluster** - Inline with wrapping:
```html
<div class="wa-cluster wa-gap-xs">
  <wa-tag>Tag 1</wa-tag>
  <wa-tag>Tag 2</wa-tag>
</div>
```

**Split** - Distribute items:
```html
<div class="wa-split">
  <div>Left</div>
  <div>Right</div>
</div>
```

**Flank** - Item beside content:
```html
<div class="wa-flank">
  <wa-avatar></wa-avatar>
  <div>Content</div>
</div>
```

**Frame** - Aspect ratios:
```html
<div class="wa-frame:landscape">
  <img src="image.jpg" alt="" />
</div>
```

**Gap classes:**
`wa-gap-0`, `wa-gap-3xs`, `wa-gap-xs`, `wa-gap-s`, `wa-gap-m`, `wa-gap-l`, `wa-gap-xl`

### Components Index

**Form Controls:**
- `<wa-input>` - Text input with label, hint, clear, password toggle
- `<wa-textarea>` - Multi-line with auto-resize
- `<wa-select>` - Dropdown, single or multiple
- `<wa-checkbox>` - With indeterminate state
- `<wa-radio-group>` - Radio buttons
- `<wa-switch>` - Toggle switch
- `<wa-slider>` - Range slider
- `<wa-color-picker>` - Color selection
- `<wa-rating>` - Star rating

**Actions:**
- `<wa-button>` - Variants, sizes, loading state
- `<wa-button-group>` - Group related buttons
- `<wa-dropdown>` - Menu with items and submenus
- `<wa-copy-button>` - Copy to clipboard

**Feedback:**
- `<wa-callout>` - Inline message with variants
- `<wa-badge>` - Status indicator
- `<wa-tag>` - Label/category
- `<wa-spinner>` - Loading indicator
- `<wa-progress-bar>` / `<wa-progress-ring>` - Progress
- `<wa-skeleton>` - Loading placeholder
- `<wa-tooltip>` - Hover information

**Organization:**
- `<wa-card>` - Container with header, body, footer
- `<wa-dialog>` - Modal
- `<wa-drawer>` - Slide-in panel
- `<wa-details>` - Expandable disclosure
- `<wa-divider>` - Visual separator
- `<wa-tab-group>` - Tabbed interface

**Imagery:**
- `<wa-icon>` - 2000+ Font Awesome icons
- `<wa-avatar>` - User avatar with fallback
- `<wa-carousel>` - Image carousel
- `<wa-qr-code>` - Generate QR codes

**Formatters:**
- `<wa-format-bytes>` - KB, MB, etc.
- `<wa-format-date>` - Localized dates
- `<wa-format-number>` - Localized numbers
- `<wa-relative-time>` - "2 hours ago"

### Common Patterns

**Form with validation:**
```html
<form class="wa-stack">
  <wa-input label="Email" type="email" required></wa-input>
  <wa-textarea label="Message" required></wa-textarea>
  <wa-checkbox required>I agree to terms</wa-checkbox>
  <wa-button type="submit" variant="brand">Submit</wa-button>
</form>
```

**Card grid:**
```html
<div class="wa-grid" style="--min-column-size: 280px;">
  <wa-card>
    <img slot="media" src="image.jpg" alt="" />
    <h3 slot="header">Title</h3>
    <p>Description</p>
    <wa-button slot="footer" variant="brand">Action</wa-button>
  </wa-card>
</div>
```

**Dialog:**
```html
<wa-dialog label="Confirm" id="confirm-dialog">
  Are you sure?
  <div slot="footer" class="wa-cluster">
    <wa-button data-dialog="close">Cancel</wa-button>
    <wa-button variant="danger" data-dialog="close">Delete</wa-button>
  </div>
</wa-dialog>

<wa-button data-dialog="open confirm-dialog">Open</wa-button>
```

**Tabs:**
```html
<wa-tab-group>
  <wa-tab panel="overview">Overview</wa-tab>
  <wa-tab panel="settings">Settings</wa-tab>

  <wa-tab-panel name="overview">Overview content</wa-tab-panel>
  <wa-tab-panel name="settings">Settings content</wa-tab-panel>
</wa-tab-group>
```

## Practical Implications

- Use design tokens for consistent theming across components
- Layout utilities handle common patterns without custom CSS
- Slots provide composition flexibility in cards and dialogs
- `data-dialog` attributes simplify dialog open/close
- Semantic colors (`brand`, `danger`, `success`) ensure consistent intent
- Form controls share tokens for uniform appearance

## Sources & Further Reading

- Documentation: https://webawesome.com/docs
- Components: https://webawesome.com/docs/components
- Design Tokens: https://webawesome.com/docs/tokens/
- Layout Utilities: https://webawesome.com/docs/layout/

## Open Questions

- Custom theming beyond token overrides
- Server-side rendering compatibility
- Accessibility audit results and WCAG compliance level
