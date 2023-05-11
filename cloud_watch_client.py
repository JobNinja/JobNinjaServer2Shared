import sys
import logging

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
    _logger = None
    _raise_exceptions = False

    def __init__(self, namespace='', metric_dimensions={}, alarm_config={},
                 unit='None', logger=None, debug_mode=False, raise_exceptions=False, AWS_ACCESS_KEY_ID='',
                 AWS_ACCESS_KEY_SECRET=''):
        """
        Initialize client before calling any methods
        Args:
            namespace: (str) AWS namespace. Use format: jn.importer
            metric_dimensions: (dict) Set default dimension for this client which are added to all calls of submit_value().
                            Use dimension name as key and dimension value as value
            unit: (str, default: 'Unit') Set a default unit for this client. Note: Needs to be one of AWS pre-defined unit types.
            debug_mode: (boolean, default: False) If set to True, all data is submitted to aws region "af-south-1" (CapeTown)
            raise_exceptions: (boolean, default: False) If False, no exceptions will be raised from submit_value(). Exceptions are logged only.
        """
        self._namespace = self._normalise_string(namespace)
        self._metric_dimensions = self._normalise_dimensions(metric_dimensions)
        self._alarm_config = alarm_config
        self._unit = unit
        self._debug = debug_mode
        self._raise_exceptions = raise_exceptions
        self._logger = logger or self._get_logger()

        if self._client is None:
            self._client = boto3.client(
                'cloudwatch',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_ACCESS_KEY_SECRET,
                config=Config(region_name=AWS_CLOUD_WATCH_REGION if not self._debug else DEBUG_AWS_CLOUD_WATCH_REGION)
            )

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
            MetricData=[{
                'MetricName': metric_name,
                'Dimensions': self._get_dimensions_as_list(dimensions),
                'Value': val,
                'Unit': unit or self._unit
            }]
        )
        my_conf = {**my_conf, **additional_params}
        try:
            resp = self._client.put_metric_data(**my_conf)
        except Exception as e:
            self._logger.exception(
                f'CloudWatchClient::submit_value() {"DEBUG_MODE" if self._debug else ""} - EXCEPTION: {e}\n'
                f'Request config: {my_conf}')
            if self._raise_exceptions:
                raise e
        else:
            request_id = resp.get('ResponseMetadata', {}).get('RequestId')
            self._logger.info(f'CloudWatchClient::submit_value() {"DEBUG_MODE" if self._debug else ""} - OK  {metric_name}: {val}'
                              f' - request_id: {request_id}, request config: {my_conf}')
        return my_conf

    def set_alarm(self, alarm_name, metric_name, threshold=0, dimensions=None, unit=None,
                  update_if_exists=False, additional_params={}):
        full_alarm_name = self._get_full_normalized_alarm_name(alarm_name)
        metric_name = self._normalise_string(metric_name)
        alarm_exists = None
        if not update_if_exists:
            alarm_exists = self._alarm_existing(full_alarm_name, metric_name, dimensions=dimensions)
        if update_if_exists or not alarm_exists:
            # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.put_metric_alarm
            my_conf = dict(
                Namespace=self._namespace,
                AlarmName=full_alarm_name,
                # AlarmDescription='string',
                MetricName=metric_name,
                Statistic='Average',  # 'SampleCount' | 'Average' | 'Sum' | 'Minimum' | 'Maximum',
                # ExtendedStatistic='string',
                Dimensions=self._get_dimensions_as_list(dimensions),
                Period=60 * 60 * 3,
                Unit=unit or self._unit,  # 'Seconds'|'Microseconds'|'Milliseconds'|'Bytes'|'Kilobytes'|'Megabytes'|'Gigabytes'|'Terabytes'|'Bits'|'Kilobits'|'Megabits'|'Gigabits'|'Terabits'|'Percent'|'Count'|'Bytes/Second'|'Kilobytes/Second'|'Megabytes/Second'|'Gigabytes/Second'|'Terabytes/Second'|'Bits/Second'|'Kilobits/Second'|'Megabits/Second'|'Gigabits/Second'|'Terabits/Second'|'Count/Second'|'None',
                EvaluationPeriods=8,
                DatapointsToAlarm=8,
                Threshold=threshold,
                ComparisonOperator='GreaterThanThreshold',
                # 'GreaterThanOrEqualToThreshold' | 'GreaterThanThreshold' | 'LessThanThreshold' | 'LessThanOrEqualToThreshold' | 'LessThanLowerOrGreaterThanUpperThreshold' | 'LessThanLowerThreshold' | 'GreaterThanUpperThreshold',
                TreatMissingData='breaching',  # breaching | notBreaching | ignore | missing
            )
            my_conf = {**my_conf, **self._alarm_config, **additional_params}
            try:
                resp = self._client.put_metric_alarm(**my_conf)
            except Exception as e:
                self._logger.exception(
                    f'CloudWatchClient::set_alarm() {"DEBUG_MODE" if self._debug else ""} - EXCEPTION: {e}\n'
                    f'Request config: {my_conf}')
                if self._raise_exceptions:
                    raise e
            else:
                request_id = resp.get('ResponseMetadata', {}).get('RequestId')
                self._logger.info(f'CloudWatchClient::set_alarm() {"DEBUG_MODE" if self._debug else ""} - OK  '
                                  f'alarm name: {full_alarm_name}, threshold: {threshold}'
                                  f' - request_id: {request_id}, request config: {my_conf}')
            return my_conf

    def delete_alarm(self, alarm_name):
        full_alarm_name = self._get_full_normalized_alarm_name(alarm_name)
        my_conf = dict(
            AlarmNames=[full_alarm_name],
        )
        my_conf = {**my_conf, **self._alarm_config}
        try:
            resp = self._client.delete_alarms(**my_conf)
        except Exception as e:
            self._logger.exception(
                f'CloudWatchClient::delete_alarm() {"DEBUG_MODE" if self._debug else ""} - EXCEPTION: {e}\n'
                f'Request config: {my_conf}')
            if self._raise_exceptions:
                raise e
        else:
            request_id = resp.get('ResponseMetadata', {}).get('RequestId')
            self._logger.info(f'CloudWatchClient::delete_alarm() {"DEBUG_MODE" if self._debug else ""} - OK  '
                              f'alarm name: {full_alarm_name}'
                              f' - request_id: {request_id}, request config: {my_conf}')
        return my_conf

    def get_alarms(self, state="ALARM"):
        res = []
        my_conf = dict(
            StateValue=state,
            MaxRecords=100
        )
        if self._namespace:
            # Cloud watch does not accept an empty sting for AlarmNamePrefix
            my_conf['AlarmNamePrefix'] = self._get_full_normalized_alarm_name('')
        try:
            resp = None
            next_token = None
            while resp is None or next_token is not None:
                resp = self._client.describe_alarms(**my_conf)
                res.extend(resp.get('MetricAlarms', []))
                next_token = resp.get('NextToken')
                my_conf['NextToken'] = next_token
        except Exception as e:
            self._logger.exception(
                f'CloudWatchClient::delete_alarm() {"DEBUG_MODE" if self._debug else ""} - EXCEPTION: {e}\n'
                f'Request config: {my_conf}')
            if self._raise_exceptions:
                raise e
        else:
            request_id = resp.get('ResponseMetadata', {}).get('RequestId')
            self._logger.info(f'CloudWatchClient::get_alarms() {"DEBUG_MODE" if self._debug else ""} - OK  '
                              f" - Found {len(res)} alarms for namespace {self._namespace}"
                              f' - request_id: {request_id}, request config: {my_conf}')
        return res



    def _alarm_existing(self, full_alarm_name, metric_name, dimensions={}):
        # add only params which describe an alarm in a unique way.
        # Don't add things like 'unit' b/c you will not find an existing alarm if you filter with the incorrect unit,
        # e.g. if the unit got changed manually.
        my_conf = dict(
            Namespace=self._namespace,
            MetricName=metric_name,
            Dimensions=self._get_dimensions_as_list(dimensions),
        )
        try:
            resp = self._client.describe_alarms_for_metric(**my_conf)
        except Exception as e:
            self._logger.exception(
                f'CloudWatchClient::_alarm_existing() {"DEBUG_MODE" if self._debug else ""} - EXCEPTION: {e}\n'
                f'Request config: {my_conf}')
            if self._raise_exceptions:
                raise e
            return False
        else:
            request_id = resp.get('ResponseMetadata', {}).get('RequestId')
            existing = len([a for a in resp.get('MetricAlarms') if a.get('AlarmName') == full_alarm_name]) > 0
            self._logger.info(f'CloudWatchClient::_alarm_existing() {"DEBUG_MODE" if self._debug else ""} - OK  '
                              f'alarm name: {full_alarm_name}, existing: {existing}, request_id: {request_id}, request config: {my_conf}')
            return existing

    def _normalise_string(self, val_string):
        line = val_string.replace("ä", "ae").replace("Ä", "Äe") \
            .replace("ö", "oe").replace("Ö", "oe") \
            .replace("ü", "ue").replace("Ü", "Ue") \
            .replace("ß", "ss")
        line = line.encode('ascii', 'ignore').decode("utf-8")
        return line

    def _normalise_dimensions(self, dimensions: dict):
        result = {}
        for key, val in dimensions.items():
            result[self._normalise_string(key)] = self._normalise_string(val)
        return result

    def _get_dimensions_as_list(self, local_dimensions):
        local_dimensions = self._normalise_dimensions(local_dimensions or {})
        return self._dict_as_list({**self._metric_dimensions, **local_dimensions}, key_name='Name')

    def _dict_as_list(self, my_dict, key_name='Name'):
        return [{key_name: k, 'Value': v} for k, v in my_dict.items()]

    def _get_full_normalized_alarm_name(self, alarm_name):
        if not self._namespace:
            return self._normalise_string(alarm_name)
        return f"{self._namespace}.{self._normalise_string(alarm_name)}"

    def _get_logger(self):
        my_logger = logging.getLogger('CloudWatchClient')
        my_logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        my_logger.addHandler(handler)
        return my_logger
