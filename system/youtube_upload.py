#!/usr/bin/env python3
"""Upload a video to your YouTube channel (config.json "youtube.channel_handle"). Unlisted unless told otherwise.

    python3 system/youtube_upload.py auth
    python3 system/youtube_upload.py upload <file.mp4> --title "..." [--description-file d.txt]
        [--tags a,b,c] [--privacy unlisted|private|public] [--publish-at 2026-10-20T17:00:00Z]
        [--ai] [--thumbnail t.jpg] [--go]
    python3 system/youtube_upload.py status <video_id>
    python3 system/youtube_upload.py selftest

auth: one-time browser consent. Sign in with the Google account that owns your channel and pick
that channel; the refresh token lands in .env as YOUTUBE_OAUTH_REFRESH_TOKEN (keep a copy where
you keep your other secrets). Needs YOUTUBE_OAUTH_CLIENT_ID and YOUTUBE_OAUTH_CLIENT_SECRET.
upload: dry-run by default, --go uploads. Refuses unless the token's channel handle is
youtube.channel_handle (one Google account can hold several channels).

config.json "youtube": channel_handle ("@yourhandle"), description_footer (lines added under
every description: a string or a list of lines), default_tags (used when a video has none),
category_id (default "27", Education).

Gotchas baked in:
- the API defaults privacyStatus to PUBLIC and ignores Studio upload defaults, so every
  upload sets privacy, madeForKids=false and containsSyntheticMedia explicitly
- --ai marks AI-avatar videos as altered/synthetic; real-camera footage stays unmarked
- Google's docs disagree on whether unverified API projects get locked to private, so
  the upload reads its privacy back and says if Google changed it
- make the OAuth client a Desktop app and set its consent screen to Internal (Google Workspace)
  or In production: a refresh token from a Testing-mode app expires after 7 days
"""

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config.json"
YT = (json.loads(CONFIG.read_text()) if CONFIG.exists() else {}).get("youtube") or {}
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.readonly",
          "https://www.googleapis.com/auth/youtube",  # edit status/publishAt after upload (schedule.py reslot)
          "https://www.googleapis.com/auth/youtube.force-ssl",  # post comments (pinning stays manual; the API has no pin)
          "https://www.googleapis.com/auth/yt-analytics.readonly"]  # numbers for the test log
TOKEN_URI = "https://oauth2.googleapis.com/token"
# Mirrors Studio > Settings > Upload defaults, which API uploads ignore.
_footer = YT.get("description_footer") or ""
FOOTER = "\n\n---\n" + (_footer if isinstance(_footer, str) else "\n".join(_footer)) if _footer else ""
DEFAULT_TAGS = YT.get("default_tags") or []
CATEGORY = str(YT.get("category_id", "27"))  # 27 = Education; match your Studio upload default


def env_value(key, required=True):
    if os.environ.get(key):  # an env var already set wins over .env
        return os.environ[key]
    env = REPO / ".env"
    for line in (env.read_text().splitlines() if env.exists() else []):
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"')
    if required:
        sys.exit(f"{key} is not in .env")
    return None


def set_env(key, value):
    path = REPO / ".env"
    lines = path.read_text().splitlines() if path.exists() else []
    lines = [l for l in lines if not l.startswith(f"{key}=")] + [f"{key}={value}"]
    path.write_text("\n".join(lines) + "\n")


