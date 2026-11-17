import logging
import sys

import boto3
from botocore.client import Config

AWS_CLOUD_WATCH_REGION = "eu-central-1"

DEBUG_AWS_CLOUD_WATCH_REGION = "af-south-1"


class CloudWatchClient:
    """
    CloudWatchClient to send monitoring data to AWS CloudWatch.
    Read basic info about AWS CloudWatch, and concepts liek namespaces, metric, dimensions, etc here:
    https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html
    """

    _client = None
    _logger_default = None
    _raise_exceptions = False

    def __init__(
        self,
        namespace="",
        metric_dimensions={},
        unit="None",
        logger=None,
        debug_mode=False,
        raise_exceptions=False,
        AWS_ACCESS_KEY_ID="",
        AWS_ACCESS_KEY_SECRET="",
        AWS_ENDPOINT_URL=None,
    ):
        """
        Initialize client before calling any methods
        Args:
            namespace: (str) AWS namespace. Use format: jn.importer
            metric_dimensions: (dict) Set default dimension for this client which are added to all calls of submit_value().
                            Use dimension name as key and dimension value as value
            unit: (str, default: 'Unit') Set a default unit for this client. Note: Needs to be one of AWS pre-defined unit types.
            debug_mode: (boolean, default: False) If set to True, all data is submitted to aws region "af-south-1" (CapeTown)
            raise_exceptions: (boolean, default: False) If False, no exceptions will be raised from submit_value(). Exceptions are logged only.
            AWS_ACCESS_KEY_ID: (str) AWS access key id - Shared between all instances!! - Set it once in the first instance
            AWS_ACCESS_KEY_SECRET: (str) AWS access key secret - Shared between all instances!! - Set it once in the first instance
            AWS_ENDPOINT_URL: (str, default: None) AWS CloudWatch endpoint - Shared between all instances!! - Set it once in the first instance
        """
        self._namespace = self._normalise_string(namespace)
        self._metric_dimensions = self._normalise_dimensions(metric_dimensions)
        self._unit = unit
        self._debug = debug_mode
        self._raise_exceptions = raise_exceptions
        self._logger = logger or CloudWatchClient._get_default_logger()

        # This is dirty!
        # Users might not expect, that all instances share the same boto3.client
        # and passing other creaditals to later instances is futile.
        if CloudWatchClient._client is None:
            CloudWatchClient._client = boto3.client(
                "cloudwatch",
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_ACCESS_KEY_SECRET,
                endpoint_url=AWS_ENDPOINT_URL,
                config=Config(
                    region_name=AWS_CLOUD_WATCH_REGION
                    if not self._debug
                    else DEBUG_AWS_CLOUD_WATCH_REGION
                ),
            )
        self._client = CloudWatchClient._client

    def submit_value(self, metric_name, val, dimensions=None, unit=None, additional_params={}):
        """
        Send a value to CloudWatch
        Boto3 documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.put_metric_data
        Args:
            metric_name: (str)
            val:
            dimensions: (dict) add more dimensions to this specific value. Gets merged with default dimensions, if same name, this one will orverride defaults
            unit: (str) set specific unit

        Returns: None

        """
        metric_name = self._normalise_string(metric_name)
        my_conf = dict(
            Namespace=self._namespace,
            MetricData=[
                {
                    "MetricName": metric_name,
                    "Dimensions": self._get_dimensions_as_list(dimensions),
                    "Value": val,
                    "Unit": unit or self._unit,
                }
            ],
        )
        my_conf = {**my_conf, **additional_params}
        try:
            resp = self._client.put_metric_data(**my_conf)
        except Exception as e:
            self._logger.exception(
                f"CloudWatchClient::submit_value() {'DEBUG_MODE' if self._debug else ''} - EXCEPTION: {e}\n"
                f"Request config: {my_conf}"
            )
            if self._raise_exceptions:
                raise e
        else:
            request_id = resp.get("ResponseMetadata", {}).get("RequestId")
            self._logger.info(
                f"CloudWatchClient::submit_value() {'DEBUG_MODE' if self._debug else ''} - OK  {metric_name}: {val}"
                f" - request_id: {request_id}, request config: {my_conf}"
            )
        return my_conf

    def _normalise_string(self, val_string):
        line = (
            str(val_string)
            .replace("ä", "ae")
            .replace("Ä", "Äe")
            .replace("ö", "oe")
            .replace("Ö", "oe")
            .replace("ü", "ue")
            .replace("Ü", "Ue")
            .replace("ß", "ss")
        )
        line = line.encode("ascii", "ignore").decode("utf-8")
        return line

    def _normalise_dimensions(self, dimensions: dict):
        result = {}
        for key, val in dimensions.items():
            result[self._normalise_string(key)] = self._normalise_string(val)
        return result

    def _get_dimensions_as_list(self, local_dimensions):
        local_dimensions = self._normalise_dimensions(local_dimensions or {})
        return self._dict_as_list({**self._metric_dimensions, **local_dimensions}, key_name="Name")

    def _dict_as_list(self, my_dict, key_name="Name"):
        return [{key_name: k, "Value": v} for k, v in my_dict.items()]

    @staticmethod
    def _get_default_logger():
        if CloudWatchClient._logger_default is None:
            my_logger = logging.getLogger("CloudWatchClient")
            my_logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            my_logger.addHandler(handler)
            CloudWatchClient._logger_default = my_logger
        return CloudWatchClient._logger_default
