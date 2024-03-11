const objToString=Object.prototype.toString;class InfinityList{constructor(t){this.generator=t,this[Symbol.iterator]=t}"!!"(t){if(t<0)throw Error("!! got negative index.");return 0===t?this.head():this.tail()["!!"](t-1)}concat(t){const i=this.generator;return new InfinityList(function*(){yield*i(),yield*t.generator()})}drop(t){const i=this.generator;return new InfinityList(function*(){const e=i();for(let i=0;i<t;i++)e.next();yield*e})}head(){return this.generator().next().value}init(){const t=this.generator;return new InfinityList(function*(){const i=t();let e=i.next(),n=i.next();for(;!n.done;)yield e.value,e=n,n=i.next()})}inits(){return this.generator().next().done?List.empty:this.init().inits().concat(this)}insert(t){return this.insertBy((t,i)=>t-i,t)}insertBy(t,i){return t(this.head(),i)<0?List.of(this.head()).concat(this.tail().insertBy(t,i)):List.of(i).concat(this)}intersect(t){const i=[];for(const e of this)t.any(t=>t===e)&&i.push(e);return new List(i)}intersperse(t){const i=this.generator();return i.next().done?List.empty:i.next().done?this:new List([this.head(),t]).concat(this.tail().intersperse(t))}lines(){const t=this.generator;return new InfinityList(function*(){const i=t();let e="";for(const t of i)"\n"===t?""!==e&&(yield e,e=""):e+=t})}map(t){const i=this.generator;return new InfinityList(function*(){const e=i();for(const i of e)yield t(i)})}span(t){if(t(this.head())){const[i,e]=this.tail().span(t);return[List.of(this.head()).concat(i),e]}return[List.empty,this]}splitAt(t){return[this.take(t),this.drop(t)]}tail(){const t=this.generator;return new InfinityList(function*(){const i=t();i.next(),yield*i})}tails(){const t=this;return new InfinityList(function*(){let i=t;for(;yield i,!(i=i.tail()).generator().next().done;);})}take(t){const i=[],e=this.generator();for(let n=0;n<t;n=0|n+1)i.push(e.next().value);return new List(i)}takeWhile(t){const i=[];for(const e of this){if(!t(e))break;i.push(e)}return new List(i)}unlines(){const t=this.generator;return new InfinityList(function*(){const i=t();for(const t of i)yield*t,yield"\n"})}unwords(){const t=this.generator;return new InfinityList(function*(){const i=t();yield*i.next().value;for(const t of i)yield" ",yield*t})}words(){const t=this.generator;return new InfinityList(function*(){const i=t(),e=/\s/;let n="";for(const t of i)e.test(t)?""!==n&&(yield n,n=""):n+=t})}}export default class List extends InfinityList{constructor(t){if(!Array.isArray(t))throw Error("expect array. Got "+t);const i=new Array(t.length);for(let e=0,n=t.length;e<n;e++)Array.isArray(t[e])?i[e]=new List(t[e]):i[e]=t[e];super(function*(){yield*i}),this.value=i,this.length=i.length}"!!"(t){if(t<0)throw Error("!! got negative index.");return this.value[t]}"\\"(t){let i=this;for(const e of t)i=i.delete(e);return i}"\\\\"(t){return this["\\"](t)}all(t){return this.map(t).and()}and(){return this.foldr((t,i)=>t&&i,!0)}any(t){return this.map(t).or()}ap(t){const i=t.value.length,e=new Array(this.value.length*i);for(let n=0,s=this.value.length;n<s;n++)for(let s=0,r=i;s<r;s++)e[n*i+s]=this.value[n](t.value[s]);return new List(e)}break(t){for(let i=0,e=this.length;i<e;i++)if(t(this.value[i]))return[new List(this.value.slice(0,i)),new List(this.value.slice(i))];return[this,List.empty]}chain(t){return List.concat(this.map(t))}concatMap(t){return List.concat(this.map(t))}concat(t){return t instanceof List?new List(this.value.concat(t.value)):super.concat(t)}cycle(){const t=this.value;return new InfinityList(function*(){for(;;)yield*t})}delete(t){for(let i=0,e=this.length;i<e;i++)if(this.value[i]===t)return new List(this.value.slice(0,i).concat(this.value.slice(i+1)));return this}deleteBy(t,i){for(let e=0,n=this.length;e<n;e++)if(t(i,this.value[e]))return new List(this.value.slice(0,e).concat(this.value.slice(e+1)));return this}drop(t){return 0===t?this:this.tail().drop(t-1)}dropWhile(t){return t(this.head())?this.tail().dropWhile(t):this}dropWhileEnd(t){return t(this.last())?this.init().dropWhileEnd(t):this}elem(t){return this.any(i=>t===i)}empty(){return List.empty}equals(t){return t instanceof List&&function t(i,e){if(i.length!==e.length)return!1;for(let n=0,s=i.length;n<s;n++){if(objToString.call(i[n])!==objToString.call(e[n]))return!1;if(i[n]&&"function"==typeof i[n].equals){if(!i[n].equals(e[n]))return!1}else if(Array.isArray(i[n])){if(!t(i[n],e[n]))return!1}else if(i[n]!==e[n])return!1}return!0}(this.value,t.value)}filter(t){return this.chain(i=>t(i)?List.pure(i):List.empty)}foldl(t,i){return 0===this.value.length?i:this.tail().foldl(t,t(i,this.head()))}reduce(t,i){return 0===this.value.length?i:this.tail().foldl(t,t(i,this.head()))}foldl1(t){return this.tail().foldl(t,this.head())}foldr(t,i){return this.generator().next().done?i:t(this.head(),this.tail().foldr(t,i))}foldr1(t){return this.init().foldr(t,this.last())}init(){return new List(this.value.slice(0,-1))}inits(){return 0===this.length?List.of(this.value):this.init().inits().concat(List.of(this.value))}intercalate(t){return List.concat(this.intersperse(t))}isnull(){return this.equals(List.empty)}isInfixOf(t){return 0===this.length||t.tails().any(t=>this.isPrefixOf(t))}isPrefixOf(t){return 0===this.length||0!==t.length&&(t.head()===this.head()&&this.tail().isPrefixOf(t.tail()))}isSuffixOf(t){return 0===this.length||0!==t.length&&(t.last()===this.last()&&this.init().isSuffixOf(t.init()))}null(){return this.equals(List.empty)}last(){return this.value[this.value.length-1]}lines(){const t=[];let i="";for(const e of this)"\n"===e?""!==i&&(t.push(i),i=""):i+=e;return""!==i&&t.push(i),new List(t)}map(t){const i=new Array(this.value.length);for(let e=0,n=i.length;e<n;e++)i[e]=t(this.value[e]);return new List(i)}mapAccumL(t,i){const e=[];for(let n,s=0,r=this.length;s<r;s++)[i,n]=t(i,this.value[s]),e.push(n);return[i,new List(e)]}mapAccumR(t,i){const e=[];for(let n,s=this.length-1;s>=0;s--)[i,n]=t(i,this.value[s]),e.push(n);return[i,new List(e.reverse())]}maximum(){if(this.value.length<=1)return this.value[0];const t=this.tail().maximum();return t>this.head()?t:this.head()}minimum(){if(this.value.length<=1)return this.value[0];const t=this.tail().minimum();return t<this.head()?t:this.head()}nub(){return this.nubBy((t,i)=>t===i)}nubBy(t){if(0===this.length)return List.empty;const i=this.head(),e=this.tail();return List.of(i).concat(e.filter(e=>!t(i,e)).nubBy(t))}of(...t){return new List(t)}or(){return this.foldr((t,i)=>t||i,!1)}permutations(){let t=List.empty;if(0===this.length)return List.of(List.empty);for(let i=0,e=this.length;i<e;i++)t=t.concat(this.take(i).concat(this.drop(i+1)).permutations().map(t=>List.of(this.value[i]).concat(t)));return t}product(){return this.foldl((t,i)=>t*i,1)}reverse(){return 0===this.value.length?List.empty:this.tail().reverse().concat(List.of(this.head()))}scanl(t,i){return this.foldl((i,e)=>i.concat(List.of(t(i.last(),e))),List.of(i))}scanl1(t){return 0===this.length?List.empty:this.tail().foldl((i,e)=>i.concat(List.of(t(i.last(),e))),List.of(this.head()))}scanr(t,i){return this.foldr((i,e)=>List.of(t(e.head(),i)).concat(e),List.of(i))}scanr1(t){if(this.length<=1)return new List(this.value);const i=this.tail().scanr1(t);return List.of(t(i.head(),this.head())).concat(i)}sequence(t){return this.foldr((t,i)=>t.chain(t=>0===i.value.length?List.pure(t):i.chain(i=>List.pure(List.of(t).concat(i)))),new List([[]]))}sort(){return new List(this.value.concat().sort((t,i)=>t>i))}sortBy(t){return new List(this.value.concat().sort(t))}subsequences(){return this.foldl((t,i)=>t.concat(t.map(t=>t.concat(List.of(i)))),new List([List.empty]))}sum(){return this.foldl((t,i)=>t+i,0)}tail(){return new List(this.value.slice(1))}tails(){return 0===this.length?List.of(this.value):List.of(this.value).concat(this.tail().tails())}toArray(){return this.reduce((t,i)=>i instanceof List?t.concat([i.toArray()]):t.concat(i),[])}transpose(){const t=this.map(t=>t.length).maximum(),i=[];for(let e=0;e<t;e++){i[e]=[];for(let t=0,n=this.length;t<n;t++)this.value[t]&&this.value[t].value&&this.value[t].value[e]&&i[e].push(this.value[t].value[e])}return new List(i)}traverse(t,i){return this.map(t).sequence(i)}union(t){return this.unionBy((t,i)=>t===i,t)}unionBy(t,i){let e=i.nub();for(const i of this)e=e.deleteBy(t,i);return this.concat(e)}unlines(){let t="";for(let i=0,e=this.length;i<e;i++){if("[object String]"!==objToString.call(this.value[i]))throw Error("expected [String].");t+=this.value[i]+"\n"}return new List([...t])}unwords(){const t=[];for(let i=0,e=this.length;i<e;i++){if("[object String]"!==objToString.call(this.value[i]))throw Error("expected [String].");t.push(this.value[i])}return new List([...t.join(" ")])}unzipHelper(t){const i=t=>i=>i["!!"]?i["!!"](t):i[t],e=[];for(let n=0;n<t;n++)e.push(this.map(i(n)));return new List(e)}unzip(){return this.unzipHelper(2)}unzip3(){return this.unzipHelper(3)}unzip4(){return this.unzipHelper(4)}unzip5(){return this.unzipHelper(5)}unzip6(){return this.unzipHelper(6)}unzip7(){return this.unzipHelper(7)}words(){const t=[],i=/\s/;let e="";for(const n of this)i.test(n)?""!==e&&(t.push(e),e=""):e+=n;return""!==e&&t.push(e),new List(t)}}List.pure=(t=>new List([t])),List.concat=(t=>0===t.length?List.empty:t.head().concat(List.concat(t.tail()))),List.empty=new List([]),List.iterate=((t,i)=>{return new InfinityList(function*(){let e=i;for(;;)yield[e,e=t(e)][0]})}),List.repeat=(t=>{return new InfinityList(function*(){for(;;)yield t})}),List.replicate=((t,i)=>List.repeat(i).take(t)),List.of=List.prototype.of,List._zip_=((...t)=>{t=t.map(t=>t instanceof List?t.toArray():t);const i=Math.min(...t.map(t=>t.length)),e=[];for(let n=0;n<i;n++)e.push(new List(t.map(t=>t[n])));return new List(e)}),List._zipWith_=((t,...i)=>{i=i.map(t=>t instanceof List?t.toArray():t);const e=Math.min(...i.map(t=>t.length)),n=[];for(let s=0;s<e;s++)n.push(t(...i.map(t=>t[s])));return new List(n)}),List.zip=((t,i)=>List._zip_(t,i)),List.zip3=((t,i,e)=>List._zip_(t,i,e)),List.zip4=((t,i,e,n)=>List._zip_(t,i,e,n)),List.zip5=((t,i,e,n,s)=>List._zip_(t,i,e,n,s)),List.zip6=((t,i,e,n,s,r)=>List._zip_(t,i,e,n,s,r)),List.zip7=((t,i,e,n,s,r,h)=>List._zip_(t,i,e,n,s,r,h)),List.zipWith=((t,i,e)=>List._zipWith_(t,i,e)),List.zipWith3=((t,i,e,n)=>List._zipWith_(t,i,e,n)),List.zipWith4=((t,i,e,n,s)=>List._zipWith_(t,i,e,n,s)),List.zipWith5=((t,i,e,n,s,r)=>List._zipWith_(t,i,e,n,s,r)),List.zipWith6=((t,i,e,n,s,r,h)=>List._zipWith_(t,i,e,n,s,r,h)),List.zipWith7=((t,i,e,n,s,r,h,o)=>List._zipWith_(t,i,e,n,s,r,h,o));