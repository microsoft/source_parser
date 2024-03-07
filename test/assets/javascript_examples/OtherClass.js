// File Doc

// class
let Animal = class {
    constructor(type) {
        this.type = type;
    }
    identify() {
        console.log(this.type);
    }
}


// treat as function
var animal = (
    function() {
        this.b = 0;
    }()
)