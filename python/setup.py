#!/usr/bin/env python3
"""
Setup script for Pentaho Language Pack Installer (Python version).
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read long description from README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding='utf-8')

setup(
    name='pentaho-languagepack-installer',
    version='9.0.0',
    description='Python-based language pack installer for Pentaho BI Server (v9+)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Pentaho Language Pack Team',
    url='https://github.com/lucasgdutra/pentahoLanguagePacks',
    packages=find_packages(),
    python_requires='>=3.7',
    install_requires=[
        'Flask>=2.3.0,<3.0.0',
        'flask-cors>=4.0.0',
    ],
    extras_require={
        'server': ['gunicorn>=21.2.0'],
    },
    entry_points={
        'console_scripts': [
            'pentaho-langpack=cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'Topic :: Software Development :: Localization',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
