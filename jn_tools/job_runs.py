"""Count job runs as an OpenTelemetry metric, so Better Stack can alert on them.

The caller passes its own meter: this module never sets up OpenTelemetry or touches
its globals, so it is safe in worker processes.

Better Stack alerts on this counter (alerts live in JobNinjaInfra). Keep the metric
name and labels stable, or those alerts stop matching.
"""

METRIC_NAME = "jn.job.runs"
STATUSES = ("success", "failure", "skipped")


class JobRuns:
    def __init__(self, meter):
        self._counter = meter.create_counter(
            METRIC_NAME, unit="{run}", description="Finished job runs, by job and status"
        )

    def record(self, job: str, status: str, **labels):
        """Count one run. `labels` are extra low-cardinality labels, e.g. a source name."""
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}, got {status!r}")
        self._counter.add(1, {"job": job, "status": status, **labels})

    @staticmethod
    def status_for(exit_code) -> str:
        return "success" if not exit_code else "failure"
