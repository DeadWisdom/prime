# Bun Bundler

researched: 2026-01-29
status: complete
tags: bun, bundler, javascript, typescript, build-tools, frontend

## Executive Summary

Bun includes a fast native bundler for JavaScript, TypeScript, JSX, and CSS, accessible via `bun build` CLI or the `Bun.build()` JavaScript API. It supports HTML entrypoints with zero-config static site building, code splitting, tree shaking, minification, a universal plugin system, and watch mode. It is significantly faster than esbuild on benchmarks (bundling 10 copies of three.js) and handles TypeScript/JSX natively without separate tooling.

## Background

Bun's bundler is written in native code (Zig) and leverages multi-threading. It is designed as an integrated part of the Bun runtime rather than a standalone tool. The bundler is not a replacement for `tsc` -- it strips types but does not perform type checking or emit declaration files.

Key reasons to bundle: reducing HTTP requests, code transforms (TS/JSX to JS), framework features (plugins, code splitting), and full-stack application builds.

---

## Basic Usage

### CLI

```bash
# Single entrypoint
bun build ./index.tsx --outdir ./out

# Multiple entrypoints
bun build ./entry-a.ts ./entry-b.ts --outdir ./out

# Write to a single file
bun build ./index.tsx --outfile ./out/bundle.js

# Production build with minification
bun build ./index.tsx --outdir ./out --minify

# Shorthand: --production sets NODE_ENV and enables minification
bun build ./index.tsx --outdir ./out --production
```

### JavaScript API

```ts
const result = await Bun.build({
  entrypoints: ["./index.tsx"],
  outdir: "./out",
});

// result: { success: boolean, outputs: BuildArtifact[], logs: BuildMessage[] }

for (const output of result.outputs) {
  console.log(output.path);     // absolute path on disk
  console.log(output.kind);     // "entry-point" | "chunk" | "asset" | "sourcemap"
  await output.text();          // read as string
  new Response(output);         // serve directly (Content-Type auto-set)
}
```

If `outdir` is omitted from the JS API, files are not written to disk but returned as `BuildArtifact` objects (which implement `Blob`).

### In-Memory Bundling

The JS API supports a `files` map for virtual files:

```ts
const result = await Bun.build({
  entrypoints: ["/app/index.ts"],
  files: {
    "/app/index.ts": `import { greet } from "./greet.ts"; console.log(greet("World"));`,
    "/app/greet.ts": `export function greet(name: string) { return "Hello, " + name + "!"; }`,
  },
});
```

Virtual files take priority over disk files, useful for injecting build-time constants or testing with mocks.

---

## Entrypoints, Outdir, and Naming

### Entrypoints

An array of file paths. One bundle is generated per entrypoint.

```ts
await Bun.build({
  entrypoints: ["./index.tsx", "./admin.tsx"],
  outdir: "./out",
});
```

### Root Directory

The `root` option controls how output paths are computed. If unspecified, it is the first common ancestor of all entrypoints.

```bash
# Without root: pages/index.tsx -> out/index.js
# With root=".": pages/index.tsx -> out/pages/index.js
bun build ./pages/index.tsx --outdir ./out --root .
```

### Naming Conventions

Default: `[dir]/[name].[ext]`

Available tokens: `[name]`, `[ext]`, `[hash]`, `[dir]`

```ts
await Bun.build({
  entrypoints: ["./index.tsx"],
  outdir: "./out",
  naming: {
    entry: "[dir]/[name].[ext]",        // entrypoint bundles
    chunk: "[name]-[hash].[ext]",       // code-split chunks
    asset: "[name]-[hash].[ext]",       // copied assets (images, etc.)
  },
});
```

CLI equivalents: `--entry-naming`, `--chunk-naming`, `--asset-naming`.

---

## TypeScript and JSX/TSX

Bun handles TypeScript and JSX natively through built-in loaders:

| Extension          | Loader | Behavior                                    |
|--------------------|--------|---------------------------------------------|
| `.ts`, `.mts`, `.cts` | `ts`   | Strips TypeScript syntax, no type checking  |
| `.tsx`             | `tsx`  | Strips TS + transforms JSX to JS            |
| `.jsx`, `.js`      | `jsx`  | Transforms JSX to JS                        |

