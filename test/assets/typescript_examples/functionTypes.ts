/*
return type explicitly stated
*/
function getTime(): number {
    return new Date().getTime();
}

/*
input types explicitly stated
*/
function multiply(a: number, b: number) {
    return a * b;
}

/*
Default values specified
*/
function pow(value: number, exponent: number = 10) {
    return value ** exponent;
}

function firstElement1<Type>(arr: Type[]) {
    return arr[0];
  }
  