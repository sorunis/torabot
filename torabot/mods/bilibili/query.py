import json
from ...core.connection import autoccontext
from ...core.local import get_current_conf
from ...core.query import query
from . import name


def get_bangumi():
    with autoccontext(commit=True) as conn:
        q = query(
            conn=conn,
            kind=name,
            text=json.dumps(dict(method='bangumi')),
            timeout=get_current_conf()['TORABOT_SPY_TIMEOUT'],
        )
    return q.result.content