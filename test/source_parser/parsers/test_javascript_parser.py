# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# pylint: disable=line-too-long
from pprint import pprint
import pytest
from source_parser.parsers import JavascriptParser
from source_parser.parsers.language_parser import children_of_type


DIR = "test/assets/javascript_examples/"


def create_javascript_parser(source):
    with open(source, 'r', encoding='utf-8') as file:
        jp = JavascriptParser(file.read())
    return jp


@pytest.mark.parametrize(
    "source, target",
    [
        (
            "test/assets/javascript_examples/QueueUsing2Stacks.js",
            " implementation of Queue using 2 stacks\n contribution made by hamza chabchoub for a university project",
        ),
        (
            "test/assets/javascript_examples/NumberOfSubsetEqualToGivenSum.js",
            "\nGiven an array of non-negative integers and a value sum,\ndetermine the total number of the subset with sum\nequal to the given sum.\n",
        ),
        (
            "test/assets/javascript_examples/SHA256.js",
            "= ===============================================================\n SHA256.js\n\n Module that replicates the SHA-256 Cryptographic Hash\n function in Javascript.\n= ===============================================================",
        ),
        (
            "test/assets/javascript_examples/SHA1.js",
            "= ===============================================================\n SHA1.js\n\n Module that replicates the SHA-1 Cryptographic Hash\n function in Javascript.\n= ===============================================================",
        ),
        (
            "test/assets/javascript_examples/Abs.js",
            "\nauthor: PatOnTheBack\nlicense: GPL-3.0 or later\n\nModified from:\nhttps://github.com/TheAlgorithms/Python/blob/master/maths/abs.py\n\nThis script will find the absolute value of a number.\n\nMore about absolute values:\nhttps://en.wikipedia.org/wiki/Absolute_value\n",
        ),
        (
            "test/assets/javascript_examples/AverageMean.js",
            "\nauthor: PatOnTheBack\nlicense: GPL-3.0 or later\n\nModified from:\nhttps://github.com/TheAlgorithms/Python/blob/master/maths/average.py\n\nThis script will find the average (mean) of an array of numbers.\n\nMore about mean:\nhttps://en.wikipedia.org/wiki/Mean\n",
        ),
        (
            "test/assets/javascript_examples/BinarySearchTree.js",
            " Binary Search Tree!!\n\nNodes that will go on the Binary Tree.\nThey consist of the data in them, the node to the left, the node\nto the right, and the parent from which they came from.\n\nA binary tree is a data structure in which an element\nhas two successors(children). The left child is usually\nsmaller than the parent, and the right child is usually\nbigger.\n",
        ),
        ("test/assets/javascript_examples/Graph2.js", " create a graph class"),
    ],
)
def test_file_docstring(source, target):
    jp = create_javascript_parser(source)
    file_docstring = jp.file_docstring
    print("file_docstring")
    print(file_docstring)
    print("target")
    print(target)
    assert file_docstring == target


@pytest.mark.parametrize(
    "source, target",
    [
        ("test/assets/javascript_examples/QueueUsing2Stacks.js", []),
        (
            "test/assets/javascript_examples/NumberOfSubsetEqualToGivenSum.js",
            [
                "\nGiven solution is O(n*sum) Time complexity and O(sum) Space complexity\n",
                "",
            ],
        ),
        ("test/assets/javascript_examples/Abs.js", [""]),
        ("test/assets/javascript_examples/AverageMean.js", [""]),
        ("test/assets/javascript_examples/Graph2.js", []),
    ],
)
def test_function_docstring(source, target):
    function_docstring_list = []
    jp = create_javascript_parser(source)
    function_nodes = children_of_type(jp.tree.root_node, "function_declaration")
    for func in function_nodes:
        function_docstring_list.append(jp.get_docstring(jp.tree.root_node, func))
    print(target)
    print("now mine")
    print(function_docstring_list)
    assert function_docstring_list == target


