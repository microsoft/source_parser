
function Animal (name) {
    this.name = name;  
}
Animal.prototype.speak = function () {
    console.log(`${this.name} makes a noise.`);
}

// comment
var animal = (
    function() {
        this.a = 0;
    }
)


// comment
BobsGarage.Car = function() {

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
};

// comment
const obj = {
    foo() {
        return 'bar';
    }
};

//  comment
const factorial = function fac(n=1) {return n < 2 ? 1 : n * fac(n-1)}

var myFunction = function(x, y) {return 0;}

// generator function
var myFunction = function*(x, y) {
    return x+y;
}

var myFunction = function namedFunction(){
    return 0;
}
