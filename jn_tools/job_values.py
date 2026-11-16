"""Record values a job reports as an OpenTelemetry gauge, so Better Stack can alert on them.

The caller passes its own meter: this module never sets up OpenTelemetry or touches
its globals, so it is safe in worker processes.

Better Stack alerts on this gauge (alerts live in JobNinjaInfra). Keep the metric
name and labels stable, or those alerts stop matching.
"""

METRIC_NAME = "jn.job.value"


class JobValues:
    def __init__(self, meter):
        self._gauge = meter.create_gauge(
            METRIC_NAME, description="Values reported by a job run, by job and metric"
        )

    def record(self, job: str, metric: str, value, **labels):
        """Record one value. `labels` are extra low-cardinality labels, e.g. a provider."""
        if value is None:
            return
        self._gauge.set(value, {"job": job, "metric": metric, **labels})
