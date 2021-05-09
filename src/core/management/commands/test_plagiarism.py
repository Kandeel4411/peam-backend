import re
import difflib
import collections
import dataclasses
from typing import Tuple, List

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from tree_sitter import Language, Parser


@dataclasses.dataclass(init=True)
class Token:
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


def tokenize_source(old_source, new_source, marker="@", start_token="{{", end_token="}}"):
    tokenized_source = ""
    word_start = False
    for old_ch, new_ch in zip(old_source, new_source):
        if new_ch == marker and new_ch != old_ch:
            if not word_start:
                tokenized_source += "{{"
                word_start = True
        else:
            if word_start:
                tokenized_source += "}}"
                word_start = False
        tokenized_source += old_ch

    if word_start:
        tokenized_source += "}}"
    return tokenized_source


def parse_tree(cursor) -> List[Token]:
    result = []
    last_child = None
    while cursor.goto_first_child():
        last_child = cursor.node

    if last_child:
        result.append(Token(string=last_child.type, line=(last_child.start_byte, last_child.end_byte)))
    else:
        result.append(Token(string=cursor.node.type, line=(cursor.node.start_byte, cursor.node.end_byte)))

    while True:
        while cursor.goto_next_sibling():
            result.extend(parse_tree(cursor=cursor))
        if not cursor.goto_parent():
            break

    return result


class Command(BaseCommand):
    def handle(self, *args, **options):
        PY_LANG = Language(settings.PLAG_COMPILED_LIBRARY, "python")
        parser = Parser()
        parser.set_language(PY_LANG)

        first_source: str = """
        SomethingElse = 9
        def main():
            if bar:
                baz()
            def foo():
                potato += 1
                if bar:
                    baz()
        SomethingElse = 10
        """.strip()
        first_tree = parser.parse(
            bytes(
                first_source,
                "utf8",
            )
        )

        second_source: str = """
        Test = 9
        def foo():
            def main():
                potato = potato + 1
                if bar:
                    baz()
            if bar:
                baz()
        Test = 10
        """.strip()
        second_tree = parser.parse(
            bytes(
                second_source,
                "utf8",
            )
        )

        first_cursor = first_tree.walk()
        second_cursor = second_tree.walk()

        first_parse: list[Token] = parse_tree(first_cursor)
        second_parse: list[Token] = parse_tree(second_cursor)

        first = first_parse if len(first_parse) > len(second_parse) else second_parse
        first_taken_size = min(len(first_parse), len(second_parse))

        print("_________________________________\n")
        for fp, sp in zip(first_parse, second_parse):
            print(f"{str(fp):<20} | {str(sp)}")
        for leftover in first[first_taken_size:]:
            if first == first_parse:
                print(f"{str(leftover):<20} |")
            else:
                print(f"{' ':<20} | {str(leftover)}")

        print("_________________________________\n")

        seq_matcher = difflib.SequenceMatcher(None, first_parse, second_parse)
        new_first_source = first_source
        new_second_source = second_source
        for match in seq_matcher.get_matching_blocks():
            if match.size:
                for tkn in first_parse[match.a : match.a + match.size]:
                    new_first_source = (
                        new_first_source[: tkn.line[0]]
                        + "@" * (tkn.line[1] - tkn.line[0])
                        + new_first_source[tkn.line[1] :]
                    )
                for tkn in second_parse[match.b : match.b + match.size]:
                    new_second_source = (
                        new_second_source[: tkn.line[0]]
                        + "@" * (tkn.line[1] - tkn.line[0])
                        + new_second_source[tkn.line[1] :]
                    )

        print(tokenize_source(old_source=first_source, new_source=new_first_source))
        print("\n----------")
        print(tokenize_source(old_source=second_source, new_source=new_second_source))
        print(f"\n\nPlagiarism Percentage: {seq_matcher.ratio()*100}%")
