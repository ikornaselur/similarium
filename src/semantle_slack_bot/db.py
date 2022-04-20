import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker

Base = declarative_base()

engine = create_async_engine("sqlite+aiosqlite:///word2vec.db")
session = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


class Nearby(Base):
    __tablename__ = "nearby"

    word = sa.Column(sa.Text)
    neighbor = sa.Column(sa.Text)
    similarity = sa.Column(sa.Float)
    percentile = sa.Column(sa.Integer)

    __table_args__ = (
        sa.PrimaryKeyConstraint(word, neighbor),
        {},
    )

    def __repr__(self) -> str:
        return (
            f"<Nearby ({self.word} -> {self.neighbor}: "
            f"{self.similarity:.02f} {self.percentile})>"
        )


class SimilarityRange(Base):
    __tablename__ = "similarity_range"

    word = sa.Column(sa.Text, primary_key=True)
    top = sa.Column(sa.Float)
    top10 = sa.Column(sa.Float)
    rest = sa.Column(sa.Float)

    def __repr__(self) -> str:
        return (
            f"<SimilarityRange ({self.word}: {self.top:0.2f} "
            f"{self.top10:0.2f} {self.rest:0.2})>"
        )


class Word2Vec(Base):
    __tablename__ = "word2vec"

    word = sa.Column(sa.Text, primary_key=True)
    vec = sa.Column(sa.BLOB)

    def __repr__(self) -> str:
        return f"<Word2Vec ({self.word})>"
