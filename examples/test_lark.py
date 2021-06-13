import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.joinpath('..').resolve()))

from lark import Lark
import lark


from wikipedia_ql import selectors as s

from wikipedia_ql import fragment
from wikipedia_ql import media_wiki

query = '''from "The Beatles" { section["Discography"] as "albums" { li { a as "title" } } }'''

# class T(Transformer):
#     def css_selector(self, tok):
#         print(tok)
#         return tok

# query_parser = Lark(open('wikipedia_ql/wikipedia_ql.lark').read(), start="query", parser="lalr", transformer=T())
query_parser = Lark(open('wikipedia_ql/wikipedia_ql.lark').read(), start="query", propagate_positions=True)

parsed = query_parser.parse(query)

class QueryInterpreter(lark.visitors.Interpreter):
    def __init__(self, query):
        super().__init__()

        self.query_str = query

        self.page = None
        self.selectors = None

    def query(self, tree):
        self.page = eval(tree.children[0].children[0])

        self.selectors = self.visit(tree.children[1])

    def nested_selectors(self, tree):
        return [nested for selector in tree.children for nested in self.visit(selector)]

    def selector(self, tree):
        sel = self.visit(tree.children[0])
        nested = []
        into = None
        if len(tree.children) > 1:
            if tree.children[1].data == 'as_named':
                into = eval(tree.children[1].children[0])
                if len(tree.children) > 2:
                    nested = self.visit(tree.children[2])
            else:
                nested = self.visit(tree.children[1])

        if into:
            sel.into(into)

        return [sel, *nested]

    def selectors(self, tree):
        return s.all([self.visit(child) for child in tree.children])

    def section_selector(self, tree):
        return s.section(eval(tree.children[0]))

    def sentence_selector(self, tree):
        return s.sentence(eval(tree.children[0]))

    def text_selector(self, tree):
        return s.text(re.compile(str(tree.children[0])[1:-2]))

    def css_selector(self, tree):
        source = self.query_str[tree.meta.start_pos:tree.meta.end_pos]
        return s.css(source)

    def run(self):
        w = media_wiki.Wikipedia()
        print(self.selectors)
        return w.get_page(self.page).query(*self.selectors)

# print(TreeTransformer().transform(parsed))
i = QueryInterpreter(query)
i.visit(parsed)
# print(i.page)
# print(i.selectors)

print(i.run())

# page = parsed.children[0]
# print(parsed.children)

print( parsed.pretty() )
