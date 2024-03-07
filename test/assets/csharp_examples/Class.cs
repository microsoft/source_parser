// Copyright Syncfusion Inc. 2001 - 2020. All rights reserved.
using System;
using System.Globalization;
using System.Reflection;
using System.IO;
using System.Diagnostics;
using System.Collections.Generic;
using System.Linq;
namespace Eto.Drawing
{
        /// <summary>
        /// Represents a frame in an <see cref="Icon"/>.
        /// </summary>
        /// <remarks>
        /// The IconFrame represents a single frame in an Icon.
        /// Each IconFrame can have a specific pixel size and scale, which will automatically be chosen based on the display and
        /// draw size of the image in various Eto controls.
        ///
        /// You can load an icon from an .ico, where all frames will have a 1.0 scale (pixel size equals logical size)
        /// </remarks>
        [Handler(typeof(IHandler))]
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
        }
}