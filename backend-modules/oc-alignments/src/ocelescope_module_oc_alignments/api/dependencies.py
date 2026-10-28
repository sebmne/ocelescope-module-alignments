"""Composition root: the only place that knows which adapter implements which port."""

from typing import Annotated

from fastapi import Depends
from ocelescope_backend.app.dependencies import ApiSession

from ocelescope_module_oc_alignments.application.ports.alignment_repository import AlignmentRepository
from ocelescope_module_oc_alignments.application.ports.job_registry import JobRegistry
from ocelescope_module_oc_alignments.application.ports.run_repository import RunRepository
from ocelescope_module_oc_alignments.application.use_cases.cancel_run import CancelRun
from ocelescope_module_oc_alignments.application.use_cases.delete_run import DeleteRun
from ocelescope_module_oc_alignments.application.use_cases.get_alignments import GetAlignments
from ocelescope_module_oc_alignments.application.use_cases.get_execution import GetExecution
from ocelescope_module_oc_alignments.application.use_cases.get_run import GetRun
from ocelescope_module_oc_alignments.application.use_cases.get_variant import GetVariant
from ocelescope_module_oc_alignments.application.use_cases.list_alignments import ListAlignments
from ocelescope_module_oc_alignments.application.use_cases.list_nets import ListNets
from ocelescope_module_oc_alignments.application.use_cases.list_runs import ListRuns
from ocelescope_module_oc_alignments.application.use_cases.start_run import StartRun
from ocelescope_module_oc_alignments.infrastructure.adapters.ocelescope_alignment_repository import (
    OcelescopeAlignmentRepository,
)
from ocelescope_module_oc_alignments.infrastructure.adapters.ocelescope_event_log_source import OcelescopeEventLogSource
from ocelescope_module_oc_alignments.infrastructure.adapters.ocelescope_net_source import OcelescopeNetSource
from ocelescope_module_oc_alignments.infrastructure.adapters.session_job_registry import SessionJobRegistry
from ocelescope_module_oc_alignments.infrastructure.adapters.session_run_repository import SessionRunRepository
from ocelescope_module_oc_alignments.infrastructure.adapters.sse_run_notifier import SseRunNotifier
from ocelescope_module_oc_alignments.infrastructure.aligner.process_aligner import ProcessAligner


def get_run_repository(session: ApiSession) -> RunRepository:
    return SessionRunRepository(session)


def get_job_registry(session: ApiSession) -> JobRegistry:
    return SessionJobRegistry(session)


def get_alignment_repository(session: ApiSession) -> AlignmentRepository:
    return OcelescopeAlignmentRepository(session)


Runs = Annotated[RunRepository, Depends(get_run_repository)]
Jobs = Annotated[JobRegistry, Depends(get_job_registry)]
Alignments = Annotated[AlignmentRepository, Depends(get_alignment_repository)]


def get_list_nets(session: ApiSession) -> ListNets:
    return ListNets(nets=OcelescopeNetSource(session))


def get_start_run(session: ApiSession, runs: Runs, jobs: Jobs, alignments: Alignments) -> StartRun:
    return StartRun(
        nets=OcelescopeNetSource(session),
        logs=OcelescopeEventLogSource(session),
        aligner=ProcessAligner(),
        runs=runs,
        jobs=jobs,
        alignments=alignments,
        notifier=SseRunNotifier(session.id),
    )


def get_list_runs(runs: Runs) -> ListRuns:
    return ListRuns(runs=runs)


def get_get_run(runs: Runs) -> GetRun:
    return GetRun(runs=runs)


def get_cancel_run(runs: Runs, jobs: Jobs) -> CancelRun:
    return CancelRun(runs=runs, jobs=jobs)


def get_delete_run(runs: Runs, jobs: Jobs) -> DeleteRun:
    return DeleteRun(runs=runs, jobs=jobs)


def get_list_alignments(alignments: Alignments) -> ListAlignments:
    return ListAlignments(alignments=alignments)


def get_get_alignments(alignments: Alignments) -> GetAlignments:
    return GetAlignments(alignments=alignments)


def get_get_variant(alignments: Alignments) -> GetVariant:
    return GetVariant(alignments=alignments)


def get_get_execution(alignments: Alignments) -> GetExecution:
    return GetExecution(alignments=alignments)
