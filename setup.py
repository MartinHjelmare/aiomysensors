"""Set up file for aiomysensors package."""
from pathlib import Path

from setuptools import find_packages, setup

PROJECT_DIR = Path(__file__).parent.resolve()
README_FILE = PROJECT_DIR / "README.md"
LONG_DESCR = README_FILE.read_text(encoding="utf-8")
VERSION = (PROJECT_DIR / "aiomysensors" / "VERSION").read_text().strip()
GITHUB_URL = "https://github.com/MartinHjelmare/aiomysensors"
DOWNLOAD_URL = f"{GITHUB_URL}/archive/master.zip"

REQUIRES = ["marshmallow"]


setup(
    name="aiomysensors",
    version=VERSION,
    description="Provide a package for aiomysensors",
    long_description=LONG_DESCR,
    long_description_content_type="text/markdown",
    author="Martin Hjelmare",
    author_email="marhje52@gmail.com",
    url=GITHUB_URL,
    download_url=DOWNLOAD_URL,
    packages=find_packages(exclude=["contrib", "docs", "tests*"]),
    python_requires=">=3.7",
    install_requires=REQUIRES,
    include_package_data=True,
    license="Apache-2.0",
    zip_safe=False,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Home Automation",
    ],
)
