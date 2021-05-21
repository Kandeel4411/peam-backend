from django.core.management.base import BaseCommand, CommandError
from tree_sitter import Language, Parser, Tree

from plagiarism.tokens import Token, parse_tree
from plagiarism.sources import parse_source, detect_plagiarism, tokenize_source


class Command(BaseCommand):
    def handle(self, *args, **options):
        first_source: str = """
        Test = 9
        def foo():
            def main():
                potato = potato + 1
                if bar:
                    baz()
            if bar:
                baz()
        Test = 10
        """
        second_source: str = """
        SomethingElse = 9
        def main():
            if bar:
                baz()
            def foo():
                potato += 1
                if bar:
                    baz()
        SomethingElse = 10
        """

        # Generate source tree
        first_tree: Tree = parse_source(source=first_source, ext=".py")
        second_tree: Tree = parse_source(source=second_source, ext=".py")

        # Parse tree to generate list of tokens
        first_parse: list[Token] = parse_tree(first_tree.walk(), is_named=None, child_only=False)
        second_parse: list[Token] = parse_tree(second_tree.walk(), is_named=None, child_only=False)

        # Displaying the two lists of tokens side by side
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

        # Detect plagiarism between two list of tokens and mark similarity in source code
        marked_first_source, marked_second_source, plag_ratio = detect_plagiarism(
            tokens1=first_parse, tokens2=second_parse, source1=first_source, source2=second_source
        )
        print(
            # Display highlighted plagiarism
            tokenize_source(
                source=first_source, marked_source=marked_first_source, start_token="\033[94m", end_token="\033[0m"
            )
        )
        print("\n----------")
        print(
            # Display highlighted plagiarism
            tokenize_source(
                source=second_source, marked_source=marked_second_source, start_token="\033[94m", end_token="\033[0m"
            )
        )
        print(f"\n\nPlagiarism Percentage: {plag_ratio*100:.5}%")
