from nose.tools import assert_in
from sqlalchemy.sql import text as sql
from ..ut.bunch import bunchr
from .error import error_guard


def add_user(conn, name, email, openid):
    return conn.execute((
        'insert into "user" (name, email, openid)'
        'values (%s, %s, %s) '
        'returning *'
    ), (name, email, openid)).fetchone()[0]


def get_user_id_bi_openid(conn, openid):
    ret = conn.execute('select id from "user" where openid = %s', (openid,)).fetchone()
    return None if ret is None else ret[0]


def get_user_name_bi_openid(conn, openid):
    ret = conn.execute('select name from "user" where openid = %s', (openid,)).fetchone()
    return None if ret is None else ret[0]


def get_user_name_bi_id(conn, id):
    ret = conn.execute(sql('select name from "user" where id = :id'), id=id).fetchone()
    return None if ret is None else ret[0]


def get_user_email_bi_id(conn, id):
    ret = conn.execute('select email from "user" where id = %s', (id,)).fetchone()
    return None if ret is None else ret[0]


def get_user_bi_id(conn, id):
    ret = conn.execute('select * from "user" where id = %s', (id,)).fetchone()
    return None if ret is None else bunchr(**ret)


def set_email(conn, id, email):
    conn.execute(
        'update "user" set email = %s where id = %s',
        (email, id)
    )


def get_users(conn, offset=None, limit=None):
    result = conn.execute(sql('\n'.join([
        'select * from "user" order by id',
        '' if offset is None else 'offset :offset',
        '' if limit is None else 'limit :limit'
    ])), **dict(offset=offset, limit=limit))
    return [bunchr(**row) for row in result.fetchall()]


def get_users_detail(conn, offset=None, limit=None):
    result = conn.execute(sql('\n'.join([
        '''
        select u0.*, (select count(1) from watch as w0 where w0.user_id = u0.id) watch_count
        from "user" as u0
        order by u0.id
        ''',
        '' if offset is None else 'offset :offset',
        '' if limit is None else 'limit :limit'
    ])), **dict(offset=offset, limit=limit))
    return [bunchr(**row) for row in result.fetchall()]


def get_user_count(conn):
    return conn.execute('select count(1) from "user"').fetchone()[0]


@error_guard
def set_user_field_bi_id(conn, id, field, value):
    assert_in(field, ('name', 'email', 'openid', 'maxwatch'))
    conn.execute(
        sql('update "user" set %s = :value where id = :id' % field),
        id=id,
        value=value
    )


@error_guard
def has_user_bi_openid(conn, openid):
    return conn.execute(
        sql('select 1 from "user" where openid = :openid'),
        openid=openid
    ).fetchone() is not None


@error_guard
def activate_user_bi_id(conn, id):
    conn.execute(sql('update "user" set activated = TRUE where id = :id'), id=id)


@error_guard
def inactivate_user_bi_id(conn, id):
    conn.execute(sql('update "user" set activated = FALSE where id = :id'), id=id)


@error_guard
def user_activated_bi_id(conn, id):
    return conn.execute(
        sql('select activated from "user" where id = :id'),
        id=id
    ).fetchone()[0]
