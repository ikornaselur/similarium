import enum
import random

from similarium.utils import get_celeration_emoji

celebration_messages_top_10 = [
    "The guessing gods have blessed us! <@{user_id}> just guessed `{word}` in the top 10! {celebrate_emoji}",
    "We've got a genius in our midst! <@{user_id}> just guessed `{word}` in the top 10! {celebrate_emoji}",
    "The guessing elite! <@{user_id}> just guessed `{word}` in the top 10! {celebrate_emoji}",
    "Our top guessers strike again! `{word}` was just guessed by <@{user_id}> in the top 10! {celebrate_emoji}",
    "The top 10 has been breached! <@{user_id}> just guessed `{word}`! {celebrate_emoji}",
    "Incredible guess by <@{user_id}>! `{word}` has been guessed in the top 10! {celebrate_emoji}",
    "What a guess! <@{user_id}> just guessed `{word}` in the top 10! {celebrate_emoji}",
    "That's what we call guessing! `{word}` was just guessed by <@{user_id}> in the top 10! {celebrate_emoji}",
    "We have a new leader! <@{user_id}> just guessed `{word}` in the top 10! {celebrate_emoji}",
    "What a game! <@{user_id}> just guessed `{word}` in the top 10! {celebrate_emoji}",
    "That's how it's done! `{word}` has just been guessed in the top 10 by <@{user_id}>! {celebrate_emoji}",
    "Bravo <@{user_id}>! `{word}` has just made it to the top 10! {celebrate_emoji}",
]

celebration_messages_top_100 = [
    "Our guessers are on fire! <@{user_id}> just guessed `{word}` in the top 100! {celebrate_emoji}",
    "The guessing is heating up! <@{user_id}> just guessed `{word}` in the top 100! {celebrate_emoji}",
    "The guesses are getting better! We just got a guess from <@{user_id}> "
    "of `{word}` in the top 100! {celebrate_emoji}",
    "The guesses are getting stronger! <@{user_id}> just guessed `{word}` in the top 100! {celebrate_emoji}",
    "The guessing is getting better! A guess of `{word}` from <@{user_id}> is in the top 100! {celebrate_emoji}",
    "Things are heating up! A guess from <@{user_id}> of `{word}` is in the top 100! {celebrate_emoji}",
    "We have a contender! <@{user_id}> guessed `{word}` in the top 100! {celebrate_emoji}",
    "We're getting close! A guess from <@{user_id}> of `{word}` is in the top 100! {celebrate_emoji}",
    "We're making progress! <@{user_id}> guessed `{word}` in the top 100! {celebrate_emoji}",
    "We're on a roll! A guess of `{word}` from <@{user_id}> has just entered the top 100! {celebrate_emoji}",
]

celebration_messages_top_1000 = [
    "<@{user_id}>'s getting close! The word `{word}` has just been guessed in the top 1000! {celebrate_emoji}",
    "The guessing is starting off strong! <@{user_id}> just guessed `{word}` in the top 1000! {celebrate_emoji}",
    "We're getting there! A guess of `{word}` from <@{user_id}> has been made in the top 1000! {celebrate_emoji}",
    "Great job <@{user_id}>! A guess of `{word}` has made it into the top 1000! {celebrate_emoji}",
    "Well done <@{user_id}>! `{word}` has been guessed and is in the top 1000! {celebrate_emoji}",
    "Keep it up <@{user_id}>! A guess of `{word}` has just entered the top 1000! {celebrate_emoji}",
    "Great guess <@{user_id}>! `{word}` has just made it into the top 1000! {celebrate_emoji}",
    "Excellent work <@{user_id}>! `{word}` has been guessed and is in the top 1000! {celebrate_emoji}",
    "Well guessed <@{user_id}>! The word `{word}` has just been guessed and is in the top 1000! {celebrate_emoji}",
    "Congratulations <@{user_id}>! `{word}` is in the top 1000! {celebrate_emoji}",
    "That's a great guess <@{user_id}>! `{word}` has just made it to the top 1000! {celebrate_emoji}",
]

celebration_messages_top_10_first_guess = [
    "Unbelievable! The first green guess of `{word}` by <@{user_id}> was so close to the secret! "
    "It's like they have a sixth sense! {celebrate_emoji}",
    "No way! The first green guess of `{word}` by <@{user_id}> was almost spot on! "
    "They must have a crystal ball or something! {celebrate_emoji}",
    "Wow! The first green guess of `{word}` by <@{user_id}> was insanely close to the secret! "
    "I think we have a genius among us! {celebrate_emoji}",
    "Incredible! The first green guess of `{word}` by <@{user_id}> was only a hair's breadth away from the secret! "
    "I'm in awe! {celebrate_emoji}",
    "Mind-blowing! The first green guess of `{word}` by <@{user_id}> was so close to the secret, "
    "they must have a direct line to the game master! {celebrate_emoji}",
]
celebration_messages_top_1000_first_guess = [
    "Holy smokes! The very first guess of `{word}` and it's green! "
    "<@{user_id}>, you're a natural! <celebrate_emoji>",
    "Stop the presses! The first guess from <@{user_id}> with `{word}` just landed in the top 1000! "
    "This is going to be epic! <celebrate_emoji>",
    "Unbelievable! The first guess from <@{user_id}> of `{word}` is a green one! "
    "We must be playing with a team of mind readers! <celebrate_emoji>",
    "No way! The very first guess from <@{user_id}> of `{word}` and it's already in the top 1000! "
    "Our team is on fire! <celebrate_emoji>",
]


class CelebrationType(str, enum.Enum):
    # When the first guess of the game is either top 10 or top 1000, we celebrate a little extra
    TOP_10_FIRST = "TOP_10_FIRST"
    TOP_1000_FIRST = "TOP_1000_FIRST"
    TOP_10 = "TOP_10"
    TOP_100 = "TOP_100"
    TOP_1000 = "TOP_1000"


def get_celebration_message(
    celebration_type: CelebrationType, user_id: str, word: str
) -> str:
    match celebration_type:
        case CelebrationType.TOP_10_FIRST:
            message = random.choice(celebration_messages_top_10_first_guess)
        case CelebrationType.TOP_1000_FIRST:
            message = random.choice(celebration_messages_top_1000_first_guess)
        case CelebrationType.TOP_10:
            message = random.choice(celebration_messages_top_10)
        case CelebrationType.TOP_100:
            message = random.choice(celebration_messages_top_100)
        case CelebrationType.TOP_1000:
            message = random.choice(celebration_messages_top_1000)
        case _:
            raise NotImplementedError()

    celebrate_emoji = get_celeration_emoji()

    return message.format(user_id=user_id, word=word, celebrate_emoji=celebrate_emoji)
