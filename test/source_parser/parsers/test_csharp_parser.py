# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import pytest
from source_parser.parsers import CSharpParser

DIR = "test/assets/csharp_examples/"


@pytest.mark.parametrize(
    "source, target",
    [
        (
            DIR + "AttributeMethod.cs",
            """Copyright 2011 The Noda Time Authors. All rights reserved.
 Use of this source code is governed by the Apache License 2.0,
 as found in the LICENSE.txt file.""",
        ),
        (
            DIR + "Class.cs",
            """Copyright Syncfusion Inc. 2001 - 2020. All rights reserved.""",
        ),
        (
            DIR + "RegionCase.cs",
            "",
        ),
    ],
)
def test_file_docstring(source, target):
    with open(source, "r") as f:
        cp = CSharpParser(f.read())
        assert cp.schema["file_docstring"] == target


@pytest.mark.parametrize(
    "source, target",
    [
        (
            DIR + "AttributeClass.cs",
            [
                "using System;",
                "using DNTFrameworkCore.Authorization;",
            ],
        ),
        (
            DIR + "Class.cs",
            [
                "using System;",
                "using System.Globalization;",
                "using System.Reflection;",
                "using System.IO;",
                "using System.Diagnostics;",
                "using System.Collections.Generic;",
                "using System.Linq;",
            ],
        ),
    ],
)
def test_context(source, target):
    with open(source, "r") as f:
        cp = CSharpParser(f.read())
        assert cp.schema["contexts"] == target


def test_classes():
    source = DIR + "Class.cs"
    with open(source, "r") as f:
        cp = CSharpParser(f.read())

        classes = cp.schema['classes']
        assert len(classes) == 1

        cl = classes[0]

        assert cl["original_string"] == """        [Handler(typeof(IHandler))]
        public class IconFrame : IControlObjectSource, IHandlerSource
        {
                // field _a
                private virtual readonly string _a;
                public Size _s;
                object IHandlerSource.Handler
                {
                        get { return Handler; }
                }
                IHandler Handler { get; set; }

                /// <summary>
                /// Gets the pixel size of the frame's bitmap
                /// </summary>
                /// <value>The size in pixels of the frame.</value>
                public Size PixelSize { get { return Handler.GetPixelSize(this); } }

                public Size Size
                {
                        get { return Size.Ceiling((SizeF)PixelSize / Scale); }
                }
                // constructor
                IconFrame(float scale)
                {
                        Handler = Platform.Instance.CreateShared<IHandler>();
                        Scale = scale;
                }
                /// <summary>
                /// Initializes a new instance of the <see cref="Eto.Drawing.IconFrame"/> class.
                /// </summary>
                /// <param name="scale">Scale of logical to physical pixels.</param>
                /// <param name="bitmap">Bitmap for the frame</param>
                public IconFrame(float scale, Bitmap bitmap)
                        : this(scale)
                {
                        ControlObject = Handler.Create(this, bitmap);
                }
                /**
                 * This is used by platform implementations to create instances of this class with the appropriate control object.
                 * This is not intended to be called directly.
                 */
                public static IconFrame FromControlObject(float scale, object controlObject)
                {
                        return new IconFrame(scale) { ControlObject = controlObject };
                }

                /// <summary>
                /// Handler interface for platform implementations of the <see cref="IconFrame"/>
                /// </summary>
                [AutoInitialize(false)]
                public class IHandler
                {
                        /// <summary>
                        /// Gets the pixel size of the frame's bitmap
                        /// </summary>
                        /// <param name="frame">Frame instance to get the pixel size for</param>
                        /// <value>The size in pixels of the frame.</value>
                        Size GetPixelSize() {}
                }
        }"""

    assert cl["class_docstring"] == """<summary>
 Represents a frame in an <see cref="Icon"/>.
 </summary>
 <remarks>
 The IconFrame represents a single frame in an Icon.
 Each IconFrame can have a specific pixel size and scale, which will automatically be chosen based on the display and
 draw size of the image in various Eto controls.

 You can load an icon from an .ico, where all frames will have a 1.0 scale (pixel size equals logical size)
 </remarks>"""

    assert cl["name"] == "IconFrame"

    assert cl["body"] == """        {
                // field _a
                private virtual readonly string _a;
                public Size _s;
                object IHandlerSource.Handler
                {
                        get { return Handler; }
                }
                IHandler Handler { get; set; }

                /// <summary>
                /// Gets the pixel size of the frame's bitmap
                /// </summary>
                /// <value>The size in pixels of the frame.</value>
                public Size PixelSize { get { return Handler.GetPixelSize(this); } }

                public Size Size
                {
                        get { return Size.Ceiling((SizeF)PixelSize / Scale); }
                }
                // constructor
                IconFrame(float scale)
                {
                        Handler = Platform.Instance.CreateShared<IHandler>();
                        Scale = scale;
                }
                /// <summary>
                /// Initializes a new instance of the <see cref="Eto.Drawing.IconFrame"/> class.
                /// </summary>
                /// <param name="scale">Scale of logical to physical pixels.</param>
                /// <param name="bitmap">Bitmap for the frame</param>
                public IconFrame(float scale, Bitmap bitmap)
                        : this(scale)
                {
                        ControlObject = Handler.Create(this, bitmap);
                }
                /**
                 * This is used by platform implementations to create instances of this class with the appropriate control object.
                 * This is not intended to be called directly.
                 */
                public static IconFrame FromControlObject(float scale, object controlObject)
                {
                        return new IconFrame(scale) { ControlObject = controlObject };
                }

                /// <summary>
                /// Handler interface for platform implementations of the <see cref="IconFrame"/>
                /// </summary>
                [AutoInitialize(false)]
                public class IHandler
                {
                        /// <summary>
                        /// Gets the pixel size of the frame's bitmap
                        /// </summary>
                        /// <param name="frame">Frame instance to get the pixel size for</param>
                        /// <value>The size in pixels of the frame.</value>
                        Size GetPixelSize() {}
                }
        }"""

    assert cl["module_type"] == "class"
    assert cl["attributes"]["namespace_prefix"] == "Eto.Drawing."
    assert cl["attributes"]["bases"] == ["IControlObjectSource", "IHandlerSource"]
    assert cl["attributes"]["modifiers"] == ["public"]
    assert cl["attributes"]["attributes"] == ["Handler(typeof(IHandler))"]
    assert cl["start_point"] == (20, 8)
    assert cl["end_point"] == (80, 9)


