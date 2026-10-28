from ocelescope_backend.app.internal.exceptions import NotFound
from ocelescope_backend.app.internal.session import Session

from ocelescope_module_oc_alignments.domain.exceptions import UnknownAlignments
from ocelescope_module_oc_alignments.domain.models.alignment_set import AlignmentSet, AlignmentSetSummary
from ocelescope_module_oc_alignments.infrastructure.alignments_resource import OCAlignmentsResource


class OcelescopeAlignmentRepository:
    """Alignments kept as Ocelescope resources of the session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, alignments: AlignmentSet, name: str) -> AlignmentSetSummary:
        resource = OCAlignmentsResource.from_alignment_set(alignments)
        alignments_id = self._session.add_resource(resource, name=name)
        return alignments.summary(alignments_id, name)

    def get(self, alignments_id: str) -> tuple[str, AlignmentSet]:
        try:
            stored = self._session.get_resource(alignments_id)
        except NotFound as error:
            raise UnknownAlignments(alignments_id) from error
        if stored.schema_hash != OCAlignmentsResource.get_schema_hash():
            raise UnknownAlignments(alignments_id)
        resource = self._session.load_resource(alignments_id, OCAlignmentsResource)
        return stored.name, resource.to_alignment_set()

    def list(self) -> tuple[AlignmentSetSummary, ...]:
        summaries = [
            self.get(resource.id)[1].summary(resource.id, resource.name)
            for resource in self._session.list_resources()
            if resource.schema_hash == OCAlignmentsResource.get_schema_hash()
        ]
        return tuple(sorted(summaries, key=lambda s: s.created_at, reverse=True))