@pytest.mark.parametrize(
    "source, target",
    [
        ("test/assets/javascript_examples/QueueUsing2Stacks.js", []),
        (
            "test/assets/javascript_examples/NumberOfSubsetEqualToGivenSum.js",
            ["NumberOfSubsetSum", "main"],
        ),
        (
            "test/assets/javascript_examples/SHA256.js",
            ["pad", "chunkify", "rotateRight", "preProcess", "SHA256"],
        ),
        (
            "test/assets/javascript_examples/SHA1.js",
            ["pad", "chunkify", "rotateLeft", "preProcess", "SHA1"],
        ),
        ("test/assets/javascript_examples/Abs.js", ["absVal"]),
        ("test/assets/javascript_examples/AverageMean.js", ["mean"]),
    ],
)
def test_function_names(source, target):
    function_names = []
    jp = create_javascript_parser(source)
    function_nodes = children_of_type(jp.tree.root_node, "function_declaration")
    for func in function_nodes:
        function_names.append(
            jp.span_select(
                JavascriptParser.get_first_child_of_type(func, type_string="identifier"), indent=False
            )
        )
    print(function_names)
    print(target)
    assert function_names == target


@pytest.mark.parametrize(
    "source, target",
    [
        ("test/assets/javascript_examples/QueueUsing2Stacks.js", []),
        (
            "test/assets/javascript_examples/KadaneAlgo.js",
            ["function KadaneAlgo (array)", "function main ()"],
        ),
        (
            "test/assets/javascript_examples/NumberOfSubsetEqualToGivenSum.js",
            ["function NumberOfSubsetSum (array, sum)", "function main ()"],
        ),
        (
            "test/assets/javascript_examples/SHA256.js",
            [
                "function pad (str, bits)",
                "function chunkify (str, size)",
                "function rotateRight (bits, turns)",
                "function preProcess (message)",
                "function SHA256 (message)",
            ],
        ),
        (
            "test/assets/javascript_examples/SHA1.js",
            [
                "function pad (str, bits)",
                "function chunkify (str, size)",
                "function rotateLeft (bits, turns)",
                "function preProcess (message)",
                "function SHA1 (message)",
            ],
        ),
        ("test/assets/javascript_examples/Abs.js", ["function absVal (num)"]),
        ("test/assets/javascript_examples/AverageMean.js", ["function mean (nums)"]),
        (
            "test/assets/javascript_examples/example3.js",
            ["function sum_then_multiply(a, c, b = 1)"],
        ),
    ],
)
def test_function_signature(source, target):
    function_signatures = []
    jp = create_javascript_parser(source)
    function_nodes = children_of_type(jp.tree.root_node, "function_declaration")
    for func in function_nodes:
        function_signatures.append(
            jp.get_signature_default_args(func)[0]
        )
    print(function_signatures)
    print("target")
    print(target)
    assert function_signatures == target


