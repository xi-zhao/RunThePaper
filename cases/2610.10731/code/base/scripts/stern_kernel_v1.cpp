#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <numeric>
#include <random>
#include <unordered_map>
#include <vector>

// Binary Stern search on a systematic generator of ker(H). The information
// coordinates are partitioned; p=1,2 sums collide on ell random parity
// coordinates. Logical labels exclude the stabilizer subspace. Every answer
// is a witness/upper bound; exhausting these trials gives no lower bound.
using S = std::array<uint64_t,24>;
using V = std::array<uint64_t,40>;
struct Row { V v{}; uint64_t label=0; };
struct Item { int i,j; uint64_t label; };
int main(int argc,char** argv) {
    if(argc!=7) return 2;
    std::ifstream in(argv[1]);int m,n;in>>m>>n;
    const int sw=(m+63)/64,vw=(n+63)/64;
    if(!in || sw>24 || vw>40 || m<1 || n<1) return 3;
    std::vector<S> columns(n);std::vector<uint64_t> labels(n);std::vector<int> cost(n);
    for(int j=0;j<n;j++){for(int w=0;w<sw;w++)in>>columns[j][w];in>>labels[j]>>cost[j];if(cost[j]!=1)return 5;}
    if(!in)return 4;
    int trials=std::stoi(argv[3]),ell_requested=std::stoi(argv[5]),stop_below=std::stoi(argv[6]);
    if(ell_requested<0 || ell_requested>24)return 6;
    std::mt19937_64 rng(std::stoull(argv[4]));
    std::vector<int> order(n);std::iota(order.begin(),order.end(),0);
    std::vector<S> bs(m);std::vector<Row> bv(m);std::vector<bool> present(m);
    int best=n+1,best_trial=-1,best_kind=-1,rank=0,completed=0;Row witness;
    uint64_t collision_count=0,nontrivial_count=0,basis_count=0;
    auto start=std::chrono::steady_clock::now();
    auto examine=[&](const Row& r,int t,int kind){
        if(!r.label)return;
        int weight=0;for(int w=0;w<vw;w++)weight+=__builtin_popcountll(r.v[w]);
        if(weight<best){best=weight;best_trial=t;best_kind=kind;witness=r;}
    };
    for(int t=0;t<trials;t++){
        std::shuffle(order.begin(),order.end(),rng);std::fill(present.begin(),present.end(),false);
        std::vector<Row> kernel;std::vector<int> pivots;rank=0;
        for(int j:order){
            S s=columns[j];Row v;v.v[j/64]=uint64_t(1)<<(j%64);v.label=labels[j];bool pivot=false;
            for(int w=sw-1;w>=0;w--){
                while(s[w]){
                    int p=w*64+63-__builtin_clzll(s[w]);
                    if(!present[p]){present[p]=true;bs[p]=s;bv[p]=v;rank++;pivots.push_back(j);pivot=true;break;}
                    for(int z=0;z<=w;z++)s[z]^=bs[p][z];
                    for(int z=0;z<vw;z++)v.v[z]^=bv[p].v[z];v.label^=bv[p].label;
                }
                if(pivot)break;
            }
            if(!pivot){kernel.push_back(v);examine(v,t,0);basis_count++;}
        }
        std::shuffle(kernel.begin(),kernel.end(),rng);std::shuffle(pivots.begin(),pivots.end(),rng);
        int ell=std::min(rank,ell_requested),k=kernel.size(),half=k/2;
        std::vector<uint32_t> sig(k,0);
        for(int i=0;i<k;i++)for(int b=0;b<ell;b++)sig[i]|=((kernel[i].v[pivots[b]/64]>>(pivots[b]%64))&1)<<b;
        for(int p=1;p<=2;p++){
            std::unordered_map<uint32_t,std::vector<Item>> table;
            for(int i=0;i<half;i++)for(int j=(p==1?-1:i+1);j<(p==1?0:half);j++){
                table[sig[i]^(j<0?0:sig[j])].push_back({i,j,kernel[i].label^(j<0?0:kernel[j].label)});
            }
            for(int i=half;i<k;i++)for(int j=(p==1?-1:i+1);j<(p==1?0:k);j++){
                auto it=table.find(sig[i]^(j<0?0:sig[j]));if(it==table.end())continue;
                for(auto a:it->second){
                    collision_count++;uint64_t lab=a.label^kernel[i].label^(j<0?0:kernel[j].label);
                    if(!lab)continue;nontrivial_count++;Row v;v.label=lab;
                    for(int w=0;w<vw;w++)v.v[w]=kernel[a.i].v[w]^(a.j<0?0:kernel[a.j].v[w])^kernel[i].v[w]^(j<0?0:kernel[j].v[w]);
                    examine(v,t,p);
                }
            }
        }
        completed=t+1;
        if(stop_below>0 && best<stop_below)break;
    }
    std::ofstream out(argv[2]);
    out<<"{\"requested_trials\":"<<trials<<",\"trials\":"<<completed<<",\"seed\":"<<argv[4]
       <<",\"ell_requested\":"<<ell_requested<<",\"rank\":"<<rank<<",\"seconds\":"
       <<std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()
       <<",\"best_cost\":"<<(best_trial<0?-1:best)<<",\"best_trial\":"<<best_trial
       <<",\"best_kind\":"<<best_kind<<",\"logical_label\":"<<witness.label
       <<",\"basis_candidates\":"<<basis_count<<",\"collisions\":"<<collision_count
       <<",\"nontrivial_collisions\":"<<nontrivial_count<<",\"support\":[";
    bool first=true;for(int j=0;j<n;j++)if((witness.v[j/64]>>(j%64))&1){if(!first)out<<",";first=false;out<<j;}
    out<<"]}\n";
}
