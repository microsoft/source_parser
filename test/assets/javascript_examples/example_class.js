//class Node
class Node {
    //Node in the tree
    constructor (val) {
        this.value = val
        this.left = null
        this.right = null
    }

    //Search the tree for a value
    search(val) {
        if(this.value === val) {
            return this
        } else if (val < this.value && this.left !== null) {   
            return this.left.search(val)
        } else if (val > this.value && this.right !== null) {
            return this.right.search(val)
        }
        return null
    }

    //Visit a node
    visit() {
        //Recursively go left
        if (this.left != null) {
            this.left.visit()
        }
        //Print out value
        console.log(this.value)
        //Recursively go right
        if (this.right != null) {
            this.right.visit()
        }
    }

}

