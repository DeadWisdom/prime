# Gmail Search

Search Gmail for threads matching a query and display their contents.

## Usage

```
/gmail <search query>
```

## Examples

```
/gmail from:sarah@joincolumn.com
/gmail subject:invoice
/gmail is:unread
/gmail from:boss@company.com after:2024/01/01
```

## Instructions

Run the gmail_search.py script with the provided query. Use the Bash tool:

```bash
uv run gmail_search.py "$ARGUMENTS"
```

If the user wants to see more results, use the `--limit` flag:
```bash
uv run gmail_search.py "$ARGUMENTS" --limit 20
```

If there are more pages available, use `--page` to fetch subsequent pages:
```bash
uv run gmail_search.py "$ARGUMENTS" --page 2
```

Present the results clearly to the user. If they ask for correspondence from a specific person (like "emails from Sarah"), construct the appropriate Gmail search query (e.g., `from:sarah@joincolumn.com`).
