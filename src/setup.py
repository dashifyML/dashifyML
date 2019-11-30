from setuptools import find_packages, setup

setup(
    name='dashify',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        "dash",
        "dash-bootstrap-components"
    ],
    python_requires="3.0"
)