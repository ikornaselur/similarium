# pyright: reportWildcardImportFromLibrary=false
# flake8: noqa: F401 F403
import datetime as dt

import pytz
import sqlalchemy as sa
from IPython import embed
from sqlalchemy.future import select

from similarium import db
from similarium.models import *
from similarium.config import config

banner1 = """
███████╗██╗███╗   ███╗██╗██╗      █████╗ ██████╗ ██╗██╗   ██╗███╗   ███╗
██╔════╝██║████╗ ████║██║██║     ██╔══██╗██╔══██╗██║██║   ██║████╗ ████║
███████╗██║██╔████╔██║██║██║     ███████║██████╔╝██║██║   ██║██╔████╔██║
╚════██║██║██║╚██╔╝██║██║██║     ██╔══██║██╔══██╗██║██║   ██║██║╚██╔╝██║
███████║██║██║ ╚═╝ ██║██║███████╗██║  ██║██║  ██║██║╚██████╔╝██║ ╚═╝ ██║
╚══════╝╚═╝╚═╝     ╚═╝╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝     ╚═╝

Preloaded imports:

    import datetime as dt

    import pytz
    import sqlalchemy as sa
    from sqlalchemy.future import select

    from similarium import db
    from similarium.models import *
    from similarium.config import config
"""

embed(using="asyncio", colors="Neutral", banner1=banner1)
