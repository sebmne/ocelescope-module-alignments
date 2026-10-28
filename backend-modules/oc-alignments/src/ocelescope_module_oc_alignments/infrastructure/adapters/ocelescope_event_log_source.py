from datetime import datetime

from ocelescope.ocel.constants.pm4py import ACTIVITY_COL, EID_COL, OID_COL, OTYPE_COL, TIMESTAMP_COL
from ocelescope.ocel.constants.tables import E2O_TABLE, EVENTS_TABLE, OBJECTS_TABLE
from ocelescope.util.sql import ident
from ocelescope_backend.app.internal.exceptions import NotFound
from ocelescope_backend.app.internal.session import Session

from ocelescope_module_oc_alignments.domain.exceptions import UnknownLog
from ocelescope_module_oc_alignments.domain.models.log import Event, EventLog


class OcelescopeEventLogSource:
    """The session's logs, in their current (filtered) view, read with one DuckDB query.

    Events without objects are left out: they belong to no process execution.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def read(self, ocel_id: str) -> EventLog:
        try:
            ocel = self._session.get_ocel(ocel_id)
        except NotFound as error:
            raise UnknownLog(ocel_id) from error
        try:
            eid, oid, otype = ident(EID_COL), ident(OID_COL), ident(OTYPE_COL)
            activity, timestamp = ident(ACTIVITY_COL), ident(TIMESTAMP_COL)
            rows = ocel.sql(
                f"SELECT r.{eid}, e.{activity}, e.{timestamp}, r.{oid}, o.{otype} "
                f"FROM {ident(E2O_TABLE)} r "
                f"JOIN {ident(EVENTS_TABLE)} e USING ({eid}) "
                f"JOIN {ident(OBJECTS_TABLE)} o USING ({oid}) "
                f"ORDER BY e.{timestamp}, r.{eid}, r.{oid}"
            ).fetchall()
        finally:
            ocel.close()

        events: dict[str, tuple[str, datetime, set[str]]] = {}
        object_types: dict[str, str] = {}
        for event_id, event_activity, event_time, object_id, object_type in rows:
            events.setdefault(str(event_id), (str(event_activity), event_time, set()))[2].add(str(object_id))
            object_types[str(object_id)] = str(object_type)
        return EventLog(
            name=self._session.ocels[ocel_id].name,
            events=tuple(
                Event(id=event_id, activity=act, timestamp=time, objects=tuple(sorted(objects)))
                for event_id, (act, time, objects) in events.items()
            ),
            object_types=object_types,
        )
