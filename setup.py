from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="vibe-scraping",
    version="0.1.0",
    author="Luka",
    author_email="your.email@example.com",
    description="A library for scraping product information from websites using Groq API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/l0rtk/vibe-scraping",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "requests",
        "beautifulsoup4",
        "groq",
        "python-dotenv",
        "selenium",
    ],
    extras_require={
        "advanced": ["undetected-chromedriver", "webdriver-manager"],
    },
    entry_points={
        "console_scripts": [
            "vibe-scrape=vibe_scraping.cli:main",
        ],
    },
) 