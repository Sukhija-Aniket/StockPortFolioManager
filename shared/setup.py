from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="stock-portfolio-shared",
    version="0.1.5",
    author="Stock Portfolio Manager",
    description="Shared utilities for Stock Portfolio Manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=1.3.0",
        "gspread==6.1.2",
        "google-auth>=1.12.0",
        "google-auth-oauthlib>=0.4.1",
        "openpyxl>=3.0.0",
        "numpy>=1.20.0",
        "requests>=2.25.0",
        "python-dotenv>=0.19.0",
        "yfinance>=0.1.70",
        "pytz>=2021.1",
        "urllib3<2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
    },
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "stock-portfolio-shared=stock_portfolio_shared.cli:main",
        ],
    },
) 