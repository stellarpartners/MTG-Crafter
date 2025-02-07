from setuptools import setup, find_packages

setup(
    name="mtg-crafter",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'pyperclip',
        'requests',
        'tqdm',
        'beautifulsoup4'
    ],
    python_requires='>=3.8'
) 