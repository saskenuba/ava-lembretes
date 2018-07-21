from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine(
    'postgresql+psycopg2://martin:159753as@localhost/ava_rememberme',
    convert_unicode=True)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()
Base.metadata.bind = engine


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    from ava_rememberme.database_models import Users, Profiles, Assignments
    Base.metadata.reflect()
    # Base.metadata.drop_all()
    # Base.metadata.create_all()
