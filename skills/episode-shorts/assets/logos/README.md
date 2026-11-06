# Logos (not shipped)

Brand logos are their owners' trademarks, so the kit ships none. `s.logo("<file>", ...)` in a spec looks for the file here
(kit-wide) or in the episode's `<shorts>/logos/` (episode logos win), and the build stops with a "missing" error naming
any file it can't find.

Filenames the kit's example specs use (add the ones you need):

| File | Mark |
|---|---|
| `claude_c.png` | Claude |
| `openai_c.png` | OpenAI / ChatGPT |
| `gmail_c.png` | Gmail |
| `googlesheets_c.png` | Google Sheets |
| `googledrive_c.png` | Google Drive |
| `googleads_c.png` | Google Ads |
| `google.svg` | Google "G" |
| `chrome.svg` | Google Chrome |
| `meta_c.png` | Meta |
| `quickbooks_c.png` | QuickBooks |
| `obsidian_c.png` | Obsidian |
| `notion.svg` | Notion |
| `canva.svg` | Canva |
| `microsoft-word.svg` | Microsoft Word |
| `markdown-light.svg` | Markdown mark |
| `toast_wordmark.png` | Toast (wordmark, wide) |

Format: `*_c.png` is the full-colour mark on a transparent background, square, 512×512; `.svg` files are the official
vector marks. The tile shows the logo at 62% of its size on white, so a mark with its own white or square background
looks wrong: use the bare glyph.

Where to get them:
- [svgl.app](https://svgl.app) and [Simple Icons](https://simpleicons.org) for SVG marks (check each brand's own usage
  rules; Simple Icons lists them).
- The brand's official press or brand-assets page for a colour PNG, then export at 512×512 with transparency.
- Use a logo only to show the real tool you used on screen, never to suggest an endorsement.
