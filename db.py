import sqlalchemy as sa

metadata = sa.MetaData()

connection = {
    'user': 'your user name',
    'database': 'your database name',
    'host': 'your host',
    'password': 'password for this database'
}

dsn = 'postgresql://{user}:{password}@{host}/{database}'.format(**connection)

Article = sa.Table(
    'blog_articles_py4seo_4', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('name', sa.String),
    sa.Column('slug', sa.String, unique=True),
    sa.Column('source', sa.String),
    sa.Column('category', sa.String),
    sa.Column('content', sa.Text),
    sa.Column('image', sa.String),
    sa.Column('parsed_time', sa.DateTime),
)

if __name__ == '__main__':
    engine = sa.create_engine(dsn)
    metadata.drop_all(engine)
    metadata.create_all(engine)