@pytest.mark.parametrize(
    "source, target",
    [
        ("test/assets/javascript_examples/QueueUsing2Stacks.js", []),
        (
            "test/assets/javascript_examples/NumberOfSubsetEqualToGivenSum.js",
            [
                "function NumberOfSubsetSum (array, sum) {\n  const dp = [] // create an dp array where dp[i] denote number of subset with sum equal to i\n  for (let i = 1; i <= sum; i++) {\n    dp[i] = 0\n  }\n  dp[0] = 1 // since sum equal to 0 is always possible with no element in subset\n\n  for (let i = 0; i < array.length; i++) {\n    for (let j = sum; j >= array[i]; j--) {\n      if (j - array[i] >= 0) {\n        dp[j] += dp[j - array[i]]\n      }\n    }\n  }\n  return dp[sum]\n}",
                "function main () {\n  const array = [1, 1, 2, 2, 3, 1, 1]\n  const sum = 4\n  const result = NumberOfSubsetSum(array, sum)\n  console.log(result)\n}",
            ],
        ),
        (
            "test/assets/javascript_examples/SHA256.js",
            [
                "function pad (str, bits) {\n  let res = str\n  while (res.length % bits !== 0) {\n    res = '0' + res\n  }\n  return res\n}",
                "function chunkify (str, size) {\n  const chunks = []\n  for (let i = 0; i < str.length; i += size) {\n    chunks.push(str.slice(i, i + size))\n  }\n  return chunks\n}",
                "function rotateRight (bits, turns) {\n  return bits.substr(bits.length - turns) + bits.substr(0, bits.length - turns)\n}",
                "function preProcess (message) {\n  // covert message to binary representation padded to\n  // 8 bits, and add 1\n  let m = message.split('')\n    .map(e => e.charCodeAt(0))\n    .map(e => e.toString(2))\n    .map(e => pad(e, 8))\n    .join('') + '1'\n\n  // extend message by adding empty bits (0)\n  while (m.length % 512 !== 448) {\n    m += '0'\n  }\n\n  // length of message in binary, padded, and extended\n  // to a 64 bit representation\n  let ml = (message.length * CHAR_SIZE).toString(2)\n  ml = pad(ml, 8)\n  ml = '0'.repeat(64 - ml.length) + ml\n\n  return m + ml\n}",
                "function SHA256 (message) {\n  // initial hash variables\n  let H0 = 0x6a09e667\n  let H1 = 0xbb67ae85\n  let H2 = 0x3c6ef372\n  let H3 = 0xa54ff53a\n  let H4 = 0x510e527f\n  let H5 = 0x9b05688c\n  let H6 = 0x1f83d9ab\n  let H7 = 0x5be0cd19\n\n  // pre-process message and split into 512 bit chunks\n  const bits = preProcess(message)\n  const chunks = chunkify(bits, 512)\n\n  chunks.forEach(function (chunk, i) {\n    // break each chunk into 16 32-bit words\n    const words = chunkify(chunk, 32)\n\n    // extend 16 32-bit words to 80 32-bit words\n    for (let i = 16; i < 64; i++) {\n      const W1 = words[i - 15]\n      const W2 = words[i - 2]\n      const R1 = rotateRight(W1, 7)\n      const R2 = rotateRight(W1, 18)\n      const R3 = rotateRight(W2, 17)\n      const R4 = rotateRight(W2, 19)\n      const S0 = parseInt(R1, 2) ^ parseInt(R2, 2) ^ (parseInt(W1, 2) >>> 3)\n      const S1 = parseInt(R3, 2) ^ parseInt(R4, 2) ^ (parseInt(W2, 2) >>> 10)\n      const val = parseInt(words[i - 16], 2) + S0 + parseInt(words[i - 7], 2) + S1\n      words[i] = pad((val >>> 0).toString(2), 32)\n    }\n\n    // initialize variables for this chunk\n    let [a, b, c, d, e, f, g, h] = [H0, H1, H2, H3, H4, H5, H6, H7]\n\n    for (let i = 0; i < 64; i++) {\n      const S1 = [6, 11, 25]\n        .map(turns => rotateRight(pad(e.toString(2), 32), turns))\n        .map(bitstring => parseInt(bitstring, 2))\n        .reduce((acc, curr) => acc ^ curr, 0) >>> 0\n      const CH = ((e & f) ^ (~e & g)) >>> 0\n      const temp1 = (h + S1 + CH + K[i] + parseInt(words[i], 2)) >>> 0\n      const S0 = [2, 13, 22]\n        .map(turns => rotateRight(pad(a.toString(2), 32), turns))\n        .map(bitstring => parseInt(bitstring, 2))\n        .reduce((acc, curr) => acc ^ curr, 0) >>> 0\n      const maj = ((a & b) ^ (a & c) ^ (b & c)) >>> 0\n      const temp2 = (S0 + maj) >>> 0\n\n      h = g\n      g = f\n      f = e\n      e = (d + temp1) >>> 0\n      d = c\n      c = b\n      b = a\n      a = (temp1 + temp2) >>> 0\n    }\n\n    // add values for this chunk to main hash variables (unsigned)\n    H0 = (H0 + a) >>> 0\n    H1 = (H1 + b) >>> 0\n    H2 = (H2 + c) >>> 0\n    H3 = (H3 + d) >>> 0\n    H4 = (H4 + e) >>> 0\n    H5 = (H5 + f) >>> 0\n    H6 = (H6 + g) >>> 0\n    H7 = (H7 + h) >>> 0\n  })\n\n  // combine hash values of main hash variables and return\n  const HH = [H0, H1, H2, H3, H4, H5, H6, H7]\n    .map(e => e.toString(16))\n    .map(e => pad(e, 8))\n    .join('')\n\n  return HH\n}",
            ],
        ),
        (
            "test/assets/javascript_examples/SHA1.js",
            [
                "function pad (str, bits) {\n  let res = str\n  while (res.length % bits !== 0) {\n    res = '0' + res\n  }\n  return res\n}",
                "function chunkify (str, size) {\n  const chunks = []\n  for (let i = 0; i < str.length; i += size) {\n    chunks.push(str.slice(i, i + size))\n  }\n  return chunks\n}",
                "function rotateLeft (bits, turns) {\n  return bits.substr(turns) + bits.substr(0, turns)\n}",
                "function preProcess (message) {\n  // convert message to binary representation padded to\n  // 8 bits, and add 1\n  let m = message.split('')\n    .map(e => e.charCodeAt(0))\n    .map(e => e.toString(2))\n    .map(e => pad(e, 8))\n    .join('') + '1'\n\n  // extend message by adding empty bits (0)\n  while (m.length % 512 !== 448) {\n    m += '0'\n  }\n\n  // length of message in binary, padded, and extended\n  // to a 64 bit representation\n  let ml = (message.length * CHAR_SIZE).toString(2)\n  ml = pad(ml, 8)\n  ml = '0'.repeat(64 - ml.length) + ml\n\n  return m + ml\n}",
                "function SHA1 (message) {\n  // main variables\n  let H0 = 0x67452301\n  let H1 = 0xEFCDAB89\n  let H2 = 0x98BADCFE\n  let H3 = 0x10325476\n  let H4 = 0xC3D2E1F0\n\n  // pre-process message and split into 512 bit chunks\n  const bits = preProcess(message)\n  const chunks = chunkify(bits, 512)\n\n  chunks.forEach(function (chunk, i) {\n    // break each chunk into 16 32-bit words\n    const words = chunkify(chunk, 32)\n\n    // extend 16 32-bit words to 80 32-bit words\n    for (let i = 16; i < 80; i++) {\n      const val = [words[i - 3], words[i - 8], words[i - 14], words[i - 16]]\n        .map(e => parseInt(e, 2))\n        .reduce((acc, curr) => curr ^ acc, 0)\n      const bin = (val >>> 0).toString(2)\n      const paddedBin = pad(bin, 32)\n      const word = rotateLeft(paddedBin, 1)\n      words.push(word)\n    }\n\n    // initialize variables for this chunk\n    let [a, b, c, d, e] = [H0, H1, H2, H3, H4]\n\n    for (let i = 0; i < 80; i++) {\n      let f, k\n      if (i < 20) {\n        f = (b & c) | (~b & d)\n        k = 0x5A827999\n      } else if (i < 40) {\n        f = b ^ c ^ d\n        k = 0x6ED9EBA1\n      } else if (i < 60) {\n        f = (b & c) | (b & d) | (c & d)\n        k = 0x8F1BBCDC\n      } else {\n        f = b ^ c ^ d\n        k = 0xCA62C1D6\n      }\n      // make sure f is unsigned\n      f >>>= 0\n\n      const aRot = rotateLeft(pad(a.toString(2), 32), 5)\n      const aInt = parseInt(aRot, 2) >>> 0\n      const wordInt = parseInt(words[i], 2) >>> 0\n      const t = aInt + f + e + k + wordInt\n      e = d >>> 0\n      d = c >>> 0\n      const bRot = rotateLeft(pad(b.toString(2), 32), 30)\n      c = parseInt(bRot, 2) >>> 0\n      b = a >>> 0\n      a = t >>> 0\n    }\n\n    // add values for this chunk to main hash variables (unsigned)\n    H0 = (H0 + a) >>> 0\n    H1 = (H1 + b) >>> 0\n    H2 = (H2 + c) >>> 0\n    H3 = (H3 + d) >>> 0\n    H4 = (H4 + e) >>> 0\n  })\n\n  // combine hash values of main hash variables and return\n  const HH = [H0, H1, H2, H3, H4]\n    .map(e => e.toString(16))\n    .map(e => pad(e, 8))\n    .join('')\n\n  return HH\n}",
            ],
        ),
        (
            "test/assets/javascript_examples/Abs.js",
            [
                "function absVal (num) {\n  // Find absolute value of `num`.\n  'use strict'\n  if (num < 0) {\n    return -num\n  }\n  // Executes if condition is not met.\n  return num\n}"
            ],
        ),
        (
            "test/assets/javascript_examples/AverageMean.js",
            [
                "function mean (nums) {\n  'use strict'\n  var sum = 0\n  var avg\n\n  // This loop sums all values in the 'nums' array.\n  nums.forEach(function (current) {\n    sum += current\n  })\n\n  // Divide sum by the length of the 'nums' array.\n  avg = sum / nums.length\n  return avg\n}"
            ],
        ),
    ],
)
def test_function_original_string(source, target):
    func_original = []
    jp = create_javascript_parser(source)
    function_nodes = children_of_type(jp.tree.root_node, "function_declaration")
    for func in function_nodes:
        func_original.append(jp.span_select(func, indent=False))
    assert func_original == target


