// Java program implements method inside method 
public class GFG { 
  
    // function have implementation of another  
    // function inside local class 
    static void Foo() 
    { 
        // local class 
        class Local { 
            void fun() 
            { 
                System.out.println("geeksforgeeks"); 
            } 
        } 
        new Local().fun(); 
    } 

    public class nested(){

    }

} 