from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _reset_singleton():
    from jn_tools.cloud_watch_client import CloudWatchClient

    CloudWatchClient._client = None
    CloudWatchClient._logger_default = None
    yield
    CloudWatchClient._client = None
    CloudWatchClient._logger_default = None


@pytest.fixture
def boto_client():
    with patch("jn_tools.cloud_watch_client.boto3") as boto3_mock:
        client = MagicMock()
        boto3_mock.client.return_value = client
        yield client


def _make_client(**overrides):
    from jn_tools.cloud_watch_client import CloudWatchClient

    defaults = dict(
        namespace="jn.test",
        metric_dimensions={"Environment": "Test"},
        debug_mode=True,
        AWS_ACCESS_KEY_ID="id",
        AWS_ACCESS_KEY_SECRET="secret",
    )
    defaults.update(overrides)
    return CloudWatchClient(**defaults)


def test_submit_value_calls_put_metric_data(boto_client):
    boto_client.put_metric_data.return_value = {"ResponseMetadata": {"RequestId": "r1"}}

    client = _make_client()
    conf = client.submit_value("TestMetric", 100, dimensions={"Instance": "i-abc"}, unit="Count")

    boto_client.put_metric_data.assert_called_once()
    assert conf["Namespace"] == "jn.test"
    assert conf["MetricData"][0]["MetricName"] == "TestMetric"
    assert conf["MetricData"][0]["Value"] == 100
    assert conf["MetricData"][0]["Unit"] == "Count"


def test_submit_value_swallows_exceptions_by_default(boto_client):
    boto_client.put_metric_data.side_effect = RuntimeError("boom")

    client = _make_client()
    client.submit_value("TestMetric", 1)


def test_submit_value_raises_when_configured(boto_client):
    boto_client.put_metric_data.side_effect = RuntimeError("boom")

    client = _make_client(raise_exceptions=True)
    with pytest.raises(RuntimeError):
        client.submit_value("TestMetric", 1)


def test_normalise_string_replaces_umlauts(boto_client):
    client = _make_client()
    assert client._normalise_string("für Müller") == "fuer Mueller"