@pytest.mark.parametrize(
    "source, target",
    [
        (
            "test/assets/javascript_examples/Graph2.js",
            [
                " adjacent list",
                " add vertex to the graph",
                " add edge to the graph",
                " Prints the vertex and adjacency list",
            ],
        ),
        (
            "test/assets/javascript_examples/QueueUsing2Stacks.js",
            [
                "",
                " Push item into the inputstack",
                "",
                " display elements of the inputstack",
                " display element of the outputstack",
            ],
        ),
    ]
    # these are the method docstrings inside of classes
)
def test_method_docstring(source, target):
    method_docstring = []
    jp = create_javascript_parser(source)
    class_nodes = children_of_type(jp.tree.root_node, "class_declaration")
    for class_node in class_nodes:
        class_method_nodes = []
        for child in class_node.children:
            if child.type == "class_body":
                class_body = child
                for grand_child in class_body.children:
                    if grand_child.type == "method_definition":
                        class_method_nodes.append(grand_child)
        parent_node = JavascriptParser.get_first_child_of_type(class_node, type_string="class_body")
        for method in class_method_nodes:
            method_docstring.append(jp.get_docstring(parent_node, method))
    print(method_docstring)
    print("target")
    print(target)
    assert method_docstring == target


@pytest.mark.parametrize(
    "source, target", [("test/assets/javascript_examples/example3.js", [{'a': '', 'c': '', 'b': '1'}])]
)
def test_func_default(source, target):
    jp = create_javascript_parser(source)
    list_of_default_dicts = []
    function_nodes = children_of_type(jp.tree.root_node, "function_declaration")
    for function in function_nodes:
        list_of_default_dicts.append(
            jp.get_signature_default_args(function)[1]
        )
    print(list_of_default_dicts)
    print("target")
    print(target)
    assert list_of_default_dicts == target


