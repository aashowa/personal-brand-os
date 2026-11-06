# Read 2 · App playbook: Palmier Pro (how)

The app-specific half of the pipeline; the look (numbers, specs) is in [the-look.md](the-look.md) and does not change per app. Another editor (Premiere, Resolve, CapCut, Final Cut) gets its own playbook file the first time it is used; until then this skill drives Palmier.

For batches of calls use `scripts/palmier_mcp.mjs` (one session per batch: open project → set timeline → calls; images saved to the cwd).

## Discovery and session targeting

Prefer native Palmier MCP tools. If the configured MCP is reachable but not exposed in the current tool catalog, use its documented HTTP endpoint. During the worked run it was `http://127.0.0.1:19789/mcp`; resolve current configuration rather than assuming that port on another machine.

Registration is not connectivity. Initialize, list tools, inspect schemas, then call `manage_project` to list/open the exact project. Call `get_timeline` and `get_media` before referencing clips/assets. A new HTTP session has its own target: **initialize → initialized notification → open project → select timeline → read state**. “Editor not available” can mean the session has no target, not that the app needs reinstalling.

This dependency-free JavaScript pattern was exercised successfully. Run it in a tool with network access, such as `ctx_execute`, and print only derived fields. Keep every dependent operation in the same session:

```javascript
const endpoint = 'http://127.0.0.1:19789/mcp'; // verify configuration
const headers = {'Content-Type':'application/json',
                 'Accept':'application/json, text/event-stream'};
let nextId = 1;
async function rpc(method, params, notification = false) {
  const body = {jsonrpc:'2.0', method, params};
  if (!notification) body.id = nextId++;
  const r = await fetch(endpoint, {
    method:'POST', headers, body:JSON.stringify(body),
    signal:AbortSignal.timeout(45000)
  });
  const session = r.headers.get('mcp-session-id');
  if (session) headers['Mcp-Session-Id'] = session;
  const raw = await r.text();
  if (!r.ok) throw Error(`MCP HTTP ${r.status}`);
  if (!raw.trim()) {
    if (notification) return;
    throw Error('Empty MCP response; outcome unknown. Inspect before retrying.');
  }
  const events = raw.split(/\r?\n\r?\n/).map(block =>
    block.split(/\r?\n/).filter(l => l.startsWith('data:'))
      .map(l => l.slice(5).trimStart()).join('\n'));
  const messages = events.filter(Boolean).map(s => JSON.parse(s));
  const out = messages.length
    ? messages.find(m => m.id === body.id) : JSON.parse(raw);
  if (!out || out.error || out.result?.isError)
    throw Error('MCP error; inspect the bounded result before another action.');
  return out.result;
}
await rpc('initialize', {protocolVersion:'2024-11-05', capabilities:{},
  clientInfo:{name:'video-edit',version:'1.0'}});
await rpc('notifications/initialized', {}, true);
const catalog = await rpc('tools/list', {});
// Read current schemas, then use:
// await rpc('tools/call', {name:'manage_project', arguments:{action:'open',path:project}});
// await rpc('tools/call', {name:'set_active_timeline', arguments:{timelineId}});
```

SSE responses can begin with `id:`, not `event:` or `data:`. Do not classify them by their first characters. Some tools return JSON encoded in a text content block; parse that block deliberately. Do not dump base64 images, whole libraries or credentials. A failed/empty mutation response stops dependent operations; read state before retrying. The snippet is a finite request helper, not a subscription client.

## Fragile editing invariants

