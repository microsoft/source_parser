# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# pylint: disable=line-too-long,fixme,too-many-nested-blocks,too-many-locals,too-many-branches

from collections import Counter
from typing import List, Tuple, Dict
import pickle
import re
from tree_sitter import Parser
from .config import get_language, LanguageId

PARSER = Parser()

# This dict will be removed when the file dir names equal to tree_sitter like names
lang2dirname = {
    LanguageId.BASH: "Bash",
    LanguageId.C: "C",
    LanguageId.CSS: "CSS",
    LanguageId.CPP: "C++",
    LanguageId.CSHARP: "CSharp",
    LanguageId.GO: "Go",
    LanguageId.HTML: "HTML",
    LanguageId.JAVA: "Java",
    LanguageId.JAVASCRIPT: "JavaScript",
    LanguageId.LUA: "Lua",
    LanguageId.PYTHON: "Python",
    LanguageId.PHP: "PHP",
    LanguageId.REGEX: "Regex",
    LanguageId.RUBY: "Ruby",
    LanguageId.RUST: "Rust",
    LanguageId.TYPESCRIPT: "TypeScript",
}

keywords = set(["int", "integer", "float", "string", "char", "character"])

lang2lits = {
    LanguageId.C: [["number_literal"], ["string_literal"], ["char_literal"], []],
    LanguageId.CPP: [
        ["number_literal"],
        ["string_literal", "raw_string_literal"],
        ["char_literal"],
        [],
    ],
    LanguageId.CSHARP: [
        ["integer_literal", "real_literal"],
        ["string_literal", "verbatim_string_literal"],
        ["character_literal"],
        [],
    ],
    LanguageId.GO: [
        ["int_literal", "float_literal", "imaginary_literal"],
        ["interpreted_string_literal", "raw_string_literal", "rune_literal"],
        [],
        [],
    ],
    LanguageId.JAVA: [
        [
            "decimal_floating_point_literal",
            "decimal_integer_literal",
            "hex_floating_point_literal",
            "hex_integer_literal",
            "octal_integer_literal",
            "binary_integer_literal"
        ],
        ["string_literal"],
        ["character_literal"],
        [],
    ],
    LanguageId.JAVASCRIPT: [
        ["number"],
        ["string", "template_string"],
        [],
        ["regex_pattern"],
    ],
    LanguageId.LUA: [["number"], ["string"], [], []],
    LanguageId.PYTHON: [["integer", "float"], ["string"], [], []],
    LanguageId.PHP: [["integer", "float"], ["string"], [], []],
    LanguageId.RUBY: [["integer", "float"], ["string", "bare_string"], [], []],
    LanguageId.RUST: [
        ["integer_literal", "float_literal"],
        ["string_literal", "raw_string_literal"],
        ["char_literal"],
        [],
    ],
    LanguageId.TYPESCRIPT: [
        ["number"],
        ["string", "template_string"],
        [],
        ["regex_pattern"],
    ],
}

lang2statements = {
    LanguageId.CSHARP: [
        "namespace_declaration",
        "class_declaration",
        "method_declaration",
        "struct_declaration",
        "interface_declaration",
        "operator_declaration",
        "record_declaration",
        "constructor_declaration",
        "destructor_declaration",
        "enum_declaration",
        "event_declaration",
        "event_field_declaration",
        "field_declaration",
        "property_declaration",
        "using_directive",
    ],
}


def get_tokens(node, tokens: List, types: List, preserve_statement: bool = False, lang: LanguageId = None):
    """
    Get all tokens from a TreeSitter like root node recursively.

    String-type node will be seen as one token.

    Parameters:

    node (`tree_sitter.Node`):
        A TreeSitter like root node
    tokens (`List`):
        List of all token positions. A token position is a list [start_point, end_point]. A point is a tuple (row, col).
    types (`List`):
        List of string, containing all token types.
    preserve_statement (`bool`):
        Whether to use a special token to mark the end of a statement.
    lang (`LanguageId`):
        LanguageId, default is None. It must be specified if preserve_statement is True.
    """
    if preserve_statement:
        assert lang is not None
    if len(node.children) == 0:
        tokens.append([node.start_point, node.end_point])
        types.append(str(node.type))
        return
    if (
        str(node.type) not in ["concatenated_string", "string_array", "chained_string"]
        and "string" in str(node.type)
        or "char" in str(node.type)
    ):
        tokens.append([node.children[0].start_point, node.children[-1].end_point])
        types.append(str(node.type))
        return
    for child in node.children:
        get_tokens(child, tokens, types, preserve_statement, lang)
        if preserve_statement:
            if "statement" in child.type or child.type in lang2statements[lang]:
                if types[-1] != "endofstatement":
                    tokens.append([-1, -1])
                    types.append("endofstatement")