@pytest.mark.parametrize(
    "source, target",
    [
        (
            "test/assets/javascript_examples/example4.js",
            [
                {
                    "attributes": {
                        "decorators": ["@mixin(BrainMixin, PhilosophyMixin)"],
                        "expression": ["width = 20", "height = 10"],
                        "heritage": [],
                    }
                }
            ],
        ),
        (
            "test/assets/javascript_examples/example6.js",
            [
                {"attributes": {"decorators": [], "expression": [], "heritage": []}},
                {
                    "attributes": {
                        "decorators": [],
                        "expression": [],
                        "heritage": ["extends Animal"],
                    }
                },
            ],
        ),
    ],
)
def test_class_attributes(source, target):
    jp = create_javascript_parser(source)
    class_nodes = children_of_type(jp.tree.root_node, "class_declaration")
    results_holder = []
    for class_node in class_nodes:
        results = {}
        results["attributes"] = {}
        results["attributes"]["decorators"] = [
            jp.span_select(decorator_node, indent=False)
            for decorator_node in children_of_type(class_node, "decorator")
        ]
        results["attributes"]["expression"] = [
            jp.span_select(child, indent=False)
            for child in children_of_type(
                class_node.children[-1], "public_field_definition"
            )
        ]
        results["attributes"]["heritage"] = [
            jp.span_select(child, indent=False)
            for child in children_of_type(class_node, "class_heritage")
        ]
        results_holder.append(results)
    print(results_holder)
    print("target")
    print(target)
    assert results_holder == target


