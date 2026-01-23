from setuptools import setup

from opus.constants import __version__

setup(
    name="opus",
    version=__version__,
    description="Text defined in Python for output to PDF, DOCX and EPUB.",
    author="Per Kraulis",
    author_email="per.kraulis@gmail.com",
    license="MIT",
    install_requires=[
        "python-docx",
        "reportlab",
        "EbookLib",
        "PyYAML",
    ],
)
