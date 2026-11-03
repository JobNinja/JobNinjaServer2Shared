import pytest

from jn_tools.job_runs import METRIC_NAME, JobRuns


class FakeCounter:
    def __init__(self):
        self.adds = []

    def add(self, amount, attributes=None):
        self.adds.append((amount, attributes))


class FakeMeter:
    def __init__(self):
        self.counters = {}

    def create_counter(self, name, unit="", description=""):
        self.counters[name] = FakeCounter()
        return self.counters[name]


@pytest.fixture
def meter():
    return FakeMeter()


def test_uses_the_callers_meter(meter):
    JobRuns(meter)
    assert list(meter.counters) == [METRIC_NAME]


@pytest.mark.parametrize("status", ["success", "failure", "skipped"])
def test_counts_a_run_with_job_and_status(meter, status):
    JobRuns(meter).record("import_leads", status)
    assert meter.counters[METRIC_NAME].adds == [(1, {"job": "import_leads", "status": status})]


def test_extra_labels_are_added(meter):
    JobRuns(meter).record("crawl", "success", source="stepstone")
    assert meter.counters[METRIC_NAME].adds == [
        (1, {"job": "crawl", "status": "success", "source": "stepstone"})
    ]


def test_rejects_unknown_status(meter):
    with pytest.raises(ValueError):
        JobRuns(meter).record("import_leads", "ok")


@pytest.mark.parametrize(
    "exit_code, status", [(0, "success"), (None, "success"), (1, "failure"), (2, "failure")]
)
def test_status_from_exit_code(exit_code, status):
    assert JobRuns.status_for(exit_code) == status
