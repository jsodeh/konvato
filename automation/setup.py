from setuptools import setup, find_packages

setup(
    name="betslip-converter-automation",
    version="1.0.0",
    description="Browser automation for betslip conversion",
    packages=find_packages(),
    install_requires=[
        "browser-use>=0.1.4",
        "playwright>=1.40.0",
        "openai>=1.3.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
    ],
    python_requires=">=3.11",
)