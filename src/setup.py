from setuptools import find_packages, setup

setup(
    name='dashifyML',
    version='0.1.2',
    packages=find_packages(),
    package_dir={'dashify': 'dashify'},
    package_data={'dashify': ['visualization/assets/css/*.css',
                              'visualization/assets/img/*.png',
                              'visualization/assets/img/*.svg']
                  },
    install_requires=[
        "pandas",
        "tqdm",
        "dash",
        "dash-bootstrap-components",
        "dash_daq",
        "Flask-Caching",
        "pandas",
        "tqdm",
        "seaborn",
        "dill"
    ],
    python_requires=">=3.0",
    scripts=['starter_scripts/dashify-vis'],
    url="https://github.com/dashifyML/dashifyML"
)