| Situation | Correct action and reason |
|---|---|
| Duplicate a timeline | All clip/track IDs are new. Re-read before editing the copy. |
| Any tool says track indices shifted | Re-read and resolve the intended track by current identity/content. Deleting the last clip may remove its track. |
| Add overlapping clips to one track | Existing media can be overwritten, not layered. Same-time titles need separate tracks/calls. |
| Add graphics above footage | In the observed schema, omitting `trackIndex` on every entry auto-creates a new visual track; confirm that behavior in the live schema. Never reuse an old numeric index after deleting a graphic track. |
| Silence/filler removal | Linked partners are cut and gaps closed. Other tracks may shift or be split; inspect graphics and narration after the operation. |
| Animation split by word edits | Restore one continuous source animation, align to the revised beat, and retime it slightly if needed. Do not retain accidental jumps inside it. |
| Exact frame range | Use half-open `[start,end)` project frames. `source:[a,b]` is source seconds; trims are source offsets measured in project-frame units. Verify schema. |
| Replace a source | `swap_clip_media` preserves timing/effects/framing. Reset inherited crop/transform when replacement dimensions differ. Compatible media type and sufficient source duration are required. |
| Show the presenter | Split/remove only overlay windows, without ripple deletion of the speech. Underlying footage then appears. |
| Cover the presenter | Add or extend the intended overlay on an upper track for the exact interval. Preserve the speech beneath it; check the visual before and after the cover. |
| Bad placement accidentally overwrites narration | Stop. Confirm the most recent actions are yours before using shared undo; otherwise restore on a safe copy. Verify full narration and linked A/V before export. |
| Caption/CTA too large or overlapping | Inspect exported frames, reduce native font sizes and separate concurrent text tracks. HyperFrames/browser size is not a guarantee of Palmier text size. |
| Palette change at image-to-video handoff | Match media format and color metadata. A video freeze of the first frame can avoid the PNG/video color-management mismatch observed here. |
| Export queued/started | Poll that exact export job to completion, then inspect the actual file. Tool acceptance alone is not export success. |

Native `remove_words` indices come from a fresh `get_transcript` with a specific dialogue track/provider. Re-read after each word edit. `inspect_media` and `get_transcript` disagreed materially in this run; resolve disputed timing with waveform boundaries and local seam playback rather than automatically trusting either provider.

For deliberate all-video speed changes, a layered source plus one finishing transform is straightforward. If the final delivery is reimported as a single rendered clip, identify it as an assembled delivery, and preserve the layered source separately. A source timestamp and a sped-up delivery timestamp are not interchangeable.

Imported local files are referenced in place. Keep them stable; when packaging, include actual media or use the documented project-package export. Never claim a project is portable merely because its `.palmier` file exists.

Run `node scripts/check_transport.mjs` from this skill folder to exercise the documented helper against offline JSON/SSE, notification and failure fixtures. `--live` additionally makes only the initialize/list-tools calls against the locally configured example endpoint; inspect/update that endpoint first if configuration differs.

## Long-form lessons: verified behaviour

