# Birth batch

One `batch` call creates the doc with both tabs and both enums. Send it before writing anything else.
Replace `<…>`. Add or drop `sN` pending blocks to match the inventory (one per stakeholder subsection; one per alternative; none if there are no alternatives).

```json
{
 "container": {"kind": "project", "create": {"name": "<Title>",
  "doc": {
   "blocks": {
    "asof": {"type": "date", "value": "<YYYY-MM-DD>"},
    "me": {"type": "mention", "user": "me"},
    "lead": {"type": "pending", "intent": "Lead: what, size, who builds, what we need from whom, how to respond"},
    "goals": {"type": "pending", "intent": "Goals and not-goals"},
    "shape": {"type": "pending", "intent": "Shape: a diagram of how the parts fit together, drawn first"},
    "dec": {"type": "pending", "intent": "Decisions: what is decided, proposed and open"},
    "alt1": {"type": "pending", "intent": "Alternative considered: <name>, a diagram with numbered consequences"},
    "s1": {"type": "pending", "intent": "For <Name> (<role>): questions with leans"},
    "s2": {"type": "pending", "intent": "For <Name> (<role>): questions with leans"},
    "nd": {"type": "pending", "intent": "No decision needed"},
    "oos": {"type": "pending", "intent": "Out of scope"}
   },
   "markdown": "# <Title>\n\n<?claude block asof?> · <?claude block me?>\n\n<?claude block lead?>\n\n<?claude block goals?>\n\n<?claude block shape?>\n\n<?claude block dec?>\n\n<?claude block alt1?>\n\n## What we need from you\n\n<?claude block s1?>\n\n<?claude block s2?>\n\n<?claude block nd?>\n\n<?claude block oos?>"
  }}},
 "batch": [
  {"$lid": "st", "verb": "create", "object": "enum", "payload": {"value": {"name": "Status", "options": [{"name": "Decided"}, {"name": "Proposed"}, {"name": "Open"}]}}},
  {"$lid": "dc", "verb": "create", "object": "enum", "payload": {"value": {"name": "Decision", "options": [{"name": "Agree"}, {"name": "Change"}, {"name": "Discuss"}]}}},
  {"$lid": "f2", "verb": "create", "object": "file", "payload": {"value": {"birthName": "Reference.ldoc"}}},
  {"$lid": "n2", "verb": "create", "object": "node", "engine": "prose",
   "payload": {"parent": {"object": "file", "id": "$lid:f2"},
    "source": {"as": "markdown", "blocks": {
      "r0": {"type": "pending", "intent": "Changes since last review"},
      "r1": {"type": "pending", "intent": "Glossary"},
      "r2": {"type": "pending", "intent": "Component sections R1..Rn with evidence"},
      "r3": {"type": "pending", "intent": "Acceptance checks"},
      "r4": {"type": "pending", "intent": "Tickets and size"},
      "r5": {"type": "pending", "intent": "References"}},
     "from": {"kind": "inline", "content": "# Reference\n\n<?claude block r0?>\n\n<?claude block r1?>\n\n<?claude block r2?>\n\n<?claude block r3?>\n\n<?claude block r4?>\n\n<?claude block r5?>"}}}},
  {"verb": "update", "ref": {"object": "file", "id": "$lid:f2"}, "payload": {"kind": "value", "value": {"birthName": "Reference.ldoc", "content": {"kind": "node", "id": "$lid:n2"}}}},
  {"verb": "update", "ref": {"object": "project", "id": "$lid:p"}, "payload": {"kind": "patch", "patch": [
    {"op": "set", "path": ["tabs", "$lid:f"], "value": {"name": "Overview", "order": "a0"}},
    {"op": "set", "path": ["tabs", "$lid:f2"], "value": {"name": "Reference", "order": "a1"}}]}}
 ]
}
```

The "What we need from you" heading is written at birth because several pending blocks sit under it; each stakeholder fill starts with `### For <Name> (<role>)`.

Record from the ack: doc id and link, `lids.f` / `lids.n` (Overview tab and body), `lids.f2` / `lids.n2` (Reference), `lids.st` / `lids.dc` (enum ids), and each pending block's id from the xml (`keys`).
If the batch is refused, read the refusal: drop the members it names (enums can also be created later in a fill batch), never retry the same body unchanged.
