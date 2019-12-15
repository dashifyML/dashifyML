from setuptools import find_packages, setup

setup(
    name='dashify',
    version='0.0.1',
    packages=['dashify'],
    package_dir={'dashify': 'dashify'},
    package_data={'dashify': ['visualization/assets/css/*.css',
                              'visualization/assets/img/*.png',
                              'visualization/assets/img/*.svg']
                  },
    install_requires=[
        "dash",
        "dash-bootstrap-components",
        "dash_daq",
        "Flask-Caching"
    ],
    python_requires=">=3.0",
    scripts=['starter_scripts/dashify-vis'],
)