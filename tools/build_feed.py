#!/usr/bin/env python3
"""Build a podcast RSS feed for The Playlist Rundown.

Scans /mnt/project-files/pod-runs/<date>/playlist-rundown-<date>.mp3, copies each
MP3 into site/episodes/, and writes site/feed.xml + site/index.html.
Titles/descriptions come from episodes.json when present, otherwise from the
first paragraph and episode table of that run's playlist-summaries.md.

  python3 build_feed.py --base-url https://example.github.io/rundown-feed
"""
import argparse, datetime as dt, email.utils, glob, html, json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = "/mnt/project-files/pod-runs"

def duration(p):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "default=nw=1:nk=1", p]).decode().strip()
    return int(float(out))

def hms(s):
    return f"{s//3600}:{s%3600//60:02d}:{s%60:02d}" if s >= 3600 else f"{s//60}:{s%60:02d}"

def plain(md):
    md = re.sub(r"\*\*(.+?)\*\*", r"\1", md)
    md = re.sub(r"`(.+?)`", r"\1", md)
    return md.replace("\\|", "|").strip()

def auto_meta(date):
    p = os.path.join(RUNS, date, "playlist-summaries.md")
    lines = open(p).read().splitlines() if os.path.exists(p) else []
    paras, cur = [], []
    for l in lines[1:]:
        if l.strip() == "":
            if cur: paras.append(" ".join(cur)); cur = []
        elif not l.startswith(("|", "#")):
            cur.append(l.strip())
    shows = []
    for l in lines:
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", l)]
        if len(cells) > 4 and cells[1].isdigit():
            shows.append(f"{plain(cells[2])}: {plain(cells[3])}")
    d = dt.date.fromisoformat(date)
    return {"title": f"The Playlist Rundown, {d.strftime('%a %b')} {d.day}",
            "summary": plain(paras[0]) if paras else "", "shows": shows}

def build(base):
    base = base.rstrip("/")
    meta = json.load(open(os.path.join(HERE, "episodes.json"))) if os.path.exists(os.path.join(HERE, "episodes.json")) else {}
    site = os.path.join(HERE, "site"); os.makedirs(os.path.join(site, "episodes"), exist_ok=True)
    items = []
    for mp3 in sorted(glob.glob(os.path.join(RUNS, "*", "playlist-rundown-*.mp3"))):
        date = re.search(r"(\d{4}-\d{2}-\d{2})\.mp3$", mp3).group(1)
        name = f"playlist-rundown-{date}.mp3"; dst = os.path.join(site, "episodes", name)
        if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(mp3):
            shutil.copyfile(mp3, dst)
        m = {**auto_meta(date), **meta.get(date, {})}
        secs = duration(dst)
        # publish at 07:00 UTC on the run date unless overridden
        pub = dt.datetime.fromisoformat(m.get("published", f"{date}T07:00:00+00:00"))
        desc_txt = m["summary"] + ("\n\nShows covered:\n" + "\n".join("- " + s for s in m["shows"]) if m["shows"] else "")
        desc_html = f"<p>{html.escape(m['summary'])}</p>" + (
            "<p>Shows covered:</p><ul>" + "".join(f"<li>{html.escape(s)}</li>" for s in m["shows"]) + "</ul>" if m["shows"] else "")
        items.append(dict(date=date, title=m["title"], url=f"{base}/episodes/{name}", size=os.path.getsize(dst),
                          secs=secs, pub=pub, txt=desc_txt, html=desc_html, summary=m["summary"]))
    items.sort(key=lambda i: i["pub"], reverse=True)
    x = html.escape
    now = email.utils.format_datetime(dt.datetime.now(dt.timezone.utc))
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" '
           'xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom" '
           'xmlns:podcast="https://podcastindex.org/namespace/1.0">',
           '<channel>',
           '<title>The Playlist Rundown</title>',
           f'<link>{base}/</link>',
           f'<atom:link href="{base}/feed.xml" rel="self" type="application/rss+xml"/>',
           '<language>en-us</language>',
           '<description>A two-host audio rundown of the podcasts in my playlist: each episode boils a batch of shows down into one conversation. AI-generated summaries and voices; names and figures come partly from automatic transcripts.</description>',
           '<itunes:summary>A two-host audio rundown of the podcasts in my playlist, generated with AI.</itunes:summary>',
           '<itunes:author>The Playlist Rundown</itunes:author>',
           f'<itunes:image href="{base}/cover.jpg"/>',
           f'<image><url>{base}/cover.jpg</url><title>The Playlist Rundown</title><link>{base}/</link></image>',
           '<itunes:category text="News"><itunes:category text="Tech News"/></itunes:category>',
           '<itunes:explicit>false</itunes:explicit>',
           '<itunes:type>episodic</itunes:type>',
           '<itunes:block>Yes</itunes:block>',
           '<podcast:locked>yes</podcast:locked>',
           f'<lastBuildDate>{now}</lastBuildDate>']
    for i in items:
        out += ['<item>',
                f'<title>{x(i["title"])}</title>',
                f'<description>{x(i["txt"])}</description>',
                f'<content:encoded><![CDATA[{i["html"]}]]></content:encoded>',
                f'<itunes:summary>{x(i["summary"])}</itunes:summary>',
                f'<enclosure url="{i["url"]}" length="{i["size"]}" type="audio/mpeg"/>',
                f'<guid isPermaLink="false">playlist-rundown-{i["date"]}</guid>',
                f'<pubDate>{email.utils.format_datetime(i["pub"])}</pubDate>',
                f'<itunes:duration>{i["secs"]}</itunes:duration>',
                '<itunes:episodeType>full</itunes:episodeType>',
                '<itunes:explicit>false</itunes:explicit>',
                '</item>']
    out += ['</channel>', '</rss>']
    open(os.path.join(site, "feed.xml"), "w").write("\n".join(out) + "\n")
    rows = "".join(f'<li><a href="episodes/playlist-rundown-{i["date"]}.mp3">{x(i["title"])}</a> ({hms(i["secs"])})</li>' for i in items)
    open(os.path.join(site, "index.html"), "w").write(
        f'<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex"><meta name="viewport" content="width=device-width">'
        f'<title>The Playlist Rundown</title><body style="font-family:system-ui;max-width:640px;margin:2em auto;padding:0 16px">'
        f'<img src="cover.jpg" width="200" alt=""><h1>The Playlist Rundown</h1>'
        f'<p>Subscribe in a podcast app with: <code>{base}/feed.xml</code></p><ul>{rows}</ul>')
    open(os.path.join(site, "robots.txt"), "w").write("User-agent: *\nDisallow: /\n")
    open(os.path.join(site, ".nojekyll"), "w").write("")
    print(f"{len(items)} episodes -> {site}/feed.xml")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--base-url", required=True)
    build(ap.parse_args().base_url)
