from lark import Lark
import lark

from wikipedia_ql import selectors as s

class Parser:
    def __init__(self):
        # TODO: open_from_package
        self.lark = Lark.open(
            'wikipedia_ql/wikipedia_ql.lark',
            start=["query", "selector"],
            propagate_positions=True
        )

    def parse(self, source):
        tree = self.lark.parse(source, start="query")
        tree = ValueTransformer().transform(tree)
        return Interpreter(source).visit(tree)

    def parse_selector(self, source):
        tree = self.lark.parse(source, start="selector")
        tree = ValueTransformer().transform(tree)
        return Interpreter(source).visit(tree)

class ValueTransformer(lark.visitors.Transformer):
    def STRING(self, val):
        return val[1:-1]

    def NUMBER(self, children):
        return int(children[0])

    def IDENT(self, val):
        return str(val)

    def attrib(self, children):
        k, op, v = children
        return {k: v}

class Interpreter(lark.visitors.Interpreter):
    def __init__(self, source):
        super().__init__()

        self.source = source

    def query(self, tree):
        return (tree.children[0].children[0], self.visit(tree.children[1]))

    def nested_selectors(self, tree):
        return self.visit(tree.children[0])

    def selector(self, tree):
        sel = self.visit(tree.children[0])
        nested = []
        into = None
        if len(tree.children) > 1:
            if tree.children[1].data == 'as_named':
                into = tree.children[1].children[0]
                if len(tree.children) > 2:
                    nested = self.visit(tree.children[2])
            else:
                nested = self.visit(tree.children[1])

        if into:
            sel.into(into)
        if nested:
            sel.nested = nested

        return sel

    def selectors(self, tree):
        return s.alt(*(self.visit(child) for child in tree.children))

    def section_selector(self, tree):
        attrs = {}
        for c in tree.children:
            attrs = {**attrs, **c}
        return s.section(**attrs)

    def sentence_selector(self, tree):
        pattern = tree.children[0] if tree.children else None
        return s.sentence(pattern=pattern)

    def text_selector(self, tree):
        return s.text(pattern=tree.children[0])

    def text_slice_selector(self, tree):
        return s.text_slice(group_id=tree.children[0])

    def css_selector(self, tree):
        source = self.source[tree.meta.start_pos:tree.meta.end_pos]
        return s.css(css_selector=source)
