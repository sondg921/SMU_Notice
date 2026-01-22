import bs4
import pandas as pd
import requests

from feedgen.feed import FeedGenerator
fg = FeedGenerator ()
fg.id ('http://lernfunk.de/media/654321')
fg.title('Some Testfeed' )
fg.author({'name': 'John Doe', 'email': 'john@example.de'})
fg. link( href='http://example.com', rel='alternate' )
fg. logo ('http://ex.com/logo.jpg')
fg.subtitle('This is a cool feed!')
fg. link( href='http://larskiesow.de/test.atom', rel='self' )
fg. language('en')
fg.rss_file('docs/rss.xml')

url = "https://www.smu.ac.kr/kor/life/notice.do?srCampus=smu"
html = requests.get(url).text

soup = bs4.BeautifulSoup(html, "html.parser")

data = []

css_selector = "div.board-name-thumb.board-wrap > ul > li > dl"

for tag in soup.select(css_selector):
    head = tag.select_one("td:nth-child(3) > a").get_text().strip()
    date = tag.select_one("li.board-thumb-content-date").get_text().strip().replace('작성일\n', '').strip()  # '작성일\nyyyy-mm-dd'
    url = tag.select_one("td:nth-child(3) > a").get("href")
    fullUrl = "https://www.smu.ac.kr/kor/life/notice.do" + url
    data.append((head, date, fullUrl))

df = pd.DataFrame(data = data, columns = ["Head", "Date", "Url"])
df['Date'] = pd.to_datetime(df['Date'])
df.to_csv("docs/notice.csv", index = False)
