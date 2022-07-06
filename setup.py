import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name='CloudWatchClient',
    version='0.0.1',
    scripts=['cloud_watch_client.py'],
    author="JobNinjaServer",
    author_email="it@jobninja.com",
    description="JobNinja CloudWatch Client",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yorubadeveloper/cloudwatchclient",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=requirements
)