from setuptools import setup, find_packages

setup(
    name="mtg-crafter",
    version="0.1.0",
    description="MTG Crafter - Data Management Tool for Magic: The Gathering",
    author="MTG Crafter Team",
    author_email="support@mtgcrafter.com",
    url="https://github.com/mtgcrafter/mtg-crafter",
    packages=find_packages(),
    install_requires=[
        "pyperclip",
        "requests",
        "tqdm",
        "beautifulsoup4"
    ],
    python_requires=">=3.8",
) 