### JSX Configuration

JSX transform can be configured via `tsconfig.json` (recommended), `bunfig.toml`, or the JS API:

```ts
// Automatic runtime (React 17+, Preact, etc.)
await Bun.build({
  entrypoints: ["./app.tsx"],
  outdir: "./out",
  jsx: {
    runtime: "automatic",
    importSource: "react",  // or "preact", "solid-js", etc.
  },
});

// Classic runtime
await Bun.build({
  entrypoints: ["./app.tsx"],
  outdir: "./out",
  jsx: {
    runtime: "classic",
    factory: "h",
    fragment: "Fragment",
  },
});
```

**Important**: Bun does not down-convert modern ECMAScript syntax. If you use recent syntax, it appears as-is in the output.

---

## Loaders and Content Types

### Built-in Loaders

| Extensions | Loader | Output |
|---|---|---|
| `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs`, `.mts`, `.cjs`, `.cts` | js/jsx/ts/tsx | Transpiled JS with tree shaking |
| `.json` | json | Inlined as JS object |
| `.jsonc` | jsonc | JSON with comments, inlined as JS object |
| `.toml` | toml | Parsed and inlined as JS object |
| `.yaml`, `.yml` | yaml | Parsed and inlined as JS object |
| `.txt` | text | Inlined as string |
| `.html` | html | Processes and bundles referenced assets |
| `.css` | css | Bundled into single CSS file per entry |
| `.node`, `.wasm` | file | Copied as-is to outdir (asset) |
| Unrecognized | file | Copied to outdir, import resolves to path |

### Overriding Loaders

```ts
await Bun.build({
  entrypoints: ["./index.tsx"],
  outdir: "./out",
  loader: {
    ".png": "dataurl",   // inline as data URL
    ".txt": "file",      // copy as asset
    ".svg": "text",      // inline as string
  },
});
```

CLI: `--loader .png:dataurl --loader .txt:file`

### Import Attributes

You can override the loader per-import using `with` syntax:

```ts
import my_toml from "./my_file" with { type: "toml" };
import html from "./index.html" with { type: "text" };
```

---

## Plugins System

Plugins are objects with a `name` and `setup` function. They work identically in the runtime and the bundler.

```ts
import type { BunPlugin } from "bun";

const myPlugin: BunPlugin = {
  name: "My Plugin",
  setup(build) {
    // Lifecycle hooks go here
  },
};

await Bun.build({
  entrypoints: ["./app.ts"],
  outdir: "./out",
  plugins: [myPlugin],
});
```

### Lifecycle Hooks

#### onStart

Runs once when the bundler starts. Can return a Promise.

```ts
build.onStart(() => {
  console.log("Bundle started!");
});
```

#### onResolve

Intercepts module resolution. Takes a `filter` regex and optional `namespace`.

```ts
build.onResolve({ filter: /^images\//, namespace: "file" }, (args) => {
  return {
    path: args.path.replace("images/", "./public/images/"),
  };
});
```

#### onLoad

Intercepts module loading. Can return custom `contents` and `loader`.

```ts
build.onLoad({ filter: /\.env$/ }, (args) => {
  return {
    contents: `export default ${JSON.stringify(process.env)}`,
    loader: "js",
  };
});
```

The `onLoad` callback also receives a `defer` function that returns a Promise resolved when all other modules have loaded -- useful for generating summary/stats modules.

#### onBeforeParse (Native)

For performance-critical plugins written as NAPI modules (Rust, C). Runs on parser threads before a file is parsed. Must be thread-safe.

```ts
build.onBeforeParse(
  { namespace: "file", filter: "**/*.tsx" },
  { napiModule: myNativeAddon, symbol: "my_transform" },
);
```

### Plugin Namespaces

Every module has a namespace (default: `"file"`). Custom namespaces prefix imports in transpiled code. Common namespaces: `"file"`, `"bun"`, `"node"`.