def file_tokenizer(code: str, lang: LanguageId) -> List[str]:
    """
    Tokenize a source code snippet. (File, method or anything can be parsed by tree-sitter is ok)

    Parameters:

    code (`string`):
        source code snippets
    lang (`LanguageId`):
        program language of code

    Returns:

    tokens (`List[str]`):
        tokenized code
    """
    try:
        PARSER.set_language(get_language(lang))
        tree = PARSER.parse(bytes(code, "utf8"))
        root = tree.root_node
        tokens = []
        types = []
        get_tokens(root, tokens, types)
        _, tokens, _ = _file_tokenizer(code, tokens, types, False)
        return tokens
    except Exception:
        return []


def _file_tokenizer(
    code: str, positions: List, types: List, keep_newline: bool = True
) -> Tuple[List, List, List]:
    """
    Tokenize a file from token positions and their types. Return positions, code tokens and types.

    Returned positions and types are not exact same as the original. '\\n' with no position and type 'new_line' is added.

    Parameters:

    code (`string`):
        source code snippets
    positions (`List`):
        List of all token positions. A token position is a list [start_point, end_point]. A point is a tuple (row, col).
    types (`List`):
        List of string, containing all token types.
    Keep_newline (`bool`):
        whether count '\n' as a token

    Returns:

    ret_pos (`List`):
        Same as tokens except '\\n' has no position
    ret_code (`List`):
        code tokens
    ret_type (`List`):
        Same as types except '\\n' has type 'new_line'
    """
    code = bytes(code, "utf8")
    code = code.split(b"\n")
    prev_line = 0
    ret_pos = []
    ret_code = []
    ret_type = []
    for i, token in enumerate(positions):
        if token[0] == -1 and types[i] == "endofstatement":
            # special
            ret_pos.append([])
            ret_code.append("<endofstatement>")
            ret_type.append("endofstatement")
            continue
        sp = token[0]
        ep = token[1]
        if sp[0] != prev_line and keep_newline:
            ret_pos.append([])
            ret_code.append("\n")
            ret_type.append("new_line")
        prev_line = ep[0]
        if types[i] == "preproc_arg":
            # This occurs in C++ after #defines and other preprocs
            # Everything after the identifier is thrown in here,
            # hence requires separate processing
            ret_pos.append(token)
            ret_type.append(types[i])

            # This will at least get rid of comments
            uncommented_code = code[sp[0]][sp[1]: ep[1]].decode("utf-8").split("//")[0]
            uncommented_code = re.sub(r"\/\*(.|\n)*\*\/", "", uncommented_code)
            ret_code.append(uncommented_code)
        elif sp[0] == ep[0]:
            ret_pos.append(token)
            ret_code.append(code[sp[0]][sp[1]: ep[1]].decode("utf-8"))
            ret_type.append(types[i])
        else:
            out = code[sp[0]][sp[1]:]
            for lineid in range(sp[0] + 1, ep[0]):
                out += code[lineid]
            out += code[ep[0]][: ep[1]]
            ret_pos.append(token)
            ret_code.append(out.decode("utf-8"))
            ret_type.append(types[i])

    # Manually check for empty final line
    if code[-1].strip() == b"" and keep_newline and ret_code[-1] != "\n":
        ret_pos.append([])
        ret_code.append("\n")
        ret_type.append("new_line")

    return ret_pos, ret_code, ret_type


