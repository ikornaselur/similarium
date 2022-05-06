# flake8: noqa: F401 F403
from IPython import embed

from sqlalchemy.future import select

from similarium import db
from similarium.models import *

banner1 = """
███████╗██╗███╗   ███╗██╗██╗      █████╗ ██████╗ ██╗██╗   ██╗███╗   ███╗
██╔════╝██║████╗ ████║██║██║     ██╔══██╗██╔══██╗██║██║   ██║████╗ ████║
███████╗██║██╔████╔██║██║██║     ███████║██████╔╝██║██║   ██║██╔████╔██║
╚════██║██║██║╚██╔╝██║██║██║     ██╔══██║██╔══██╗██║██║   ██║██║╚██╔╝██║
███████║██║██║ ╚═╝ ██║██║███████╗██║  ██║██║  ██║██║╚██████╔╝██║ ╚═╝ ██║
╚══════╝╚═╝╚═╝     ╚═╝╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝     ╚═╝

Preloaded imports:

    from sqlalchemy.future import select

    from similarium import db
    from similarium.models import *
"""

embed(using="asyncio", colors="Neutral", banner1=banner1)
