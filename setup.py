from setuptools import setup

import opus

setup(
    name="opus",
    packages=["opus-python"],
    package_dir={"opus-python": "opus"},
    version=opus.__version__,
    description="Text defined in Python for output to different formats.",
    author="Per Kraulis",
    author_email="per.kraulis@gmail.com",
    license="MIT",
    install_requires=[
        "python-docx",
        "reportlab",
        "pyyaml",
    ],
)