class LiteralCount():

    PARSER = Parser()

    def __init__(
        self, lang: LanguageId, token_limit: int = 50000, load_file: str = None
    ):
        r"""
        Initialize lit_counter, a dict for counting all literals of 4 kinds which are:
        `number literals` like '10', `string literals` like '\_\_main\_\_', `character literals` like 'M', `regex pattern literals` like '^[a-z]+'.

        lit_counter is in this format: `{'str': Counter(), 'num': Counter(), 'char': Counter(), 'regex': Counter()}`

        Parameters:

        lang (`LanguageId`):
            language of source code
        token_limit (`int`):
            Max length of token list. If a given code has more than token_limit tokens, it will be omitted. default is 50000.
        load_file (`str`):
            path of the pickle to load. If is not None. lits_counter will be loaded from it. default is None.

        """
        self.lang = lang
        self.token_limit = token_limit
        if load_file is not None:
            self.load_from_file(load_file)
        else:
            self.lits_counter = {
                "str": Counter(),
                "num": Counter(),
                "char": Counter(),
                "regex": Counter(),
            }

    def load_from_file(self, file_name: str):
        """
        load literal counters from old saving file

        Parameters:

        file_name (`str`):
            path of file to load
        """
        try:
            with open(file_name, "rb") as f:
                self.lits_counter = pickle.load(f)
        except Exception:
            self.lits_counter = {
                "str": Counter(),
                "num": Counter(),
                "char": Counter(),
                "regex": Counter(),
            }

    def save(self, file_name: str):
        """
        save literal counters into a pickle file

        Parameters:

        file_name (`str`):
            path of file to save
        """
        with open(file_name, "wb") as f:
            pickle.dump(self.lits_counter, f)

    def get_top_lits(
        self,
        num_keep: int = 50,
        str_keep: int = 100,
        char_keep: int = 30,
        regex_keep: int = 20,
    ) -> Dict:
        """
        Get high-frequency literals for each type

        Parameters:

        num_keep (`int`):
            how many number literals to keep, default is 50
        str_keep (`int`):
            how many string literals to keep, default is 100
        char_keep (`int`):
            how many character literals to keep, default is 30
        regex_keep (`int`):
            how many regex pattern literals to keep, default is 20

        Returns:
         (`Dict`):
            high-frequency literals {'num': List, 'str': List, 'char': List, 'regex': List}
        """
        num_lits = [key for key, _ in self.lits_counter["num"].most_common(num_keep)]
        str_lits = [key for key, _ in self.lits_counter["str"].most_common(str_keep)]
        char_lits = [key for key, _ in self.lits_counter["char"].most_common(char_keep)]
        regex_lits = [
            key for key, _ in self.lits_counter["regex"].most_common(regex_keep)
        ]
        return {
            "num": num_lits,
            "str": str_lits,
            "char": char_lits,
            "regex": regex_lits,
        }

    def count_lits(self, code: str) -> Dict:
        """
        Count number, string, character and regex pattern literals in given source code.

        Parameters:

        code (`str`):
            source code which can be parsed by tree-sitter

        Returns:

        lits (`Dict`):
            Number of all literals. {'num': Counter(), 'str': Counter(), 'char': Counter(), 'regex': Counter()}
        """
        lits = {
            "num": Counter(),
            "str": Counter(),
            "char": Counter(),
            "regex": Counter(),
        }
        if re.sub(re.compile(r"\s*\n"), "\n", code).count("\n") < 2:
            return lits
        str_quote_options = [
            r"(?<=\"\"\")(.*)(?=\"\"\")",
            r"(?<=\'\'\')(.*)(?=\'\'\')",
            r"(?<=\')(.*)(?=\')",
            r"(?<=\")(.*)(?=\")",
        ]
        try:
            tree = LiteralCount.PARSER.parse(bytes(code, "utf8"))
            root = tree.root_node
            tokens = []
            types = []
            get_tokens(root, tokens, types)
            if len(tokens) > self.token_limit:
                return lits
            _, tokens, types = _file_tokenizer(code, tokens, types)
            for token, tp in zip(tokens, types):
                if tp in lang2lits[self.lang][0]:
                    lits["num"][token] += 1
                elif tp in lang2lits[self.lang][1]:
                    for q in str_quote_options:
                        match = re.search(q, token)
                        if match:
                            strlit = match.group(0)
                            if 0 < len(strlit) <= 25:
                                strlit = strlit.replace(" ", "U+0020")
                                strlit = strlit.replace(",", "U+002C")
                                lits["str"][strlit] += 1
                            break
                elif tp in lang2lits[self.lang][2]:
                    for q in str_quote_options[2:]:
                        match = re.search(q, token)
                        if match:
                            charlit = match.group(0)
                            charlit = charlit.replace(" ", "U+0020")
                            charlit = charlit.replace(",", "U+002C")
                            lits["char"][charlit] += 1
                            break
                # TODO: regex pattern in TypeScript are not always right, fix it later
                elif tp in lang2lits[self.lang][3]:
                    if 0 < len(token) < 25 and " " not in token:
                        lits["regex"][token] += 1

            return lits
        except Exception:
            return lits

    def update(self, litses: List[Dict]):
        """
        Update self.lit_counter with list of new lits

        Parameters:

        litses (`List[Dict]`):
            List of lits, lits comes from count_lits
        """
        for lits in litses:
            for lit_type in ["num", "str", "char", "regex"]:
                self.lits_counter[lit_type].update(lits[lit_type])

    def prune(self, keep_num=50000):
        """
        Prune lits_counter given the number to keep in case of out-of-memory and remove lits only appearing once

        Parameters:

        keep_num (`int`):
            number of high-frequency literals to keep, default is 50000
        """
        for lit_type in ["num", "str", "char", "regex"]:
            kvs = self.lits_counter[lit_type].most_common(keep_num)
            self.lits_counter[lit_type].clear()
            for k, v in kvs:
                self.lits_counter[lit_type][k] = v


