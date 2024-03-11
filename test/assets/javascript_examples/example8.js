const objToString = Object.prototype.toString;
class InfinityList {
    constructor(generator) {
        this.generator = generator;
        this[Symbol.iterator] = generator;
    }
    '!!'(n) {
        if (n < 0) throw Error('!! got negative index.');
        if (n === 0) return this.head();
        return this.tail()['!!'](n - 1);
    }
    concat(b) {
        const gen = this.generator;
        const res = new InfinityList(function*() {
            yield* gen();
            yield* b.generator();
        });
        return res;
    }
    drop(n) {
        const gen = this.generator;
        const res = new InfinityList(function*() {
            const iter = gen();
            for (let i = 0; i < n; i++) iter.next();
            yield* iter;
        });
        return res;
    }
    head() {
        const iter = this.generator();
        return iter.next().value;
    }
    init() {
        const gen = this.generator;
        const res = new InfinityList(function*() {
            const iter = gen();
            let val = iter.next();
            let next = iter.next();
            while (!next.done) {
                yield val.value;
                val = next;
                next = iter.next();
            }
        });
        return res;
    }
    inits() {
        if (this.generator().next().done) return List.empty;
        return this.init().inits().concat(this);
    }
    insert(n) {
        return this.insertBy((x, y) => x - y, n);
    }
    insertBy(f, n) {
        if (f(this.head(), n) < 0) return List.of(this.head()).concat(this.tail().insertBy(f, n));
        return List.of(n).concat(this);
    }
    intersect(l) {
        const res = [];
        for (const val of this) {
            if (l.any(x => x === val)) res.push(val);
        }
        return new List(res);
    }
    intersperse(s) {
        const iter = this.generator();
        if (iter.next().done) return List.empty;
        if (iter.next().done) return this;
        return new List([this.head(), s]).concat(this.tail().intersperse(s));
    }
    lines() {
        const gen = this.generator;
        const res = new InfinityList(function*() {
            const iter = gen();
            let line = '';
            for (const val of iter) {
                if (val === '\n') {
                    if (line !== '') {
                        yield line;
                        line = '';
                    }
                } else line += val;
            }
        });
        return res;
    }
    map(f) {
        const gen = this.generator;
        const res = new InfinityList(function*() {
            const iter = gen();
            for (const val of iter) {
                yield f(val);
            }
        });
        return res;
    }
    span(f) {
        if (f(this.head())) {
            const [ys, zs] = this.tail().span(f);
            return [List.of(this.head()).concat(ys), zs];
        }
        return [List.empty, this];
    }
    splitAt(n) {
        return [this.take(n), this.drop(n)];
    }
    tail() {
        const gen = this.generator;
        const res = new InfinityList(function*() {
            const iter = gen();
            iter.next();
            yield* iter;
        });
        return res;
    }
    tails() {
        const self = this;
        const res = new InfinityList(function*() {
            let tail = self;
            while (true) {
                yield tail;
                tail = tail.tail();
                if (tail.generator().next().done) break;
            }
        });
        return res;
    }
    take(n) {
        const res = [];
        const iter = this.generator();
        for (let i = 0; i < n; i = 0 | i + 1) {
            res.push(iter.next().value);
        }
        return new List(res);
    }
    takeWhile(f) {
        const res = [];
        for (const val of this) {
            if (!f(val)) break;
            res.push(val);
        }
        return new List(res);
    }
    unlines() {
        const gen = this.generator;
        const res = new InfinityList(function*() {
            const iter = gen();
            for (const val of iter) {
                yield* val;
                yield '\n';
            }
        });
        return res;
    }
    unwords() {
        const gen = this.generator;
        const res = new InfinityList(function*() {
            const iter = gen();
            yield* iter.next().value;
            for (const val of iter) {
                yield ' ';
                yield* val;
            }
        });
        return res;
    }
    words() {
        const gen = this.generator;
        const res = new InfinityList(function*() {
            const iter = gen();
            const ws = /\s/;
            let word = '';
            for (const val of iter) {
                if (ws.test(val)) {
                    if (word !== '') {
                        yield word;
                        word = '';
                    }
                } else word += val;
            }
        });
        return res;
    }
}

