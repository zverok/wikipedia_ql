import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="wikipedia_ql",
    version="0.0.1",
    author="Victor Shepelev",
    author_email="zverok.offline@gmail.com",
    description="Query Language for Wikipedia",
    long_description=long_description,
    url="https://github.com/zverok/wikipedia_ql",
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires='>=3.7'
)
