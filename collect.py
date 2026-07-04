import json, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone, timedelta
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

NEGATIVE_WORDS = [
    "炎上", "批判", "苦情", "問題", "不適切", "違反", "流出", "漏えい",
    "個人情報", "保全", "SNS", "拡散", "抗議", "謝罪", "処分", "事故"
]

POSITIVE_WORDS = [
    "好評", "参加", "開催", "募集", "説明会", "体験", "見学", "採用",
    "イベント", "協力", "紹介"
]

STOPWORDS = {
    "nbsp", "http", "https", "www", "com", "co", "jp", "go", "mod", "in",
    "the", "and", "for", "with", "html", "news", "google", "rss",
    "東京", "自衛隊", "東京地本", "地方協力本部"
}

def google_news_rss(query):
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=ja&gl=JP&ceid=JP:ja"
    with urllib.request.urlopen(url, timeout=20) as r:
        return r.read()

def parse_date(text):
    try:
        return parsedate_to_datetime(text).astimezone(JST)
    except Exception:
        return None

def judge_sentiment(text):
    if any(w in text for w in NEGATIVE_WORDS):
        return "否定"
    if any(w in text for w in POSITIVE_WORDS):
        return "肯定"
    return "中立"

def clean_text(s):
    return re.sub(r"\s+", " ", re.sub(r"<.*?>", "", s or "")).strip()

def extract_keywords(items):
    text = " ".join((i["title"] + " " + i["snippet"]) for i in items)
    words = re.findall(r"[一-龥ぁ-んァ-ヶA-Za-z0-9]{2,}", text)
    words = [w for w in words if w not in STOPWORDS and not w.isdigit()]
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
                link = item.findtext("link") or ""
                snippet = clean_text(item.findtext("description"))
                pub = parse_date(item.findtext("pubDate"))

                if not title or not pub:
                    continue
                if pub < cutoff:
                    continue

                text = title + " " + snippet
                key = title[:80]
                if key in seen:
                    continue
                seen.add(key)

                sentiment = judge_sentiment(text)

                items.append({
                    "title": title,
                    "link": link,
                    "snippet": snippet,
                    "source": "GoogleニュースRSS",
                    "date": pub.strftime("%Y-%m-%d %H:%M"),
                    "sentiment": sentiment,
                    "query": query
                })
        except Exception as e:
            items.append({
                "title": "取得エラー",
                "link": "",
                "snippet": f"{query}: {e}",
                "source": "system",
                "date": now.strftime("%Y-%m-%d %H:%M"),
                "sentiment": "否定",
                "query": query
            })

    items.sort(key=lambda x: (x["sentiment"] != "否定", x["date"]), reverse=False)
    items = items[:MAX_ITEMS]

    counts = Counter(i["sentiment"] for i in items)
    summary = (
        f"直近{DAYS_LIMIT}日間の公開情報から{len(items)}件を抽出。"
        f"肯定{counts['肯定']}件、中立{counts['中立']}件、否定{counts['否定']}件。"
        f"否定・リスク語を含む項目を優先表示します。"
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
