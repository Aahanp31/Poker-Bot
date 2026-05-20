#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <algorithm>
#include <cstdint>
#include <random>
#include <vector>

namespace py = pybind11;

// Card encoding: card_int = (rank - 2) * 4 + suit
//   rank_idx = card_int >> 2  (0=Two ... 12=Ace)
//   suit     = card_int  & 3

// This struct implements the xoshiro256++ PRNG. It seeds from system entropy and
// produces 64-bit values with strong statistical quality and low overhead.
struct Xoshiro {
    uint64_t s[4];

    Xoshiro() {
        std::random_device rd;
        for (auto& x : s) x = (uint64_t)rd() << 32 | (uint64_t)rd();
    }

    uint64_t next() {
        const uint64_t r = rotl(s[0] + s[3], 23) + s[0];
        const uint64_t t = s[1] << 17;
        s[2] ^= s[0]; s[3] ^= s[1];
        s[1] ^= s[2]; s[0] ^= s[3];
        s[2] ^= t;
        s[3]  = rotl(s[3], 45);
        return r;
    }

    static uint64_t rotl(uint64_t x, int k) { return x << k | x >> (64 - k); }
};

// 9-comparator sorting network for 5 elements, descending
#define CSWAP(a, b) do { if ((a) < (b)) { int _t=(a); (a)=(b); (b)=_t; } } while(0)

static inline void sort5d(int* r) {
    CSWAP(r[0],r[1]); CSWAP(r[2],r[3]);
    CSWAP(r[0],r[2]); CSWAP(r[1],r[3]);
    CSWAP(r[1],r[2]); CSWAP(r[0],r[4]);
    CSWAP(r[1],r[4]); CSWAP(r[2],r[4]);
    CSWAP(r[3],r[4]);
}

// This function evaluates a 5-card hand and returns a comparable score.
// Parameters:
//   - c: array of 5 card integers (card_int = rank_idx*4 + suit, rank_idx 0=Two..12=Ace)
// Returns:
//   - uint32_t: hand score (higher is better), encoded as class*1000000 + tiebreaker
static uint32_t eval5(const int* c) {
    int r[5], s[5];
    for (int i = 0; i < 5; i++) { r[i] = c[i] >> 2; s[i] = c[i] & 3; }
    sort5d(r);

    const bool flush    = s[0]==s[1] && s[1]==s[2] && s[2]==s[3] && s[3]==s[4];
    const bool unique   = r[0]!=r[1] && r[1]!=r[2] && r[2]!=r[3] && r[3]!=r[4];
    const bool wheel    = r[0]==12 && r[1]==3 && r[2]==2 && r[3]==1 && r[4]==0;
    const bool straight = wheel || (unique && r[0]-r[4]==4);

    int cnt[13] = {};
    for (int i = 0; i < 5; i++) cnt[r[i]]++;

    struct G { int cnt, rank; };
    G g[5]; int ng = 0;
    for (int rk = 12; rk >= 0; rk--)
        if (cnt[rk]) g[ng++] = {cnt[rk], rk};

    for (int i = 1; i < ng; i++) {
        G tmp = g[i]; int j = i;
        while (j > 0 && g[j-1].cnt < tmp.cnt) { g[j] = g[j-1]; --j; }
        g[j] = tmp;
    }

    const uint32_t B = 13;
    uint32_t cls, tb;

    if (straight && flush) {
        cls = 8; tb = wheel ? 3u : (uint32_t)r[0];
    } else if (g[0].cnt == 4) {
        cls = 7; tb = g[0].rank*B + g[1].rank;
    } else if (g[0].cnt == 3 && ng == 2) {
        cls = 6; tb = g[0].rank*B + g[1].rank;
    } else if (flush) {
        cls = 5; tb = r[0]*B*B*B*B + r[1]*B*B*B + r[2]*B*B + r[3]*B + r[4];
    } else if (straight) {
        cls = 4; tb = wheel ? 3u : (uint32_t)r[0];
    } else if (g[0].cnt == 3) {
        cls = 3; tb = g[0].rank*B*B + g[1].rank*B + g[2].rank;
    } else if (g[0].cnt == 2 && g[1].cnt == 2) {
        cls = 2; tb = g[0].rank*B*B + g[1].rank*B + g[2].rank;
    } else if (g[0].cnt == 2) {
        cls = 1; tb = g[0].rank*B*B*B + g[1].rank*B*B + g[2].rank*B + g[3].rank;
    } else {
        cls = 0; tb = r[0]*B*B*B*B + r[1]*B*B*B + r[2]*B*B + r[3]*B + r[4];
    }

    return cls * 1000000u + tb;
}

