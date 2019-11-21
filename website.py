import aiohttp_jinja2
import jinja2
from aiohttp import web
from aiopg.sa import create_engine
from db import connection, Article
from sqlalchemy import func
from sqlalchemy.sql import select

DESCRIPTION = '''Лучший блог о поисковых системах и интернет-маркетинге на русском языке.
Крупнейший каталог статей о поисковом маркетинге, сео оптимизации и парсинге.
Заходи и читай самые свежие новости в мире сео!'''

print(len(DESCRIPTION))
KEYWORDS = '''cео, seo, seo оптимизация, сео продвижение, сео оптимизация, продвижение, оптимизация сайта,
seo это, поисковая оптимизация, сео сайта, ыущ, сео это, раскрутка, продвижение в интернете, парсинг, блог,
что такое парсинг, парсер контента, ключевые слова гугл, как парсить сайт'''
key_num = len(KEYWORDS.split(','))
print(key_num)


async def go(request, sql):
    results = []
    async with request.app['engine'].acquire() as conn:
        async for row in conn.execute(sql):
            results.append(row)
    return results[0] if len(results) == 1 else results


async def index(request):
    art_count = 30
    page = int(request.rel_url.query.get('page', 0))
    if page == 1:
        raise web.HTTPFound('/')
    art_sql = Article.select().limit(art_count).offset(page*art_count)
    articles = await go(request, art_sql)

    co_sql = select([func.count(Article.c.id)])
    count = await go(request, co_sql)
    count = count[0] // 30 + 1
    pages = [x for x in range(1, count)]
    context = {
        'h1': 'Спаршенный Блог о SEO',
        'description': DESCRIPTION,
        'keywords': KEYWORDS,
        'articles': articles,
        'pages': pages
    }
    response = aiohttp_jinja2.render_template(
        'index.html', request, context)
    return response


async def article(request):
    article_slug = request.match_info.get('slug')
    sql = select([Article]).where(Article.c.slug == article_slug)
    article = await go(request, sql)
    context = {'article': article,
               'description': DESCRIPTION,
               'keywords': KEYWORDS
               }
    response = aiohttp_jinja2.render_template(
        'post.html', request, context)
    return response


async def on_init(app):
    app['engine'] = await create_engine(**connection)


app = web.Application()
app.on_startup.append(on_init)

aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))

app.add_routes([web.get('/', index)])
app.add_routes([web.get('/article/{slug}', article)])

app.router.add_static('/static', 'static')

web.run_app(app)
