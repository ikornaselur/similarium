# flake8: noqa: F401 F403
from IPython import embed

from sqlalchemy.future import select

from semantle_slack_bot import db
from semantle_slack_bot.models import *

banner1 = """

███████╗███████╗███╗   ███╗ █████╗ ███╗   ██╗████████╗██╗     ███████╗
██╔════╝██╔════╝████╗ ████║██╔══██╗████╗  ██║╚══██╔══╝██║     ██╔════╝
███████╗█████╗  ██╔████╔██║███████║██╔██╗ ██║   ██║   ██║     █████╗
╚════██║██╔══╝  ██║╚██╔╝██║██╔══██║██║╚██╗██║   ██║   ██║     ██╔══╝
███████║███████╗██║ ╚═╝ ██║██║  ██║██║ ╚████║   ██║   ███████╗███████╗
╚══════╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚══════╝
Preloaded imports:

    from sqlalchemy.future import select

    from semantle_slack_bot import db
    from semantle_slack_bot.models import *
"""

embed(using="asyncio", colors="Neutral", banner1=banner1)
