from setuptools import setup, find_packages

setup(
    name="by.b",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["flask", "requests"],
    entry_points={
        "console_scripts": [
            "by.b=byb.cli:main",
        ],
    },
)
