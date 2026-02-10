from setuptools import setup, find_packages

with open("../README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="toil-tracker",
    version="0.1.1",
    author="Amrut Pagidipally",
    author_email="amrutp24@github.com",
    description="Enhanced DevOps toil detection with advanced analytics and integrations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/amrutp24/toil-tracker",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "streamlit>=1.29.0",
        "pandas>=2.0.0",
        "plotly>=5.0.0",
        "pyyaml>=6.0",
        "requests>=2.25.0",
        "click>=8.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=22.0",
            "flake8>=4.0",
        ],
        "integrations": [
            "slack-sdk>=3.0",
            "jira>=3.0",
            "github-api>=1.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "toil-tracker=v2.enhanced_cli:main",
            "toil-analytics=v2.toil_analytics:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)