| Situation | What works |
|---|---|
| OBS HEVC long-GOP source | Palmier's renderer dropped random stretches to black, even in full-res captures. Before placing clips, make an intermediate (`ffmpeg -hwaccel videotoolbox -i SRC -c:v h264_videotoolbox -b:v 16M -g 30 -bf 0 -profile:v high -pix_fmt yuv420p -c:a copy OUT`) and `swap_clip_media` every clip to it. Check frame alignment (offset 0) first. `footage_health.py` flags this at intake. |
| MCP stops answering (header timeout) | Memory pressure during a heavy transcode. Check `project.json` holds the last edits (autosave), quit and relaunch Palmier, re-open the session. Don't run 4K transcodes while editing. |
| Import of a freshly written file on the iCloud-synced Desktop | `import_media` ran past the 300 s client timeout and left an asset with duration 0 that `add_clips` can't trim ("needs a known source length"). The same file cloned into the episode folder (not iCloud) imported `ready`. Write new intermediates outside Desktop/Documents, import from there, delete the dead asset with `organize_media`. |
| Zoom keyframes | `position` = top-left, `scale` = normalised width/height (not a factor). For an eased move write dense `linear` rows sampled from an ease curve; `smooth` behaves like a spline and overshoots holds. `zooms.py` writes them per clip piece from a shot list. |
| Speed | `edit_speed` refuses nested timelines; per-clip speed breaks keyframed zooms/graphics. Apply speed once at Final (`finish.py`). |
| Pause/filler cuts | `remove_silence` needs a cached `get_transcript`, which may pick cloud transcription and spend credits. Instead: `speech_gaps.py` → `ripple_delete_ranges` with `trackIndex` = Dialogue, all ranges in one call (pre-cut coordinates). |
| What a ripple cut does | Linked camera/screen/dialogue cut together; masks and zoom keyframes stay attached to content (verified side by side). Overlays on other tracks are split at the cut: rejoin split graphics (remove the second piece, extend the first, re-key). Exclude ranges under a pre-timed music stem. |
| Transparency | PNG and ProRes 4444 alpha both composite correctly. A new image clip is fitted to the canvas: set keyframes/transform to its native normalised size. |
| Highlighter that follows a zoom | Full-canvas PNG with the rectangle drawn at the text's SOURCE position, the same scale/position keyframes as the zoomed clip (frame-shifted), `blendMode: multiply`. `crop` keyframes act as a mask: animating the right inset gives a left-to-right wipe. |
| Swap to a smaller intermediate | `swap_clip_media` keeps timing, keyframes and normalised transforms; a 1080p corner-camera file replaces a 4K one without re-framing. Same duration required. |
| Tracks | `add_clips` without `trackIndex` creates a new top track (one per overlap slot); an emptied track disappears; `manage_tracks` reorder by `trackId`; name every track. |
| Frame-exact placement | `add_clips` `source` seconds are floored to frames, so `frame/30` can land one frame early; a 1-frame overlap then sends that clip's linked audio to a new A2 track (removing A2 deletes it). Pass `(frame + 0.5) / fps` and compare the placed `frames`/`trimStartFrame` with the plan. |
| Checking frames | `inspect_timeline` returns a 512 px composite with a grid: enough for layout and motion sequences. `capture_frame` adds a library asset; delete test assets with `organize_media {"deletes": [...]}` (also deletes timelines). |
| Paid generation | Dry run first (free). Observed prices (check current ones): ElevenLabs Music v2.5, 40 s instrumental = 8 credits; Lyria 3 Pro 8; MiniMax 3. Ask with the number before the real call. |
| Captions from your own SRT | `import_media` the .srt (type subtitle), then `add_captions {subtitleMediaRef}` (no transcription, no credits) and style the group with `update_text {captionGroupId, style, transform}`. The last cue can run past the video end: trim it. `get_timeline {captionDetail: true}` shows at most 200 caption rows and NOT in time order: page with startFrame/endFrame before editing one caption, or you stretch the wrong caption. |
| Audio polish without an in-app compressor | Process the dialogue offline (highpass, gentle compression, gain, limiter), remux it with the SAME video stream (`-c:v copy`, PCM audio in .mov), import, and `swap_clip_media` the dialogue clips (linked screen clips follow). Raise music clips by the same measured gain to keep an approved balance. |
| Grade | `inspect_color` → `apply_color` on one clip → re-inspect → copy the returned `color` object to every other clip of that camera (`apply_color {clipIds, color}`). `hueCurves.targets` need `targetHue`. |
| Privacy masks | Rectangle masks live on the clip, in SOURCE coordinates (zooms don't move them), and have no keyframes. For scrolling content, `split_clips` at each content change and give each piece its own boxes (`privacy_scan.py` → `--splits` → `--ops` → `masks_apply.mjs`). Splits copy the masks to both halves. Removing a track (`manage_tracks {remove: [{trackId}]}`) deletes its clips, captions included. |
| Long batches and memory | Every new MCP session's `manage_project open` adds a "Now editing" line to Palmier's chat panel, so run batches in ONE long-lived session (a node loop, as in the mask apply). Check `sysctl vm.swapusage` before big batches: with swap nearly full (observed: 17.5 of 18.4 GB, about 1,300 clips and 1,800 masks) the app stalls in UI layout and MCP calls time out. Free memory, or quit after an autosave and reopen. |
| Export | `export_project` writes H.264 at about 11.7 Mb/s at 4K (no bitrate option; small screen text stays sharp); a 17:50 timeline at 4K took ~19 min. ProRes for that timeline would need ~90 GB. Poll `manage_exports` in one session about once a minute; the partial file is a hidden `.name-UUID.partial.mp4` until done. |
