from dataclasses import dataclass
from wikipedia_ql.selectors import text, sentence, section, css, alt

def test_repr():
    assert text('.{4,10}').__repr__() == "text['.{4,10}']"
    assert section(heading='Section 1').__repr__() == "section[heading='Section 1']"
    assert css("li.foo").__repr__() == "css['li.foo']"
    assert sentence(r'This.*cool\.').__repr__() == r"sentence['This.*cool\\.']"

    assert alt(text('.{4,10}'), section(heading='Section 1')).__repr__() == \
        "text['.{4,10}'];section[heading='Section 1']"

    assert text('.{4,10}').into("x").__repr__() == "text['.{4,10}'] as 'x'"


    assert section(heading='Section 1',
        nested=css("li.foo",
            nested=text('.{4,10}')
        )
    ).__repr__() == "section[heading='Section 1'] { css['li.foo'] { text['.{4,10}'] } }"

    assert section(heading='Section 1',
        nested=css("li.foo",
            nested=text('.{4,10}').into("txt")
        ).into("item")
    ).into('section').__repr__() == \
        "section[heading='Section 1'] as 'section' { css['li.foo'] as 'item' { text['.{4,10}'] as 'txt' } }"
