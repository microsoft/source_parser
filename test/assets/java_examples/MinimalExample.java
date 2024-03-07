// Copyright (c) 2013 The Chromium Authors. All rights reserved.

package org.chromium.android_webview;
import android.content.SharedPreferences;

/*
 * Class1 javadoc
 */
@MyMarkerNotation
public class Class1 {

    /*
     * Field javadoc
     */
    private int a;

    public Class1(int a) {
        self.a = a;
    }

    // A function
    public int returnA() {
        return self.a;
    }

    @Marker
    public static void printHi() {
        System.out.println("Hi");
    } 
    
}
