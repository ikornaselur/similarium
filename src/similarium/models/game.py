from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.sql.schema import Index

from similarium.ai import chat_completion_request, get_hint_prompt, get_overview_prompt
from similarium.config import config
from similarium.db import Base
from similarium.exceptions import InvalidWord, NotFound, UserAlreadyWon
from similarium.logging import logger
from similarium.models.game_user_hint_association import GameUserHintAssociation
from similarium.models.game_user_winner_association import GameUserWinnerAssociation
from similarium.utils import get_secret, get_similarity, timestamp_ms

if TYPE_CHECKING:
    from similarium.models import Guess, User

TOP_GUESSES_CTX = 10


class Game(Base):
    __tablename__ = "game"

    id = sa.Column(sa.Integer, primary_key=True)
    channel_id = sa.Column(sa.Text, sa.ForeignKey("channel.id"), nullable=False)
    thread_ts = sa.Column(sa.Text, nullable=False)
    puzzle_number = sa.Column(sa.Integer, nullable=False)
    date = sa.Column(sa.Text, nullable=False)
    active = sa.Column(sa.Boolean, nullable=False)
    secret = sa.Column(sa.Text, nullable=False)

    channel = relationship("Channel", backref="games", lazy="joined")
    guesses = relationship("Guess", back_populates="game", lazy="joined")
    winners = relationship(
        "GameUserWinnerAssociation", order_by="GameUserWinnerAssociation.created"
    )

    hint = sa.Column(sa.Text, nullable=True)
    hint_seekers = relationship(
        "GameUserHintAssociation", order_by="GameUserHintAssociation.created"
    )

    similarity_range = relationship(
        "SimilarityRange", primaryjoin="foreign(Game.secret) == SimilarityRange.word"
    )

    __table_args__ = (Index("channel_thread_idx", channel_id, thread_ts),)

    @classmethod
    def new(
        cls,
        *,
        channel_id: str,
        thread_ts: str,
        puzzle_number: int,
        puzzle_date: str,
        active: bool = True,
    ) -> Game:
        secret = get_secret(channel_id, puzzle_number)
        logger.debug(
            f"Creating new Game: {channel_id=} {thread_ts=} {puzzle_number=} {secret=}"
        )
        return cls(
            channel_id=channel_id,
            thread_ts=thread_ts,
            puzzle_number=puzzle_number,
            date=puzzle_date,
            active=active,
            secret=secret,
        )

    @classmethod
    async def get(
        cls,
        *,
        channel_id: str,
        thread_ts: str,
        session: AsyncSession,
    ) -> Optional[Game]:
        logger.debug(f"Getting Game: {channel_id=} {thread_ts=}")
        stmt = (
            select(cls)
            .where(
                cls.channel_id == channel_id,
                cls.thread_ts == thread_ts,
            )
            .options(selectinload(cls.guesses))
            .options(selectinload(cls.similarity_range))
            .options(selectinload(cls.winners))
            .options(selectinload(cls.hint_seekers))
        )

        result = await session.execute(stmt)

        return result.scalars().one_or_none()

    @classmethod
    async def get_active_in_channel(
        cls, channel_id: str, /, *, session: AsyncSession
    ) -> list[Game]:
        stmt = (
            select(cls)
            .where(cls.channel_id == channel_id, cls.active)
            .options(selectinload(cls.guesses))
            .options(selectinload(cls.similarity_range))
            .options(selectinload(cls.winners))
            .options(selectinload(cls.hint_seekers))
        )

        result = await session.execute(stmt)

        return result.scalars().all()

    @classmethod
    async def by_id(cls, game_id: int, /, *, session: AsyncSession) -> Optional[Game]:
        return (
            await session.scalars(
                select(cls)
                .where(cls.id == game_id)
                .options(selectinload(cls.guesses))
                .options(selectinload(cls.similarity_range))
                .options(selectinload(cls.winners))
                .options(selectinload(cls.hint_seekers))
            )
        ).one_or_none()

    async def add_guess(
        self, *, word: str, user_id: str, session: AsyncSession
    ) -> tuple[Guess, bool]:
        """Add a guess to the game

        Returns a tuple of the guess and if it's a new guess or an existing one
        """
        from .guess import Guess
        from .nearby import Nearby
        from .word2vec import Word2Vec

        logger.debug(f"Adding guess {word=} to {self=}")

        # Check if user has already won
        stmt = select(GameUserWinnerAssociation).where(
            GameUserWinnerAssociation.game_id == self.id,
            GameUserWinnerAssociation.user_id == user_id,
        )
        existing_assoc = await session.scalar(stmt)
        if existing_assoc is not None:
            raise UserAlreadyWon("User already won")

        if word == self.secret:
            logger.debug(f"Guess was the secret, adding {user_id=} to winners")
            self.winners.append(
                GameUserWinnerAssociation(
                    game_id=self.id, user_id=user_id, guess_idx=len(self.guesses) + 1
                )
            )
            similarity = 100.0
            percentile = config.rules.similarity_count
        else:
            try:
                nearby = await Nearby.get(
                    session=session, word=self.secret, neighbor=word
                )
            except NotFound:
                guess_vec = await Word2Vec.get(word, session=session)
                if guess_vec is None:
                    logger.debug(f"Word not recognised: {word=}")
                    raise InvalidWord(f"Word not recognised: {word}")

                logger.debug(f"Guess was not within {config.rules.similarity_count}")
                secret_vec = await Word2Vec.get(self.secret, session=session)
                if secret_vec is None:
                    raise Exception("Secret word not recognised?")

                similarity = get_similarity(
                    secret_vec.expanded_vec, guess_vec.expanded_vec
                )
                percentile = 0
            else:
                similarity = get_similarity(
                    nearby.word_vec.expanded_vec, nearby.neighbor_vec.expanded_vec
                )
                percentile = nearby.percentile

        # Check if guess exists
        guess = await Guess.get(session=session, word=word, game_id=self.id)
        if guess is not None:
            logger.debug(f"Guess has already been made {guess=}")
            guess.updated = timestamp_ms()  # type: ignore
            guess.latest_guess_user_id = user_id  # type: ignore
            return (guess, False)

        # Create a new guess
        guess = await Guess.new(
            session=session,
            game=self,
            user_id=user_id,
            word=word,
            percentile=percentile,
            similarity=similarity,
        )
        session.add(guess)
        await session.refresh(self)

        return (guess, True)

    async def top_guesses(self, n: int, /, *, session: AsyncSession) -> list[Guess]:
        from .guess import Guess

        stmt = (
            select(Guess)
            .where(Guess.game_id == self.id)
            .order_by(Guess.similarity.desc())
            .options(selectinload(Guess.game))
            .limit(n)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def latest_guesses(self, n: int, /, *, session: AsyncSession) -> list[Guess]:
        from .guess import Guess

        stmt = (
            select(Guess)
            .where(Guess.game_id == self.id)
            .order_by(Guess.updated.desc())
            .options(selectinload(Guess.game))
            .limit(n)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def has_guessed(self, user_id: str, /, *, session: AsyncSession) -> bool:
        """Check if a user has guessed in this game already"""

        from .guess import Guess

        stmt = (
            select(Guess)
            .where(Guess.game_id == self.id, Guess.user_id == user_id)
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar() is not None

    def get_winners_messages(self) -> list[str]:
        winners = []
        # Get hint seekers map so we can mark if the winner saw the hint
        hint_seekers: dict[str, int] = {
            hint_seeker.user.id: hint_seeker.guess_idx
            for hint_seeker in self.hint_seekers
        }
        winner: GameUserWinnerAssociation
        for idx, winner in enumerate(self.winners):
            match idx:
                case 0:
                    # All wins, except the first, have to have the guess count
                    # reduced by one, as the first win is not revealed to
                    # others
                    reduction = 0
                    medal = ":first_place_medal: "
                case 1:
                    reduction = 1
                    medal = ":second_place_medal: "
                case 2:
                    reduction = 1
                    medal = ":third_place_medal: "
                case _:
                    reduction = 1
                    medal = ""

            message = (
                f"{medal}<@{winner.user_id}> got the secret on guess"
                f" {winner.guess_idx - reduction}!"
            )
            if (
                hint_guess_idx := hint_seekers.get(winner.user_id)
            ) and hint_guess_idx < winner.guess_idx:
                message += f" (Hint was used at guess {hint_guess_idx - reduction})"
            winners.append(message)
        return winners

    async def get_hint(
        self, user: User, close_words_context_count: int = 20, *, session: AsyncSession
    ) -> str:
        """Get a hint from ChatGPT for this game secret"""

        if self.channel_id not in config.openai.channel_ids:
            return "AI features are not enabled on this channel"

        # Ensure user is added to hint seekers
        if user.id not in [hint_seeker.user.id for hint_seeker in self.hint_seekers]:
            self.hint_seekers.append(
                GameUserHintAssociation(
                    game_id=self.id, user_id=user.id, guess_idx=len(self.guesses)
                )
            )
            await session.commit()

        if self.hint is not None:
            return self.hint

        # First get the close words to use for context
        from .nearby import Nearby

        stmt = select(Nearby).where(
            Nearby.word == self.secret,
            Nearby.percentile >= 1000 - close_words_context_count,
            Nearby.percentile < 1000,
        )
        result = await session.execute(stmt)

        close_words = [word.neighbor for word in result.scalars()]

        # Then craft the prompt
        prompt = get_hint_prompt(self.secret, close_words)

        # And get the hint, commit and return
        self.hint = await chat_completion_request(prompt)
        await session.commit()

        return self.hint

    async def get_overview(self, *, session: AsyncSession) -> Optional[str]:
        """Get an overview of the game from ChatGPT"""
        if self.channel_id not in config.openai.channel_ids:
            return None

        def _get_guess_ctx(guess: Guess) -> str:
            if guess.percentile == 0:
                return (
                    f"<@{guess.user_id}> guessed '{guess.word}', which was far from the"
                    " secret"
                )
            if guess.percentile < 900:
                return f"<@{guess.user_id}> guessed '{guess.word}' in top 1000 words"
            if guess.percentile < 990:
                return f"<@{guess.user_id}> guessed '{guess.word}' in top 100 words"
            if guess.percentile == 1000:
                return f"<@{guess.user_id}> guessed the secret '{guess.word}'"
            return f"<@{guess.user_id}> guessed '{guess.word}' in top 10 words"

        def _get_non_winner_ctx() -> list[str]:
            """Go through the guesses and get context for non winners"""
            winner_user_ids = {winner.user_id for winner in self.winners}
            top_non_winners: dict[str, Guess] = {}
            guess: Guess

            # Get best guess of everyone that didn't win, but participated
            for guess in self.guesses:
                if guess.user_id in winner_user_ids:
                    continue

                if (
                    guess.user_id not in top_non_winners
                    or guess.percentile > top_non_winners[guess.user_id].percentile
                ):
                    top_non_winners[guess.user_id] = guess

            if not top_non_winners:
                return []

            ctx = [
                "",
                "The following players made guesses, but didn't find the secret:",
            ]
            for user_id, guess in top_non_winners.items():
                if guess.percentile == 0:
                    ctx.append(
                        f"Best guess from <@{user_id}> was '{guess.word}' but it didn't"
                        " reach top 1000"
                    )
                elif guess.percentile < 900:
                    ctx.append(
                        f"Best guess from <@{user_id}> was '{guess.word}' in top 1000"
                        " words"
                    )
                elif guess.percentile < 990:
                    ctx.append(
                        f"Best guess from <@{user_id}> was '{guess.word}' in top 100"
                        " words"
                    )
                else:
                    ctx.append(
                        f"Best guess from <@{user_id}> was '{guess.word}' in top 10"
                        " words"
                    )

            return ctx

        context = []

        # Get win state context
        if self.guesses:
            context.append("")
            if winners_ctx := self.get_winners_messages():
                # Remove any Slack emojis from the string with regex
                context.extend([re.sub(r":[^:]+:\s*", "", ctx) for ctx in winners_ctx])
                context.append("Congratulate the winners by referencing them directly.")
            else:
                context.append("No one got the secret")

            # Get non winner context
            context.extend(_get_non_winner_ctx())

        # Get guesser context
        context.append("")
        if top_guesses := await self.top_guesses(TOP_GUESSES_CTX, session=session):
            guess_count = len(self.guesses)
            context.append(f"There were a total of {guess_count} guesses made")
            if guess_count < 50:
                context.append("That is not a lot of guesses needed")
            elif guess_count < 100:
                context.append("That is a normal amount of guesses")
            elif guess_count < 200:
                context.append("That is starting to be a lot of guesses")
            else:
                context.append("That is a lot of guesses overall")
            context.append(f"The top {min(TOP_GUESSES_CTX, guess_count)} guesses were:")
            context.extend([_get_guess_ctx(g) for g in top_guesses])
        else:
            context.append("No one made a guess. I guess no one was playing at all.")

        # Get the prompt
        context.append("")
        secret = self.secret

        prompt = get_overview_prompt(secret, context)

        logger.debug(f"Prompt for overview:\n\n{prompt}")

        return await chat_completion_request(prompt)

    def __repr__(self) -> str:
        return (
            f"<Game (id={self.id} puzzle_number={self.puzzle_number} "
            f"channel_id={self.channel_id} secret={self.secret})>"
        )
