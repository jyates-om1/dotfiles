# Claude Docs quirks (learned the hard way)

Each of these cost a refused call or a wrong render at least once.

## Writes
- **`row_too_large`:** a markdown table write with many `[text](#id)` links is refused. Write tables with plain Ref labels, then add each link with a format op:
  `{"op":"format","target":{"kind":"find","text":"§R3 Middleware","within":{"kind":"cell","table":"<table id>","row":2,"col":3}},"add":[{"type":"link","href":"#<block id>"}]}`. The key is `add`, not `mark`.
- **Two inserts can't share an anchor** in one call ("2 adds share after"). Merge them into one insert whose content holds both rows or blocks.
- **`as:"text"` keeps markdown literal:** backticks and `**` show as characters. Use `as:"markdown"` for formatted content, or `as:"blocks"` with marks (`{"type":"code"}`, `{"type":"bold"}`).
- **`as:"markdown"` on a whole block drops what it doesn't re-spell** (notice `dropped`). Re-read the block first and re-spell its links and chips.
- **Block replace needs both guards:** `ifHash` = the block's newest `h`, `ifRev` = the rev of the read that showed it. A cell replace needs `ifRev` only.
- **`find_ambiguous`:** scope the find with `"parentId"` or `"within"`. **`find_none`:** the words changed; re-read and quote what's there now.
- **An empty text node is refused** in `as:"blocks"` content. An empty cell is `{"type":"paragraph"}` with no content.

## Tables
- **Insert a row:** `insert` with `as:"blocks"`, every cell spelled, `side:"after"` a row id (or `"end"` on the table id).
- **Dropdowns in a new table go inline** (verified 2026-10-21): in the fill's markdown, put `<?claude block d0?>` in the cell and `"d0":{"type":"dropdown","enum":"<enum id>"}` (plus `"index":k` to preset) in `blocks`. One chip key per cell.
- **Dropdowns in an existing table take two steps** (new row or new column): insert the row with an empty last cell, then replace that cell:
  `{"op":"replace","target":{"kind":"cell","table":"<id>","row":N,"col":M},"ifRev":<rev>,"with":{"as":"markdown","blocks":{"d1":{"type":"dropdown","enum":"<enum id>"}},"from":{"kind":"inline","content":"<?claude block d1?>"}}}`.
  Add `"index":k` in the dropdown to preset an option (Status column).
- **Add a column:** one `insert` with `"each":true` over every row id, `as:"text"`, empty content. Then fill the cells.
- **Delete a row:** `delete` with the row id plus `ifHash` (the row's `h`) and `ifRev`.
- **Cell row indexes shift** after a row insert or delete in the same call. Put cell replaces first, then deletes, then inserts.

## Links and embeds
- **In-doc links** are `#<block id>`. Prefer heading ids. Both tabs' blocks share one id prefix (`<session>.<n>`), so a Reference heading id can equal a character id in Overview. Whether a cross-tab `#id` link scrolls to the other tab is [U]: ask the user to click one in step 6. If it doesn't, fall back to a tab mention chip (`{"type":"mention","ref":"file/<tab id>"}`) plus the section name.
- **Change an embed caption:** `{"op":"set","target":{"kind":"blocks","ids":["<embed id>"]},"attrs":{"caption":"…"}}`.

## Birth
- The birth batch in birth.md works as written (verified 2026-10-21): two tabs, both enums and all pending blocks in one call. Filling a pending block needs no guards.

## Reading
- Outline first (`payload {"projection":"outline"}`), then `{"kind":"view","parentId":"<id>"}` for one table or list, or `{"kind":"search","text":"…"}`. Never read the whole tab.
- Big outputs spill to a file; probe them with `jq` or Python.
