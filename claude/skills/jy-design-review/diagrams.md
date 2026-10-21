# Diagram kit

Diagrams are Claude Docs widget nodes: one JS module returning an `<svg>`. Create and place each in ONE batch: the widget `create`, then a prose `update` replacing the section's pending block with `## <Heading>`, the embed and the sentence under it. If a module is refused at publish, read `guide(["topic.diagram"])` once and fix it.

## Which diagram where

| Section | Pattern | Shows |
|---|---|---|
| Shape | **Bands** (pattern A) | Layers or phases as tinted bands, components as boxes inside, arrows for the main flow, one accent box for the thing under decision |
| Alternative considered | **Markers** (pattern B) | The rejected shape, with numbered markers on each cost; the numbers match the consequences list below it |
| A runtime flow worth reading step by step | **Sequence** (pattern C) | Actors as lanes, numbered steps as arrows, a text column of step descriptions |

Seed Shape first, in step 3, before any prose. It is the doc's first picture and anchors every later section.

## Hard rules (the validator refuses otherwise)

- Every `<text>` carries its own literal `data-claude-text-id='slug'` and literal words. Never put ids or words inside `.map()`; shapes may come from helpers.
- Two lines = two `<tspan data-claude-text-id=…>` inside one `<text>` that has no id.
- One `<g data-claude-anchor='slug'>` per box, lane or step, around its shape and labels.
- Colour only through tokens: `var(--cds-text-primary)`, `var(--cds-text-secondary)`, `var(--cds-chart-axis)`, `var(--cds-chart-grid)`, `var(--cds-chart-reference-tint)`, `var(--cds-chart-categorical-1)` (the accent), `var(--cds-chart-status-critical)` (markers). Every `<text>` sets `fill`.
- No computed index (`xs[i]`): use `.at(i)` or a literal read. No identifiers named `top`, `parent`, `self` or `window`.
- No `<style>`, `<use>` or `<foreignObject>`. Escape `<` in text as `&lt;`.
- `viewBox='0 0 760 H'`; everything inside it with ≥ 24 clear on the right.

## Sizing (count before sending; the frame shows at about 0.88 scale)

- Text sizes: 15/600 for the title, 13/600 for box names, 11.5 for body lines.
- Characters per line ≈ (box width − 24) ÷ unit: 7.4 for a 13/600 name, 6.2 for an 11.5 line.
- Box height = 40 + 16 × body lines. Gaps ≥ 16 between boxes; connectors run in the gaps, never across a box or a label.
- Edge labels sit beside their line with a clear gap. If a label crosses a band header or lane, move the label or the line.

## Pattern A: bands (shape)

```js
export default () => { const edge = 'var(--cds-chart-axis)', accent = 'var(--cds-chart-categorical-1)', ink = 'var(--cds-text-primary)', quiet = 'var(--cds-text-secondary)', tint = 'var(--cds-chart-reference-tint)'; const box = (x, y, w, h, main) => <rect x={x} y={y} width={w} height={h} rx='8' fill={main ? accent : 'none'} fillOpacity={main ? 0.12 : 1} stroke={main ? accent : edge} strokeWidth={main ? 2 : 1.25}/>; const band = (x, y, w, h) => <rect x={x} y={y} width={w} height={h} rx='8' fill={tint} stroke={edge} strokeWidth='1'/>; return <svg viewBox='0 0 760 396' role='img' aria-label='<finding as title>' fontSize='13'><defs><marker id='shape-arrow' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='6' markerHeight='6' orient='auto-start-reverse'><path d='M0 0L10 5L0 10z' fill={edge}/></marker></defs><text data-claude-text-id='title' x='24' y='34' fontSize='15' fontWeight='600' fill={ink}><finding as title></text><g data-claude-anchor='band-1'>{band(24, 56, 712, 148)}<text data-claude-text-id='band-1-head' x='40' y='80' fontWeight='600' fill={ink}><Band 1 · what it is · who owns it></text></g><g data-claude-anchor='step-a'>{box(40, 96, 154, 72, false)}<text data-claude-text-id='a-name' x='52' y='120' fontWeight='600' fill={ink}><Name></text><text data-claude-text-id='a-1' x='52' y='140' fontSize='11.5' fill={quiet}><line 1></text><text data-claude-text-id='a-2' x='52' y='156' fontSize='11.5' fill={quiet}><line 2></text></g>…<g data-claude-anchor='connectors' fill='none' stroke={edge} strokeWidth='1.25'><path d='M194 140H218' markerEnd='url(#shape-arrow)'/></g></svg>; };
```

Layout that worked: four 154-wide boxes per band at x = 40, 218, 396, 574 (gap 24), or three 200-wide boxes at x = 40, 280, 520. A band is 148 tall for 72–88-tall boxes. To hand off between bands, run an elbow from the last box down, along the gap between bands, and into the next band's first box, with the label above the run. Keep band headers clear of the elbow's vertical segment.

## Pattern B: markers (alternative)

Same boxes as A. For each cost of the rejected option, add a numbered marker next to the part that causes it:

```js
const mark = (cx, cy) => <circle cx={cx} cy={cy} r='10' fill='var(--cds-chart-status-critical)' fillOpacity='0.15' stroke='var(--cds-chart-status-critical)' strokeWidth='1.5'/>;
// per marker, written out by hand (literal id and number):
<g data-claude-anchor='mark-1'>{mark(210, 120)}<text data-claude-text-id='mark-1-n' x='210' y='124' textAnchor='middle' fontSize='11.5' fontWeight='600' fill={ink}>1</text></g>
```

Under the diagram: "Each red marker is a cost of this option; the numbers match the list below." Then a numbered list, one consequence per marker, and one sentence on why we chose otherwise.

## Pattern C: sequence

Lanes as vertical grid lines with 13/600 headers. Steps are horizontal arrows, each with a ringed number and a description in a text column on the right: `nx` = ring x, `tx` = text x = nx + 20. Spread rows with an explicit list, e.g. `const ys = [124, 164, …]; const y = i => ys.at(i);`, leaving +48 instead of +40 after a two-line step. One accent arrow (`strokeWidth 2`, accent marker) for the step under decision; dashed arrows for edge or header effects, explained in a subtitle. Five lanes fit at x = 52, 140, 228, 316, 404 with the text column at 460 (about 41 characters per line).

## Changing a diagram later

- Words only: `update(…, engine:"widget", payload:{"kind":"text","id":"<text id>","value":"…"})`. Publishes at once.
- Small code change: `{"kind":"draft-edit","edits":[{"quote":{"exact":"…"},"replacement":"…"}]}`, then `{"kind":"publish"}`. A staged edit nobody publishes is invisible.
- Bigger change: `{"kind":"draft","basePub":<current pub>,"code":"…"}`, keeping every text id on its words.
- Check: `read(…, engine:"widget", payload:{"kind":"screenshot"})`, as its own call.
