from requests import get
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import asyncio
import aiohttp


class Mhtwyat():

    def __init__(self, chunk_length=2000):
        self.url = 'https://mhtwyat.com/'
        self.website = get(self.url).content
        self.content = BeautifulSoup(self.website, 'html.parser')
        self.categories = self.content.find_all("div", {"class": "category"})
        self.scrapped_categories = []
        self.scrapped_articles = {}
        self.articles = []
        self.get_categories()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"
        options = webdriver.ChromeOptions()
        options.headless = True
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument("--window-size=1920,1080")
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument("--disable-extensions")
        options.add_argument("--proxy-server='direct://'")
        options.add_argument("--proxy-bypass-list=*")
        options.add_argument("--start-maximized")
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        self.driver = webdriver.Chrome(options=options)
        self.chunk_length = chunk_length

    def get_categories(self):
        for category in self.categories:
            main_category = category.find_next("h2").find("span", {"class": "title"}).text
            category_dic = {"main_category": main_category, "sub_category": [sub_category["href"] for sub_category in
                                                                             category.find_next("ul").find_all("a")]}
            self.scrapped_categories.append(category_dic)
        print(self.scrapped_categories)

    def get_category_articles(self, main_category, category):
        url = f'{category}'
        print(f'{url} under scrapping . . . ')
        self.driver.get(url)
        click_more = True
        try:
            element = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.ID, 'more_results_btn')))
            counter = 1
            while click_more:
                if counter == 100:
                    click_more = False
                time.sleep(10)
                print(f'{url} see more articles . . . ({counter})')
                if element.is_displayed() and element.get_attribute('value') != 'لا يوجدالمزيد من نتائج':
                    # element.click()
                    self.driver.execute_script('arguments[0].click()', element)
                else:
                    click_more = False
                counter += 1
        except Exception as e:
            print(f'{url} Error . . . {e}')

        website = self.driver.page_source
        content = BeautifulSoup(website, 'html.parser')
        articles = content.find_all("a", {"class": "category-box"})
        if main_category in self.scrapped_articles:
            self.scrapped_articles[main_category].extend([article['href'] for article in articles])
        else:
            self.scrapped_articles[main_category] = [article['href'] for article in articles]

        website = self.driver.page_source
        content = BeautifulSoup(website, 'html.parser')
        articles = content.find_all("a", {"class": "category-box"})
        if main_category in self.scrapped_articles:
            self.scrapped_articles[main_category].extend([article['href'] for article in articles])
        else:
            self.scrapped_articles[main_category] = [article['href'] for article in articles]

    def save_all_articles_title_into_file(self, file_name=f'{(int(time.time() * 1000))}_mhtwyat_article_titles.json'):
        for index, category in enumerate(self.scrapped_categories):
            main_category = category['main_category']
            for sub_category in category['sub_category']:
                print(f'scrapping main category : {main_category} -> sub category : {sub_category}')
                self.get_category_articles(main_category, sub_category)
        print(len(self.scrapped_articles))

        with open(file_name, 'w') as file:
            json.dump(self.scrapped_articles, file)

    def extract_sub_category(self, strCateg=''):
        slash_matches = [i for i, ltr in enumerate(strCateg) if ltr == '/']
        result = ''
        try:
            result = strCateg[slash_matches[0]:slash_matches[1]].strip()
        except:
            pass
        if result.find(',') != -1:
            result = result.split(',')[1].strip()
        if result.find('،') != -1:
            result = result.split('،')[1].strip()
        if result.find('/') != -1:
            result = result.split('/')[1].strip()
        return result

    async def get_target_article(self, category, title,session,index=0):
        url = f'{title}'
        try:
            async with session.get(url) as r:
                if r.status != 200:
                    r.raise_for_status()
                website = await r.text()
                content = BeautifulSoup(website, 'html.parser')
                sub_category = ''
                article = ''

                try:
                    article = content.find('div', {'class': 'article-text'})
                except:
                    pass
                try:
                    sub_category = content.find('ul', {'class': 'breadcrumbs'}).text
                    sub_category = self.extract_sub_category(sub_category)
                except:
                    pass
                try:
                    temp = article.find('div', {'id': 'toc_container'})
                    temp.decompose()
                except Exception as e:
                    print(e)
                    pass
                try:
                    [banner.decomposed() for banner in article.find_all('div', {'class': 'post-banner'})]
                except:
                    pass
                try:
                    article.find('div', {'class': 'FAQPage'}).decompose()
                except:
                    pass
                try:
                    article.find('h2', {'class': 'references-title'}).find_parent('div').decompose()
                except:
                    pass
                try:
                    see_more = article.find_all('strong')
                    for item in see_more:
                        if str(item.text).find('شاهد أيضًا') != -1:
                            item.find_parent('p').decompose()
                except:
                    pass

                try:
                    [script.decompose() for script in article.find_all('script')]
                except:
                    pass
                try:
                    article.find('div', {'class': 'printfooter'}).decompose()
                except:
                    pass
                try:
                    article.find('ul', {'class': 'related-articles-list1'}).decompose()
                except:
                    pass
                try:
                    article.find('div', {'class': 'toc'}).decompose()
                except:
                    pass
                try:
                    article.find('div', {'class': 'feedback-feature'}).decompose()
                except:
                    pass
                try:
                    article.find('div', {'id': 'feedback-yes-option'}).decompose()
                except:
                    pass
                try:
                    article.find('div', {'id': 'feedback-no-option'}).decompose()
                except:
                    pass
                try:
                    article.find('div', {'id': 'feedback-thanks-msg'}).decompose()
                except:
                    pass
                try:
                    article = article.get_text(separator=' ')
                except:
                    pass

                article_dict = {'category': category, 'sub_category': sub_category, 'title': title, 'content': article}
                print(index+1,article_dict)
                self.articles.append(article_dict)
                if len(self.articles) == self.chunk_length:
                    with open(f'{(int(time.time() * 1000))}_mhtwyat_articles.json', 'w') as json_file:
                        json.dump(self.articles, json_file, ensure_ascii=False)
                    self.articles = []
        except Exception as e:
            print(e)

    async def save_articles_into_file(self, titles_file):
        with open(titles_file) as json_file:
            data = json.load(json_file)
            counter = 1
            category_counter = 1
            tasks = []
            total_timeout = aiohttp.ClientTimeout(total=60 * 500)
            connector = aiohttp.TCPConnector(limit=50)
            semaphore = asyncio.Semaphore(200)
            async with semaphore:
                async with aiohttp.ClientSession(timeout=total_timeout,connector=connector) as session:
                    try:
                        for category, title_list in data.items():
                            print(f'{category_counter}. {category} is under scrapping . . . ')
                            for title in title_list:
                                print(f'{counter}. {self.url}{title} scrapping article . . . ')
                                task = asyncio.create_task(self.get_target_article(category, title,session,counter))
                                tasks.append(task)
                                counter += 1
                            category_counter += 1
                        await asyncio.gather(*tasks)
                    except Exception as e:
                        with open(f'{(int(time.time() * 1000))}_mhtwyat_articles.json', 'w') as json_file:
                            json.dump(self.articles, json_file, ensure_ascii=False)
                        self.articles = []
                        print(e)
