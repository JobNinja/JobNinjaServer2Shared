import sys
import os
import time

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cloud_watch_client import CloudWatchClient

# Initialize the CloudWatchClient in debug mode
client = CloudWatchClient(
    namespace='test_namespace',
    metric_dimensions={'Environment': 'Test'},
    debug_mode=True,
    AWS_ACCESS_KEY_ID='',
    AWS_ACCESS_KEY_SECRET=''
)

# Submit a test metric value
client.submit_value(
    metric_name='TestMetric',
    val=100,
    dimensions={'Instance': 'i-1234567890abcdef0'},
    unit='Count'
)


