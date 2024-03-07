# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest
from source_parser.parsers import JavascriptParser

DIR = "test/assets/typescript_examples/"


@pytest.mark.parametrize(
    "source, target",
    [
        (
            "test/assets/typescript_examples/exports.ts",
            [{'attributes': {'decorators': [],
                             'expression': ['name: string', 'year: number'],
                             'heritage': []},
              'definition': '       class Car',
              'byte_span': (149, 421),
              'class_docstring': '\nexported class\n',
              'end_point': (27, 1),
              'methods': [{'attributes': {},
                           'body': '{\n'
                           '      this.name = name;\n'
                           '      this.year = year;\n'
                           '    }',
                           'byte_span': (206, 285),
                           'default_arguments': {'name': '', 'year': ''},
                           'docstring': '',
                           'end_point': (18, 5),
                           'name': 'constructor',
                           'original_string': 'constructor(name, year) {\n'
                           '      this.name = name;\n'
                           '      this.year = year;\n'
                           '    }',
                           'signature': 'constructor(name, year)',
                           'start_point': (15, 4),
                           'syntax_pass': True},
                          {'attributes': {},
                           'body': '{\n'
                           '      let date = new Date();\n'
                           '      return date.getFullYear() - this.year;\n'
                           '    }',
                           'byte_span': (332, 419),
                           'default_arguments': {},
                           'docstring': '\nget the age of the car\n',
                           'end_point': (26, 5),
                           'name': 'age',
                           'original_string': 'age() {\n'
                           '      let date = new Date();\n'
                           '      return date.getFullYear() - '
                           'this.year;\n'
                           '    }',
                           'signature': 'age()',
                           'start_point': (23, 4),
                           'syntax_pass': True}],
              'name': 'Car',
              'original_string': 'export class Car {\n'
              '    name: string;\n'
              '    year: number;\n'
              '    \n'
              '    constructor(name, year) {\n'
              '      this.name = name;\n'
              '      this.year = year;\n'
              '    }\n'
              '\n'
              '    /*\n'
              '    get the age of the car\n'
              '    */\n'
              '    age() {\n'
              '      let date = new Date();\n'
              '      return date.getFullYear() - this.year;\n'
              '    }\n'
              '}',
              'start_point': (11, 7),
              'syntax_pass': True}]
        )
    ],
)
def test_get_exported_class(source, target):
    jp = JavascriptParser(open(source).read())
    print("target")
    print(target)
    assert jp.schema['classes'] == target


@pytest.mark.parametrize(
    "source, target",
    [
        (
            "test/assets/typescript_examples/exports.ts",
            set([
                "export function printHello(name)",
                "export const trustlySerializeData = function(data, method?, uuid?)"
            ])
        ),
        (
            "test/assets/typescript_examples/lawnMower.ts",
            set([
                "export async function myAsync(): Promise<Record<string, number | string>>"
            ])
        ),
        (
            "test/assets/typescript_examples/functionTypes.ts",
            set([
                "function getTime(): number",
                "function multiply(a: number, b: number)",
                "function pow(value: number, exponent: number = 10)",
                "function firstElement1<Type>(arr: Type[])"
            ])
        )
    ],
)
def test_get_signatures(source, target):
    jp = JavascriptParser(open(source).read())
    signatures = []
    for method in jp.schema['methods']:
        signatures.append(method['signature'])
    print("target")
    print(target)
    assert set(signatures) == target