// Precomputed index sets for all C(7,5) = 21 combinations
static const uint8_t CHOOSE[21][5] = {
    {2,3,4,5,6}, {1,3,4,5,6}, {1,2,4,5,6}, {1,2,3,5,6}, {1,2,3,4,6}, {1,2,3,4,5},
    {0,3,4,5,6}, {0,2,4,5,6}, {0,2,3,5,6}, {0,2,3,4,6}, {0,2,3,4,5},
    {0,1,4,5,6}, {0,1,3,5,6}, {0,1,3,4,6}, {0,1,3,4,5},
    {0,1,2,5,6}, {0,1,2,4,6}, {0,1,2,4,5},
    {0,1,2,3,6}, {0,1,2,3,5},
    {0,1,2,3,4},
};

// This function finds the best 5-card hand from 7 cards by evaluating all C(7,5) = 21 subsets.
// Parameters:
//   - cards: array of 7 card integers
// Returns:
//   - uint32_t: best eval5 score across all subsets
static uint32_t eval7(const int* cards) {
    uint32_t best = 0;
    for (int i = 0; i < 21; i++) {
        const uint8_t* idx = CHOOSE[i];
        const int five[5] = {cards[idx[0]], cards[idx[1]], cards[idx[2]],
                              cards[idx[3]], cards[idx[4]]};
        const uint32_t s = eval5(five);
        if (s > best) best = s;
    }
    return best;
}

// This function runs Monte Carlo equity estimation for a Texas Hold'em hand.
// Parameters:
//   - hole: hero's 2 hole cards as card integers
//   - board: known community cards (0-5 card integers)
//   - num_opponents: number of active opponents to simulate
//   - num_sims: number of random runouts to evaluate
// Returns:
//   - dict: {'win': float, 'tie': float, 'loss': float} as fractions of total simulations
py::dict monte_carlo(
    const std::vector<int>& hole,
    const std::vector<int>& board,
    int num_opponents,
    int num_sims
) {
    bool used[52] = {};
    for (int c : hole)  used[c] = true;
    for (int c : board) used[c] = true;

    std::vector<int> remaining;
    remaining.reserve(52 - (int)hole.size() - (int)board.size());
    for (int c = 0; c < 52; c++)
        if (!used[c]) remaining.push_back(c);

    const int board_size   = (int)board.size();
    const int board_need   = 5 - board_size;
    const int cards_needed = board_need + num_opponents * 2;
    const int n            = (int)remaining.size();

    Xoshiro rng;

    int my7[7];
    my7[0] = hole[0]; my7[1] = hole[1];
    for (int i = 0; i < board_size; i++) my7[2 + i] = board[i];

    std::vector<std::array<int,7>> opp_base(num_opponents);
    for (int o = 0; o < num_opponents; o++)
        for (int i = 0; i < board_size; i++)
            opp_base[o][2 + i] = board[i];

    int wins = 0, ties = 0, losses = 0;
    std::vector<int> pool(n);

    for (int sim = 0; sim < num_sims; sim++) {
        std::copy(remaining.begin(), remaining.end(), pool.begin());
        for (int i = 0; i < cards_needed; i++) {
            const int j = i + rng.next() % (uint64_t)(n - i);
            std::swap(pool[i], pool[j]);
        }

        for (int i = 0; i < board_need; i++)
            my7[2 + board_size + i] = pool[i];

        const uint32_t my_score = eval7(my7);
        uint32_t best_opp = 0;

        for (int o = 0; o < num_opponents; o++) {
            auto& opp = opp_base[o];
            opp[0] = pool[board_need + o * 2];
            opp[1] = pool[board_need + o * 2 + 1];
            for (int i = 0; i < board_need; i++)
                opp[2 + board_size + i] = pool[i];
            const uint32_t opp_score = eval7(opp.data());
            if (opp_score > best_opp) best_opp = opp_score;
        }

        if      (my_score > best_opp)  wins++;
        else if (my_score == best_opp) ties++;
        else                           losses++;
    }

    py::dict result;
    result["win"]  = (double)wins   / num_sims;
    result["tie"]  = (double)ties   / num_sims;
    result["loss"] = (double)losses / num_sims;
    return result;
}

PYBIND11_MODULE(mc_cpp, m) {
    m.doc() = "Fast C++ Monte Carlo poker equity calculator";
    m.def("monte_carlo", &monte_carlo,
        py::arg("hole_cards"),
        py::arg("board"),
        py::arg("num_opponents"),
        py::arg("num_sims") = 10000);
}