export default class List extends InfinityList {
    constructor(_arr) {
        if (!Array.isArray(_arr)) {
            throw Error('expect array. Got ' + _arr);
            return;
        }
        const arr = new Array(_arr.length);
        for (let i = 0, _i = _arr.length; i < _i; i++) {
            if (Array.isArray(_arr[i])) {
                arr[i] = new List(_arr[i]);
            } else {
                arr[i] = _arr[i];
            }
        }
        super(function*() {
            yield* arr;
        });
        this.value = arr;
        this.length = arr.length;
    }
    '!!'(n) {
        if (n < 0) throw Error('!! got negative index.');
        return this.value[n];
    }
    '\\'(l) {
        let res = this;
        for (const val of l) {
            res = res.delete(val);
        }
        return res;
    }
    '\\\\'(l) {
        return this['\\'](l);
    }
    all(f) {
        return this.map(f).and();
    }
    and() {
        return this.foldr((a, b) => a && b, true);
    }
    any(f) {
        return this.map(f).or();
    }
    ap(b) {
        const bLength = b.value.length;
        const res = new Array(this.value.length * bLength);
        for (let i = 0, _i = this.value.length; i < _i; i++) {
            for (let j = 0, _j = bLength; j < _j; j++) {
                res[i * bLength + j] = this.value[i](b.value[j]);
            }
        }
        return new List(res);
    }
    break(f) {
        for (let i = 0, _i = this.length; i < _i; i++) {
            if (f(this.value[i])) return [new List(this.value.slice(0, i)), new List(this.value.slice(i))];
        }
        return [this, List.empty];
    }
    chain(f) {
        return List.concat(this.map(f));
    }
    concatMap(f) {
        // same as chain()
        return List.concat(this.map(f));
    }
    concat(b) {
        if (b instanceof List) return new List(this.value.concat(b.value));
        return super.concat(b);
    }
    cycle() {
        const value = this.value;
        const res = new InfinityList(function*() {
            while (true) {
                yield* value;
            }
        });
        return res;
    }
    delete(a) {
        for (let i = 0, _i = this.length; i < _i; i++) {
            if (this.value[i] === a) return new List(this.value.slice(0, i).concat(this.value.slice(i + 1)));
        }
        return this;
    }
    deleteBy(f, x) {
        for (let i = 0, _i = this.length; i < _i; i++) {
            if (f(x, this.value[i])) return new List(this.value.slice(0, i).concat(this.value.slice(i + 1)));
        }
        return this;
    }
    drop(n) {
        if (n === 0) return this;
        return this.tail().drop(n - 1);
    }
    dropWhile(f) {
        if (f(this.head())) return this.tail().dropWhile(f);
        return this;
    }
    dropWhileEnd(f) {
        if (f(this.last())) return this.init().dropWhileEnd(f);
        return this;
    }
    elem(x) {
        return this.any(y => x === y);
    }
    empty() {
        return List.empty;
    }
    equals(b) {
        function isEquals(a, b) {
            if (a.length !== b.length) return false;
            for (let i = 0, _i = a.length; i < _i; i++) {
                if (objToString.call(a[i]) !== objToString.call(b[i])) return false;
                if (a[i] && typeof a[i].equals === 'function') {
                    if (!a[i].equals(b[i])) return false;
                } else if (Array.isArray(a[i])) {
                    if (!isEquals(a[i], b[i])) return false;
                } else {
                    if (a[i] !== b[i]) return false;
                }
            }
            return true;
        };
        if (!(b instanceof List)) return false;
        return isEquals(this.value, b.value);
    }
    filter(f) {
        return this.chain(m => f(m) ? List.pure(m) : List.empty);
    }
    foldl(f, acc) {
        if (this.value.length === 0) return acc;
        return this.tail().foldl(f, f(acc, this.head()));
    }
    reduce(f, acc) {
        // same as foldl()
        if (this.value.length === 0) return acc;
        return this.tail().foldl(f, f(acc, this.head()));
    }
    foldl1(f) {
        return this.tail().foldl(f, this.head());
    }
    foldr(f, acc) {
        if (this.generator().next().done) return acc;
        return f(this.head(), this.tail().foldr(f, acc));
    }
    foldr1(f) {
        return this.init().foldr(f, this.last());
    }
    init() {
        return new List(this.value.slice(0, -1));
    }
    inits() {
        if (this.length === 0) return List.of(this.value);
        return this.init().inits().concat(List.of(this.value));
    }
    intercalate(s) {
        return List.concat(this.intersperse(s));
    }
    isnull() {
        return this.equals(List.empty);
    }
    isInfixOf(l) {
        if (this.length === 0) return true;
        return l.tails().any(l => this.isPrefixOf(l));
    }
    isPrefixOf(l) {
        if (this.length === 0) return true;
        if (l.length === 0) return false;
        return l.head() === this.head() && this.tail().isPrefixOf(l.tail());
    }
    isSuffixOf(l) {
        if (this.length === 0) return true;
        if (l.length === 0) return false;
        return l.last() === this.last() && this.init().isSuffixOf(l.init());
    }
    null() {
        // same as isnull()
        return this.equals(List.empty);
    }
    last() {
        return this.value[this.value.length - 1];
    }
    lines() {
        const res = [];
        let line = '';
        for (const val of this) {
            if (val === '\n') {
                if (line !== '') {
                    res.push(line);
                    line = '';
                }
            } else line += val;
        }
        if (line !== '') res.push(line);
        return new List(res);
    }
    map(f) {
        const res = new Array(this.value.length);
        for (let i = 0, _i = res.length; i < _i; i++) {
            res[i] = f(this.value[i]);
        }
        return new List(res);
    }
    mapAccumL(f, x) {
        const res = [];
        for (let i = 0, _i = this.length, y; i < _i; i++) {
            [x, y] = f(x, this.value[i]);
            res.push(y);
        }
        return [x, new List(res)];
    }
    mapAccumR(f, x) {
        const res = [];
        for (let i = this.length - 1, y; i >= 0; i--) {
            [x, y] = f(x, this.value[i]);
            res.push(y);
        }
        return [x, new List(res.reverse())];
    }
    maximum() {
        // if (this.value.length === 0) return undefined;
        // if (this.value.length === 1) return this.value[0];
        if (this.value.length <= 1) return this.value[0];
        const max = this.tail().maximum();
        if (max > this.head()) return max;
        else return this.head();
    }
    minimum() {
        // if (this.value.length === 0) return undefined;
        // if (this.value.length === 1) return this.value[0];
        if (this.value.length <= 1) return this.value[0];
        const min = this.tail().minimum();
        if (min < this.head()) return min;
        else return this.head();
    }
    nub() {
        return this.nubBy((x, y) => x === y);
    }
    nubBy(f) {
        if (this.length === 0) return List.empty;
        const x = this.head(), xs = this.tail();
        return List.of(x).concat(xs.filter(y => !f(x, y)).nubBy(f));
    }
    of(...args) {
        return new List(args);
    }
    or() {
        return this.foldr((a, b) => a || b, false);
    }
    permutations() {
        let res = List.empty;
        if (this.length === 0) return List.of(List.empty);
        for (let i = 0, _i = this.length; i < _i; i++) {
            res = res.concat(this.take(i).concat(this.drop(i + 1)).permutations().map(l => List.of(this.value[i]).concat(l)));
        }
        return res;
    }
    product() {
        return this.foldl((a, b) => a * b, 1);
    }
    reverse() {
        if (this.value.length === 0) return List.empty;
        return this.tail().reverse().concat(List.of(this.head()));
    }
    scanl(f, acc) {
        return this.foldl((acc, x) => acc.concat(List.of(f(acc.last(), x))), List.of(acc));
    }
    scanl1(f) {
        if (this.length === 0) return List.empty;
        return this.tail().foldl((acc, x) => acc.concat(List.of(f(acc.last(), x))), List.of(this.head()));
    }
    scanr(f, acc) {
        return this.foldr((x, acc) => List.of(f(acc.head(), x)).concat(acc), List.of(acc));
    }
    scanr1(f) {
        if (this.length <= 1) return new List(this.value);
        const qs = this.tail().scanr1(f);
        return List.of(f(qs.head(), this.head())).concat(qs);
    }
    sequence(of) {
        return this.foldr((m, ma) => m.chain(x => {
                if (ma.value.length === 0) return List.pure(x);
                return ma.chain(xs => List.pure(List.of(x).concat(xs)));
            }), new List([[]]));
    }
    sort() {
        return new List(this.value.concat().sort((a, b) => a > b));
    }
    sortBy(f) {
        return new List(this.value.concat().sort(f));
    }
    subsequences() {
        return this.foldl((acc, x) => acc.concat(acc.map(item => item.concat(List.of(x)))), new List([List.empty]));
    }
    sum() {
        return this.foldl((a, b) => a + b, 0);
    }
    tail() {
        return new List(this.value.slice(1));
    }
    tails() {
        if (this.length === 0) return List.of(this.value);
        return List.of(this.value).concat(this.tail().tails());
    }
    toArray() {
        return this.reduce((acc, x) => {
            if (x instanceof List) return acc.concat([x.toArray()]);
            return acc.concat(x);
        }, []);
    }
    transpose() {
        const max = this.map(item => item.length).maximum();
        const res = [];
        for (let i = 0; i < max; i++) {
            res[i] = [];
            for (let j = 0, _j = this.length; j < _j; j++) {
                if (this.value[j] && this.value[j].value && this.value[j].value[i]) {
                    res[i].push(this.value[j].value[i]);
                }
            }
        }
        return new List(res);
    }
    traverse(f, of) {
        return this.map(f).sequence(of);
    }
    union(l) {
        return this.unionBy((x, y) => x === y, l);
    }
    unionBy(f, l) {
        let res = l.nub();
        for (const val of this) {
            res = res.deleteBy(f, val);
        }
        return this.concat(res);
    }
    unlines() {
        let res = '';
        for (let i = 0, _i = this.length; i < _i; i++) {
            if (objToString.call(this.value[i]) !== '[object String]') throw Error('expected [String].');
            res += this.value[i] + '\n';
        }
        return new List([...res]);
    }
    unwords() {
        const res = [];
        for (let i = 0, _i = this.length; i < _i; i++) {
            if (objToString.call(this.value[i]) !== '[object String]') throw Error('expected [String].');
            res.push(this.value[i]);
        }
        return new List([...res.join(' ')])
    }
    unzipHelper(n) {
        const get = n => x => x['!!'] ? x['!!'](n) : x[n];
        const res = [];
        for (let i = 0; i < n; i++) {
            res.push(this.map(get(i)));
        }
        return new List(res);
    }
    unzip() {return this.unzipHelper(2);}
    unzip3() {return this.unzipHelper(3);}
    unzip4() {return this.unzipHelper(4);}
    unzip5() {return this.unzipHelper(5);}
    unzip6() {return this.unzipHelper(6);}
    unzip7() {return this.unzipHelper(7);}
    words() {
        const res = [];
        const ws = /\s/;
        let word = '';
        for (const val of this) {
            if (ws.test(val)) {
                if (word !== '') {
                    res.push(word);
                    word = '';
                }
            } else word += val;
        }
        if (word !== '') res.push(word);
        return new List(res);
    }
};
List.pure = x => new List([x]);
List.concat = list => {
    if (list.length === 0) return List.empty;
    return list.head().concat(List.concat(list.tail()));
};
List.empty = new List([]);
List.iterate = (f, _x) => {
    // create infinity list
    const res = new InfinityList(function*() {
        let x = _x;
        while (true) yield [x, x = f(x)][0];
    });
    return res;
};
List.repeat = x => {
    const res = new InfinityList(function*() {
        while (true) yield x;
    });
    return res;
}
List.replicate = (n, x) => {
    return List.repeat(x).take(n);
}
List.of = List.prototype.of;
List._zip_ = (...args) => {
    args = args.map(val => {
        if (val instanceof List) return val.toArray();
        return val;
    });
    const n = Math.min(...(args.map(a => a.length)));
    const res = [];
    for (let i = 0; i < n; i++) {
        res.push(new List(args.map(a => a[i])));
    }
    return new List(res);
};
List._zipWith_ = (f, ...args) => {
    args = args.map(val => {
        if (val instanceof List) return val.toArray();
        return val;
    });
    const n = Math.min(...(args.map(a => a.length)));
    const res = [];
    for (let i = 0; i < n; i++) {
        res.push(f(...args.map(a => a[i])));
    }
    return new List(res);
};
List.zip = (a, b) => List._zip_(a, b);
List.zip3 = (a, b, c) => List._zip_(a, b, c);
List.zip4 = (a, b, c, d) => List._zip_(a, b, c, d);
List.zip5 = (a, b, c, d, e) => List._zip_(a, b, c, d, e);
List.zip6 = (a, b, c, d, e, f) => List._zip_(a, b, c, d, e, f);
List.zip7 = (a, b, c, d, e, f, g) => List._zip_(a, b, c, d, e, f, g);

List.zipWith = (_f, a, b) => List._zipWith_(_f, a, b);
List.zipWith3 = (_f, a, b, c) => List._zipWith_(_f, a, b, c);
List.zipWith4 = (_f, a, b, c, d) => List._zipWith_(_f, a, b, c, d);
List.zipWith5 = (_f, a, b, c, d, e) => List._zipWith_(_f, a, b, c, d, e);
List.zipWith6 = (_f, a, b, c, d, e, f) => List._zipWith_(_f, a, b, c, d, e, f);
List.zipWith7 = (_f, a, b, c, d, e, f, g) => List._zipWith_(_f, a, b, c, d, e, f, g);