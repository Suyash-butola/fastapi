"""Download captions from known course embeds without controlling a browser."""
import html
import json
import os
from pathlib import Path
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).parent / "transcripts"
ROOT.mkdir(exist_ok=True)

def fetch(url):
    request = urllib.request.Request(url, headers={"Referer": "https://learn.kodekloud.com/", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")

def download(video_id):
    page = fetch(f"https://player.vimeo.com/video/{video_id}?app_id=122963")
    config = json.JSONDecoder().raw_decode(page.split("window.playerConfig = ", 1)[1])[0]
    track = next(t for t in config["request"]["text_tracks"] if t["lang"].startswith("en"))
    title = re.sub(r"[^a-zA-Z0-9_-]+", "-", config["video"]["title"])
    captions = fetch(track["url"])
    if not captions.lstrip().startswith("WEBVTT"):
        raise ValueError("Response is not WebVTT")
    (ROOT / f"{title}.en.vtt").write_text(captions, encoding="utf-8")
    lines = [html.unescape(re.sub(r"<[^>]+>", "", line)).strip() for line in captions.splitlines() if line.strip() and not line.startswith("WEBVTT") and "-->" not in line and not line.strip().isdigit()]
    (ROOT / f"{title}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Downloaded {title}")

if __name__ == "__main__":
    ids = json.loads((ROOT / "video_ids.json").read_text(encoding="utf-8"))
    failed = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks = {pool.submit(download, video_id): video_id for video_id in ids}
        for task in as_completed(tasks):
            try:
                task.result()
            except Exception as error:
                failed.append({"video_id": tasks[task], "error": str(error)})
    (ROOT / "download_errors.json").write_text(json.dumps(failed, indent=2), encoding="utf-8")
    print(f"Downloaded {len(ids) - len(failed)}/{len(ids)} transcripts")
    if failed:
        raise SystemExit(1)
