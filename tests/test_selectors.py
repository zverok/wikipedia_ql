from dataclasses import dataclass
from wikipedia_ql.selectors import text, sentence, section, css, alt

def test_repr():
    assert text(pattern='.{4,10}').__repr__() == "text[pattern='.{4,10}']"
    assert section(heading='Section 1').__repr__() == "section[heading='Section 1']"
    assert css(css_selector="li.foo").__repr__() == "css[css_selector='li.foo']"
    assert sentence(pattern=r'This.*cool\.').__repr__() == r"sentence[pattern='This.*cool\\.']"

    assert alt(text(pattern='.{4,10}'), section(heading='Section 1')).__repr__() == \
        "text[pattern='.{4,10}']; section[heading='Section 1']"

    assert text(pattern='.{4,10}', name="x").__repr__() == "text[pattern='.{4,10}'] as 'x'"


    assert section(heading='Section 1',
        nested=css(css_selector="li.foo",
            nested=text(pattern='.{4,10}')
        )
    ).__repr__() == "section[heading='Section 1'] { css[css_selector='li.foo'] { text[pattern='.{4,10}'] } }"

    assert section(heading='Section 1', name='section',
                   nested=css(css_selector="li.foo", name="item",
                              nested=alt(text(pattern='.{4,10}', name="txt"), text(pattern=r'\s{2}', name="space")))
        ).__repr__() == \
        "section[heading='Section 1'] as 'section' { " + \
        "css[css_selector='li.foo'] as 'item' { " + \
        "text[pattern='.{4,10}'] as 'txt'; text[pattern='\\\\s{2}'] as 'space' " + \
        "} }"
