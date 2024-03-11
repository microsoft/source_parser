# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
A bunch of auxiliary functions for working with source-parser
"""

from copy import deepcopy
import re
from tree_sitter import Parser
from source_parser.parsers.python_parser import PythonParser
from source_parser.tree_sitter import normalize
from source_parser.tree_sitter.config import get_language, LanguageId

PARSER = Parser()
PARSER.set_language(get_language(LanguageId("python")))


def schematize_file(file_contents, parser=PARSER):
    return PythonParser(file_contents, parser=parser, remove_comments=False).schema


def schematize_method(meth_string, parser=PARSER):
    # raises IndexError when it fails (e.g. if the method has a terrible syntax error)
    schem_meth = schematize_file(left_adjust(meth_string), parser)["methods"][0]
    schem_meth["original_string"] = meth_string
    return schem_meth


def schematized_methods_are_equal(schematized_method1, schematized_method2):
    # in future will want to add a line number check
    if schematized_method1["original_string"] == schematized_method2["original_string"]:
        return True
    return False


def replace_schem_method(schem_file, schem_method, schem_bug):
    """Replaces schem_method from schem_file with schem_bug

    Used for inserting synthetic bugs
    """
    new_schem_file = deepcopy(schem_file)
    for i, cls in enumerate(schem_file["classes"]):
        for j, method in enumerate(cls["methods"]):
            if schematized_methods_are_equal(method, schem_method):
                new_schem_file["classes"][i]["methods"][j] = schem_bug
                return new_schem_file
    for i, method in enumerate(schem_file["methods"]):
        if schematized_methods_are_equal(method, schem_method):
            new_schem_file["methods"][i] = schem_bug
            return new_schem_file
    assert False  # should never get here...


def meth_has_syn_err(meth_string, parser=PARSER):
    """left adjusts the meth_string and then says if that has a syntax error"""
    try:
        schem_meth = schematize_method(meth_string, parser)
        if not schem_meth["syntax_pass"]:
            return True
    # pylint: disable=bare-except
    except:
        # pylint: enable=bare-except
        # can get IndexError, IndentationError, SyntaxError, TabError, ParseError, TokenError, TimeoutException
        return True
    return False


def filter_functions(list_of_gens):
    """filters a list of generated functions for syntactic correctness and dedupes them"""
    list_of_gens = [
        gen for gen in list_of_gens if not meth_has_syn_err(left_adjust(gen))
    ]
    normalized_gens = set()
    res = []
    for gen in list_of_gens:
        normalized_gen = normalize(gen, lang=LanguageId("python"))
        if normalized_gen not in normalized_gens:
            res.append(gen)
            normalized_gens.add(normalized_gen)
    return res


def span_select(file_text, schem_method):
    """grab the part of file_text spanned by schem_method, as dictated by its byte_span attribute"""
    file_bytes = file_text.encode("utf-8")
    start_byte, end_byte = schem_method["byte_span"]
    return file_bytes[start_byte:end_byte].decode("utf-8")


def yield_schem_meths(schem_file):
    """yields a schem_meth (dict) for each method in the schem_file

    adds a 'class_name' attribute if it's a class method
    """
    yield from schem_file["methods"]
    for schem_class in schem_file["classes"]:
        for schem_meth in schem_class["methods"]:
            schem_meth["class_name"] = schem_class["name"]
            yield schem_meth


def get_schem_meth_by_line_num(schem_file, line_num):
    for schem_meth in yield_schem_meths(schem_file):
        if schem_meth["start_point"][0] <= line_num <= schem_meth["end_point"][0]:
            return schem_meth
    return None


def get_filepath_to_schem_file(touched_filepaths):
    filepath_to_schem_file = {}
    for filepath in touched_filepaths:
        if filepath.strip():
            with open(filepath, "r", encoding="utf-8") as f:
                filetext = f.read()
            filepath_to_schem_file[filepath] = schematize_file(filetext)
    return filepath_to_schem_file


def get_class_dot_methname(schem_meth):
    """gets a canonical name for the method e.g. my_class.my_meth"""
    class_dot_methname = ""
    if "class_name" in schem_meth:
        class_dot_methname += schem_meth["class_name"] + "."
    class_dot_methname += schem_meth["name"]
    return class_dot_methname


def get_schem_meth_by_name(meth_name, schem_file, class_name=None):
    """provide a class_name iff we're looking for a class method"""
    for schem_meth in yield_schem_meths(schem_file):
        if not schem_meth["name"] == meth_name:
            continue
        if class_name is None and ("class_name" not in schem_meth):
            return schem_meth
        if class_name is not None and ("class_name" in schem_meth):
            if class_name == schem_meth["class_name"]:
                return schem_meth
    return None


def get_leading_whitespace(string):
    start, end = re.match(r"^(\s*)", string).span()
    return string[start:end]


def reindent(og_function, new_function):
    """reindents the new function in accordance with how the original function was indented"""
    indent = get_leading_whitespace(og_function)
    if len(indent) == 0:
        return new_function
    return indent + ("\n" + indent).join(new_function.splitlines())


def get_indent_str(schem_file):
    """gets the file's base unit of indentation e.g. '\t' or '    '"""
    for cls in schem_file["classes"]:
        for method in cls["methods"]:
            return get_leading_whitespace(method["original_string"])
    for method in schem_file["methods"]:
        first_line = method["original_string"].splitlines()[0].rstrip()
        if (
            first_line.endswith(":")
            and not first_line.strip().startswith("#")
            or first_line.startswith("@")
        ):
            rest = method["original_string"].splitlines()[1:]
            for line in rest:
                if line.strip() and not line.strip().startswith("#"):
                    leading_whitespace = get_leading_whitespace(line)
                    if len(leading_whitespace) > 0:
                        return leading_whitespace
    return "    "


def left_adjust(string):
    """needed because the schem_method['original_string']'s still have all their leading whitespace,
    and my edit model is trained to just take the left-adjusted method as input

    assumes that every line is at least as indented as the first
    """
    leading_whitespace_len = re.match(r"\s*", string).span()[1]
    if leading_whitespace_len == 0:
        return string
    return "\n".join(
        [line[leading_whitespace_len:] for line in string.splitlines()]
    )
