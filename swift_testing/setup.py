#!/usr/bin/env python3
"""
Setup script for the SWIFT Message Routing Testing Framework.
"""

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="swift-testing",
    version="1.0.0",
    author="Simona Strecanska",
    author_email="simona.strec@gmail.com",
    description="Framework for testing SWIFT message generation and routing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/simonastrecanska/bachelor_thesis",
    package_dir={"": "."},
    packages=find_packages(where="."),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "psycopg2-binary>=2.9.5",
        "sqlalchemy>=2.0.0",
        "pandas>=1.5.0",
        "scikit-learn>=1.0.0",
        "matplotlib>=3.5.0",
        "pytest>=7.0.0",
        "python-dotenv>=0.21.0",
        "numpy>=1.22.0"
    ],
    entry_points={
        "console_scripts": [
            "swift-testing=swift_testing.src.interface.cli:main",
            "swift-check-db=swift_testing.check_database:main",
            "swift-view-messages=view_messages:main",
            "swift-generate-messages=generate_swift_messages:main",
            "swift-populate-templates=swift_testing.populate_templates:main",
            "swift-populate-variator-data=swift_testing.populate_variator_data:main"
        ],
    },
    include_package_data=True,
    package_data={
        "": ["config/*.yaml", "templates/*.txt"],
    },
) 