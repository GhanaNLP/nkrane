from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tc-translate",
    version="0.1.0",
    author="Mich-Seth Owusu",
    author_email="michsethowusu@gmail.com",
    description="Terminology-Controlled Translator with Google Translate API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/GhanaNLP/tc-translate",
    packages=find_packages(),
    package_data={
        'tc_translate': ['terminologies/*.csv'],
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "googletrans @ git+https://github.com/michsethowusu/py-googletrans",
        "pandas>=1.3.0",
        "click>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "tc-translate=tc_translate.cli:main",
        ],
    },
    keywords="translation, terminology, google translate, localization",
)
