from dataclasses import dataclass
from wikipedia_ql.selectors import text

@dataclass
class FakeFragment:
    text: str
    soup = None

def test_text():
    def check(pattern, source):
        selector = text(text=pattern)
        return [*selector(FakeFragment(text=source))]

    assert check("1.*3", "0123456") == [(1, 4)]


    assert text(".{4,10").__repr__() == "text[text=~'.{4,10']"
