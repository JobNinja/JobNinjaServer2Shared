import pytest

from jn_tools.job_values import METRIC_NAME, JobValues


class FakeGauge:
    def __init__(self):
        self.sets = []

    def set(self, amount, attributes=None):
        self.sets.append((amount, attributes))


class FakeMeter:
    def __init__(self):
        self.gauges = {}

    def create_gauge(self, name, unit="", description=""):
        self.gauges[name] = FakeGauge()
        return self.gauges[name]


@pytest.fixture
def meter():
    return FakeMeter()


def test_uses_the_callers_meter(meter):
    JobValues(meter)
    assert list(meter.gauges) == [METRIC_NAME]


def test_records_a_value_with_job_and_metric(meter):
    JobValues(meter).record("clean_import", "cleaned_jobs", 42)
    assert meter.gauges[METRIC_NAME].sets == [
        (42, {"job": "clean_import", "metric": "cleaned_jobs"})
    ]


def test_extra_labels_are_added(meter):
    JobValues(meter).record("import_apps", "system_errors", 3, provider="ba")
    assert meter.gauges[METRIC_NAME].sets == [
        (3, {"job": "import_apps", "metric": "system_errors", "provider": "ba"})
    ]


def test_skips_a_missing_value(meter):
    JobValues(meter).record("clean_import", "cleaned_jobs", None)
    assert meter.gauges[METRIC_NAME].sets == []
