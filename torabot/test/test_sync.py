from .g import g
from .mixin import ModelMixin
from ..model import Session, Art, Change, Query
from nose.tools import assert_equal
from .mock import mockrequests
from httmock import HTTMock
from ..sync import sync
from .. import what


class TestSync(ModelMixin):

    def sync(self, session):
        with HTTMock(mockrequests):
            sync('大嘘', session)
        session.flush()

    def test_sync(self):
        s = Session()
        self.sync(s)
        assert_equal(s.query(Art).count(), 8)
        assert_equal(s.query(Change).filter(Change.what == what.NEW).count(), 8)
        assert_equal(s.query(Change).filter(Change.what == what.RESERVE).count(), 2)
        assert_equal(s.query(Query).count(), 1)
        assert_equal(len(list(s.query(Query).one().arts)), 8)

    def test_sync_twice(self):
        s = Session()
        self.sync(s)
        self.sync(s)
        assert_equal(s.query(Art).count(), 8)
        assert_equal(s.query(Change).filter(Change.what == what.NEW).count(), 8)
        assert_equal(s.query(Change).filter(Change.what == what.RESERVE).count(), 2)
        assert_equal(s.query(Query).count(), 1)
        assert_equal(len(list(s.query(Query).one().arts)), 8)
