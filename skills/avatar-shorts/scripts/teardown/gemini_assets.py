"""Gemini animated-asset inventory of one Reel. usage: python3 -I gemini_assets.py VIDEO OUT_JSON"""
import sys, json, base64, os, urllib.request
video, out = sys.argv[1], sys.argv[2]
PROMPT = """You are a motion designer cataloguing the ANIMATED ASSETS in this Instagram Reel so a team can build a reusable asset library.
An asset is any illustrated or graphic element that is not the presenter, not plain caption text, and not a raw screen recording:
mascots and characters (e.g. the pixel-art Claude Code crab), props (hats, spotlights, mics), emoji, icons, app-icon tiles, animated logos,
stickers and stamps, rebuilt UI mock-ups, diagrams, charts, mini-scenes and simulations (e.g. a game or a race), decorative frames.
Look at every frame (10 fps). Return JSON only:
{"assets": [ {"t": start sec, "end": end sec,
   "category": one of mascot_character | prop | emoji | icon_or_app_tile | animated_logo | sticker_or_stamp | ui_mockup | diagram | chart | mini_scene | decorative_frame | other,
   "what": short description (e.g. "Claude Code pixel crab", "graduation cap", "eye emoji in white app tile"),
   "style": pixel art | flat vector | 3D emoji | glossy app icon | sticker with white outline | realistic | UI | other,
   "behaviour": every way it moves or acts (e.g. "idles with a bob, blinks, multiplies into 3 copies that scatter to rows", "drops onto the crab's head"),
   "interacts_with": other assets it touches or reacts to, or null,
   "on_word": the spoken word that triggers it,
   "likely_build": how an editor most likely made it (Lottie, After Effects shape layer, SVG, vendor asset, AI image, Apple emoji, screen recording, etc.),
   "fun_factor": 1-5 how much it adds personality/fun }],
 "recurring_characters": list of characters/mascots that appear more than once and what they do,
 "asset_count": number, "fun_moments": the 3 moments with the most personality and why}"""
key = os.environ["GEMINI_API_KEY"]
body = {"contents": [{"parts": [
    {"inline_data": {"mime_type": "video/mp4", "data": base64.b64encode(open(video, "rb").read()).decode()}, "video_metadata": {"fps": 10}},
    {"text": PROMPT}]}], "generationConfig": {"responseMimeType": "application/json"}}
req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent",
    data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key})
r = json.load(urllib.request.urlopen(req, timeout=900))
json.dump(json.loads(r["candidates"][0]["content"]["parts"][-1]["text"]), open(out, "w"), indent=1)
print("ok", os.path.basename(video))
