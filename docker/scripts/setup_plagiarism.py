"""
Compiles supported languages into a usable library for plagiarism detection.
"""

import time

from tree_sitter import Language


print("Compiling..")
start_time: float = time.perf_counter()

Language.build_library("build/languages.so", ["tree-sitter-python", "tree-sitter-javascript"])

end_time: float = time.perf_counter() - start_time
print(f"Successfully compiled libraries in  {end_time:.5}s.")
