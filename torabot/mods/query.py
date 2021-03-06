import json
from ..ut.bunch import bunchr


def query(kind, query, timeout):
    from ..core.connection import autoccontext
    from ..core.query import query as search
    with autoccontext(commit=True) as conn:
        q = search(
            conn=conn,
            kind=kind,
            text=query,
            timeout=timeout
        )
    return q.result


def parse_json(query):
    if isinstance(query, str):
        try:
            query = json.loads(query)
            if not isinstance(query, dict):
                raise Exception('not standard')
            return bunchr(query)
        except:
            pass


def parse_dict(query):
    if isinstance(query, dict):
        return bunchr(query)


def illegal(query):
    assert False, 'illegal query: %s' % query
