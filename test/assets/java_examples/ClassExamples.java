// Copyright (c) 2013 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package org.chromium.android_webview;
import android.content.SharedPreferences;
import org.chromium.content.browser.ContentViewStatics;

/**
 * This is Javadoc for ClassExample1
 *
 */
public class ClassExample1 {

    /*
     * fields can have javadoc
     */
    private int a;
    private ArrayList<Integer> b;

    public ClassExample1(int a, int c) {
        self.a = a;
    }

    /**
     * This is a function.
     * it does something.
     */
    public void returnA() {
        return self.a;
    }

    /**
     * nested class should be ignored by the parser
     */
    private class InnerClass{
        private int b;
        public InnerClass(int b){
            self.b = b
        }
    }

}

class AnotherClass {
    private int a;

    /**
     * this is a constructor
     */
    public AnotherClass(int a) {
        self.a = a;
    }
}