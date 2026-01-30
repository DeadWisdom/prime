# Streaming Markdown Rendering in the Browser

researched: 2026-01-30
status: complete
tags: markdown, streaming, lit, web-components, chat-ui, llm, rendering

## Executive Summary

For a Lit-based chat UI receiving text chunks over WebSocket, the best option is **streaming-markdown** (`smd.js`) -- a 3kB framework-agnostic library that appends DOM nodes incrementally without re-parsing. It has the simplest API, the smallest footprint, works as a plain ES module, and is recommended by Chrome's developer documentation. For richer needs (syntax highlighting built-in, animation), **@nlux/markdown** is a strong second choice. Avoid the naive approach of concatenating chunks and re-parsing with `marked` or `markdown-it` -- it is O(n^2) and creates security risks via `innerHTML`.

## Background

When an LLM streams a response character-by-character or chunk-by-chunk, the frontend must render markdown progressively. The naive approach -- concatenate all chunks, parse the full string with a standard markdown parser, set `innerHTML` -- has two critical problems:

1. **Performance**: Every chunk triggers a full re-parse and full DOM replacement. This is O(n^2) over the life of a message. For long responses with code blocks, this becomes visibly janky.
2. **Security**: Setting `innerHTML` with user-influenced content opens XSS vectors. A malicious prompt injection could cause the model to emit raw HTML.

The solution is a **streaming markdown parser** that incrementally appends DOM nodes as chunks arrive, combined with a **DOM sanitizer** (DOMPurify or the Sanitizer API) for defense in depth.

### The Incomplete Syntax Problem

Streaming parsers must handle partial markdown gracefully. When the stream contains just `*`, it could be:
- A list item (`* item`)
- Italic opening (`*italic*`)
- Bold opening (`**bold**`)
- Part of a horizontal rule (`***`)

Good streaming parsers use "optimistic" rendering -- they make a best guess and correct if needed -- or they buffer ambiguous tokens until enough context arrives.

## Key Findings

### 1. streaming-markdown (smd.js) -- RECOMMENDED

**npm**: `streaming-markdown`
**Size**: ~3kB gzipped
**License**: MIT
**Framework**: Agnostic (vanilla JS, ES module)
**GitHub**: https://github.com/thetarnav/streaming-markdown

The standout option for our stack. Framework-agnostic, tiny, and purpose-built for this exact use case. Recommended by Google Chrome's developer documentation for rendering streamed LLM responses.

#### API

```js
import * as smd from 'streaming-markdown'

// 1. Create renderer targeting a DOM element
const element = document.getElementById('markdown-output')
const renderer = smd.default_renderer(element)
const parser = smd.parser(renderer)

// 2. Feed chunks as they arrive from WebSocket
websocket.onmessage = (event) => {
  smd.parser_write(parser, event.data)
}

// 3. Finalize when stream ends
websocket.onclose = () => {
  smd.parser_end(parser)
}
```

#### How It Works

- The parser only **appends** new DOM nodes -- it never modifies or replaces existing ones.
- Uses `appendChild()` internally for new tags and text nodes.
- Optimistic rendering: when it sees `` ` `` it immediately creates a `<code>` element and styles it. If the syntax turns out to be something else, it corrects.
- Users can select and copy text that has already streamed in (no DOM thrashing).

#### Custom Renderer Interface

For Lit integration, you can implement a custom renderer instead of using `default_renderer`:

```js
const renderer = {
  data: { /* your state */ },
  add_token(data, token_type) { /* called when a token opens */ },
  end_token(data, token_type) { /* called when a token closes */ },
  add_text(data, text)        { /* called to append text content */ },
  set_attr(data, attr, value) { /* called for attributes like href, lang */ },
}
const parser = smd.parser(renderer)
```

This is how you would integrate syntax highlighting -- capture the language attribute via `set_attr`, accumulate text in code blocks via `add_text`, and apply highlighting via highlight.js or Shiki in `end_token`.

#### Supported Markdown

Headers, bold, italic, strikethrough, inline code, fenced code blocks (with language attr), links, images, autolinks, ordered/unordered lists, task lists, blockquotes, tables, horizontal rules, LaTeX expressions, `<br>` tags.

#### Syntax Highlighting

**Not built-in.** You must implement it via the custom renderer interface. This is a trade-off for the tiny bundle size. In practice, you would:
1. Detect code block open + language via `set_attr`
2. Buffer text content via `add_text`
3. Apply highlight.js or Prism on `end_token`
4. Or apply Shiki for more accurate highlighting (but it's heavier)

#### Lit Integration Pattern

```js
import { LitElement, html } from 'lit'
import * as smd from 'streaming-markdown'