@pytest.mark.parametrize(
    "source, target",
    [
        ("test/assets/javascript_examples/NumberOfSubsetEqualToGivenSum.js", []),
        (
            "test/assets/javascript_examples/SHA1.js",
            [
                """import {reallyReallyLongModuleExportName as shortName}
  from '/modules/my-module.js';""",
            ],
        ),
        (
            "test/assets/javascript_examples/Abs.js",
            ["import {foo, bar} from '/modules/my-module.js';"],
        ),
        ("test/assets/javascript_examples/AverageMean.js", []),
    ],
)
def test_file_context(source, target):
    jp = create_javascript_parser(source)
    file_context = jp.file_context
    print("file_context")
    print(file_context)
    print("target")
    print(target)
    assert file_context == target


def test_schema_method():
    source = DIR + "example1.js"
    jp = create_javascript_parser(source)

    m1 = jp.schema["methods"][0]

    assert (
        m1["original_string"]
        == """function bytes(value, options, mone=12) {
  if (typeof value === 'string') {
    return parse(value);
  }

  if (typeof value === 'number') {
    return format(value, options);
  }

  return null;
}"""
    )
    assert (
        m1["docstring"]
        == """
Convert the given value in bytes into a string or parse to string to an integer in bytes.

@param {string|number} value
@param {{
 case: [string],
 decimalPlaces: [number]
 fixedDecimals: [boolean]
 thousandsSeparator: [string]
 unitSeparator: [string]
 }} [options] bytes options.

@returns {string|number|null}
"""
    )
    assert (
        m1["body"]
        == """{
  if (typeof value === 'string') {
    return parse(value);
  }

  if (typeof value === 'number') {
    return format(value, options);
  }

  return null;
}"""
    )
    assert m1["default_arguments"] == {'value': '', 'options': '', 'mone': '12'}
    assert m1["attributes"] == {"keywords": "function"}
    assert m1["name"] == "bytes"
    assert m1["signature"] == "function bytes(value, options, mone=12)"
    assert m1["start_point"] == (53, 0)
    assert m1["end_point"] == (63, 1)

    source = DIR + "functions.js"
    jp = create_javascript_parser(source)

    m1, m2, m3, m4, m5, m6, _, _, _ = jp.schema["methods"]

    assert (
        m2["original_string"]
        == """Animal.prototype.speak = function () {
    console.log(`${this.name} makes a noise.`);
}"""
    )
    assert m2["docstring"] == ""
    assert (
        m2["body"]
        == """{
    console.log(`${this.name} makes a noise.`);
}"""
    )
    assert m2["attributes"] == {}
    assert m2["name"] == ""
    assert m2["signature"] == "Animal.prototype.speak = function ()"
    assert m2["start_point"] == (4, 25)
    assert m2["end_point"] == (6, 1)

    assert (
        m3["original_string"]
        == """var animal = (
    function() {
        this.a = 0;
    }
)"""
    )
    assert m3["docstring"] == " comment"
    assert (
        m3["body"]
        == """{
        this.a = 0;
    }"""
    )
    assert m3["attributes"] == {}
    assert m3["name"] == ""
    assert m3["signature"] == "var animal = (\n    function()"
    assert m3["start_point"] == (10, 4)
    assert m3["end_point"] == (12, 5)

    assert (
        m4["original_string"]
        == """BobsGarage.Car = function() {

    /**
     * Engine
     * @constructor
     * @returns {Engine}
     */
    var Engine = function() {
        // definition of an engine
    };

    Engine.prototype.constructor = Engine;
    Engine.prototype.start = function() {
        console.log('start engine');
    }

    this.engine = new Engine();
};"""
    )
    assert m4["docstring"] == " comment"
    assert (
        m4["body"]
        == """{

    /**
     * Engine
     * @constructor
     * @returns {Engine}
     */
    var Engine = function() {
        // definition of an engine
    };

    Engine.prototype.constructor = Engine;
    Engine.prototype.start = function() {
        console.log('start engine');
    }

    this.engine = new Engine();
}"""
    )
    assert m4["attributes"] == {}
    assert m4["name"] == ""
    assert m4["signature"] == "BobsGarage.Car = function()"
    assert (
        m4["methods"][0]["original_string"]
        == """var Engine = function() {
        // definition of an engine
    };"""
    )
    assert (
        m4["methods"][1]["original_string"]
        == """Engine.prototype.start = function() {
        console.log('start engine');
    }"""
    )
    assert m4["start_point"] == (17, 17)
    assert m4["end_point"] == (34, 1)

    assert (
        m5["original_string"]
        == """const obj = {
    foo() {
        return 'bar';
    }
};"""
    )
    assert m5["docstring"] == " comment"
    assert m5["name"] == "foo"
    # NOTE the signature here is incorrect. This test simply confirms the current functionality, even though the correct output would be `foo()`
    assert m5["signature"] == "const obj = {\n    foo()"
    assert m5["start_point"] == (38, 4)
    assert m5["end_point"] == (40, 5)

    assert (
        m6["original_string"] == "const factorial = function fac(n=1) {return n < 2 ? 1 : n * fac(n-1)}"
    )
    assert m6["docstring"] == "  comment"
    assert m6["body"] == "{return n < 2 ? 1 : n * fac(n-1)}"
    assert m6["default_arguments"] == {"n": "1"}
    assert m6["name"] == "factorial"  # function fac is assigned to factorial
    assert m6["signature"] == "const factorial = function fac(n=1)"
    assert m6["start_point"] == (44, 18)
    assert m6["end_point"] == (44, 69)


