from pathlib import Path
from lark import Lark
import lark

from wikipedia_ql import selectors as s

class Parser:
    def __init__(self):
        # TODO: open_from_package (can't make it work for now?..)
        self.lark = Lark.open(
            Path(__file__).parent / 'wikipedia_ql.lark',
            start=["query", "selector", "selectors"],
            propagate_positions=True
        )

    def parse(self, source):
        tree = self.lark.parse(source, start="query")
        tree = ValueTransformer().transform(tree)
        return Interpreter(source).visit(tree)

    def parse_selector(self, source):
        tree = self.lark.parse(source, start="selectors")
        tree = ValueTransformer().transform(tree)
        return Interpreter(source).visit(tree)

class ValueTransformer(lark.visitors.Transformer):
    def STRING(self, val):
        return val[1:-1]

    def NUMBER(self, val):
        return int(val)

    def IDENT(self, val):
        return str(val)

    def attrib(self, children):
        k, op, v = children
        return ['attribute', {k: v}]

    def custom_function(self, children):
        if len(children) > 1:
            k, v = children
        else:
            k = children[0]
            v = True
        return ['function', {k: v}]

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
        name = None
        attribute = None
        if len(tree.children) > 1:
            for child in tree.children[1:]:
                if child.data == 'as_named':
                    name = child.children[0]
                elif child.data == 'nested_selectors':
                    nested = self.visit(child)
                elif child.data == 'attribute_selector':
                    attribute = self.visit(child)
                else:
                    raise ValueError(f'Unidentified selector child: {child.data!r}')

        if attribute and nested:
            # TODO: Better error
            raise ValueError('Can not have both attribute and children')

        if attribute:
            nested = attribute
            nested.name = name
            name = None

        if name:
            sel.name = name
        if nested:
            sel.nested = nested

        return sel

    def selectors_group(self, tree):
        return s.alt(*(self.visit(child) for child in tree.children))

    def custom_selector(self, tree):
        kind = str(tree.children[0]).replace('-', '_')
        attrs = {}
        functions = {}
        for type, value in tree.children[1:]:
            if type == 'function':
                functions = {**functions, **value}
            elif type == 'attribute':
                attrs = {**attrs, **value}

        if not hasattr(s, kind):
            raise ValueError(f'Unrecognized selector {kind}')

        return getattr(s, kind)(attrs=attrs, functions=functions)

    def attribute_selector(self, tree):
        return s.attr(attrs={'attr_name': tree.children[0]})

    def css_selector(self, tree):
        source = self.query_source[tree.meta.start_pos:tree.meta.end_pos]
        return s.css(attrs={'css_selector': source})

    def follow_link(self, tree):
        return s.follow_link(nested=self.visit(tree.children[0]))
