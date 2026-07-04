import json, re, sys
from datetime import datetime, timezone, timedelta
from urllib.parse import quote
from urllib.request import urlopen, Request
from xml.etree import ElementTree as ET

JST = timezone(timedelta(hours=9))
QUERIES = [
    "東京地本", "自衛隊東京地方協力本部", "東京地方協力本部",
    "自衛隊 東京 募集", "東京地本 自衛隊", "防衛大学校 東京地本",
]
POS = ["良い","すごい","かっこいい","応援","安心","魅力","感謝","楽しみ","合格","頑張"]
NEG = ["問題","不安","批判","炎上","疑問","危険","不適切","苦情","最悪","反対"]

def clean(s):
    s = re.sub(r"<.*?>", "", s or "")
    return re.sub(r"\s+", " ", s).strip()

def sentiment(text):
    p = sum(w in text for w in POS)
    n = sum(w in text for w in NEG)
    if p > n: return "positive"
    if n > p: return "negative"
    return "neutral"

def google_news(query):
    url = f"https://news.google.com/rss/search?q={quote(query)}&hl=ja&gl=JP&ceid=JP:ja"
    req = Request(url, headers={"User-Agent":"Mozilla/5.0"})
    with urlopen(req, timeout=20) as r:
        root = ET.fromstring(r.read())
    for item in root.findall(".//item")[:10]:
        title = clean(item.findtext("title"))
        link = clean(item.findtext("link"))
        pub = clean(item.findtext("pubDate"))
        desc = clean(item.findtext("description"))
        text = title + " " + desc
        yield {"title": title, "source":"Google News RSS", "url":link, "published":pub, "sentiment":sentiment(text), "snippet":desc[:220]}

def main():
    seen, items = set(), []
    for q in QUERIES:
        try:
            for it in google_news(q):
                key = it["url"] or it["title"]
                if key not in seen:
                    seen.add(key); items.append(it)
        except Exception as e:
            print(f"WARN {q}: {e}", file=sys.stderr)
    text = " ".join(i["title"] + " " + i.get("snippet","") for i in items)
    words = [w for w in re.findall(r"[一-龥ぁ-んァ-ンA-Za-z0-9]{2,}", text) if w not in {"Google","News","RSS","東京","自衛隊"}]
    freq = {}
    for w in words: freq[w] = freq.get(w,0)+1
    keywords = [w for w,_ in sorted(freq.items(), key=lambda x:x[1], reverse=True)[:12]] or QUERIES[:4]
    counts = {s:sum(1 for i in items if i["sentiment"]==s) for s in ["positive","neutral","negative"]}
    summary = f"本日は{len(items)}件を取得。肯定{counts['positive']}件、中立{counts['neutral']}件、否定{counts['negative']}件。否定が増えた場合は該当記事を確認してください。"
    out = {"generated_at": datetime.now(JST).strftime("%Y-%m-%d %H:%M JST"), "summary":summary, "keywords":keywords, "items":items}
    with open("data/report.json","w",encoding="utf-8") as f: json.dump(out,f,ensure_ascii=False,indent=2)

if __name__ == "__main__": main()
