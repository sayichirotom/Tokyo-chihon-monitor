import json, re, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET
from collections import Counter

JST = timezone(timedelta(hours=9))

QUERIES = [
    "東京地方協力本部",
    "東京地本 自衛隊",
    "自衛隊 東京 募集",
    "東京地本 説明会",
    "東京地本 採用",
]

POSITIVE = ["合格","ありがとう","すごい","良い","よかった","参加したい","かっこいい","応援","安心","丁寧","魅力"]
NEGATIVE = ["炎上","批判","問題","不安","危険","違反","苦情","疑問","反対","迷惑","不適切","個人情報","保全"]
STOPWORDS = set("東京 東京地本 自衛隊 自衛官 募集 採用 記事 公開 情報 ニュース について ため より こと これ それ".split())

def fetch_rss(query):
    url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(query) + "&hl=ja&gl=JP&ceid=JP:ja"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()

def clean(s):
    s = re.sub(r"<.*?>", "", s or "")
    return re.sub(r"\s+", " ", s).strip()

def sentiment(text):
    p = sum(w in text for w in POSITIVE)
    n = sum(w in text for w in NEGATIVE)
    if n > p: return "否定"
    if p > n: return "肯定"
    return "中立"

def words(text):
    return re.findall(r"[一-龥ぁ-んァ-ンA-Za-z0-9]{2,}", text)

items = []
seen = set()

for q in QUERIES:
    try:
        xml = fetch_rss(q)
        root = ET.fromstring(xml)
        for item in root.findall(".//item")[:12]:
            title = clean(item.findtext("title"))
            link = clean(item.findtext("link"))
            desc = clean(item.findtext("description"))
            pub = clean(item.findtext("pubDate"))
            key = title + link
            if key in seen: 
                continue
            seen.add(key)
            text = title + " " + desc
            items.append({
                "title": title,
                "link": link,
                "snippet": desc[:220],
                "source": "GoogleニュースRSS",
                "date": pub,
                "sentiment": sentiment(text),
                "query": q
            })
    except Exception as e:
        items.append({
            "title": f"収集エラー: {q}",
            "link": "",
            "snippet": str(e),
            "source": "system",
            "date": datetime.now(JST).isoformat(),
            "sentiment": "中立",
            "query": q
        })

counter = Counter()
for i in items:
    for w in words(i["title"] + " " + i["snippet"]):
        if w not in STOPWORDS and len(w) >= 2:
            counter[w] += 1

counts = Counter(i["sentiment"] for i in items)
summary = (
    f"本日は公開情報から{len(items)}件を取得しました。"
    f"肯定{counts['肯定']}件、中立{counts['中立']}件、否定{counts['否定']}件です。"
    "否定・リスク語を含む項目は、件名、発信元、文脈を確認してください。"
)

data = {
    "updated": datetime.now(JST).strftime("%Y-%m-%d %H:%M JST"),
    "summary": summary,
    "keywords": [w for w, c in counter.most_common(15)],
    "items": items
}

with open("data/results.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
