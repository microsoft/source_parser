# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# pylint: disable=reimported
from .python_parser import PythonParser
from .jsts_parser import JSTSParser as JavascriptParser  # for backwards compatibility
from .jsts_parser import JSTSParser as TypescriptParser
from .java_parser import JavaParser
from .cpp_parser import CppParser
from .csharp_parser import CSharpParser
from .ruby_parser import RubyParser
