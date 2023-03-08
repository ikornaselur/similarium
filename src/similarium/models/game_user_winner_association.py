import sqlalchemy as sa
from sqlalchemy.orm import relationship

from similarium.db import Base
from similarium.utils import timestamp_ms


class GameUserWinnerAssociation(Base):
    __tablename__ = "game_user_winner_association"

    game_id = sa.Column(sa.ForeignKey("game.id"), primary_key=True)
    game = relationship("Game", back_populates="winners")

    created = sa.Column(sa.BigInteger, nullable=False, default=timestamp_ms)

    user_id = sa.Column(sa.ForeignKey("user.id"), primary_key=True)
    user = relationship("User")

    guess_idx = sa.Column(sa.Integer, nullable=False)

    def __repr__(self) -> str:
        game = self.game_id
        user = self.user_id
        return f"<Winner: guess {self.guess_idx} ({game=} {user=})>"
