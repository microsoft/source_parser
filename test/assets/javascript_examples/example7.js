var BobsGarage = BobsGarage || {}; // namespace

/**
 * BobsGarage.Car
 * @constructor
 * @returns {BobsGarage.Car}
 */
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
    };

    /**
     * Tank
     * @constructor
     * @returns {Tank}
     */
    var Tank = function() {
        // definition of a tank
    };

    Tank.prototype.constructor = Tank;
    Tank.prototype.fill = function() {
        console.log('fill tank');
    };

    this.engine = new Engine();
    this.tank = new Tank();
};

BobsGarage.Car.prototype.constructor = BobsGarage.Car;

/**
 * BobsGarage.Ferrari
 * Derived from BobsGarage.Car
 * @constructor
 * @returns {BobsGarage.Ferrari}
 */
BobsGarage.Ferrari = function() {
    BobsGarage.Car.call(this);
};
BobsGarage.Ferrari.prototype = Object.create(BobsGarage.Car.prototype);
BobsGarage.Ferrari.prototype.constructor = BobsGarage.Ferrari;
BobsGarage.Ferrari.prototype.speedUp = function() {
    console.log('speed up');
};

// Test it on the road

var car = new BobsGarage.Car();
car.tank.fill();
car.engine.start();

var ferrari = new BobsGarage.Ferrari();
ferrari.tank.fill();
ferrari.engine.start();
ferrari.speedUp();

// var engine = new Engine(); // ReferenceError

console.log(ferrari);