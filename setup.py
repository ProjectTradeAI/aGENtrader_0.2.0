#!/usr/bin/env python3
"""
aGENtrader v2 - Setup script

This script helps with the installation of the aGENtrader v2 system.
"""

from setuptools import setup, find_packages

setup(
    name="agentrader",
    version="2.1.0",
    description="aGENtrader v2 - Multi-agent AI trading system",
    author="aGENtrader Team",
    author_email="agentrader@example.com",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "numpy>=1.19.0",
        "pandas>=1.1.0",
        "matplotlib>=3.3.0",
        "python-dotenv>=0.15.0",
        "psycopg2-binary>=2.8.6",
        "pyautogen>=0.1.0"
    ],
    entry_points={
        "console_scripts": [
            "agentrader=main:main",
        ],
    },
)