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
    def __init__(self, query_source):
        super().__init__()

        self.query_source = query_source

    def query(self, tree):
        return (*self.visit(tree.children[0]), self.visit(tree.children[1]))

    def source(self, tree):
        if len(tree.children) == 1:
            return ('page', tree.children[0])
        elif len(tree.children) == 2:
            return tree.children

    def nested_selectors(self, tree):
        return self.visit(tree.children[0])

    def selector(self, tree):
        sel = self.visit(tree.children[0])
        nested = []
        into = None
        attribute = None
        if len(tree.children) > 1:
            for child in tree.children[1:]:
                if child.data == 'as_named':
                    into = child.children[0]
                elif child.data == 'nested_selectors':
                    nested = self.visit(child)
                elif child.data == 'attribute_selector':
                    attribute = child.children[0]
                else:
                    raise ValueError(f'Unidentified selector child: {child.data!r}')

        if into:
            sel.into(into)
        if nested:
            sel.nested = nested
        if attribute:
            sel.attribute = attribute

        return sel

    def selectors(self, tree):
        return s.alt(*(self.visit(child) for child in tree.children))

    def page_selector(self, tree):
        return s.page()

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

    def text_group_selector(self, tree):
        return s.text_group(group_id=tree.children[0])

    def css_selector(self, tree):
        source = self.query_source[tree.meta.start_pos:tree.meta.end_pos]
        return s.css(css_selector=source)
