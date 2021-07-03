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
    python_requires='>=3.7',
    classifiers=[
        "Development Status :: 3 - Alpha",

        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",

        "License :: OSI Approved :: MIT License",

        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",

        "Operating System :: OS Independent",

        "Topic :: Scientific/Engineering :: Information Analysis",
    ]
)
