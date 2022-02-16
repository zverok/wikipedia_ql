import setuptools

long_description = r"""
# WikipediaQL: querying structured data from Wikipedia

**WikipediaQL** is an _experimental query language_ and, executable script, and Python library for querying structured data from Wikipedia. It looks like this:

```
$ wikipedia_ql --page "Guardians of the Galaxy (film)" \
    '{
      page@title as "title";
      section[heading="Cast"] as "cast" >> {
          li >> text:matches("^(.+?) as (.+?):") >> {
              text-group[group=1] as "actor";
              text-group[group=2] as "character"
          }
      };
      section[heading="Critical response"] >> {
          sentence:contains("Rotten Tomatoes") as "RT ratings" >> {
              text:matches("\d+%") as "percent";
              text:matches("(\d+) (critic|review)") >> text-group[group=1] as "reviews";
              text:matches("[\d.]+/10") as "overall"
          }
      }
    }'

title: Guardians of the Galaxy (film)
RT ratings:
  overall: 7.8/10
  percent: 92%
  reviews: '334'
cast:
- actor: Chris Pratt
  character: Peter Quill / Star-Lord
- actor: Zoe Saldaña
  character: Gamora
...
```

[Read full README.md on GitHub](https://github.com/zverok/wikipedia_ql)
"""

setuptools.setup(
    name="wikipedia_ql",
    version="0.0.6",
    author="Victor Shepelev",
    author_email="zverok.offline@gmail.com",
    description="Query Language for Wikipedia",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zverok/wikipedia_ql",
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires='>=3.7',
    install_requires=[
        "requests",
        "lark",
        "soupsieve>=2.3.1",
        "bs4",
        "nltk",
        "pyaml",
        # "nltk-data"
    ],
    scripts=["bin/wikipedia_ql"],
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
