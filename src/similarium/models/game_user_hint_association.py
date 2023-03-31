import sqlalchemy as sa
from sqlalchemy.orm import relationship

from similarium.db import Base
from similarium.utils import timestamp_ms


class GameUserHintAssociation(Base):
    __tablename__ = "game_user_hint_association"

    game_id = sa.Column(sa.ForeignKey("game.id"), primary_key=True)
    game = relationship("Game", back_populates="hint_seekers", lazy="selectin")

    created = sa.Column(sa.BigInteger, nullable=False, default=timestamp_ms)

    user_id = sa.Column(sa.ForeignKey("user.id"), primary_key=True)
    user = relationship("User", lazy="selectin")

    guess_idx = sa.Column(sa.Integer, nullable=False)

    def __repr__(self) -> str:
        game = self.game_id
        user = self.user_id
        return f"<HintSeeker: guess {self.guess_idx} ({game=} {user=})>"