---

## External Dependencies

### Marking Specific Packages External

```ts
await Bun.build({
  entrypoints: ["./index.tsx"],
  outdir: "./out",
  external: ["lodash", "react"],
});
```

CLI: `--external lodash --external react`

External imports are left as `import` statements in the output, resolved at runtime.

### Wildcard External

```ts
external: ["*"]  // mark ALL imports external
```

### packages Option

```ts
await Bun.build({
  entrypoints: ["./index.ts"],
  packages: "external",  // all non-relative imports become external
});
```

CLI: `--packages external`

Bun treats any import not starting with `.`, `..`, or `/` as a package.

---

## Tree Shaking and Minification

### Tree Shaking

Enabled by default. Bun performs dead code elimination and respects `@__PURE__` annotations and `package.json` `"sideEffects"` fields.

```ts
// Override if library annotations are incorrect
await Bun.build({
  entrypoints: ["./index.tsx"],
  outdir: "./out",
  ignoreDCEAnnotations: true,   // ignore @__PURE__ and sideEffects
  emitDCEAnnotations: true,     // re-emit @__PURE__ even when minifying whitespace
});
```

### Compile-Time Feature Flags

```ts
import { feature } from "bun:bundle";

if (feature("PREMIUM")) {
  initPremiumFeatures();  // eliminated if PREMIUM not enabled
}
```

```ts
await Bun.build({
  entrypoints: ["./app.ts"],
  outdir: "./out",
  features: ["PREMIUM"],   // enable PREMIUM flag
  minify: true,             // dead code eliminated
});
```

CLI: `--feature PREMIUM`

### Minification

```ts
await Bun.build({
  entrypoints: ["./index.tsx"],
  outdir: "./out",
  minify: true,  // enable all
  // Or granularly:
  minify: {
    whitespace: true,
    identifiers: true,
    syntax: true,
  },
});
```

CLI: `--minify` or `--minify-whitespace --minify-identifiers --minify-syntax`

When targeting `bun`, identifiers are minified by default.

### Drop

Remove function calls from the bundle:

```ts
await Bun.build({
  entrypoints: ["./index.tsx"],
  outdir: "./out",
  drop: ["console", "debugger"],
});
```

CLI: `--drop console --drop debugger`

---

## Code Splitting

```ts
await Bun.build({
  entrypoints: ["./entry-a.ts", "./entry-b.ts"],
  outdir: "./out",
  splitting: true,
});
```

Shared code between entrypoints is extracted into chunk files (e.g., `chunk-2fce6291bf86559d.js`). Chunk naming is controlled via `naming.chunk`.

---

## Watch Mode

```bash
bun build ./index.tsx --outdir ./out --watch
```

Rebuilds incrementally when files change. Add `--no-clear-screen` to prevent terminal clearing.

---

## Targets and Formats

### Targets

| Target | Default For | Behavior |
|--------|-------------|----------|
| `browser` | default | Prioritizes `"browser"` export condition |
| `bun` | files with `#!/usr/bin/env bun` | Adds `// @bun` pragma; no re-transpile needed |
| `node` | - | Prioritizes `"node"` export condition; outputs `.mjs` |

### Formats

| Format | Status | Notes |
|--------|--------|-------|
| `esm` | Default, stable | Supports top-level await, import.meta |
| `cjs` | Experimental | Changes default target to `node` |
| `iife` | Experimental | Immediately Invoked Function Expression |

---

## Sourcemaps

```ts
await Bun.build({
  entrypoints: ["./index.tsx"],
  outdir: "./out",
  sourcemap: "linked",  // "none" | "linked" | "external" | "inline"
});
```

| Value | Behavior |
|-------|----------|
| `"none"` | Default. No sourcemap. |
| `"linked"` | Separate `.js.map` with `//# sourceMappingURL` comment |
| `"external"` | Separate `.js.map` without URL comment; uses debugId |
| `"inline"` | Base64-encoded sourcemap appended to bundle |

---

## Environment Variables

