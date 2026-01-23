import bs4
import pandas as pd
import requests
import re
import os
from feedgen.feed import FeedGenerator
from datetime import datetime
import pytz

# 1. 초기 설정 및 폴더 생성
os.makedirs('docs', exist_ok=True) # docs 폴더가 없으면 생성

fg = FeedGenerator()
fg.title('상명대학교 공지사항')
fg.link(href='https://cs.smu.ac.kr', rel='alternate')
fg.description('상명대학교 공지사항 RSS 피드입니다.')
fg.language('ko')
kst = pytz.timezone('Asia/Seoul')

# 2. 크롤링 (헤더 추가로 차단 방지)
url = "https://www.smu.ac.kr/kor/life/notice.do?srCampus=smu"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
}

try:
    response = requests.get(url, headers=headers, timeout=20)
    response.encoding = 'utf-8'
    html = response.text
    soup = bs4.BeautifulSoup(html, "html.parser")
except Exception as e:
    print(f"접속 실패: {e}")
    exit()

# 3. 데이터 추출 및 RSS 아이템 추가
data = []
css_selector = "div.board-name-thumb.board-wrap > ul > li > dl"

for tag in soup.select(css_selector):
    try:
        title_tag = tag.select_one("td:nth-child(3) > a")
        head = title_tag.get_text().strip()
        link_path = title_tag.get("href")
        fullUrl = "https://www.smu.ac.kr/kor/life/notice.do" + link_path
        date_str = tag.select_one("li.board-thumb-content-date").get_text().strip().replace('작성일\n', '').strip()
        
        data.append((head, date_str, fullUrl))

        # RSS 아이템 생성
        fe = fg.add_entry()
        fe.title(head)
        fe.link(href=fullUrl)
        
        # GUID 추출
        article_no_match = re.search(r'articleNo=(\d+)', link_path)
        fe.guid(article_no_match.group(1) if article_no_match else fullUrl, permalink=False)
        
        # 날짜 설정
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        fe.pubDate(kst.localize(dt))
    except:
        continue

# 4. 파일 저장 (경로를 docs/ 로 지정)
df = pd.DataFrame(data=data, columns=["Head", "Date", "Url"])
df.to_csv("docs/notice.csv", index=False, encoding='utf-8-sig')
fg.rss_file('docs/feed.xml', pretty=True)

print(f"성공: {len(data)}개의 공지사항을 docs 폴더에 저장했습니다.")