def test_struct():
    source = DIR + "Struct.cs"
    with open(source, "r") as f:
        cp = CSharpParser(f.read())

        s2, s1 = cp.schema['classes']

    assert s1["original_string"] == """                public partial struct FMaterialParameterCollectionInfo
                {
                        /// <summary>Id that the collection had when this material was last compiled.</summary>
                        public FGuid StateId;
                        /// <summary>The collection which this material has a dependency on.</summary>
                        public UMaterialParameterCollection ParameterCollection;
                }"""
    assert s1["class_docstring"] == "<summary>Stores information about a parameter collection that this material references, used to know when the material needs to be recompiled.</summary>"
    assert s1["name"] == "FMaterialParameterCollectionInfo"
    assert s1["body"] == """                {
                        /// <summary>Id that the collection had when this material was last compiled.</summary>
                        public FGuid StateId;
                        /// <summary>The collection which this material has a dependency on.</summary>
                        public UMaterialParameterCollection ParameterCollection;
                }"""
    assert s1["module_type"] == "struct"
    assert s1["attributes"]["namespace_prefix"] == "UnrealEngine.ChildEngine."
    assert s1["attributes"]["bases"] == []
    assert s1["attributes"]["modifiers"] == ["public", "partial"]
    assert s1["attributes"]["attributes"] == []

    assert s2["original_string"] == """public readonly struct Coords
{
    public Coords(double x, double y)
    {
        X = x;
        Y = y;
    }

    public double X { get; }
    public double Y { get; }

    public override string ToString() => $"({X}, {Y})";
}"""
    assert s2["class_docstring"] == ""
    assert s2["name"] == "Coords"
    assert s2["body"] == """{
    public Coords(double x, double y)
    {
        X = x;
        Y = y;
    }

    public double X { get; }
    public double Y { get; }

    public override string ToString() => $"({X}, {Y})";
}"""
    assert s2["module_type"] == "struct"
    assert s2["attributes"]["namespace_prefix"] == ""
    assert s2["attributes"]["bases"] == []
    assert s2["attributes"]["modifiers"] == ["public", "readonly"]
    assert s2["attributes"]["attributes"] == []
    assert s2["start_point"] == (15, 0)
    assert s2["end_point"] == (27, 1)


