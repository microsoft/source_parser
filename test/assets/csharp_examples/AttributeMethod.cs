// Copyright 2011 The Noda Time Authors. All rights reserved.
// Use of this source code is governed by the Apache License 2.0,
// as found in the LICENSE.txt file.
using System;
using NodaTime.Text;
using NUnit.Framework;
namespace NodaTime.Test.Text
{
    // comment
    public class ParseResultTest
    {
        private static readonly ParseResult<int> FailureResult = ParseResult<int>.ForInvalidValue(new ValueCursor("text"), "text");
        [Test]
        public void Value_Success()
        {
            ParseResult<int> result = ParseResult<int>.ForValue(5);
            Assert.AreEqual(5, result.Value);
        }
        [Test]
        public void Value_Failure()
        {
            Assert.Throws<UnparsableValueException>(() => FailureResult.Value.GetHashCode());
        }
    }
}