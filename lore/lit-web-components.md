# Lit Web Components Library

researched: 2025-01-26
status: complete
tags: web-components, javascript, typescript, frontend, lit

## Executive Summary

Lit is a lightweight library for building fast, reactive web components with minimal boilerplate. It uses tagged template literals for declarative rendering and provides reactive properties, lifecycle hooks, and a controller pattern for reusable logic.

## Background

Lit builds on web standards (Custom Elements, Shadow DOM) to provide a simple programming model for web components. Components work with any framework or vanilla JavaScript. The library is small (~5KB minified) and focuses on developer experience with TypeScript decorators and efficient DOM updates.

## Key Findings

### Installation

```bash
bun add lit
```

### Basic Component

```typescript
import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('the-greeting')
export class TheGreeting extends LitElement {
  static styles = css`
    :host {
      display: block;
      padding: 16px;
    }
    .name {
      color: blue;
    }
  `;

  @property() name = 'World';

  render() {
    return html`<p>Hello, <span class="name">${this.name}</span>!</p>`;
  }
}
```

Usage:
```html
<the-greeting name="Alice"></the-greeting>
```

### Properties and Attributes

**@property decorator** - Reactive properties trigger re-renders:

```typescript
@property() name: string = '';           // String, syncs to attribute
@property({ type: Number }) count = 0;   // Number, converts from attribute
@property({ type: Boolean }) active = false;
@property({ type: Array }) items: string[] = [];
@property({ type: Object }) config = {};

// Options
@property({ attribute: 'full-name' }) fullName = '';  // Custom attribute name
@property({ attribute: false }) data = {};  // No attribute, JS-only
@property({ reflect: true }) status = '';   // Reflect to attribute
```

**@state decorator** - Internal reactive state (no attribute):

```typescript
import { state } from 'lit/decorators.js';

@state() private _loading = false;
@state() private _error: Error | null = null;
```

### Templates

**Expression types:**
```typescript
render() {
  return html`
    <!-- Text content -->
    <p>${this.message}</p>

    <!-- Attribute binding -->
    <input type="text" value=${this.value}>

    <!-- Boolean attribute (present/absent) -->
    <button ?disabled=${this.isDisabled}>Submit</button>

    <!-- Property binding (for non-string values) -->
    <the-component .items=${this.itemArray}></the-component>

    <!-- Event listener -->
    <button @click=${this._handleClick}>Click</button>
  `;
}
```

**Conditionals:**
```typescript
render() {
  return html`
    ${this.loading
      ? html`<wa-spinner></wa-spinner>`
      : html`<div>${this.content}</div>`
    }
  `;
}
```

**Lists:**
```typescript
render() {
  return html`
    <ul>
      ${this.items.map(item => html`<li>${item.name}</li>`)}
    </ul>
  `;
}
```

Use `repeat()` for efficient keyed updates:
```typescript
import { repeat } from 'lit/directives/repeat.js';

${repeat(this.items, item => item.id, item => html`<li>${item.name}</li>`)}
```

**Slots:**
```typescript
render() {
  return html`
    <div class="card">
      <header><slot name="header">Default Header</slot></header>
      <main><slot></slot></main>
      <footer><slot name="footer"></slot></footer>
    </div>
  `;
}
```

### Styling