def test_interface():
    source = DIR + "Interface.cs"
    with open(source, "r") as f:
        cp = CSharpParser(f.read())

        i1, i2, c1 = cp.schema['classes']

    assert i1["original_string"] == """    interface IEquatable<T>
    {
        bool Equals(T obj);
    }"""
    assert i1["class_docstring"] == ""
    assert i1["name"] == "IEquatable"
    assert i1["body"] == """    {
        bool Equals(T obj);
    }"""
    assert i1["module_type"] == "interface"
    assert i1["attributes"]["namespace_prefix"] == "Equal."
    assert i1["attributes"]["bases"] == []
    assert i1["attributes"]["modifiers"] == []
    assert i1["attributes"]["attributes"] == []
    assert i1["start_point"] == (3, 4)
    assert i1["end_point"] == (6, 5)

    assert i2["original_string"] == """    public interface ISampleInterface
    {
        // Property declaration:
        string Name
        {
            get;
            set;
        }
    }"""
    assert i2["class_docstring"] == ""
    assert i2["name"] == "ISampleInterface"
    assert i2["body"] == """    {
        // Property declaration:
        string Name
        {
            get;
            set;
        }
    }"""
    assert i2["module_type"] == "interface"
    assert i2["attributes"]["namespace_prefix"] == "Equal."
    assert i2["attributes"]["bases"] == []
    assert i2["attributes"]["modifiers"] == ["public"]
    assert i2["attributes"]["attributes"] == []
    assert i2["start_point"] == (8, 4)
    assert i2["end_point"] == (16, 5)


def test_class_fields():
    source = DIR + "Class.cs"
    with open(source, "r") as f:
        cp = CSharpParser(f.read())

        classes = cp.schema['classes']
        assert len(classes) == 1

        cl = classes[0]

    f1, f2 = cl["attributes"]["fields"]
    assert f1["original_string"] == "private virtual readonly string _a;"
    assert f1["docstring"] == "field _a"
    assert f1["modifiers"] == ["private", "virtual", "readonly"]
    assert f1["type"] == "string"
    assert f1["name"] == "_a"

    assert f2["original_string"] == "public Size _s;"
    assert f2["docstring"] == ""
    assert f2["modifiers"] == ["public"]
    assert f2["type"] == "Size"
    assert f2["name"] == "_s"


def test_class_properties():
    source = DIR + "Class.cs"
    with open(source, "r") as f:
        cp = CSharpParser(f.read())

        classes = cp.schema['classes']
        assert len(classes) == 1

        cl = classes[0]

    p1, p2, p3, p4 = cl["attributes"]["properties"]
    assert p1["original_string"] == """object IHandlerSource.Handler
                {
                        get { return Handler; }
                }"""
    assert p1["docstring"] == ""
    assert p1["modifiers"] == []
    assert p1["type"] == "object"
    assert p1["name"] == "Handler"
    assert p1["accessors"] == """{
                        get { return Handler; }
                }"""

    assert p2["original_string"] == "IHandler Handler { get; set; }"
    assert p2["docstring"] == ""
    assert p2["modifiers"] == []
    assert p2["type"] == "IHandler"
    assert p2["name"] == "Handler"
    assert p2["accessors"] == "{ get; set; }"

    assert p3["original_string"] == "public Size PixelSize { get { return Handler.GetPixelSize(this); } }"
    assert p3["docstring"] == """<summary>
 Gets the pixel size of the frame's bitmap
 </summary>
 <value>The size in pixels of the frame.</value>"""
    assert p3["modifiers"] == ["public"]
    assert p3["type"] == "Size"
    assert p3["name"] == "PixelSize"
    assert p3["accessors"] == "{ get { return Handler.GetPixelSize(this); } }"

    assert p4["original_string"] == """public Size Size
                {
                        get { return Size.Ceiling((SizeF)PixelSize / Scale); }
                }"""
    assert p4["docstring"] == ""
    assert p4["modifiers"] == ["public"]
    assert p4["type"] == "Size"
    assert p4["name"] == "Size"
    assert p4["accessors"] == """{
                        get { return Size.Ceiling((SizeF)PixelSize / Scale); }
                }"""


def test_struct_fields_properties():
    source = DIR + "Struct.cs"
    with open(source, "r") as f:
        cp = CSharpParser(f.read())

        s2, s1 = cp.schema['classes']

    f1, f2 = s1["attributes"]["fields"]
    assert f1["original_string"] == "public FGuid StateId;"
    assert f1["docstring"] == "<summary>Id that the collection had when this material was last compiled.</summary>"
    assert f1["modifiers"] == ["public"]
    assert f1["type"] == "FGuid"
    assert f1["name"] == "StateId"

    assert f2["original_string"] == "public UMaterialParameterCollection ParameterCollection;"
    assert f2["docstring"] == "<summary>The collection which this material has a dependency on.</summary>"
    assert f2["modifiers"] == ["public"]
    assert f2["type"] == "UMaterialParameterCollection"
    assert f2["name"] == "ParameterCollection"

    p1, p2 = s2["attributes"]["properties"]
    assert p1["original_string"] == "public double X { get; }"
    assert p1["docstring"] == ""
    assert p1["modifiers"] == ["public"]
    assert p1["type"] == "double"
    assert p1["name"] == "X"
    assert p1["accessors"] == "{ get; }"


