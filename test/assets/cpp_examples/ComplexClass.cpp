// Written by celbree
#include <iostream>
#include <vector>
using namespace std;

/** This is the first class
 */
class FirstClass{
public:
    vector<int> x;
    // a variable
    inline int y;
    FirstClass(int x): x(x) {}
    bool func(const vector<double>& values);
    static int static_func(int a=0){
        return a;
    }
private:
    auto at;
    /*
     * a private member function
     */
    vector<int> private_func(int i, int j) const{
        vector<int> v;
        v.push_back(i);
        return v;
    }
};

/*
 * Compare two intergers
 */
bool FirstClass::func(const vector<double>& values){
    return values[0] < 0; // return true if a < b
}


// a lambda expression
auto glambda = [](auto a, auto&& b) { return a < b; };
