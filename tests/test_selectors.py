from dataclasses import dataclass
from wikipedia_ql.selectors import text, sentence, section, css, alt
from wikipedia_ql.parser import Parser

def repr(selector_source):
    return Parser().parse_selector(selector_source).__repr__()

def test_repr():
    assert repr('text:matches(".{4,10}")') == "text:matches('.{4,10}')"
    assert repr('section[heading="Section 1"]') == "section[heading='Section 1']"
    assert repr('li.foo') == "css[css_selector='li.foo']"
    assert repr(r'sentence:contains("This.*cool\.")') == r"sentence:contains('This.*cool\\.')"

    assert repr('{ text:matches(".{4,10}"); section[heading="Section 1"] }') == \
        "{ text:matches('.{4,10}'); section[heading='Section 1'] }"

    assert repr('text:matches(".{4,10}") as "x"') == "text:matches('.{4,10}') as 'x'"


    assert repr('section[heading="Section 1"] >> li.foo >> text:matches(".{4,10}")') == \
        "section[heading='Section 1'] >> css[css_selector='li.foo'] >> text:matches('.{4,10}')"

    assert repr('section[heading="Section 1"] as "section" >> ' + \
        'li.foo as "item" >> ' + \
        r'{ text:contains(".{4,10}") as "txt"; text:contains("\\s{2}") as "space" }') == \
        "section[heading='Section 1'] as 'section' >> css[css_selector='li.foo'] as 'item' >> " + \
        r"{ text:contains('.{4,10}') as 'txt'; text:contains('\\\\s{2}') as 'space' }"
