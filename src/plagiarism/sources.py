import difflib
from typing import Optional, Tuple


from django.conf import settings
from tree_sitter import Language, Parser, Tree

from .tokens import Token


class SupportedLanguages:
    """
    Structure that represents the supported languages for plagiarism
    """

    python: str = "python"
    javascript: str = "javascript"
    exts: dict[str] = {".py": python, ".js": javascript}

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


def detect_plagiarism(
    tokens1: list[Token], tokens2: list[Token], source1: str, source2: str, marker: str
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
    source: str, marked_source: str, marker: str = "@", start_token: str = "{{", end_token: str = "}}"
) -> str:
    """
    Takes source code and marked source with a specific marker and returns a new tokenized source i.e:
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
