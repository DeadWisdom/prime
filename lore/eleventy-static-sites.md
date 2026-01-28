# Eleventy (11ty) Static Site Generator

researched: 2025-01-26
status: complete
tags: static-site-generator, javascript, nodejs, web, templates

## Executive Summary

Eleventy is a zero-config static site generator that transforms templates into HTML. It requires no client-side JavaScript by default, supports multiple template languages, and uses a data cascade system for flexible content management.

## Background

Eleventy (11ty) is designed to be simpler than other static site generators while remaining powerful. It works with multiple template languages including HTML, Markdown, Nunjucks, Liquid, JavaScript, WebC, and more. The recommended approach is HTML (Nunjucks) for layouts and Markdown for content.

**Requirements:** Node.js 18+

## Key Findings

### Installation and Setup

```bash
# Install with bun
bun add -d @11ty/eleventy

# Build site
bunx @11ty/eleventy

# Dev server with hot reload
bunx @11ty/eleventy --serve
```

### Project Structure

```
site/
├── _includes/        # Layouts and partials
│   └── base.html
├── _data/            # Global data files
│   └── site.json
├── posts/            # Content directory
│   ├── posts.json    # Directory data (applies to all posts)
│   └── first-post.md
├── index.md          # Homepage
└── eleventy.config.js
```

Minimal configuration:

```javascript
export default function(eleventyConfig) {
  return {
    dir: {
      input: "src",
      output: "_site",
      includes: "_includes",
      data: "_data"
    }
  };
};
```

### Layouts

Layouts wrap content and live in `_includes/`. They can chain (layouts wrapping other layouts).

**`_includes/base.html`:**
```html
<!DOCTYPE html>
<html>
<head>
  <title>{{ title }}</title>
</head>
<body>
  {{ content | safe }}
</body>
</html>
```

**Content using layout:**
```markdown
---
layout: base.html
title: The Page
---

# Hello World
```

### Front Matter

YAML metadata at the top of template files:

```yaml
---
title: Post Title
date: 2025-01-15
tags: [blog, tutorial]
layout: post.html
permalink: /custom-url/
eleventyExcludeFromCollections: false
---
```

### Data Cascade

Data merges from multiple sources (highest priority first):

1. **Computed Data** - Dynamic values from `eleventyComputed`
2. **Front Matter** - Template YAML
3. **Template Data Files** - `page.11tydata.js` alongside template
4. **Directory Data Files** - `posts/posts.json` applies to all in folder
5. **Layout Front Matter** - From layout chain
6. **Global Data** - Files in `_data/` directory

### Collections

Group content by tags for iteration:

```yaml
---
tags: post
---
```

```html
<ul>
{% for post in collections.post %}
  <li><a href="{{ post.url }}">{{ post.data.title }}</a></li>
{% endfor %}
</ul>
```

Custom collections via config:

```javascript
eleventyConfig.addCollection("featured", function(collectionApi) {
  return collectionApi.getFilteredByTag("post")
    .filter(item => item.data.featured);
});
```

### Filters and Shortcodes

**Custom filter:**
```javascript
eleventyConfig.addFilter("dateFormat", function(date) {
  return new Date(date).toLocaleDateString("en-US", {
    year: "numeric", month: "long", day: "numeric"
  });
});
```

**Shortcode:**
```javascript
eleventyConfig.addShortcode("image", function(src, alt) {
  return `<img src="${src}" alt="${alt}" loading="lazy">`;
});
```

**Paired shortcode:**
```javascript
eleventyConfig.addPairedShortcode("callout", function(content, type = "info") {
  return `<div class="callout callout-${type}">${content}</div>`;
});
```

### Pagination

Generate pages from data:

```yaml
---
pagination:
  data: collections.post
  size: 10
  alias: posts
permalink: /blog/{% if pagination.pageNumber > 0 %}page/{{ pagination.pageNumber + 1 }}/{% endif %}
---
```

### Key Plugins

- **@11ty/eleventy-img** - Image optimization with responsive sizes and formats
- **@11ty/eleventy-plugin-syntaxhighlight** - Code syntax highlighting
- **@11ty/eleventy-plugin-rss** - RSS feed generation
- **@11ty/eleventy-navigation** - Navigation building

### Passthrough Copy

Copy static assets without processing:

```javascript
eleventyConfig.addPassthroughCopy("css");
eleventyConfig.addPassthroughCopy({ "src/assets": "assets" });
```

## Practical Implications

- Start with the data cascade in mind; use directory data files to reduce repetition
- Use collections and tags to organize related content
- Leverage layout chaining for consistent page structures with variations
- Image optimization plugin is essential for performance
- Permalinks offer complete control over URL structure

## Sources & Further Reading

- Documentation: https://www.11ty.dev/docs/
- Starter Projects: https://www.11ty.dev/docs/starter/
- Plugins: https://www.11ty.dev/docs/plugins/
- Community: https://www.11ty.dev/docs/community/

## Open Questions

- Performance at scale with very large sites (1000+ pages)
- Best practices for incremental builds in production
