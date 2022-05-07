# pyright: reportWildcardImportFromLibrary=false
# flake8: noqa: F401 F403
import datetime as dt

from IPython import embed
import pytz
import sqlalchemy as sa
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

    import datetime as dt

    import pytz
    import sqlalchemy as sa
    from sqlalchemy.future import select

    from similarium import db
    from similarium.models import *
"""

embed(using="asyncio", colors="Neutral", banner1=banner1)
