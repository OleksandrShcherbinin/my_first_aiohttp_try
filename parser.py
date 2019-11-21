from os import sys
import random
import asyncio
from asyncio.queues import Queue
from requests_html import AsyncHTMLSession
from requests.exceptions import ConnectionError, ReadTimeout
from db import Article, connection
from aiopg.sa import create_engine
from slugify import slugify
from gtrans import translate_text
from datetime import datetime


with open('new_users.txt', 'r', encoding='utf-8') as f:
    user_agents = f.read().split('\n')

with open('fresh_socks.txt', 'r', encoding='utf-8') as f:
    proxies_list = f.read().split('\n')


articles = set()


async def worker(qu, coro_num, session, engine):
    loop = asyncio.get_running_loop()
    while True:
        if qu.qsize() == 0:
            break

        url = await qu.get()
        try:

            prox = random.choice(proxies_list)
            proxies = {'http': prox, 'https': prox}
            headers = {'User-Agent': random.choice(user_agents)}

            print(f'[Send request in {coro_num}] [queue_size {qu.qsize()}]', url)
            response = await session.get(url, headers=headers, timeout=10)

            if '/category/' in url:
                post_urls = response.html.xpath('//h3/a/@href')
                for u in post_urls:
                    if u.endswith('.html'):
                        if u not in articles:
                            await qu.put(u)
                            articles.add(u)
                continue

            post = {}
            name = response.html.xpath('//h1/text()')[0]
            post['name'] = await loop.run_in_executor(
                None, translate_text, name, 'ru', 'uk')
            post['slug'] = slugify(post['name'])
            post['source'] = url
            post['category'] = response.html.xpath('//ul[@class="td-category"]/li/a/text()')
            post['category'] = ','.join(post['category'])
            post['image'] = response.html.xpath('//div[@class="td-post-featured-image"]//img/@src')[0]
            elements = response.html.xpath('//p')
            post['content'] = ''
            post['parsed_time'] = datetime.now().date()
            for elem in elements:
                translated = await loop.run_in_executor(
                None, translate_text, elem.text, 'ru', 'uk')
                post['content'] += f'<p>{translated}</p>\n'
                del translated

            async with engine.acquire() as cursor:
                sql = Article.insert().values(**post)
                await cursor.execute(sql)

            print('[Article saved]', post["name"])

            del url, prox, proxies, headers, response, post, sql

        except (ConnectionError, ReadTimeout):
            await qu.put(url)

        except KeyboardInterrupt:
            quit()

        except Exception as e:
            print(e, type(e), sys.exc_info()[2].tb_lineno)


async def main():
    urls_queue = Queue()
    workers_count = 100
    pages = 97
    category_base_url = 'https://www.searchengines.ru/category/seo/page/{}'
    for i in range(1, pages):
        cat_url = category_base_url.format(i)
        urls_queue.put_nowait(cat_url)

    session = AsyncHTMLSession()
    engine = await create_engine(**connection)

    tasks = []
    for num in range(workers_count):
        task = worker(urls_queue, num, session, engine)
        tasks.append(task)

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
