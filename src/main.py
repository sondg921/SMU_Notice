import bs4
import pandas as pd
import requests
import re
import os
from feedgen.feed import FeedGenerator
from datetime import datetime
import pytz

# 1. 초기 설정
os.makedirs('docs', exist_ok=True)
kst = pytz.timezone('Asia/Seoul')

fg = FeedGenerator()
fg.title('상명대학교 공지사항 통합 피드')
fg.link(href='https://www.smu.ac.kr', rel='alternate')
fg.description('상명대 전체 공지 및 컴퓨터과학전공 공지 통합 피드입니다.')
fg.language('ko')


# 2. 크롤링 함수 (선택자를 인자로 받음)
def fetch_notices(url, category_name, base_url, row_selector, title_selector, date_selector):
    notices = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.encoding = 'utf-8'
        soup = bs4.BeautifulSoup(response.text, "html.parser")

        # row_selector로 각 공지사항 행을 찾음
        for tag in soup.select(row_selector):
            try:
                # 제목과 링크 추출
                title_tag = tag.select_one(title_selector)
                if not title_tag: continue

                head = title_tag.get_text().strip()
                display_title = f"[{category_name}] {head}"

                link_path = title_tag.get("href")
                full_url = base_url + link_path

                # 날짜 추출 및 정제
                raw_date = tag.select_one(date_selector).get_text().strip()
                date_str = raw_date.replace('작성일\n', '').replace('작성일', '').strip()

                # articleNo 추출
                article_no_match = re.search(r'articleNo=(\d+)', link_path)
                article_no = article_no_match.group(1) if article_no_match else full_url

                notices.append({
                    'title': display_title,
                    'date': date_str,
                    'url': full_url,
                    'id': f"{category_name}_{article_no}"
                })
            except Exception as e:
                continue
    except Exception as e:
        print(f"{category_name} 에러: {e}")

    return notices


# 3. 각 사이트별 맞춤형 데이터 수집
# (참고: 사이트 구조를 확인하여 선택자를 각각 지정합니다)

# (1) 전체 공지사항
all_notices = fetch_notices(
    url="https://www.smu.ac.kr/kor/life/notice.do?srCampus=smu",
    category_name="전체",
    base_url="https://www.smu.ac.kr/kor/life/notice.do",
    row_selector="div.board-name-thumb.board-wrap > ul > li > dl",
    title_selector="td:nth-child(3) > a",
    date_selector="li.board-thumb-content-date"
)

# (2) 컴퓨터과학전공 공지사항 (학과 사이트 구조에 맞춰 수정 필요)
cs_notices = fetch_notices(
    url="https://cs.smu.ac.kr/cs/community/notice.do",
    category_name="컴과",
    base_url="https://cs.smu.ac.kr/cs/community/notice.do",
    row_selector="div.board-name-thumb.board-wrap > ul > li > dl",
    title_selector="dt > a",
    date_selector="dd > ul > li.board-thumb-content-date"
)

# 4. 통합, 정렬 및 저장
combined_data = all_notices + cs_notices
combined_data.sort(key=lambda x: x['date'], reverse=True)

final_list_for_df = []
for item in combined_data:
    fe = fg.add_entry()
    fe.title(item['title'])
    fe.link(href=item['url'])
    fe.guid(item['id'], permalink=False)

    try:
        dt = datetime.strptime(item['date'], '%Y-%m-%d')
        fe.pubDate(kst.localize(dt))
    except:
        fe.pubDate(datetime.now(kst))

    final_list_for_df.append((item['title'], item['date'], item['url']))

df = pd.DataFrame(data=final_list_for_df, columns=["Head", "Date", "Url"])
df.to_csv("docs/notice.csv", index=False, encoding='utf-8-sig')
fg.rss_file('docs/feed.xml', pretty=True)

print(f"통합 완료: 총 {len(combined_data)}개")