```ts
await Bun.build({
  entrypoints: ["./index.tsx"],
  outdir: "./out",
  env: "inline",           // inline ALL env vars
  // env: "PUBLIC_*",      // only vars matching prefix
  // env: "disable",       // no env var replacement
});
```

CLI: `--env inline` or `--env PUBLIC_*`

### Define (Build-Time Constants)

```ts
await Bun.build({
  entrypoints: ["./index.tsx"],
  outdir: "./out",
  define: {
    "process.env.API_URL": JSON.stringify("https://api.example.com"),
    "DEBUG": "false",
  },
});
```

CLI: `--define 'process.env.API_URL="https://api.example.com"'`

---

## HTML Entrypoints and Static Sites

Bun has first-class HTML support. Pass an HTML file as an entrypoint and it bundles all referenced scripts, stylesheets, and assets:

```bash
# Development server (zero config)
bun ./index.html

# Production build
bun build ./index.html --outdir ./dist --minify
```

### Single Page Apps (SPA)

When a single `.html` file is passed, Bun uses it as a fallback for all routes, enabling client-side routing:

```bash
bun index.html
# All routes (/about, /users/123, etc.) serve the same HTML
```

### Multi-Page Apps

```bash
bun ./index.html ./about.html
# Routes: / -> index.html, /about -> about.html
```

### What Gets Processed in HTML

- `<script src>` -- bundled through JS/TS/JSX pipeline
- `<link rel="stylesheet">` -- bundled through CSS pipeline
- `<img>`, `<video>`, `<audio>`, `<source>` -- copied and hashed
- All local asset paths are rewritten with content hashes

### CSS Bundling

CSS files imported from JavaScript are bundled into a single CSS file per entry:

```ts
import "./styles.css";
import "./more-styles.css";
// generates app.css alongside app.js
```

CSS `@import` statements are resolved and inlined.

---

## Banner and Footer

```ts
await Bun.build({
  entrypoints: ["./index.tsx"],
  outdir: "./out",
  banner: '"use client";',
  footer: "// built with love",
});
```

Useful for React Server Components directives or license comments.

---

## Metafile (Bundle Analysis)

```ts
const result = await Bun.build({
  entrypoints: ["./src/index.ts"],
  outdir: "./dist",
  metafile: true,
});

// Analyze
for (const [path, meta] of Object.entries(result.metafile.inputs)) {
  console.log(`${path}: ${meta.bytes} bytes`);
}

// Save for tools like esbuild's bundle analyzer
await Bun.write("./dist/meta.json", JSON.stringify(result.metafile));
```

CLI: `--metafile ./dist/meta.json` and/or `--metafile-md ./dist/meta.md`

---

## Bytecode and Executables

### Bytecode

Generates `.jsc` bytecode files for faster startup. Only works with `format: "cjs"` and `target: "bun"`.

```bash
bun build ./index.tsx --outdir ./out --bytecode
```

### Standalone Executables

```bash
bun build ./cli.tsx --outfile mycli --compile
./mycli
```

Embeds the Bun binary into the output for distribution without requiring Bun installed.

---

## Configuration: bunfig.toml vs CLI vs JS API

### bunfig.toml

Bun reads `bunfig.toml` for some build-related settings, but the bundler does not have a dedicated `[build]` section in bunfig.toml. The relevant bunfig.toml settings are:

```toml
# JSX configuration (also reads from tsconfig.json)
jsx = "react"
jsxFactory = "h"
jsxFragment = "Fragment"
jsxImportSource = "react"

# Custom loaders
[loader]
".bagel" = "tsx"

# Build-time defines
[define]
"process.env.bagel" = "'lox'"

# Dev server plugins (for `bun ./index.html`)
[serve.static]
plugins = ["bun-plugin-tailwind"]
env = "PUBLIC_*"
```

### Priority Order

CLI flags > bunfig.toml > tsconfig.json defaults

### tsconfig.json

Bun reads `tsconfig.json` for:
- `compilerOptions.jsx` / `jsxFactory` / `jsxFragment` / `jsxImportSource`
- `compilerOptions.paths` (path aliases)
- `compilerOptions.experimentalDecorators`
- `compilerOptions.baseUrl`

