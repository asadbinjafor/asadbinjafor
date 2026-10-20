"""Refresh public GitHub metadata; no token, account permissions or scheduled job required."""
from pathlib import Path
from datetime import datetime, date
from zoneinfo import ZoneInfo
from collections import Counter
import json
import re
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
USER = "asadbinjafor"


def fetch(url):
    request=urllib.request.Request(url,headers={"User-Agent":"Asad-Profile-Builder"})
    with urllib.request.urlopen(request,timeout=30) as response:
        return response.read().decode("utf-8")


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
    tips={key:int(value.replace(",","")) if value!="No" else 0
          for key,value in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>\s*([\d,]+|No) contributions? on',html)}
    days=[]
    for tag in re.findall(r'<td\b[^>]*data-date="[^"]+"[^>]*>',html):
        attrs=dict(re.findall(r'([\w-]+)="([^"]*)"',tag))
        if attrs["id"] not in tips:
            raise ValueError("GitHub's contribution markup changed; retaining existing snapshot.")
        days.append({"date":attrs["data-date"],"level":int(attrs["data-level"]),"count":tips[attrs["id"]]})
    if len(days)<350:
        raise ValueError("Incomplete contribution graph; retaining existing snapshot.")
    days.sort(key=lambda x:x["date"])
    snapshot={
        "username":USER,"updated":datetime.now(ZoneInfo("Asia/Dhaka")).date().isoformat(),
        "public_repos":user["public_repos"],"followers":user["followers"],
        "stars":sum(r["stargazers_count"] for r in repos),
        "languages":dict(Counter(r["language"] for r in repos if r["language"] and not r["fork"])),
        "contributions":days,"sources":[user_url,repos_url,graph_url],
    }
    (ROOT/"data/github-snapshot.json").write_text(json.dumps(snapshot,indent=2)+"\n",encoding="utf-8")
    readme=ROOT/"README.md"
    content=readme.read_text(encoding="utf-8")
    stamp=date.fromisoformat(snapshot["updated"])
    content=re.sub(r'Activity snapshot: \*\*[^*]+\*\*',
                   f'Activity snapshot: **{stamp.day} {stamp:%B %Y}**',content)
    content=re.sub(r'GitHub activity snapshot dated [^:]+:',
                   f'GitHub activity snapshot dated {stamp:%B} {stamp.day}, {stamp.year}:',content)
    start=date.fromisoformat(days[0]["date"])
    end=date.fromisoformat(days[-1]["date"])
    def formatted(d):
        return f"{d:%B} {d.day}, {d.year}"
    content=re.sub(r'My GitHub contribution history from .*? to .*?, with a decorative',
                   f'My GitHub contribution history from {formatted(start)} to {formatted(end)}, with a decorative',content)
    readme.write_text(content,encoding="utf-8")
    subprocess.run([sys.executable,str(ROOT/"scripts/build_profile.py")],check=True)


if __name__=="__main__":
    refresh()
