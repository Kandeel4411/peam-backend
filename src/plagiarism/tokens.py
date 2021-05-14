import dataclasses
from typing import Tuple, List

from tree_sitter import TreeCursor


@dataclasses.dataclass(init=True)
class Token:
    """
    Structure that represents each source token with its original location and type
    """

    line: Tuple[int, int]
    string: str

    def __hash__(self):
        return hash(self.string)

    def __eq__(self, other):
        if isinstance(other, Token):
            return self.string == other.string
        else:
            return self.string == other

    def __repr__(self):
        return self.string


def parse_tree(cursor: TreeCursor, child_only: bool = True, is_named: bool = True) -> List[Token]:
    """
    Takes a root tree_setter cursor and returns a list of tokens in order.

    :child_only: if to return only child(leaf) nodes while navigating
    :is_named: if to return only named nodes
    """
    tokens = []
    last_child = None
    while cursor.goto_first_child():
        if is_named and not cursor.node.is_named():
            continue
        if not child_only:
            tokens.append(Token(string=cursor.node.type, line=(cursor.node.start_byte, cursor.node.end_byte)))
        else:
            last_child = cursor.node

    if child_only and last_child:
        tokens.append(Token(string=last_child.type, line=(last_child.start_byte, last_child.end_byte)))
    elif not child_only:
        if is_named and cursor.node.is_named():
            tokens.append(Token(string=cursor.node.type, line=(cursor.node.start_byte, cursor.node.end_byte)))
        elif not is_named:
            tokens.append(Token(string=cursor.node.type, line=(cursor.node.start_byte, cursor.node.end_byte)))

    while True:
        while cursor.goto_next_sibling():
            tokens.extend(parse_tree(cursor=cursor))
        if not cursor.goto_parent():
            break
    return tokens
