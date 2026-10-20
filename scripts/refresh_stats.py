"""Refresh public GitHub data locally or in the scheduled GitHub Actions workflow."""
from pathlib import Path
from datetime import datetime, date
from zoneinfo import ZoneInfo
from collections import Counter
import json
import hashlib
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
USER = "asadbinjafor"


def fetch(url):
    headers={"User-Agent":"Asad-Profile-Builder","Accept-Language":"en-US"}
    # The built-in workflow token is sent only to GitHub's REST API.
    if urllib.parse.urlsplit(url).hostname == "api.github.com":
        headers["Accept"]="application/vnd.github+json"
        headers["X-GitHub-Api-Version"]="2022-11-28"
        if os.environ.get("GITHUB_TOKEN"):
            headers["Authorization"]="Bearer "+os.environ["GITHUB_TOKEN"]
    request=urllib.request.Request(url,headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request,timeout=30) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            if attempt==2 or exc.code not in (429,500,502,503,504):
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt==2:
                raise
        time.sleep(2 ** (attempt+1))


def parse_contributions(html):
    tips={key:int(value.replace(",","")) if value!="No" else 0
          for key,value in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>\s*([\d,]+|No) contributions? on',html)}
    days=[]
    for tag in re.findall(r'<td\b[^>]*data-date="[^"]+"[^>]*>',html):
        attrs=dict(re.findall(r'([\w-]+)="([^"]*)"',tag))
        if attrs["id"] not in tips:
            raise ValueError("GitHub's contribution markup changed; retaining existing snapshot.")
        level=int(attrs["data-level"])
        if level not in range(5):
            raise ValueError("Unexpected contribution level; retaining existing snapshot.")
        date.fromisoformat(attrs["data-date"])
        days.append({"date":attrs["data-date"],"level":level,"count":tips[attrs["id"]]})
    days.sort(key=lambda x:x["date"])
    if len({d["date"] for d in days}) != len(days):
        raise ValueError("Duplicate contribution days; retaining existing snapshot.")
    for before,after in zip(days,days[1:]):
        if (date.fromisoformat(after["date"])-date.fromisoformat(before["date"])).days != 1:
            raise ValueError("Gap in contribution history; retaining existing snapshot.")
    return days


def update_readme(content, snapshot):
    """Update generated labels and asset versions without touching personal content."""
    stamp=date.fromisoformat(snapshot["updated"])
    refreshed=datetime.fromisoformat(snapshot["updated_at"])
    status=(f'<sub>Auto-updated every 6 hours · Last refreshed: '
            f'**{stamp.day} {stamp:%B %Y}, {refreshed:%H:%M} BST (UTC+6)** · '
            'Language mix counts repositories by their primary language.</sub>')
    content=re.sub(r'<sub>(?:Activity snapshot:|Auto-updated every 6 hours).*?</sub>',status,content)
    content=re.sub(r'GitHub activity snapshot dated [^:]+:',
                   f'GitHub activity snapshot dated {stamp:%B} {stamp.day}, {stamp.year}:',content)
    days=snapshot["contributions"]
    def formatted(value):
        d=date.fromisoformat(value)
        return f"{d:%B} {d.day}, {d.year}"
    content=re.sub(r'My GitHub contribution history from .*? to .*?, with a decorative',
                   f'My GitHub contribution history from {formatted(days[0]["date"])} to {formatted(days[-1]["date"])}, with a decorative',content)
    for asset in ("stats.svg","stats-mobile.svg","activity.svg"):
        digest=hashlib.sha256((ROOT/"assets"/asset).read_bytes()).hexdigest()[:12]
        content=re.sub(r'(\./assets/'+re.escape(asset)+r')(?:\?v=[a-zA-Z0-9]+)?',
                       lambda match:match[1]+"?v="+digest,content)
    return content


def refresh():
    user_url=f"https://api.github.com/users/{USER}"
    repos_url=f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner"
    graph_url=f"https://github.com/users/{USER}/contributions"
    user=json.loads(fetch(user_url))
    repos=[]
    page=1
    while True:
        batch=json.loads(fetch(repos_url+f"&page={page}"))
        repos.extend(batch)
        if len(batch)<100:break
        page+=1
    html=fetch(graph_url)
    days=parse_contributions(html)
    if len(days)<350:
        raise ValueError("Incomplete contribution graph; retaining existing snapshot.")
    now=datetime.now(ZoneInfo("Asia/Dhaka")).replace(second=0,microsecond=0)
    if not -1 <= (now.date()-date.fromisoformat(days[-1]["date"])).days <= 2:
        raise ValueError("GitHub returned a stale contribution graph; retaining existing snapshot.")
    snapshot={
        "username":USER,"updated":now.date().isoformat(),"updated_at":now.isoformat(),
        "public_repos":user["public_repos"],"followers":user["followers"],
        "stars":sum(r["stargazers_count"] for r in repos),
        "languages":dict(Counter(r["language"] for r in repos if r["language"] and not r["fork"])),
        "contributions":days,"sources":[user_url,repos_url,graph_url],
    }
    (ROOT/"data/github-snapshot.json").write_text(json.dumps(snapshot,indent=2)+"\n",encoding="utf-8")
    subprocess.run([sys.executable,str(ROOT/"scripts/build_profile.py"),"--stats-only"],check=True)
    readme=ROOT/"README.md"
    readme.write_text(update_readme(readme.read_text(encoding="utf-8"),snapshot),encoding="utf-8")
    print(f"Refreshed {len(days)} days and {len(repos)} public repositories at {now.isoformat()}.")


if __name__=="__main__":
    refresh()
