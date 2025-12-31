"""
Setup configuration for Vach
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="vach",
    version="0.1.0",
    description="Automated civic accountability tracker for San Jose",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/vach",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.3",
        "lxml>=5.1.0",
        "feedparser>=6.0.11",
        "newspaper3k>=0.2.8",
        "sqlalchemy>=2.0.25",
        "ollama>=0.1.6",
        "chromadb>=0.4.22",
        "sentence-transformers>=2.3.1",
        "google-api-python-client>=2.111.0",
        "youtube-transcript-api>=0.6.2",
        "streamlit>=1.30.0",
        "plotly>=5.18.0",
        "python-dotenv>=1.0.1",
        "pandas>=2.1.4",
        "tqdm>=4.66.1",
        "tenacity>=8.2.3",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "black>=23.12.1",
            "flake8>=7.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "vach-setup=scripts.setup_database:main",
            "vach-scrape=scripts.run_scrapers:main",
            "vach-process=scripts.run_processor:main",
            "vach-health=scripts.health_check:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="civic-tech accountability government ai nlp",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/vach/issues",
        "Source": "https://github.com/yourusername/vach",
    },
)