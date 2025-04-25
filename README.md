# Shared files for python services
Used in JobNinjaServer2, HR4YOUImporter, SalesAutomation.

## Deployment and usage
Add the package to your dependencies list.
```
git+https://github.com/JobNinja/JobNinjaServer2Shared@main#egg=jn_tools
```
Import it using the name `jn_tools` in your code.
```python
from jn_tools import some_function
```
Don't install the package in the editable mode (-e) in production.

## Development
To debug the package in your dev evnironment, do the following:
- Remove the package from your dev environment via `pip uninstall jn_tools`.
- Clone the repo and change into the directory.
- Install the package in editable mode via `pip install -e . `.
- Check if the package is installed via `pip show jn_tools`. The location should point to the cloned repo.
