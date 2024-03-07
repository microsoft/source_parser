/**
 * Author: Samarth Jain
 * Max Heap implementation in Javascript
 */

class BinaryHeap {
  constructor () {
    this.heap = []
  }

  insert (value) {
    this.heap.push(value)
    this.heapify()
  }

  size () {
    return this.heap.length
  }

  // using iterative approach to reorder the heap after insertion
  heapify () {
    let index = this.size() - 1

    while (index > 0) {
      const element = this.heap[index]
      const parentIndex = Math.floor((index - 1) / 2)
      const parent = this.heap[parentIndex]

      if (parent[0] >= element[0]) break
      this.heap[index] = parent
      this.heap[parentIndex] = element
      index = parentIndex
    }
  }
}