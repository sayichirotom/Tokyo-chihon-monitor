import json, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

JST = timezone(timedelta(hours=9))
DAYS_LIMIT = 365
MAX_ITEMS = 30

QUERIES = [
    "東京地方協力本部",
    "東京地本 自衛隊",
    "自衛隊 東京 募集",
    "東京地本 説明会",
    "東京地本 採用",
]

REQUIRED_WORDS = [
    "東京地方協力本部", "東京地本", "自衛隊東京地方協力本部",
    "新小岩募集案内所", "大田出張所"
]

EXCLUDE_WORDS = [
    "海外の反応", "海外メディア", "foreign", "China", "Korea",
    "pref.miyagi.jp", "tepco.co.jp"
]

NEGATIVE_WORDS = ["炎上", "批判", "苦情", "問題", "違反", "保全", "個人情報", "SNS", "拡散", "反発", "リスク"]
POSITIVE_WORDS = ["好評", "参加", "開催", "募集", "イベント", "協力", "紹介", "見学", "体験", "説明会"]

STOPWORDS = {"nbsp", "http", "https", "the", "and", "for", "with", "東京", "自衛隊", "東京地本"}

def google_news_rss(query):
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=ja&gl=JP&ceid=JP:ja"
    with urllib.request.urlopen(url, timeout=10) as r:
        return r.read()

def parse_date(text):
    try:
        return parsedate_to_datetime(text).astimezone(JST)
    except Exception:
        return None

def clean_text(s):
    return re.sub(r"\s+", " ", s or "").strip()

def is_relevant(text):
    if any(w in text for w in EXCLUDE_WORDS):
        return False
    return any(w in text for w in REQUIRED_WORDS)

def judge_sentiment(text):
    neg = [w for w in NEGATIVE_WORDS if w in text]
    pos = [w for w in POSITIVE_WORDS if w in text]

    if neg:
        return "否定", "否定語・リスク語（" + "、".join(neg[:3]) + "）を含むため"
    if pos:
        return "肯定", "募集・イベント等の肯定語（" + "、".join(pos[:3]) + "）を含むため"
    return "中立", "肯定語・否定語が明確でなく、事実紹介中心のため"

def extract_keywords(items):
    text = " ".join(i["title"] + " " + i["snippet"] for i in items)
    words = re.findall(r"[一-龥ぁ-んァ-ヶA-Za-z0-9ー]{2,}", text)
    words = [w for w in words if w not in STOPWORDS]
    return [w for w, _ in Counter(words).most_common(12)]

def main():
    now = datetime.now(JST)
    cutoff = now - timedelta(days=DAYS_LIMIT)
    seen = set()
    items = []

    for query in QUERIES:
        try:
            root = ET.fromstring(google_news_rss(query))
            for item in root.findall(".//item"):
                title = clean_text(item.findtext("title"))
                link = clean_text(item.findtext("link"))
                snippet = clean_text(item.findtext("description"))
                pub = parse_date(item.findtext("pubDate"))

                if not title or not link:
                    continue
                if pub and pub < cutoff:
                    continue

                text = title + " " + snippet
                if not is_relevant(text):
                    continue

                key = title[:80]
                if key in seen:
                    continue
                seen.add(key)

                sentiment, reason = judge_sentiment(text)

                items.append({
                    "title": title,
                    "link": link,
                    "snippet": snippet,
                    "source": "GoogleニュースRSS",
                    "date": pub.strftime("%Y-%m-%d %H:%M") if pub else "",
                    "sentiment": sentiment,
                    "sentiment_reason": reason,
                    "query": query
                })
        except Exception:
            continue

    items.sort(key=lambda x: (x["sentiment"] != "否定", x["date"]), reverse=False)
    items = items[:MAX_ITEMS]

    counts = Counter(i["sentiment"] for i in items)
    summary = (
        f"直近{DAYS_LIMIT}日間の公開情報から{len(items)}件を抽出。"
        f"肯定{counts['肯定']}件、中立{counts['中立']}件、否定{counts['否定']}件。"
        f"判定理由を各記事に表示します。"
    )

    data = {
        "updated": now.strftime("%Y-%m-%d %H:%M"),
        "summary": summary,
        "keywords": extract_keywords(items),
        "items": items
    }

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