```typescript
static styles = css`
  :host {
    display: block;
    --the-color: blue;
  }

  :host([hidden]) { display: none; }
  :host(:hover) { background: #f0f0f0; }

  /* Style slotted content */
  ::slotted(p) { margin: 0; }
`;
```

**Multiple stylesheets:**
```typescript
static styles = [baseStyles, css`/* Component-specific */`];
```

**Dynamic classes and styles:**
```typescript
import { classMap } from 'lit/directives/class-map.js';
import { styleMap } from 'lit/directives/style-map.js';

const classes = { active: this.active, disabled: this.disabled };
const styles = { color: this.color, '--size': `${this.size}px` };

html`<div class=${classMap(classes)} style=${styleMap(styles)}>...</div>`
```

### Lifecycle

```typescript
export class TheComponent extends LitElement {
  connectedCallback() {
    super.connectedCallback();
    // Setup: add listeners, start timers
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    // Cleanup: remove listeners, clear timers
  }

  willUpdate(changedProperties: PropertyValues) {
    // Before render, compute derived state
  }

  updated(changedProperties: PropertyValues) {
    // After render completes
  }

  firstUpdated() {
    // One-time DOM setup after first render
  }
}
```

### Events

**Dispatching:**
```typescript
this.dispatchEvent(new CustomEvent('the-event', {
  detail: { value: this.value },
  bubbles: true,
  composed: true,  // Cross shadow DOM boundary
}));
```

**Listening:**
```typescript
html`<button @click=${this._onClick}>Click</button>`
```

### DOM Access

**Query decorators:**
```typescript
import { query, queryAll } from 'lit/decorators.js';

@query('#input') private _input!: HTMLInputElement;
@queryAll('.item') private _items!: NodeListOf<HTMLElement>;
```

**Ref directive:**
```typescript
import { ref, createRef, Ref } from 'lit/directives/ref.js';

private _inputRef: Ref<HTMLInputElement> = createRef();

render() {
  return html`<input ${ref(this._inputRef)}>`;
}
```

### Task Controller (Async Data)

```typescript
import { Task } from '@lit/task';

export class UserProfile extends LitElement {
  @property() userId!: string;

  private _userTask = new Task(this, {
    args: () => [this.userId],
    task: async ([userId]) => {
      const response = await fetch(`/api/users/${userId}`);
      if (!response.ok) throw new Error('Failed to load');
      return response.json();
    },
  });

  render() {
    return this._userTask.render({
      pending: () => html`<wa-spinner></wa-spinner>`,
      complete: (user) => html`<p>${user.name}</p>`,
      error: (e) => html`<wa-callout variant="danger">${e.message}</wa-callout>`,
    });
  }
}
```

### Controllers (Reusable Logic)

```typescript
import { ReactiveController, ReactiveControllerHost } from 'lit';

export class ClockController implements ReactiveController {
  host: ReactiveControllerHost;
  value = new Date();
  private _timer?: number;

  constructor(host: ReactiveControllerHost) {
    this.host = host;
    host.addController(this);
  }

  hostConnected() {
    this._timer = window.setInterval(() => {
      this.value = new Date();
      this.host.requestUpdate();
    }, 1000);
  }

  hostDisconnected() {
    clearInterval(this._timer);
  }
}
```

### Common Directives

```typescript
import { ifDefined } from 'lit/directives/if-defined.js';
import { guard } from 'lit/directives/guard.js';
import { cache } from 'lit/directives/cache.js';
import { until } from 'lit/directives/until.js';
import { live } from 'lit/directives/live.js';
import { unsafeHTML } from 'lit/directives/unsafe-html.js';
```

### TypeScript Configuration

```json
{
  "compilerOptions": {
    "experimentalDecorators": true,
    "useDefineForClassFields": false
  }
}
```

## Practical Implications

- Use `@property()` for external API, `@state()` for internal state
- Always call `super.connectedCallback()` and `super.disconnectedCallback()`
- Use `composed: true` on events that need to escape shadow DOM
- Prefer `repeat()` over `map()` for lists with keys
- Task controller simplifies async data fetching patterns
- Controllers enable sharing logic between components without inheritance

## Sources & Further Reading

- Documentation: https://lit.dev/docs/
- Playground: https://lit.dev/playground/
- Tutorial: https://lit.dev/tutorials/intro-to-lit/
- API Reference: https://lit.dev/docs/api/

## Open Questions

- Server-side rendering strategies with Lit SSR
- Best practices for testing Lit components
- Integration patterns with state management libraries
