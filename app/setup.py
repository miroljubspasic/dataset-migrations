from setuptools import setup

setup(
    name="dataset-tool",
    version="1.0",
    py_modules=["migration"],
    include_package_data=True,
    install_requires=["click", "requests", "setuptools", "typing_extensions", "pillow", "numpy", "python-dotenv", "prettytable"],
    entry_points="""
        [console_scripts]
        dataset=migration:cli
    """,
)