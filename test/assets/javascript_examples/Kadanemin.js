function KadaneAlgo(n){let a=0,o=0;for(var e=0;e<n.length;e++)(a+=n[e])<0&&(a=0),o<a&&(o=a);return o}function main(){var n=KadaneAlgo([1,2,3,4,-6]);console.log(n)}main();