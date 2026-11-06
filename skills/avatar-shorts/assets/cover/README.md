# Cover references (you add these)

`scripts/cover.py` sends these to the image model with each Reel's own logos and background. None are shipped: they
show a real person.

- `template.png`: your approved cover layout, about 1536x2736 (9:16). Every cover copies its composition, not its
  background: Nick Saraev's layout (a wordmark on top, your face between two tilted white icon tiles, a dark bottom
  third, a two-line title) with the title treatment the prompt describes: a small yellow monospace tag, a white line,
  then a near-black line on a yellow marker band. To make your first one, mock it up in any image editor with your own
  photo, or generate a version with any image model from your photo and this description, and keep the one you like.
- Identity stills, one per avatar slot: a sharp frame of that look (mouth closed, the outfit it wears in the video), at
  least 1080 px tall. `cover.py` takes `config.json` `heygen.avatars.<slot>.still` (a path relative to the repo root),
  else `assets/cover/<slot>.jpg`, so the cover wears the video's outfit. A HeyGen preview still or a frame from the
  avatar's own render both work.
- Optional: a `style-ref.jpg` of the cover that inspired your layout, for your own reference. `cover.py` never sends it.

`cover.py` stops with the list of missing files before it spends any credits.
