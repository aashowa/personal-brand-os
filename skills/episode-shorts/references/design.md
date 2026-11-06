# Design: zones, blocks, beat patterns

## Zones (1080×1920)
| Zone | Use |
|---|---|
| y 0–110 | Platform UI (search, back). Nothing important. |
| y 110–900, x 48–1032 | Top-half content. Footage cards: `WIDE` (48, 236, 984×554, 16:9) or `SQUARE` (105, 110, 870×768). |
| y 790–1030 | Seam caption band. In split beats keep headlines out of it. |
| y 960–1920 | Camera. Right ~15 % and bottom ~20 % sit under the Shorts/Reels UI. |
| Full-screen beats | Captions move to y 1260, so keep 1240–1400 clear. Instagram covers the top 230 px, below 1440 and the lower right 230 px: keep text out of those (avatar-shorts format.md § Safe zone). |

## Block helpers (`s.` in a spec; each returns `(id, html)` unless noted)
| Helper | What it makes | Motion to pair |
|---|---|---|
| `s.foot(t0, t1, v5_range, (x0, y0, w), "wide"/"square", label, push=1.06, enter=True)` | Real footage card. Returns `(id, frame_html, rect)`; the video layer is added for you | card in + slow push built in |
| `s.photo(file, rect)` | Real photo card (`<shorts>/photos/`) | `s.card_in([f"#{id}"], t)` + `s.push(f"#{id}i", t0, t1, 1.1)` |
| `s.logo(file, size, label, style)` | White logo tile with ink border, label under | `s.pop` |
| `s.chip(text, kind, style)` | Mono label. Kinds: `y` marker, `b` cobalt, `r` terracotta, `w` white, default ink | `s.snap` / `s.pop` |
| `s.head(html, size, style)` | Bricolage 800 headline; `<span class="mk">` = marker underline | `s.slam` |
| `.bubble` / `.bubble.me` divs | Chat bubbles (a question, a prompt) | `s.pop` |
| `.row` + `.tick` / `.cross` | Checklist rows | `s.snap(…, 260)` staggered |
| `.bar` (arrow, draw), `.strike` (inside a rotated wrapper) | Connectors, strike-throughs | `s.draw` |
| `s.typing(sel, text, t0, t1)` | Deterministic typing + typing SFX | - |
| `s.count(sel, t0, t1, a, b)` | Counter (int or 2 decimals) | - |
| `s.wipe(t)` / `s.wipe_full(t)` | Yellow wipe across the top half / whole frame: a section change or a kick | - |
| `s.cam_punch(t0, t1, 1.1–1.14)` | Snap zoom on the camera for emphasis (2–3 per Short) | - |
| `s.beat(t0, t1, html, nocap=False, full=False)` | One top-half beat; `full=True` covers the camera | - |

SFX are added by the motion helpers (pop, whoosh, impact on `sfx="impact-bass-1"`, ping, click, key-press, typing).
Pass `sfx=None` for quiet secondary entrances.

## Which element for which line
| The speaker says… | Top half |
|---|---|
| A tool or app | Its real logo, popped on the word |
| A result ("it finds every unpaid invoice") | The real result from the export, cropped tight, plus one chip with the number |
| A demo action ("open the browser to google.com") | The real footage of it, synced (`s.sync`) |
| A number or time saving | Big kinetic number; strike the old one, slam the new one (full-screen kick at the payoff) |
| A list or steps | Rows that snap in on each spoken item |
| A concept with no footage ("a skill is a page of instructions") | A native rebuild of your own slide with the exact text |
| A life or emotional line ("time with family") | A free real photo with one chip |
| A title or section change | Kicker chip ("FOUNDATION 2 / 3") + headline slam; mark `nocap` |

Motion language: fast entrances (0.35–0.5 s; power3/expo/power4 out, no bounce), holds long enough to read
(≥ 1 s for a word, ≥ 2 s for a sentence), slow pushes on footage and photos, and one wipe per section change. Decoratives
(grid drift, ghost word) are already in the template.
