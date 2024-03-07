// Written by celbree
#include <iostream>
#include <vector>
#include "hi.h"
using namespace std;

// define pi
#define pi 3.1415

namespace first_namespace {
    // First cmp
    bool cmp(const int& a, const int& b) const {
        return a < b;
    }
    /*
    * It's a docstring for class
    */
    class MyTask : public other_namespace::Task {
    public:
        int x;
        // This is a comment.
        const vector<int> create(int *a){
            // hi there.
            return vector<int>(2, 0);
        }
        virtual void show() const{
            cout << "OK";
        }
    private:
        short unsigned int j;
    };
    namespace second_namespace {
        /*
        * Second cmp
        */
        auto cmp(const int& a, const int& b){
            return a < b;
        }
    }
}

int main(){
    return 0;
}