def client_config():
    return {"installed": {"client_id": env_value("YOUTUBE_OAUTH_CLIENT_ID"),
                          "client_secret": env_value("YOUTUBE_OAUTH_CLIENT_SECRET"),
                          "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                          "token_uri": TOKEN_URI, "redirect_uris": ["http://localhost"]}}


def youtube(creds):
    from googleapiclient.discovery import build
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def saved_creds():
    from google.oauth2.credentials import Credentials
    cfg = client_config()["installed"]
    return Credentials(None, refresh_token=env_value("YOUTUBE_OAUTH_REFRESH_TOKEN"),
                       token_uri=TOKEN_URI, client_id=cfg["client_id"],
                       client_secret=cfg["client_secret"])  # refresh with whatever scopes were granted


def check_channel(yt):
    handle = YT.get("channel_handle") or sys.exit('set youtube.channel_handle (e.g. "@yourhandle") in config.json')
    want = "@" + handle.lstrip("@").lower()
    items = yt.channels().list(part="snippet", mine=True).execute().get("items", [])
    got = (items[0]["snippet"].get("customUrl") or "").lower() if items else None
    title = items[0]["snippet"]["title"] if items else "none"
    return got == want, f"{title} ({got})", want


def build_body(title, description, tags, privacy, ai, publish_at=None):
    if publish_at and privacy != "private":
        sys.exit("--publish-at needs --privacy private (YouTube makes it public at that time)")
    status = {"privacyStatus": privacy, "selfDeclaredMadeForKids": False,
              "containsSyntheticMedia": ai}
    if publish_at:
        status["publishAt"] = publish_at
    return {"snippet": {"title": title, "description": description + FOOTER,
                        "tags": tags or DEFAULT_TAGS, "categoryId": CATEGORY, "defaultLanguage": "en",
                        "defaultAudioLanguage": "en"},
            "status": status}


def cmd_auth(_):
    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_config(client_config(), SCOPES)
    # select_account forces the channel picker; without it Google may silently use the
    # account's default channel
    creds = flow.run_local_server(port=0, open_browser=False, prompt="select_account consent",
                                  access_type="offline",
                                  authorization_prompt_message="Open this URL to authorize:\n{url}\n")
    ok, got, want = check_channel(youtube(creds))
    if not ok:
        sys.exit(f"Authorized channel is {got}, expected {want}. Run auth again and pick {want}.")
    set_env("YOUTUBE_OAUTH_REFRESH_TOKEN", creds.refresh_token)
    print(f"Authorized for {got}. Refresh token saved to .env (keep a copy with your other secrets).")


def cmd_upload(a):
    from googleapiclient.http import MediaFileUpload
    video = Path(a.file)
    if not video.is_file():
        sys.exit(f"No such file: {video}")
    desc = Path(a.description_file).read_text() if a.description_file else ""
    tags = [t.strip() for t in a.tags.split(",") if t.strip()] if a.tags else []
    body = build_body(a.title, desc, tags, a.privacy, a.ai, a.publish_at)
    print(f"{video.name} ({video.stat().st_size / 1e6:.0f} MB) -> {a.privacy}, "
          f"AI={'yes' if a.ai else 'no'}, title: {a.title}")
    yt = youtube(saved_creds())
    ok, got, want = check_channel(yt)
    if not ok:
        sys.exit(f"Token is for {got}, not {want}. Re-run auth.")
    if not a.go:
        print(f"Dry run, target channel {got}. Add --go to upload.")
        return
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(str(video), chunksize=8 * 1024 * 1024,
                                                        resumable=True))
    resp = None
    while resp is None:
        progress, resp = req.next_chunk()
        if progress:
            print(f"  {progress.progress() * 100:.0f}%", flush=True)
    vid = resp["id"]
    if a.thumbnail:
        yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(a.thumbnail)).execute()
    print(f"Uploaded https://youtu.be/{vid}")
    report_status(yt, vid, expected=a.privacy)


def report_status(yt, vid, expected=None):
    items = yt.videos().list(part="status", id=vid).execute().get("items", [])
    if not items:
        sys.exit(f"Video {vid} not found on this channel")
    s = items[0]["status"]
    print(f"privacy={s.get('privacyStatus')} upload={s.get('uploadStatus')} "
          f"madeForKids={s.get('madeForKids')} synthetic={s.get('containsSyntheticMedia')}")
    if expected and s.get("privacyStatus") != expected:
        print(f"WARNING: requested {expected}, YouTube set {s.get('privacyStatus')} "
              "(unverified API project lock?). Change it in Studio or file the API audit.")


def cmd_status(a):
    report_status(youtube(saved_creds()), a.video_id)


def cmd_selftest(_):
    b = build_body("t", "", [], "unlisted", False)
    assert b["status"] == {"privacyStatus": "unlisted", "selfDeclaredMadeForKids": False,
                           "containsSyntheticMedia": False}
    assert b["snippet"]["description"] == FOOTER and b["snippet"]["tags"] == DEFAULT_TAGS  # the footer from config.json, or none
    assert build_body("t", "", [], "private", True, "2026-10-20T17:00:00Z")["status"]["publishAt"]
    print("selftest ok")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth").set_defaults(fn=cmd_auth)
    up = sub.add_parser("upload")
    up.add_argument("file")
    up.add_argument("--title", required=True)
    up.add_argument("--description-file")
    up.add_argument("--tags")
    up.add_argument("--privacy", choices=["unlisted", "private", "public"], default="unlisted")
    up.add_argument("--publish-at")
    up.add_argument("--ai", action="store_true", help="AI avatar / synthetic video")
    up.add_argument("--thumbnail")
    up.add_argument("--go", action="store_true")
    up.set_defaults(fn=cmd_upload)
    st = sub.add_parser("status")
    st.add_argument("video_id")
    st.set_defaults(fn=cmd_status)
    sub.add_parser("selftest").set_defaults(fn=cmd_selftest)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
