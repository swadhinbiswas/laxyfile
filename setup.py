#!/usr/bin/env python3
"""
Setup script for LaxyFile
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = []
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="laxyfile",
    version="1.0.0",
    description="Perfect Terminal-based file manager with AI integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="LaxyFile Team",
    author_email="team@laxyfile.dev",
    url="https://github.com/swadhinbiswas/laxyfile",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "laxyfile=laxyfile.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Filesystems",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    keywords="file manager terminal ui rich ai cli",
    project_urls={
        "Bug Reports": "https://github.com/swadhinbiswas/laxyfile/issues",
        "Source": "https://github.com/swadhinbiswas/laxyfile",
        "Documentation": "https://github.com/swadhinbiswas/laxyfile#readme",
    },
)
