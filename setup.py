import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name='JobNinjaServer2Shared',
    version='0.0.1',
    author="JobNinjaServer",
    author_email="it@jobninja.com",
    description="Shared file for JobNinjaServer2 and HR4YOUImporter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lolobosse/JobNinjaServer2Shared",
    packages=setuptools.find_packages(),
    install_requires=requirements
)
