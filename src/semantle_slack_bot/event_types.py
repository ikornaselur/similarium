from typing import Optional, TypedDict


class Event(TypedDict):
    client_msg_id: str
    type: str  # noqa: A003
    text: Optional[str]
    user: str
    ts: str
    team: str
    blocks: list
    channel: str
    event_ts: str
    channel_type: str


class Authorization(TypedDict):
    enterprise_id: Optional[str]
    team_id: str
    user_id: str
    is_bot: bool
    is_enterprise_install: bool


class Body(TypedDict):
    token: str
    team_id: str
    api_app_id: str
    event: Event
    type: str  # noqa: A003
    event_id: str
    event_time: int
    authorizations: list[Authorization]
    is_ext_shared_channel: bool
    event_context: str
