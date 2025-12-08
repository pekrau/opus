from setuptools import setup

setup(
    name="opus",
    version="0.1",
    description="Text structured in Python for rendering into different formats.",
    author="Per Kraulis",
    author_email="per.kraulis@gmail.com",
    license="MIT",
    install_requires=[
        "python-docx",
        "reportlab",
    ],
)
