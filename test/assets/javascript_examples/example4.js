@mixin(BrainMixin, PhilosophyMixin)
class SmallRectangle {
  width = 20;
  height = 10;
  
  get dimension() {
    return {width: this.width, height: this.height};
  }
  increaseSize() {
    this.width++;
    this.height++;
  }
}
const rectangle = new SmallRectangle();
console.log(rectangle.dimension);    // => {width: 20, height: 10}
rectangle.width = 0;       // => SyntaxError
rrectangle.height = 50;    // => SyntaxError