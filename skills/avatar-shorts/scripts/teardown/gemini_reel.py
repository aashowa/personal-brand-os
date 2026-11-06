"""Gemini structural teardown of one Reel. usage: python3 -E gemini_reel.py VIDEO OUT_JSON"""
import sys, json, base64, os, urllib.request

video, out = sys.argv[1], sys.argv[2]
MODEL = "gemini-3.1-pro-preview"
PROMPT = """You are a short-form video editor reverse-engineering this Instagram Reel so a team can rebuild the same format.
Watch every frame and listen to the audio. Return JSON only, with these keys:
- "transcript": full verbatim voiceover.
- "hook": {"spoken": first sentence, "visual": what is on screen in the first 2 seconds, "on_screen_text": text shown}
- "beats": ordered list of {"start": sec, "end": sec, "beat": one of hook|promise|item|proof|transition|cta, "summary": short}
- "assets": ordered list of every distinct visual shown while the presenter is NOT full screen. Each: {"start": sec, "end": sec, "type": one of
   official_logo | product_ui_screen_recording | website_scroll | github_repo_page | chart_or_data | kinetic_title_card | 3d_emoji_or_icon |
   photo_of_person | third_party_video_clip | ai_generated_broll | animated_diagram | tweet_or_post_screenshot | other,
   "subject": what it shows, "likely_source": where an editor would get it (e.g. "vendor website", "GitHub README", "screen capture of app", "Apple emoji", "news clip"),
   "motion": how it moves (zoom, scale-in, highlight box, cursor, scroll, parallax, none)}
- "captions": {"style": font, case, color, position, words per chunk; note if style changes between presenter shots and full-screen asset shots}
- "audio": {"music": yes/no + vibe, "sfx": list of sound effects heard (whoosh, pop, click, etc.)}
- "cta": {"keyword": the comment keyword, "wording": exact spoken CTA, "start": sec}
- "presenter": {"look": framing, background, mic visible, wardrobe}
- "words_per_minute": number
"""

key = os.environ["GEMINI_API_KEY"]
body = {
    "contents": [{"parts": [
        {"inline_data": {"mime_type": "video/mp4", "data": base64.b64encode(open(video, "rb").read()).decode()},
         "video_metadata": {"fps": 2}},
        {"text": PROMPT}]}],
    "generationConfig": {"responseMimeType": "application/json"},
}
req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
    data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": key})
r = json.load(urllib.request.urlopen(req, timeout=600))
text = r["candidates"][0]["content"]["parts"][-1]["text"]
json.dump(json.loads(text), open(out, "w"), indent=1)
print("ok", os.path.basename(video), r.get("usageMetadata", {}).get("totalTokenCount"))
