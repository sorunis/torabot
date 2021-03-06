from sqlalchemy.sql import text as sql
from ..ut.bunch import bunchr


ROOM = 2147483647


def get_notices_bi_user_id(conn, user_id, page=0, room=ROOM):
    result = conn.execute(sql('''
        select
            n0.id,
            n0.user_id,
            n0.ctime,
            n0.status,
            q0.kind as kind,
            c0.data as change
        from (
            select * from notice
            where user_id = :user_id
        ) as n0
        inner join change as c0 on n0.change_id = c0.id
        inner join query as q0 on c0.query_id = q0.id
        order by n0.ctime desc
        offset :offset
        limit :limit
    '''), user_id=user_id, offset=page * room, limit=room)
    return [bunchr(**row) for row in result.fetchall()]


def get_notice_count_bi_user_id(conn, user_id):
    return conn.execute(sql('''
        select count(*) from notice
        where user_id = :user_id
    '''), user_id=user_id).fetchone()[0]


def get_pending_notices_bi_user_id(conn, user_id, page=0, room=ROOM):
    result = conn.execute(sql('''
        select
            n0.id,
            n0.user_id,
            n0.ctime,
            n0.status,
            q0.kind as kind,
            c0.data as change
        from (
            select * from notice
            where user_id = :user_id and status = :status
        ) as n0
        inner join change as c0 on n0.change_id = c0.id
        inner join query as q0 on c0.query_id = q0.id
        order by n0.ctime desc
        offset :offset
        limit :limit
    '''), user_id=user_id, status='pending', offset=page * room, limit=room)
    return [bunchr(**row) for row in result.fetchall()]


def get_pending_notice_count_bi_user_id(conn, user_id):
    return conn.execute(sql('''
        select count(*) from notice
        where user_id = :user_id and status = :status
    '''), user_id=user_id, status='pending').fetchone()[0]


def get_pending_notices(conn):
    result = conn.execute(sql('''
        select
            n0.id,
            n0.user_id,
            n0.ctime,
            n0.status,
            q0.kind as kind,
            c0.data as change
        from (
            select * from notice
            where status = :status
        ) as n0
        inner join change as c0 on n0.change_id = c0.id
        inner join query as q0 on c0.query_id = q0.id
        order by n0.ctime desc
    '''), status='pending')
    return [bunchr(**row) for row in result.fetchall()]


def mark_notice_sent(conn, id):
    conn.execute(
        sql('update notice set status = :status where id = :id'),
        status='sent',
        id=id
    )
