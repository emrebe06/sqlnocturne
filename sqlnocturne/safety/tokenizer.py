"""Small SQL tokenizer and normalizer.

This is not a complete SQL parser. V0.1 intentionally uses conservative
heuristics so the package remains dependency-free and easy to understand.
"""

from __future__ import annotations

import re


LINE_COMMENT_RE = re.compile(r"--[^\n\r]*")
BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
WHITESPACE_RE = re.compile(r"\s+")
TOKEN_RE = re.compile(
    r"""
    (?:'[^']*(?:''[^']*)*')
    |(?:"[^"]*(?:""[^"]*)*")
    |(?:`[^`]*`)
    |(?:\b[A-Za-z_][A-Za-z0-9_]*\b)
    |(?:\d+\.\d+|\d+)
    |(?:<=|>=|<>|!=|==)
    |(?:[(),;*=<>.+\-/])
    """,
    re.VERBOSE,
)


def strip_comments(sql: str) -> str:
    without_blocks = BLOCK_COMMENT_RE.sub(" ", sql or "")
    return LINE_COMMENT_RE.sub(" ", without_blocks)


def normalize_sql(sql: str) -> str:
    text = strip_comments(sql)
    text = WHITESPACE_RE.sub(" ", text).strip()
    return text


def uppercase_keywords(sql: str) -> str:
    return normalize_sql(sql).upper()


def tokenize(sql: str) -> list[str]:
    return [match.group(0) for match in TOKEN_RE.finditer(normalize_sql(sql))]


def normalized_tokens(sql: str) -> list[str]:
    return [token.upper() if not is_string_literal(token) else token for token in tokenize(sql)]


def is_string_literal(token: str) -> bool:
    return len(token) >= 2 and token[0] in {"'", '"', "`"} and token[-1] == token[0]


def first_keyword(sql: str) -> str:
    for token in normalized_tokens(sql):
        if token and token[0].isalpha():
            return token.upper()
    return ""


def split_statements(sql: str) -> list[str]:
    """Split on semicolons outside string literals."""

    statements: list[str] = []
    current: list[str] = []
    quote: str | None = None
    index = 0
    text = sql or ""
    while index < len(text):
        ch = text[index]
        if quote:
            current.append(ch)
            if ch == quote:
                if index + 1 < len(text) and text[index + 1] == quote:
                    current.append(text[index + 1])
                    index += 1
                else:
                    quote = None
        else:
            if ch in {"'", '"'}:
                quote = ch
                current.append(ch)
            elif ch == ";":
                part = "".join(current).strip()
                if part:
                    statements.append(part)
                current = []
            else:
                current.append(ch)
        index += 1
    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def has_keyword(tokens: list[str], keyword: str) -> bool:
    return keyword.upper() in {token.upper() for token in tokens}


def keyword_index(tokens: list[str], keyword: str) -> int:
    wanted = keyword.upper()
    for index, token in enumerate(tokens):
        if token.upper() == wanted:
            return index
    return -1


def contains_keyword_after(tokens: list[str], keyword: str, after: str) -> bool:
    after_index = keyword_index(tokens, after)
    if after_index == -1:
        return False
    wanted = keyword.upper()
    return any(token.upper() == wanted for token in tokens[after_index + 1 :])
