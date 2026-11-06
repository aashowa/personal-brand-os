"""Gemini motion-graphics teardown of one Reel. usage: python3 -I gemini_motion.py VIDEO OUT_JSON  (GEMINI_API_KEY in env)"""
import sys, json, base64, os, urllib.request

video, out = sys.argv[1], sys.argv[2]
MODEL = "gemini-3.1-pro-preview"
PROMPT = """You are a senior motion designer reverse-engineering the MOTION GRAPHICS of this Instagram Reel so a developer can
rebuild every animation in GSAP/HTML. Ignore the script and topic. Look at every frame (sampled at 10 fps) and listen for sound effects.

Return JSON only, with these keys:
- "events": ordered list of EVERY animation event (an element entering, exiting, moving, or a transition between shots). Each:
  {"t": start sec, "dur": seconds the motion takes until it settles (be precise: count frames at 10 fps),
   "layout": "face" | "split" | "graphic" (graphic = full-screen asset, presenter hidden),
   "element": what moves (e.g. "Claude logo", "headline 'FREE'", "screen recording card", "whole frame", "presenter camera", "arrow", "caption word"),
   "kind": one of entrance | exit | emphasis | transition | camera | idle | text | data,
   "animation": short name, prefer this vocabulary and invent a new snake_case name only if none fits:
      scale_in_overshoot, scale_in_smooth, scale_out, fade_in, fade_out, slide_in_left/right/up/down, slide_out_*, blur_in, drop_in_bounce,
      rotate_in, flip_3d, pop_stagger (several items one after another), mask_reveal (wipe/clip reveal), line_draw (stroke draws on),
      highlight_box_draw, underline_draw, circle_draw, arrow_draw, cursor_move_click, typewriter, word_by_word_text, letter_by_letter_text,
      number_count_up, bar_grow, chart_line_draw, zoom_punch (fast scale-up), slow_push_in (ken burns), slow_pull_out, pan/scroll,
      parallax_layers, orbit (items circling a centre), pulse/glow, shake, whip_pan, zoom_transition (zoom through into next shot),
      flash_white, glitch, hard_cut, crossfade, card_flip, screen_3d_tilt (UI card tilted in 3D perspective), split_reveal, iris, other_<name>
   "from_to": the transform in numbers where you can estimate (e.g. "scale 0->1.1->1", "x -600->0", "rotateY 30deg->0", "opacity 0->1"),
   "easing": overshoot/back | elastic/bounce | snappy ease-out (expo) | smooth ease-in-out | linear | instant,
   "stagger": seconds between items if several items animate in sequence, else null,
   "sync": what triggers it: the exact spoken word it lands on, or "beat"/"cut"/"none",
   "sfx": the sound effect on it if any (whoosh, pop, click, ding, swoosh-riser, typing, camera-shutter, boom...) or null,
   "style": one line on the look of the element (colour, shadow, border, rounded corners, glow, background behind it)}
- "backgrounds": list of distinct full-screen backgrounds used under graphics (colour, gradient, grid, blur of the previous shot, texture, motion of the background itself).
- "transitions_between_shots": counts by type, e.g. {"hard_cut": 20, "zoom_punch": 5, "whip_pan": 1}.
- "presenter_camera_moves": list of {t, move, from_to, dur} for zooms/punches/reframes on the presenter shot.
- "text_animation": how on-screen headline text (not the burnt-in captions) animates in and out, with typical duration.
- "captions_motion": how the running captions animate per word/chunk (pop, scale, colour highlight of the active word, etc.).
- "idle_motion": does anything keep moving while on screen (slow zoom on screenshots, floating, rotating, pulsing)? With rate.
- "layering": how many layers are typically stacked in a full-screen graphic (background, card, logo, text, sticker...), drop shadows, depth.
- "signature_moves": the 5 most distinctive, repeatable animation moves of this editor, each with a one-line GSAP recipe
   (e.g. "logo slam: gsap.fromTo(el,{scale:0,rotation:-15},{scale:1,rotation:0,duration:0.35,ease:'back.out(2)'}) + pop sfx").
- "avg_seconds_between_animation_events": number.
"""

key = os.environ["GEMINI_API_KEY"]
body = {
    "contents": [{"parts": [
        {"inline_data": {"mime_type": "video/mp4", "data": base64.b64encode(open(video, "rb").read()).decode()},
         "video_metadata": {"fps": 10}},
        {"text": PROMPT}]}],
    "generationConfig": {"responseMimeType": "application/json"},
}
req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
    data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key})
r = json.load(urllib.request.urlopen(req, timeout=900))
text = r["candidates"][0]["content"]["parts"][-1]["text"]
json.dump(json.loads(text), open(out, "w"), indent=1)
print("ok", os.path.basename(video), r.get("usageMetadata", {}).get("totalTokenCount"))
