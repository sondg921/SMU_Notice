import bs4
import pandas as pd
import requests
import re
from feedgen.feed import FeedGenerator
from datetime import datetime
import pytz
import os

# 1. RSS 피드 기본 설정
fg = FeedGenerator()
fg.title('컴퓨터과학과')
fg.link(href='https://cs.smu.ac.kr', rel='alternate')
fg.description('상명대학교 컴퓨터과학과 공지사항 게시판의 내용을 (Atom 기반) RSS Feed로 가공한 내용입니다.')
fg.docs('http://www.rssboard.org/rss-specification')
fg.language('ko')

# 한국 시간대(KST) 설정
kst = pytz.timezone('Asia/Seoul')

# 2. 크롤링 실행
url = "https://www.smu.ac.kr/kor/life/notice.do?srCampus=smu"
html = requests.get(url).text
soup = bs4.BeautifulSoup(html, "html.parser")

data = []

css_selector = "div.board-name-thumb.board-wrap > ul > li > dl"

for tag in soup.select(css_selector):
    head = tag.select_one("td:nth-child(3) > a").get_text().strip()
    date_str = tag.select_one("li.board-thumb-content-date").get_text().strip().replace('작성일\n', '').strip()
    link_path = tag.select_one("td:nth-child(3) > a").get("href")
    fullUrl = "https://www.smu.ac.kr/kor/life/notice.do" + link_path

    data.append((head, date_str, fullUrl))

    # --- RSS 아이템(item) 생성 시작 ---
    fe = fg.add_entry()
    fe.title(head)
    fe.link(href=fullUrl)

    # 1. GUID 추출 (URL에서 articleNo 숫자만 추출하여 설정)
    article_no_match = re.search(r'articleNo=(\d+)', link_path)
    article_no = article_no_match.group(1) if article_no_match else "0"
    fe.guid(article_no, permalink=False)

    # 2. 날짜 처리 (yyyy-mm-dd -> RSS 표준 날짜 형식)
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        fe.pubDate(kst.localize(dt))
    except:
        fe.pubDate(datetime.now(kst))
    # --- RSS 아이템 생성 종료 ---

# 3. CSV 파일 저장
os.makedirs('docs', exist_ok=True)

df = pd.DataFrame(data=data, columns=["Head", "Date", "Url"])
df.to_csv("docs/notice.csv", index=False, encoding='utf-8-sig')

# 4. RSS XML 파일 저장
fg.rss_file('docs/feed.xml', pretty=True)