You can override the tsconfig path: `--tsconfig-override ./custom-tsconfig.json` or `tsconfig: "./custom-tsconfig.json"` in the JS API.

---

## Comparison with Other Bundlers

### vs esbuild

- Bun is heavily inspired by esbuild's API and plugin model
- Bun is faster on benchmarks (native Zig vs Go)
- Bun's plugin API is largely compatible in concept (onResolve, onLoad) but not a direct drop-in
- Bun adds HTML-first building, native dev server, built-in YAML/TOML loaders
- Bun metafile format is compatible with esbuild's analyzer
- esbuild has broader syntax downleveling; Bun does not down-convert modern syntax

### vs Vite

- Vite uses esbuild for dev and Rollup for production; Bun uses one native bundler for both
- Vite has a richer plugin ecosystem (Rollup plugins)
- Bun's dev server (`bun ./index.html`) is simpler -- zero config, no `vite.config.ts` needed
- Vite has HMR with framework-specific integrations; Bun supports hot module reloading
- Vite handles CSS modules, PostCSS out of the box; Bun's CSS support is more basic (native bundling, no PostCSS yet)
- Vite has more mature SPA/SSR framework integrations

### vs Webpack

- Webpack is far more configurable but much slower and complex
- Bun is orders of magnitude faster
- Webpack has a massive plugin/loader ecosystem
- Bun's plugin system is simpler (onResolve/onLoad vs Webpack's tap-based architecture)
- Webpack supports CSS modules, code splitting strategies, module federation -- features Bun is still developing

### Summary Table

| Feature | Bun | esbuild | Vite | Webpack |
|---------|-----|---------|------|---------|
| Speed | Fastest | Very fast | Fast (dev) / Moderate (build) | Slow |
| Config complexity | Minimal | Minimal | Moderate | High |
| Plugin ecosystem | Small | Small | Large (Rollup) | Largest |
| HTML entrypoints | Native | No | Via plugin | Via plugin |
| TypeScript | Native | Native | Via esbuild | Via ts-loader |
| CSS bundling | Native | Basic | Rich (PostCSS, modules) | Rich |
| Dev server | Built-in | No | Built-in | Via webpack-dev-server |
| Tree shaking | Yes | Yes | Yes | Yes |
| Code splitting | Yes | Yes | Yes | Yes |
| Syntax downleveling | No | Yes | Yes (via esbuild) | Yes (via Babel) |

---

## Practical Patterns: Lit Web Component SPA

Bun does not have Lit-specific plugins, but building a Lit SPA works well given Bun's native TypeScript and decorator support.

### Project Structure

```
src/
  index.html
  app.ts
  components/
    my-app.ts
    my-header.ts
    my-page.ts
  styles/
    global.css
```

### index.html

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>My Lit App</title>
  <link rel="stylesheet" href="./src/styles/global.css" />
  <script type="module" src="./src/app.ts"></script>
</head>
<body>
  <my-app></my-app>
</body>
</html>
```

### app.ts (Entrypoint)

```ts
// Import all components to register them
import "./components/my-app.js";
import "./components/my-header.js";
import "./components/my-page.js";
```

### A Lit Component

```ts
// src/components/my-app.ts
import { LitElement, html, css } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("my-app")
export class MyApp extends LitElement {
  static styles = css`
    :host { display: block; font-family: sans-serif; }
  `;

  @property() page = "home";

