# Diagrams (real Excalidraw, brand colors)

New diagram: copy an existing `.excalidraw` here (e.g. `sample-context-desk.excalidraw`), open it at excalidraw.com via File > Open, edit, save it back over the copy (File > Save to), then render:
`node render.mjs my-diagram.excalidraw` writes `my-diagram.png` next to it (2x, paper background, padded). It needs internet: Excalidraw 0.18.1 and its fonts load from esm.sh.

Colors:
- Canvas paper `#F7F7F5`; strokes and text ink `#111111`; secondary text pencil `#6B6B6B`; neutral box fill `#FFFFFF`
- Marker yellow `#FFD43B`: highlight or sticky fill only, never text
- Side A: stroke `#C4501B`, fill `#F6E3D8`. Side B: stroke `#2251D1`, fill `#DDE5FA` (see `../brand-sheet.html`)

Style: fill solid, stroke width 2, sloppiness "artist" (roughness 1), font Excalifont (id 5), rounded rectangles.
Labels: max about 4 words per box, sentence case, no em dashes. Put highlight rectangles behind text (Send to back). Highlight words as a separate text element, not text bound to a box: Excalidraw paints a box's own text right after the box, so a highlight behind bound text ends up on top of it.
Text should read on a 1920x1080 slide: labels 40, sub-labels 28, titles 60+.
A set of diagrams for one episode: a map (the whole video on one page) plus one diagram per chapter, named `epNN-<what>.excalidraw`. For many diagrams at once, write a small generator script that builds the scenes in code (`linkedin/creative/diagrams.mjs` shows how) instead of drawing each by hand.
Full-screen slide: keep the scene at 1824x984 with a transparent rectangle fixing the bounds, so render.mjs's padding brings it to exactly 16:9 (3840x2160). After re-rendering, copy the PNG into the episode's `excalidraw/` folder if your deck uses copies.
