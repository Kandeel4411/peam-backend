import difflib
import html
from typing import Optional, Tuple, Dict, List


from django.conf import settings
from tree_sitter import Language, Parser, Tree, TreeCursor

from .tokens import Token, parse_tree


class SupportedLanguages:
    """
    Structure that represents the supported languages for plagiarism
    """

    python: str = "python"
    javascript: str = "javascript"
    exts: Dict[str, str] = {".py": python, ".js": javascript}

    @classmethod
    def get_language(cls, language: str) -> Optional[Language]:
        """
        Takes one of the supported language options and returns a tree_sitter Language instance
        """
        if language in cls.exts.values():
            return Language(settings.PLAG_COMPILED_LIBRARY, language)
        else:
            return None

    @classmethod
    def detect_language(cls, ext: str) -> Optional[Language]:
        """
        Takes file extension and maps it to a possible supported language
        i.e  ".py" => Python
        """
        if ext in cls.exts:
            return cls.get_language(cls.exts[ext])
        else:
            return None


def parse_source(source: str, ext: str) -> Optional[Tree]:
    """
    Takes a program source code and a supported file extension and returns a valid tree_sitter Tree instance
    """
    language = SupportedLanguages.detect_language(ext=ext)
    if language is None:
        return None

    parser = Parser()
    parser.set_language(language)

    tree = parser.parse(bytes(source, "utf8"))
    return tree


def detect_plagiarism_ratio(source1: str, source2: str, ext: str) -> float:
    """
    Takes 2 sources codes and detects possible plagiarism by matching sequences and returns plagiarism ratio.
    """
    source_tree: TreeCursor = parse_source(source=source1, ext=ext)
    other_source_tree: TreeCursor = parse_source(source=source2, ext=ext)

    source_parse: list[Token] = parse_tree(source_tree.walk(), child_only=False)
    other_source_parse: list[Token] = parse_tree(other_source_tree.walk(), child_only=False)
    _, _, plag_ratio = match_sequences(
        tokens1=source_parse,
        tokens2=other_source_parse,
        source1=source1,
        source2=source2,
    )
    return plag_ratio


def match_sequences(
    tokens1: List[Token], tokens2: List[Token], source1: str, source2: str, marker: str = "@"
) -> Tuple[str, str, float]:
    """
    Takes 2 Token lists and source codes and detects possible plagiarism by matching sequences. Returns newly marked
    sources and plagiarism ratio.

    :tokens1: list of tokens that were generated from source1

    :tokens2: list of tokens that were generated from source2

    :source1: first source code

    :source2: second source code

    :marker: character marker that will be used to mark matchs
    """
    seq_matcher = difflib.SequenceMatcher(None, tokens1, tokens2)
    marked_source1 = source1
    marked_source2 = source2
    for match in seq_matcher.get_matching_blocks():
        if match.size:
            for tkn in tokens1[match.a : match.a + match.size]:  # noqa
                # Marking source 1
                marked_source1 = (
                    marked_source1[: tkn.line[0]]
                    + marker * (tkn.line[1] - tkn.line[0])  # noqa
                    + marked_source1[tkn.line[1] :]  # noqa
                )
            for tkn in tokens2[match.b : match.b + match.size]:  # noqa
                # Marking source 2
                marked_source2 = (
                    marked_source2[: tkn.line[0]]
                    + marker * (tkn.line[1] - tkn.line[0])  # noqa
                    + marked_source2[tkn.line[1] :]  # noqa
                )
    return marked_source1, marked_source2, seq_matcher.ratio()


def tokenize_source(
    source: str,
    marked_source: str,
    marker: str = "@",
    start_tokens: str = "{{",
    end_tokens: str = "}}",
    html_encoded: bool = False,
) -> str:
    """
    Takes source code and marked source with a specific marker and returns a new tokenized source:

    :source: the old source code that is unmarked

    :marked_source: the edited source code that is marked (must be the same length as :source:)

    :marker: the character marker that was used in marking the :marked_source:

    :start_tokens: tokens that will be appended at the start of each marked slice.
    if html encoding is enabled then start_tokens will be rendered as an unescaped html

    :end_tokens: tokens that will be appended at the end of each marked slice.
    if html encoding is enabled then end_tokens will be rendered as an unescaped html

    :html_encoded: if to return the tokenized source as html escaped text'

    ```
    # Source
    def foo():
        bar()
    # Marked source
    def @@@():
        @@@()
    # New tokenized source
    def {foo}():
        {bar}()
    ```
    """
    tokenized_source = ""
    word_start = False
    for old_ch, new_ch in zip(source, marked_source):
        if new_ch == marker and new_ch != old_ch:
            if not word_start:
                tokenized_source += start_tokens
                word_start = True
        else:
            if word_start:
                tokenized_source += end_tokens
                word_start = False

        if html_encoded:
            # This handles the case for if html tags were given they need to be closed before end of line
            if old_ch == "\n" and word_start:
                tokenized_source += end_tokens
                tokenized_source += html.escape(old_ch)
                tokenized_source += start_tokens
            else:
                tokenized_source += html.escape(old_ch)
        else:
            tokenized_source += old_ch

    if word_start:
        tokenized_source += end_tokens
    return tokenized_source
