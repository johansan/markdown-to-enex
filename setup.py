from setuptools import setup, find_packages

setup(
    name="markdown-to-enex",
    version="0.1.0",
    description="Convert markdown files to Evernote ENEX format",
    author="Johan",
    packages=find_packages(),
    package_data={
        "markdown_to_enex": ["../config/*.json"],
    },
    install_requires=[
        "markdown>=3.8.0",
        "commonmark>=0.9.1",
    ],
    entry_points={
        "console_scripts": [
            "markdown-to-enex=markdown_to_enex.__main__:main",
        ],
    },
    python_requires=">=3.6",
)