@pytest.mark.parametrize(
    "source, target",
    [
        (
            "test/assets/javascript_examples/example4.js",
            [
                {
                    "class_docstring": "",
                    'definition': '@mixin(BrainMixin, PhilosophyMixin)\nclass',
                    "name": "SmallRectangle",
                    "attributes": {
                        "decorators": ["@mixin(BrainMixin, PhilosophyMixin)"],
                        "expression": ["width = 20", "height = 10"],
                        "heritage": [],
                    },
                    "byte_span": (0, 229),
                    "start_point": (0, 0),
                    "end_point": (12, 1),
                    "original_string": "@mixin(BrainMixin, PhilosophyMixin)\nclass SmallRectangle {\n  width = 20;\n  height = 10;\n  \n  get dimension() {\n    return {width: this.width, height: this.height};\n  }\n  increaseSize() {\n    this.width++;\n    this.height++;\n  }\n}",
                    "syntax_pass": True,
                    "methods": [
                        {
                            "attributes": {"keywords": "get"},
                            "body": "{\n    return {width: this.width, height: this.height};\n  }",
                            "byte_span": (93, 167),
                            "start_point": (5, 2),
                            "end_point": (7, 3),
                            "original_string": "get dimension() {\n    return {width: this.width, height: this.height};\n  }",
                            "docstring": "",
                            "default_arguments": {},
                            "name": "dimension",
                            "signature": "get dimension()",
                            "syntax_pass": True,
                        },
                        {
                            "attributes": {},
                            "original_string": "increaseSize() {\n    this.width++;\n    this.height++;\n  }",
                            "body": "{\n    this.width++;\n    this.height++;\n  }",
                            "byte_span": (170, 227),
                            "start_point": (8, 2),
                            "end_point": (11, 3),
                            "docstring": "",
                            "default_arguments": {},
                            "syntax_pass": True,
                            "name": "increaseSize",
                            "signature": "increaseSize()",
                        },
                    ],
                }
            ],
        )
    ],
)
def test_schema_class(source, target):
    jp = create_javascript_parser(source)
    class_info = jp.schema["classes"]
    pprint(class_info)
    print("target")
    pprint(target)
    assert class_info == target


def test_other_class():
    source = DIR + "OtherClass.js"
    jp = create_javascript_parser(source)

    c1 = jp.schema["classes"][0]
    assert (
        c1["original_string"]
        == """class {
    constructor(type) {
        this.type = type;
    }
    identify() {
        console.log(this.type);
    }
}"""
    )
    assert c1["class_docstring"] == " class"
    assert c1["name"] == "Animal"
    assert c1["attributes"] == {"decorators": [], "expression": [], "heritage": []}

    assert (
        c1["methods"][0]["original_string"]
        == """constructor(type) {
        this.type = type;
    }"""
    )
    assert (
        c1["methods"][1]["original_string"]
        == """identify() {
        console.log(this.type);
    }"""
    )
    assert c1["start_point"] == (3, 13)
    assert c1["end_point"] == (10, 1)
