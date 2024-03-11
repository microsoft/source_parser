/*
Tests exporting of different types of functions
*/

export function printHello(name) {
    return "Hello " + name;
}

/*
exported class
*/
export class Car {
    name: string;
    year: number;
    
    constructor(name, year) {
      this.name = name;
      this.year = year;
    }

    /*
    get the age of the car
    */
    age() {
      let date = new Date();
      return date.getFullYear() - this.year;
    }
}


/*
Pulled from open source github code
*/
export const trustlySerializeData = function(data, method?, uuid?) {
    const dataType = Object.prototype.toString.call(data)
    const isObj = dataType === '[object Object]'
    const isArr = dataType === '[object Array]'
}