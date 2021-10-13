import setuptools

long_description = r"""
# WikipediaQL: querying structured data from Wikipedia

**WikipediaQL** is an _experimental query language_ and Python library for querying structured data from Wikipedia. It looks like this:

```python
from wikipedia_ql import media_wiki

wikipedia = media_wiki.Wikipedia()

print(wikipedia.query(r'''
    from "Guardians of the Galaxy (film)" {
        page@title as "title";
        section[heading="Cast"] as "cast" {
            li >> text["^(.+?) as (.+?):"] {
                text-group[1] as "actor";
                text-group[2] as "character"
            }
        };
        section[heading="Critical response"] {
            sentence["Rotten Tomatoes"] as "RT ratings" {
                text["\d+%"] as "percent";
                text["(\d+) (critic|review)"] >> text-group[1] as "reviews";
                text["[\d.]+/10"] as "overall"
            }
        }
    }
'''))

# {
#     'title': 'Guardians of the Galaxy (film)',
#     'cast': [{'actor': 'Chris Pratt', 'character': 'Peter Quill / Star-Lord'}, {'actor': 'Zoe Saldana', 'character': 'Gamora'}, {'actor': 'Dave Bautista', 'character': 'Drax the Destroyer'}, {'actor': 'Vin Diesel', 'character': 'Groot'}, {'actor': 'Bradley Cooper', 'character': 'Rocket'}, {'actor': 'Lee Pace', 'character': 'Ronan the Accuser'}, {'actor': 'Michael Rooker', 'character': 'Yondu Udonta'}, {'actor': 'Karen Gillan', 'character': 'Nebula'}, {'actor': 'Djimon Hounsou', 'character': 'Korath'}, {'actor': 'John C. Reilly', 'character': 'Rhomann Dey'}, {'actor': 'Glenn Close', 'character': 'Irani Rael'}, {'actor': 'Benicio del Toro', 'character': 'Taneleer Tivan / The Collector'}],
#     'RT ratings': {'percent': '92%', 'reviews': '328', 'overall': '7.82/10'}
# }
```

[Read full README.md on GitHub](https://github.com/zverok/wikipedia_ql)
"""

setuptools.setup(
    name="wikipedia_ql",
    version="0.0.3",
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
        "bs4",
        "nltk"
        # "nltk-data"
    ],
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
