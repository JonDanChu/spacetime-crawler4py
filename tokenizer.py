"""
COMPSCI 121: Information Retrieval
Written by Noah Kim
Part A | Assignment 1
"""

import string
import sys
from itertools import islice
from collections.abc import Generator
from pathlib import Path

CHUNK_SIZE = 1000 # 1000 lines

TOKEN_CHARS = string.ascii_letters + string.digits      # Alphanumeric letters

def tokenizeHelper(text: str) -> list[str]:
    """
    Helper function that tokenizes a single chunk of text. Modified for purposes
    of assignment 2.
    """
    tokens = []
    word_start_idx = 0
    i = 0
    while i < len(text):
        if text[i] not in TOKEN_CHARS:
            cur_word = text[word_start_idx:i]
            if cur_word:
                tokens.append(cur_word.lower())
            word_start_idx = i+1
        i += 1

    if last_word := text[word_start_idx:]:
        tokens.append(last_word.lower())

    return tokens

def tokenize(text_file_path: str) -> Generator[list[str], None, None]:
    """
    Generator function that tokenizes a text file in chunks.
    
    Time complexity: O(n)

    The function uses itertools.islice to process the text file in chunks (
    specified by CHUNK_SIZE at the top of the file). This creates a lazy
    iterator that allows us to process the text file one line at a time without
    loading it all into memory. Using the iterator, we then iterate through
    the chunk line by line and tokenize them using tokenizeHelper().

    For each line, we read it into memory and tokenizeHelper() makes two passes
    through each line (as described in the docstring for tokenizeHelper()). So
    the time complexity is O(2n), or simply O(n).
    """
    result = []
    with open(text_file_path, 'r') as text_file:
        iteration = 1
        while True:
            lines_read = 0
            for line in islice(text_file, CHUNK_SIZE):
                result += tokenizeHelper(line)
                lines_read += 1

            if lines_read == 0:   # Iterator hit end of file
                break

            # print(f"read chunk {iteration}")
            yield result
            iteration += 1
            result = []


def computeWordFrequencies(token_list: list[str], db):
    """
    Function to compute the frequency of each token in a list of tokens. Similar
    to Python's built in collections.Counter. Modified for purposes of
    assignment 2
    """
    for token in token_list:
        token = token.lower()
        db[token] = str(int(db.get(token, 0)) + 1)


def printFrequencies(frequencies: dict[str, int]):
    """
    Prints a frequency dict to the shell.

    Time complexity: O(n log n)

    The function first sorts the dictionary in descending frequency order. This
    means that tokens with the highest frequencies will go first in the list.
    This operation is O(n log n). It then makes a single pass through new sorted
    list and prints it to the shell. As a result, the time complexity becomes
    O(n log n) + O(n) = O(n log n).
    """
    for t, f in sorted(
        frequencies.items(),
        key=lambda item: item[1],
        reverse=True
    ):
        print(f"{t} {f}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        raise Exception("Missing command line argument <file_path>.")

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        raise Exception(f"Invalid file path \"{file_path}\". Please try again.")

    frequencies = dict()

    # Iterate through each chunk of tokens
    for tokens in tokenize(file_path):
        new_frequencies = computeWordFrequencies(tokens)

        for new_word, new_freq in new_frequencies.items():
            frequencies[new_word] = frequencies.get(new_word, 0) + new_freq
    
    printFrequencies(frequencies)
