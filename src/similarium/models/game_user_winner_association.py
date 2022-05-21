import sqlalchemy as sa
from sqlalchemy.orm import relationship

from similarium.db import Base


class GameUserWinnerAssociation(Base):
    __tablename__ = "game_user_winner_association"

    game_id = sa.Column(sa.ForeignKey("game.id"), primary_key=True)
    game = relationship("Game", back_populates="winners")

    user_id = sa.Column(sa.ForeignKey("user.id"), primary_key=True)
    user = relationship("User")

    guess_idx = sa.Column(sa.Integer, nullable=False)