def normalize(
    code: str,
    lang: LanguageId,
    lits: Dict[str, List[str]] = None,
    comment: str = "remove",
    indent: bool = True,
    preserve_statement: bool = False,
    special_tokens_map: Dict[str, str] = None,
    special_chars: List[str] = None,
) -> str:
    r"""
    Normalize source code.

    Parse and tokenize code, \
    remove/nomalize/keep comments, \
    replace literals with \<XX_LIT\>; form, \
    track or not \<INDENT\>/\<DEDENT\>, \
    custom replacements with given tokens. \
    untokenize the code.

    Parameters:

    code (`str`):
        source code to normalize
    lang (`LanguageId`):
        language of the code
    lits (`Dict[str, List[str]]`):
        High-frequency literals which will be normalized in &lt;XX_LIT: lit&gt; form, default is None.
    comment (`str`):
        Comment handling logic. 'remove' will remove all comments. 'normalize' will change all comments to '#<COMMENT>'. 
        'keep' will keep comments as-is. default is 'remove'
    indent (`bool`):
        whether to keep track or not of &lt;INDENT&gt;/&lt;DEDENT&gt;, default is True
    preserve_statement (`bool`):
        Whether to use a special token to mark the end of a statement.
    special_tokens_map (`Dict[str, str]`):
        custom replacements with these given tokens, default is None
    special_chars (`List[str]`):
        List of special characters to convert. They will be converted to the following format: 
        "U+0000" where 0000 is the unicode for the character. default is None

    Returns:

    norm_code (`str`):
        normalized code
    """
    PARSER.set_language(get_language(lang))
    if lits is None:
        lits = {}
    for name in ["num", "str", "char", "regex"]:
        if name not in lits:
            lits[name] = []
    if special_tokens_map is None:
        special_tokens_map = {}
    if special_chars is None:
        special_chars_map = {}
    else:
        special_chars_map = {
            c: f"U+{format(ord(c),'X').zfill(4)}" for c in special_chars
        }
    try:
        tree = PARSER.parse(bytes(code, "utf8"))
        root = tree.root_node
        tokens = []
        types = []
        get_tokens(root, tokens, types, preserve_statement, lang)
        handle_negative_number(tokens, types, lang2lits[lang][0])
        poss, tokens, types = _file_tokenizer(code, tokens, types)
        norm_code = norm_untokenize(
            poss,
            tokens,
            types,
            lang2lits[lang],
            lits,
            comment,
            indent,
            special_tokens_map,
            special_chars_map,
        )
        return norm_code
    except Exception:
        return ""


