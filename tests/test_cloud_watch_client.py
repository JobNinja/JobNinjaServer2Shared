from jn_tools.cloud_watch_client import CloudWatchClient

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
