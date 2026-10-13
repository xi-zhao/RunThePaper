#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <vector>

// Random systematic-kernel search. Each returned support is an explicit
// certificate, not a distance lower bound. No paper distance is an input.
int main(int argc, char** argv) {
    if (argc != 5) return 2;
    std::ifstream in(argv[1]);
    int m, n; in >> m >> n;
    const int sw=(m+63)/64, vw=(n+63)/64;
    if (!in || sw>24 || vw>40) return 3;
    std::vector<std::array<uint64_t,24>> columns(n);
    std::vector<uint64_t> labels(n);
    std::vector<int> weights(n);
    for(int j=0;j<n;j++) {
        for(int w=0;w<sw;w++) in >> columns[j][w];
        in >> labels[j] >> weights[j];
    }
    if (!in) return 4;
    int trials=std::stoi(argv[3]);
    std::mt19937_64 rng(std::stoull(argv[4]));
    std::vector<int> order(n); std::iota(order.begin(),order.end(),0);
    std::vector<std::array<uint64_t,24>> bs(m);
    std::vector<std::array<uint64_t,40>> bv(m);
    std::vector<uint64_t> bl(m);
    std::vector<bool> present(m);
    int best=100000000, best_trial=-1, rank=0;
    uint64_t best_label=0;
    std::array<uint64_t,40> witness{};
    auto start=std::chrono::steady_clock::now();
    for(int t=0;t<trials;t++) {
        std::shuffle(order.begin(),order.end(),rng);
        std::fill(present.begin(),present.end(),false); rank=0;
        for(int j:order) {
            auto s=columns[j]; std::array<uint64_t,40> v{};
            v[j/64]=uint64_t(1)<<(j%64); uint64_t l=labels[j];
            bool pivot=false;
            for(int w=sw-1;w>=0;w--) {
                while(s[w]) {
                    int p=w*64+63-__builtin_clzll(s[w]);
                    if(!present[p]) {
                        present[p]=true; bs[p]=s; bv[p]=v; bl[p]=l;
                        rank++; pivot=true; break;
                    }
                    for(int z=0;z<=w;z++) s[z]^=bs[p][z];
                    for(int z=0;z<vw;z++) v[z]^=bv[p][z];
                    l^=bl[p];
                }
                if(pivot) break;
            }
            if(!pivot && l) {
                int cost=0;
                for(int w=0;w<vw;w++) {
                    uint64_t word=v[w];
                    while(word) {int b=__builtin_ctzll(word);cost+=weights[64*w+b];word&=word-1;}
                    if(cost>=best) break;
                }
                if(cost<best) {best=cost;best_trial=t;witness=v;best_label=l;}
            }
        }
    }
    std::ofstream out(argv[2]);
    out << "{\"trials\":" << trials << ",\"seed\":" << argv[4]
        << ",\"rank\":" << rank << ",\"seconds\":"
        << std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()
        << ",\"best_cost\":" << (best_trial<0?-1:best)
        << ",\"best_trial\":" << best_trial << ",\"logical_label\":" << best_label
        << ",\"support\":[";
    bool first=true;
    for(int j=0;j<n;j++) if((witness[j/64]>>(j%64))&1) {
        if(!first)out<<",";first=false;out<<j;
    }
    out << "]}\n";
    return 0;
}