def handle_negative_number(tokens, types, numeric_lteral_types):
    i = 0
    while i < len(types):
        if types[i] == '-':
            handle_negative_case(tokens, types, i, numeric_lteral_types)
        i += 1


def handle_negative_case(tokens, types, negative_index, numeric_literal_types):
    if types[negative_index + 1] not in numeric_literal_types:
        return
    if (is_numeric_operator_field(types[negative_index - 1])
        or types[negative_index - 1] == ","
        or types[negative_index - 1] == "("
        or types[negative_index - 1] == "{"
            or types[negative_index - 1] == "["):
        # This is a negative number and not a subtraction
        tokens[negative_index][1] = tokens[negative_index + 1][1]
        types[negative_index] = types[negative_index + 1]

        for i in range(negative_index + 1, len(types) - 1):
            tokens[i] = tokens[i + 1]
            types[i] = types[i + 1]
        tokens.pop()
        types.pop()


def is_numeric_operator_field(field):
    return field in ("=", "==", "===", "!=", "!==", "+", "-", "*", "/", "%", "!", "not")


def norm_untokenize(
    poses: List[List[Tuple[int, int]]],
    tokens: List[str],
    types: List[str],
    litnames: List[List[str]],
    lits: Dict[str, List[str]],
    comment: str = "remove",
    indent: bool = True,
    special_tokens_map: Dict[str, str] = None,
    special_chars_map: Dict[str, str] = None,
) -> str:
    r"""
    Given code token list and their type and position in raw code.

    remove/nomalize/keep comments, \
    replace literals with \<XX_LIT\> form, \
    track or not \<INDENT\>/\<DEDENT\>, \
    custom replacements with given tokens. \
    untokenize the code and remove empty lines.

    Parameters:

    poses (`List[List[Point]]`):
        List of token positions. A position is [start_point, end_point]. A point is a tuple (row, col).
    tokens (`List[str]`):
        List of tokens.
    types (`List[str]`):
        List of token types.
    litnames (`List[List[str]]`):
        Indicates which token type is literal type for this language.
        litnames[0] is a list of number literals types, [1] is string, [2] is character, [3] is regex pattern.
        Only JavaScript and TypeScript have regex pattern.
    lits (`Dict[str, List[str]]`):
        High-frequency literals which will be normalized in &lt;XX_LIT: lit&gt; form, default is None.
    comment (`str`):
        Comment handling logic. 'remove' will remove all comments. 'normalize' will change all comments to '#<COMMENT>'. 'keep' will keep comments as-is. default is 'remove'
    indent (`bool`):
        whether to keep track or not of &lt;INDENT&gt;/&lt;DEDENT&gt;, default is True
    special_tokens_map (`Dict[str, str]`):
        custom replacements with these given tokens, default is None
    special_chars_map (`Dict[str, str]`):
        Dict of special characters to convert. They will be converted to the following format: "U+0000" where 0000 is the unicode for the character. default is None

    Returns:

    precessed_code (`str`):
        processed code.
    """
    code_string = ""
    prev_sp = None
    prev_ep = (0, 0)
    prev_indent = 0
    indent_size = -1
    for pos, token, tp in zip(poses, tokens, types):
        if tp in ("new_line", "\n"):
            code_string += "\n"
            continue
        if tp == "endofstatement":
            code_string += "<endofstatement>"
            continue
        sp = pos[0]
        ep = pos[1]
        add_token = token
        if "comment" in tp:
            if comment == "normalize":
                add_token = "#<COMMENT>"
            elif comment == "keep":
                add_token = token
            else:
                add_token = " " if token.startswith(" ") else ""
        # special token maps can't convert non-literal tokens
        elif tp in litnames[3] and token not in keywords:
            add_token = (
                special_tokens_map[token]
                if token in special_tokens_map
                else f"<REGEX_LIT:{token}>"
                if token in lits["regex"]
                else "<REGEX_LIT>"
            )
        elif tp in litnames[2] and token not in keywords:
            char_quote_options = ["'", '"']
            start_quote = ""
            end_quote = ""
            qualifier_regex = r"^[a-z]+"
            qualifier_match = re.search(qualifier_regex, token)
            qualifier = "" if not qualifier_match else qualifier_match[0]
            token_string = re.sub(qualifier_regex, "", token)
            char_lit = token_string
            for q in char_quote_options:
                if token_string.startswith(q):
                    start_quote = q
                    char_lit = char_lit[len(q):]
                    if token_string.endswith(q):
                        end_quote = q
                        char_lit = char_lit[: -len(q)]
                    break
            for sc, tc in special_chars_map.items():
                char_lit = char_lit.replace(sc, tc)
            if char_lit in special_tokens_map:
                add_token = special_tokens_map[char_lit]
            else:
                add_token = (
                    f"{qualifier}{start_quote}<CHAR_LIT:{char_lit}>{end_quote}"
                    if char_lit in lits["char"]
                    else f"{qualifier}{start_quote}<CHAR_LIT>{end_quote}"
                )
        elif tp in litnames[1] and token not in keywords:
            if token.startswith('R"('):
                # This is a C++ Raw String scenario. Must be handled separately.
                qualifier = "R"
                str_lit = token[len('R"('):-len('")')]
            else:
                # docstrings will be changed to <STR_LIT> too
                str_quote_options = ["'''", '"""', "'", '"', '`']
                start_quote = ""
                end_quote = ""
                qualifier_regex = r"^([a-z]+|@)"
                qualifier_match = re.search(qualifier_regex, token)
                # string qualifiers like 'r' for regex, 'f' for formatted string, 'b' for bytes, 'u' for unicode, etc (or combination of them)
                qualifier = "" if not qualifier_match else qualifier_match[0]
                # token string without qualifiers
                token_string = re.sub(qualifier_regex, "", token)
                # string literal without quotes
                str_lit = token_string
                for q in str_quote_options:
                    if token_string.startswith(q):
                        start_quote = q
                        str_lit = str_lit[len(q):]
                        if token_string.endswith(q):
                            end_quote = q
                            str_lit = str_lit[: -len(q)]
                        break
            # convert special characters
            for sc, tc in special_chars_map.items():
                str_lit = str_lit.replace(sc, tc)

            if str_lit in special_tokens_map:
                add_token = special_tokens_map[str_lit]
            else:
                add_token = (
                    f"{qualifier}<STR_LIT:{str_lit}>"
                    if str_lit in lits["str"]
                    else f"{qualifier}<STR_LIT>"
                )
        elif tp in litnames[0] and token not in keywords:
            add_token = (
                special_tokens_map[token]
                if token in special_tokens_map
                else f"<NUM_LIT:{token}>"
                if token in lits["num"]
                else "<NUM_LIT>"
            )

        if not prev_sp or (sp[0] == prev_ep[0] and sp[1] == prev_ep[1]):
            code_string += add_token
        elif sp[0] == prev_ep[0]:
            if code_string[-1] != " ":
                code_string += " "
            code_string += add_token
        else:
            if indent and add_token:
                code_string += "\n"
                omit = False
                if sp[1] != prev_indent and prev_indent == 0 and indent_size == -1:
                    indent_size = sp[1] - prev_indent
                if sp[1] - prev_indent > 0:
                    if sp[1] - prev_indent > 2 * indent_size:
                        omit = True
                    else:
                        for _ in range(prev_indent, sp[1], indent_size):
                            code_string += "<INDENT>"
                elif sp[1] - prev_indent < 0:
                    for _ in range(sp[1], prev_indent, indent_size):
                        code_string += "<DEDENT>"
                code_string += add_token
                if not omit:
                    prev_indent = sp[1]
            else:
                code_string += "\n"
                for _ in range(sp[1]):
                    code_string += " "
                code_string += add_token
        prev_sp, prev_ep = sp, ep
    processed_code = "".join(code_string).lstrip()
    return re.sub(re.compile(r"\s*\n"), "\n", processed_code)
