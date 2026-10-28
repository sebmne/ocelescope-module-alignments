"""The HTTP operations the generated frontend client is built from, and the resource type."""

from ocelescope_backend.app.modules.loader import build_module

from ocelescope_module_oc_alignments.module import OCAlignments


def test_the_module_offers_these_operations() -> None:
    schema = build_module(OCAlignments).create_app().openapi()
    operations = {
        (method.upper(), path, operation["operationId"])
        for path, methods in schema["paths"].items()
        for method, operation in methods.items()
    }
    assert operations == {
        ("GET", "/petri-nets", "listPetriNets"),
        ("GET", "/petri-nets/resource-type", "petriNetResourceType"),
        ("POST", "/runs", "startRun"),
        ("GET", "/runs", "listRuns"),
        ("GET", "/runs/{run_id}", "getRun"),
        ("POST", "/runs/{run_id}/cancellation", "cancelRun"),
        ("DELETE", "/runs/{run_id}", "deleteRun"),
        ("GET", "/alignments", "listAlignments"),
        ("GET", "/alignments/{alignments_id}", "getAlignments"),
        ("GET", "/alignments/{alignments_id}/variants/{variant_id}", "getVariant"),
        ("GET", "/alignments/{alignments_id}/executions/{index}", "getExecution"),
    }


def test_alignments_are_a_resource_of_the_module() -> None:
    from ocelescope_module_oc_alignments.infrastructure.alignments_resource import OCAlignmentsResource

    assert OCAlignments.resources == [OCAlignmentsResource]
    assert OCAlignmentsResource.get_label() == "OC Alignments"