class ChatMessage extends LitElement {
  #parser = null

  firstUpdated() {
    const container = this.renderRoot.querySelector('.content')
    const renderer = smd.default_renderer(container)
    this.#parser = smd.parser(renderer)
  }

  appendChunk(text) {
    smd.parser_write(this.#parser, text)
  }

  finalize() {
    smd.parser_end(this.#parser)
    this.#parser = null
  }

  render() {
    return html`<div class="content"></div>`
  }
}
```

#### Limitations

- No built-in syntax highlighting
- Marked as "WIP" on GitHub, though it is stable enough for Chrome DevDocs to recommend
- Custom renderer API is functional but not extensively documented
- No built-in sanitization (pair with DOMPurify)


### 2. @nlux/markdown

**npm**: `@nlux/markdown`
**Framework**: Agnostic core, with React helpers
**GitHub**: https://github.com/nlkitai/nlux

A more feature-rich option from the NLUX AI UI toolkit.

#### API

```js
import { createMarkdownStreamParser } from '@nlux/markdown'

const container = document.querySelector('.markdown-container')
const parser = createMarkdownStreamParser(container, {
  syntaxHighlighter: highlighterInstance,   // from @nlux/highlighter
  showCodeBlockCopyButton: true,
  skipStreamingAnimation: false,
  streamingAnimationSpeed: 10,              // ms per character
  markdownLinkTarget: 'blank',
  onComplete: () => console.log('done'),
})

// Feed chunks
parser.next('## Hello World')
parser.next('\nMore content...')

// Finalize
parser.complete()
```

#### Strengths

- **Built-in syntax highlighting** via `@nlux/highlighter` (highlight.js based)
- **Copy button** for code blocks out of the box
- **Streaming animation** with configurable speed (typewriter effect)
- **Link target control** -- useful for chat UIs where you want links opening in new tabs
- Completion callback

#### Weaknesses

- Larger bundle than `smd.js`
- Part of the NLUX ecosystem -- may pull in more than needed
- Less transparent about how it handles incomplete syntax
- React-leaning documentation, though the core parser is framework-agnostic


### 3. Incremark (@incremark/core)

**npm**: `@incremark/core`
**Latest**: 0.3.6
**GitHub**: https://github.com/kingshuaishuai/incremark

A sophisticated incremental parser focused on performance with long documents.

#### API

```js
import { createIncremarkParser } from '@incremark/core'

const parser = createIncremarkParser({ gfm: true })

parser.append('# Hello\n')
parser.append('\nWorld')
parser.finalize()

console.log(parser.getCompletedBlocks())
console.log(parser.getAst())
```

#### How It Works

The key innovation: Incremark identifies "stable" vs "unstable" blocks. Stable blocks (completed paragraphs, closed code fences, etc.) are never re-parsed. Only the trailing unstable block is re-parsed on each new chunk. This reduces complexity from O(n^2) to O(n).

Performance claims: 2-10x faster than naive re-parsing for typical LLM output, up to 46x for 20KB+ documents.

#### Strengths

- Best theoretical performance for very long documents
- GFM support, math, mermaid, code blocks
- Framework bindings for React, Vue, Svelte, Solid
- Built-in DevTools for debugging parse state

#### Weaknesses

- **No vanilla JS renderer** -- rendering is handled by framework-specific packages (`@incremark/react`, `@incremark/vue`, etc.). The core only gives you an AST and block metadata.
- For Lit, you would need to write your own renderer consuming the AST output.
- Relatively new (0.3.x), smaller community
- Heavier conceptual overhead


### 4. Semidown

**npm**: `semidown`
**GitHub**: https://github.com/chuanqisun/semidown

A pragmatic middle ground between full re-parsing and fully incremental parsing.

#### API

```js
import { Semidown } from 'semidown'

const container = document.getElementById('output')
const parser = new Semidown(container)

// Feed character by character or chunk by chunk
parser.write('# Hello\n')
parser.write('**bold** text\n')
parser.end()
```

#### How It Works

- **Block-level incremental**: New blocks are appended without reprocessing previous blocks.
- **Inline-level re-rendering**: Within the current block, inline elements (bold, italic, links) are re-rendered as content grows. This is a pragmatic compromise -- inline re-rendering within a single paragraph is cheap.

#### Strengths

- Simple, clear API
- Sensible trade-off between complexity and performance
- Framework-agnostic, works with plain DOM

#### Weaknesses

- Less mature than other options
- No built-in syntax highlighting
- Inline re-rendering within blocks means it is not fully incremental


### 5. @lixpi/markdown-stream-parser

**npm**: `@lixpi/markdown-stream-parser`
**Latest**: 0.0.3-33

A pub/sub architecture parser that decouples parsing from rendering.

#### API

```js
import { MarkdownStreamParser } from '@lixpi/markdown-stream-parser'

const parser = MarkdownStreamParser.getInstance('session-1')

// Subscribe to parsed output
parser.subscribeToTokenParse((segment, unsubscribe) => {
  console.log(segment) // { content, type, styles, status }
  if (segment.status === 'END_STREAM') {
    unsubscribe()
    MarkdownStreamParser.removeInstance('session-1')
  }
})

// Feed chunks
parser.startParsing()
parser.parseToken('Hello **world**')
parser.stopParsing()
```

#### Strengths

- Clean separation of parsing and rendering
- Singleton pattern allows feeding from one place and consuming in another
- Works on both backend and frontend

#### Weaknesses

- Very early (0.0.3 prerelease)
- Singleton pattern may feel unusual for component-based UIs
- No rendering -- you must build your own renderer from parsed segments
- Small community


### 6. Naive Approach: marked / markdown-it with Concatenation

**Not recommended for streaming**, but documented for completeness.

```js
import { marked } from 'marked'

let accumulated = ''

websocket.onmessage = (event) => {
  accumulated += event.data
  container.innerHTML = marked.parse(accumulated)
}
```

**Why this is bad:**
- O(n^2): Every chunk re-parses everything from the start.
- `innerHTML` replaces entire DOM tree, losing scroll position, text selection, and focus.
- XSS risk without explicit sanitization.
- Code blocks with syntax highlighting are re-highlighted on every chunk.

`marked` and `markdown-it` are excellent parsers for complete documents but are not designed for streaming. There is no official streaming mode for either library.


## Practical Implications

### Recommendation for Our Stack (Lit + Bun + Browser ES Modules)

**Primary choice: `streaming-markdown` (smd.js)**

Reasons:
1. **ES module native** -- works directly with `import`, no bundler gymnastics needed.
2. **Framework-agnostic** -- no React/Vue assumptions. Works perfectly with Lit's imperative DOM access.
3. **3kB gzipped** -- negligible impact on bundle size.
4. **Append-only DOM operations** -- plays well with Lit's rendering model since it operates on a container div that Lit does not manage.
5. **Custom renderer** -- if we need to integrate syntax highlighting later, the renderer interface supports it.
6. **Chrome-endorsed** -- Google's developer docs specifically recommend it.

**For syntax highlighting**, add highlight.js or Prism separately and apply it either:
- Via a custom renderer that highlights code blocks as they complete
- Or post-stream by querying code blocks and applying highlighting after `parser_end()`

**For sanitization**, pair with DOMPurify. Since `smd.js` uses DOM APIs (not `innerHTML`), the attack surface is smaller, but defense in depth is prudent for any LLM output.

### Integration Architecture

```
WebSocket chunk
    |
    v
smd.parser_write(parser, chunk)
    |
    v
DOM nodes appended to container <div>
    |
    v
(optional) On stream end: highlight code blocks, sanitize
```

The key insight: `smd.js` operates on a raw DOM element, not Lit's template system. In Lit, you would:
1. Render a container `<div>` in your template
2. Get a reference to it via `this.renderRoot.querySelector()` or `@query` decorator
3. Pass it to `smd.default_renderer()`
4. Feed chunks imperatively -- this bypasses Lit's reactive rendering, which is exactly what you want for streaming

### Performance Considerations

| Approach | Parse Cost per Chunk | DOM Cost per Chunk | Total Complexity |
|----------|--------------------|--------------------|-----------------|
| innerHTML + marked | O(n) re-parse all | O(n) replace all | O(n^2) |
| smd.js streaming | O(1) parse new | O(1) append new | O(n) |
| Incremark | O(1) parse unstable block | O(1) update last block | O(n) |
| Semidown | O(1) block + O(k) inline | O(k) re-render block | O(n * k) |

Where n = total document length, k = current block length. For typical LLM chat messages (under 5KB), all streaming parsers perform well. The differences matter for very long outputs (10KB+).

### Handling Incomplete Markdown by Library

| Library | Strategy |
|---------|----------|
| smd.js | Optimistic: immediately renders partial syntax (e.g., open code block styled as code). Corrects if needed. |
| @nlux/markdown | Buffers with configurable wait time (`waitTimeBeforeStreamCompletion`). Animation smooths visual jank. |
| Incremark | Tracks "unstable" blocks that may change. Only re-renders those. |
| Semidown | Block-level buffering. Inline elements within current block are re-rendered. |
| @lixpi | Buffers tokens, emits parsed segments. Consumer decides rendering. |


## Sources & Further Reading

- [Chrome DevDocs: Best practices to render streamed LLM responses](https://developer.chrome.com/docs/ai/render-llm-responses) -- The authoritative guide. Read this first.
- [streaming-markdown GitHub](https://github.com/thetarnav/streaming-markdown) -- Source, API docs, live demo.
- [streaming-markdown live demo](https://thetarnav.github.io/streaming-markdown/)
- [@nlux/markdown npm](https://www.npmjs.com/package/@nlux/markdown) and [docs](https://docs.nlkit.com/nlux/reference/ui/markdown)
- [Incremark docs](https://incremark-docs.vercel.app/) and [dev.to article on O(n) parsing](https://dev.to/kingshuaishuai/eliminate-redundant-markdown-parsing-typically-2-10x-faster-ai-streaming-4k94)
- [Semidown GitHub](https://github.com/chuanqisun/semidown)
- [@lixpi/markdown-stream-parser npm](https://www.npmjs.com/package/@lixpi/markdown-stream-parser)
- [Vercel Streamdown](https://github.com/vercel/streamdown) -- React-specific, but interesting architecture reference.
- [Preventing Flash of Incomplete Markdown (HN discussion)](https://news.ycombinator.com/item?id=44182941)


## Open Questions

1. **Syntax highlighting during streaming**: No library handles this perfectly. The best approach for smd.js may be to apply highlighting on `end_token` for completed code blocks, or to use a MutationObserver to detect new code blocks and highlight them.

2. **Sanitization strategy**: Should we sanitize during streaming (via custom renderer) or after stream completion? During is safer but adds complexity. After is simpler but briefly exposes unsanitized content.

3. **smd.js maturity**: The library is marked "WIP" on GitHub. Worth auditing the source (it is small) before depending on it in production. The Chrome DevDocs endorsement is encouraging.

4. **Shadow DOM compatibility**: smd.js operates on a DOM element. Lit components use Shadow DOM by default. Need to verify that `smd.default_renderer()` works correctly inside a shadow root (it should, since it uses standard DOM APIs like `appendChild`).

5. **Memory cleanup**: When a chat message component is removed from DOM, ensure the parser is properly cleaned up (`parser_end` called) to avoid memory leaks from orphaned parser state.