def test_interface_fields_properties():
    source = DIR + "Interface.cs"
    with open(source, "r") as f:
        cp = CSharpParser(f.read())

        i1, i2, c1 = cp.schema['classes']

    p1 = i2["attributes"]["properties"][0]

    assert p1["original_string"] == """string Name
        {
            get;
            set;
        }"""
    assert p1["docstring"] == "Property declaration:"
    assert p1["modifiers"] == []
    assert p1["type"] == "string"
    assert p1["name"] == "Name"
    assert p1["accessors"] == """{
            get;
            set;
        }"""


def test_methods():
    source = DIR + "Class.cs"
    with open(source, "r") as f:
        cp = CSharpParser(f.read())

        classes = cp.schema['classes']
        assert len(classes) == 1

        cl = classes[0]

    m1, m2, m3 = cl["methods"]
    assert m1["original_string"] == """                IconFrame(float scale)
                {
                        Handler = Platform.Instance.CreateShared<IHandler>();
                        Scale = scale;
                }"""
    assert m1["docstring"] == "constructor"
    assert m1["name"] == "IconFrame"
    assert m1["body"] == """                {
                        Handler = Platform.Instance.CreateShared<IHandler>();
                        Scale = scale;
                }"""
    assert m1["signature"] == "                IconFrame(float scale)"
    assert m1["attributes"]["namespace_prefix"] == ""
    assert m1["attributes"]["modifiers"] == []
    assert m1["attributes"]["attributes"] == []
    assert m1["attributes"]["parameters"] == ["float scale"]
    assert m1["attributes"]["return_type"] == ""
    assert m1["start_point"] == (43, 16)
    assert m1["end_point"] == (47, 17)

    assert m2["original_string"] == """                public IconFrame(float scale, Bitmap bitmap)
                        : this(scale)
                {
                        ControlObject = Handler.Create(this, bitmap);
                }"""
    assert m2["docstring"] == """<summary>
 Initializes a new instance of the <see cref="Eto.Drawing.IconFrame"/> class.
 </summary>
 <param name="scale">Scale of logical to physical pixels.</param>
 <param name="bitmap">Bitmap for the frame</param>"""
    assert m2["name"] == "IconFrame"
    assert m2["body"] == """                {
                        ControlObject = Handler.Create(this, bitmap);
                }"""
    assert m2["signature"] == "                public IconFrame(float scale, Bitmap bitmap)"
    assert m2["attributes"]["namespace_prefix"] == ""
    assert m2["attributes"]["modifiers"] == ["public"]
    assert m2["attributes"]["attributes"] == []
    assert m2["attributes"]["parameters"] == [
        "float scale",
        "Bitmap bitmap",
    ]
    assert m2["attributes"]["return_type"] == ""
    assert m2["start_point"] == (53, 16)
    assert m2["end_point"] == (57, 17)

    assert m3["original_string"] == """                public static IconFrame FromControlObject(float scale, object controlObject)
                {
                        return new IconFrame(scale) { ControlObject = controlObject };
                }"""
    assert m3["docstring"] == """This is used by platform implementations to create instances of this class with the appropriate control object.
This is not intended to be called directly."""
    assert m3["name"] == "FromControlObject"
    assert m3["body"] == """                {
                        return new IconFrame(scale) { ControlObject = controlObject };
                }"""
    assert m3["signature"] == "                public static IconFrame FromControlObject(float scale, object controlObject)"
    assert m3["attributes"]["namespace_prefix"] == ""
    assert m3["attributes"]["modifiers"] == ["public", "static"]
    assert m3["attributes"]["attributes"] == []
    assert m3["attributes"]["parameters"] == [
        "float scale",
        "object controlObject",
    ]
    assert m3["attributes"]["return_type"] == "IconFrame"
    assert m3["start_point"] == (62, 16)
    assert m3["end_point"] == (65, 17)

    source = DIR + "AttributeMethod.cs"
    with open(source, "r") as f:
        cp = CSharpParser(f.read())

        classes = cp.schema['classes']

        cl = classes[0]

    m1, m2 = cl["methods"]
    assert m1["original_string"] == """        [Test]
        public void Value_Success()
        {
            ParseResult<int> result = ParseResult<int>.ForValue(5);
            Assert.AreEqual(5, result.Value);
        }"""
    assert m1["docstring"] == ""
    assert m1["name"] == "Value_Success"
    assert m1["body"] == """        {
            ParseResult<int> result = ParseResult<int>.ForValue(5);
            Assert.AreEqual(5, result.Value);
        }"""
    assert m1["signature"] == "        public void Value_Success()"
    assert m1["attributes"]["namespace_prefix"] == ""
    assert m1["attributes"]["modifiers"] == ["public"]
    assert m1["attributes"]["attributes"] == ["Test"]
    assert m1["attributes"]["parameters"] == []
    assert m1["attributes"]["return_type"] == "void"

    assert m2["original_string"] == """        [Test]
        public void Value_Failure()
        {
            Assert.Throws<UnparsableValueException>(() => FailureResult.Value.GetHashCode());
        }"""
    assert m2["docstring"] == ""
    assert m2["name"] == "Value_Failure"
    assert m2["body"] == """        {
            Assert.Throws<UnparsableValueException>(() => FailureResult.Value.GetHashCode());
        }"""
    assert m2["signature"] == "        public void Value_Failure()"
    assert m2["attributes"]["namespace_prefix"] == ""
    assert m2["attributes"]["modifiers"] == ["public"]
    assert m2["attributes"]["attributes"] == ["Test"]
    assert m2["attributes"]["parameters"] == []
    assert m2["attributes"]["return_type"] == "void"

    source = DIR + "Struct.cs"
    with open(source, "r") as f:
        cp = CSharpParser(f.read())

        s2, s1 = cp.schema['classes']

    m1, m2 = s2["methods"]
    assert m1["original_string"] == """    public Coords(double x, double y)
    {
        X = x;
        Y = y;
    }"""
    assert m1["docstring"] == ""
    assert m1["name"] == "Coords"
    assert m1["body"] == """    {
        X = x;
        Y = y;
    }"""
    assert m1["signature"] == "    public Coords(double x, double y)"
    assert m1["attributes"]["namespace_prefix"] == ""
    assert m1["attributes"]["modifiers"] == ["public"]
    assert m1["attributes"]["attributes"] == []
    assert m1["attributes"]["parameters"] == ["double x", "double y"]
    assert m1["attributes"]["return_type"] == ""

    assert m2["original_string"] == """    public override string ToString() => $"({X}, {Y})";"""
    assert m2["docstring"] == ""
    assert m2["name"] == "ToString"
    assert m2["body"] == '                                      => $"({X}, {Y})"'
    assert m2["signature"] == "    public override string ToString()"
    assert m2["attributes"]["namespace_prefix"] == ""
    assert m2["attributes"]["modifiers"] == ["public", "override"]
    assert m2["attributes"]["attributes"] == []
    assert m2["attributes"]["parameters"] == []
    assert m2["attributes"]["return_type"] == "string"

    source = DIR + "Interface.cs"
    with open(source, "r") as f:
        cp = CSharpParser(f.read())

        i1, i2, c1 = cp.schema['classes']

    m1 = i1["methods"][0]
    assert m1["original_string"] == """        bool Equals(T obj);"""
    assert m1["docstring"] == ""
    assert m1["name"] == "Equals"
    assert m1["body"] == ""
    assert m1["signature"] == "        bool Equals(T obj)"
    assert m1["attributes"]["namespace_prefix"] == ""
    assert m1["attributes"]["modifiers"] == []
    assert m1["attributes"]["attributes"] == []
    assert m1["attributes"]["parameters"] == ["T obj"]
    assert m1["attributes"]["return_type"] == "bool"


def test_nested_class():
    source = DIR + "NestedClass.cs"
    with open(source, "r") as f:
        cp = CSharpParser(f.read())

        classes = cp.schema['classes']
        assert len(classes) == 1

        cl = classes[0]

    cl = cl["classes"][0]
    assert cl["original_string"] == """    private class Soldier {
        // A method
        Soldier(int x) {}
    }"""
    assert cl["class_docstring"] == "This is a nested class"
    assert cl["name"] == "Soldier"
    assert cl["body"] == """                          {
        // A method
        Soldier(int x) {}
    }"""
    assert cl["methods"][0]["original_string"] == "        Soldier(int x) {}"
    assert cl["methods"][0]["docstring"] == "A method"
    assert cl["start_point"] == (8, 4)
    assert cl["end_point"] == (11, 5)


def test_nested_namespace():
    source = DIR + "NestedNamespace.cs"
    with open(source, "r") as f:
        cp = CSharpParser(f.read())

        classes = cp.schema['classes']

        c1, c2 = classes

    assert c1["attributes"]["namespace_prefix"] == "SomeNameSpace."
    assert c2["attributes"]["namespace_prefix"] == "SomeNameSpace.Nested."