  render() {
    return html`
      <my-header></my-header>
      <main>${this.page}</main>
    `;
  }
}
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "experimentalDecorators": true,
    "useDefineForClassFields": false,
    "jsx": "react-jsx"
  }
}
```

**Note**: `useDefineForClassFields: false` is critical for Lit decorators to work correctly with TypeScript.

### Development

```bash
bun ./index.html
# Dev server with HMR at http://localhost:3000
```

### Production Build

```bash
bun build ./index.html --outdir ./dist --minify --sourcemap linked
```

### Build Script (JS API)

```ts
// build.ts
await Bun.build({
  entrypoints: ["./index.html"],
  outdir: "./dist",
  minify: true,
  sourcemap: "linked",
  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
});
```

### Key Considerations for Lit + Bun

1. **Decorators**: Bun reads `experimentalDecorators` from tsconfig.json. Lit's decorators work with this setting.
2. **CSS**: Lit uses `css` tagged template literals (processed at runtime), so no special CSS loader is needed.
3. **External lit**: For large apps, consider keeping `lit` external to leverage CDN caching: `external: ["lit", "lit/decorators.js"]`
4. **Code splitting**: Enable `splitting: true` for lazy-loaded routes if using dynamic imports.
5. **No down-conversion**: Bun outputs modern JS. If you need legacy browser support, you may need a separate step.

---

## Error Handling

```ts
try {
  const result = await Bun.build({
    entrypoints: ["./index.tsx"],
    outdir: "./out",
  });
} catch (e) {
  const error = e as AggregateError;
  // error.errors contains BuildMessage[] and ResolveMessage[]
  console.error(error);
}

// Or disable throwing:
const result = await Bun.build({
  entrypoints: ["./index.tsx"],
  outdir: "./out",
  throw: false,  // returns { success: false } instead of throwing
});
```

---

## Quick Reference: Common CLI Flags

```
bun build <entrypoints...>
  --outdir <dir>              Output directory
  --outfile <file>            Output to specific file
  --target <browser|bun|node> Execution environment (default: browser)
  --format <esm|cjs|iife>    Module format (default: esm)
  --minify                    Enable all minification
  --splitting                 Enable code splitting
  --sourcemap <type>          none|linked|inline|external
  --external <pkg>            Exclude from bundle
  --packages <mode>           bundle|external
  --watch                     Rebuild on file changes
  --env <mode>                inline|disable|PREFIX_*
  --define K=V                Replace global identifiers
  --loader .ext:loader        Map extensions to loaders
  --entry-naming <template>   Customize entry filenames
  --chunk-naming <template>   Customize chunk filenames
  --asset-naming <template>   Customize asset filenames
  --public-path <prefix>      Prefix for import paths
  --root <dir>                Project root directory
  --banner <text>             Prepend to output
  --footer <text>             Append to output
  --drop <id>                 Remove function calls
  --feature <flag>            Enable compile-time feature
  --compile                   Create standalone executable
  --production                Set NODE_ENV=production + minify
  --metafile <path>           Write JSON metafile
  --metafile-md <path>        Write Markdown metafile
  --bytecode                  Generate bytecode (CJS + bun target only)
  --no-bundle                 Transpile only, no bundling
```

---

## Sources & Further Reading

- Bun Bundler docs: https://bun.sh/docs/bundler
- Bun Loaders docs: https://bun.sh/docs/bundler/loaders
- Bun Plugins docs: https://bun.sh/docs/bundler/plugins
- Bun HTML & static sites: https://bun.sh/docs/bundler/html
- Bun bunfig.toml: https://bun.sh/docs/runtime/bunfig
- Bun full-stack docs: https://bun.sh/docs/bundler/fullstack
- Lit documentation: https://lit.dev/docs/

## Open Questions

- **IIFE format**: Documentation says "TODO: document IIFE once we support globalNames" -- the globalName option is not yet available.
- **CSS Modules**: Native CSS module support (`.module.css`) status is unclear; may require a plugin.
- **PostCSS integration**: No built-in PostCSS support. TailwindCSS has a dedicated plugin (`bun-plugin-tailwind`), but general PostCSS requires custom plugin work.
- **Syntax downleveling**: Bun does not down-convert modern syntax. If legacy browser support is needed, a supplementary tool (e.g., Babel) may be required.
- **Hot Module Replacement**: HMR is available in the dev server but framework-specific HMR (e.g., React Fast Refresh) is still maturing.
- **bunfig.toml build section**: There is no dedicated `[build]` configuration section in bunfig.toml for the bundler CLI. Most bundler configuration must be done via CLI flags or the JS API. The `[serve.static]` section covers dev server plugins and env settings.
