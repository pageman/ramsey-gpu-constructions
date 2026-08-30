/* Östergård MIS, n ≤ 256. Each suffix only asks “can we beat c[i+1]?”.
 * gcc -O3 -shared -fPIC -o native_mis.so native_mis.c
 */
#include <stdint.h>
#include <string.h>
#include <time.h>

#define WORDS 4
#define MAXN 256

typedef uint64_t word;

static int N, AIM;
static word NBR[MAXN][WORDS];
static word CLOSED[MAXN][WORDS];
static int C[MAXN + 1];
static long NODES;
static int FOUND, LOWER, TIMED_OUT;
static clock_t DEADLINE;

static inline int popc(const word *b) {
    return __builtin_popcountll(b[0]) + __builtin_popcountll(b[1])
         + __builtin_popcountll(b[2]) + __builtin_popcountll(b[3]);
}

static inline int empty(const word *b) {
    return !(b[0] | b[1] | b[2] | b[3]);
}

static inline int test(const word *p, int v) {
    return (int)((p[v >> 6] >> (v & 63)) & 1u);
}

static inline void setb(word *p, int v) {
    p[v >> 6] |= (word)1 << (v & 63);
}

static inline void clrb(word *p, int v) {
    p[v >> 6] &= ~((word)1 << (v & 63));
}

static inline int first_bit(const word *p) {
    for (int i = 0; i < WORDS; i++) {
        if (p[i]) return (i << 6) + __builtin_ctzll(p[i]);
    }
    return -1;
}

static void rec(word *p, int size) {
    if (FOUND || TIMED_OUT) return;
    NODES++;
    if ((NODES & 262143) == 0 && clock() > DEADLINE) {
        TIMED_OUT = 1;
        return;
    }
    if (size >= AIM) {
        FOUND = 1;
        return;
    }
    if (size + popc(p) < AIM) return;
    if (empty(p)) return;
    int v0 = first_bit(p);
    if (v0 >= 0 && size + C[v0] < AIM) return;

    int best_v = -1, best_d = MAXN;
    for (int w = 0; w < WORDS; w++) {
        word bits = p[w];
        while (bits) {
            int v = (w << 6) + __builtin_ctzll(bits);
            bits &= bits - 1;
            int d = 0;
            for (int i = 0; i < WORDS; i++) d += __builtin_popcountll(p[i] & NBR[v][i]);
            if (d < best_d) {
                best_d = d;
                best_v = v;
                if (d == 0) goto picked;
            }
        }
    }
picked:
    if (best_v < 0) return;
    word q[WORDS];
    for (int i = 0; i < WORDS; i++) q[i] = p[i] & ~CLOSED[best_v][i];
    rec(q, size + 1);
    if (FOUND || TIMED_OUT) return;
    memcpy(q, p, sizeof(q));
    clrb(q, best_v);
    rec(q, size);
}

static void degeneracy_relabel(int n, const uint64_t *src, int *perm) {
    int deg[MAXN];
    word raw[MAXN][WORDS];
    memset(raw, 0, sizeof(raw));
    for (int v = 0; v < n; v++) {
        deg[v] = 0;
        for (int i = 0; i < WORDS; i++) {
            raw[v][i] = src[v * WORDS + i];
            deg[v] += __builtin_popcountll(raw[v][i]);
        }
    }
    int used[MAXN] = {0};
    for (int k = 0; k < n; k++) {
        int best = -1, bd = MAXN;
        for (int v = 0; v < n; v++) {
            if (!used[v] && deg[v] < bd) {
                bd = deg[v];
                best = v;
            }
        }
        perm[n - 1 - k] = best;
        used[best] = 1;
        for (int i = 0; i < WORDS; i++) {
            word bits = raw[best][i];
            while (bits) {
                int u = (i << 6) + __builtin_ctzll(bits);
                bits &= bits - 1;
                if (!used[u]) deg[u]--;
            }
        }
    }
}

int mis_decide(int n, const uint64_t *nbr_flat, int target, double seconds,
               int greedy_lower, long *nodes_out, int *lower_out, int *timed_out) {
    if (n <= 0 || n > MAXN) {
        if (nodes_out) *nodes_out = 0;
        if (lower_out) *lower_out = greedy_lower;
        if (timed_out) *timed_out = 1;
        return 0;
    }
    FOUND = 0;
    LOWER = greedy_lower;
    TIMED_OUT = 0;
    NODES = 0;
    if (LOWER >= target) {
        *nodes_out = 0;
        *lower_out = LOWER;
        *timed_out = 0;
        return 1;
    }
    int perm[MAXN], inv[MAXN];
    degeneracy_relabel(n, nbr_flat, perm);
    for (int i = 0; i < n; i++) inv[perm[i]] = i;
    memset(NBR, 0, sizeof(NBR));
    memset(CLOSED, 0, sizeof(CLOSED));
    N = n;
    for (int ov = 0; ov < n; ov++) {
        int v = inv[ov];
        for (int i = 0; i < WORDS; i++) {
            word bits = nbr_flat[ov * WORDS + i];
            while (bits) {
                int ou = (i << 6) + __builtin_ctzll(bits);
                bits &= bits - 1;
                if (ou < n) setb(NBR[v], inv[ou]);
            }
        }
        memcpy(CLOSED[v], NBR[v], sizeof(CLOSED[v]));
        setb(CLOSED[v], v);
    }
    for (int i = 0; i <= n; i++) C[i] = 0;
    DEADLINE = clock() + (clock_t)(seconds * CLOCKS_PER_SEC);

    /* Each i: can α({i..n-1}) beat c[i+1]? Only the branch that takes i. */
    for (int i = n - 1; i >= 0; i--) {
        if (TIMED_OUT) break;
        AIM = C[i + 1] + 1;
        FOUND = 0;
        word p[WORDS] = {0};
        /* take vertex i, remaining = {i+1..n-1} \ N[i] */
        for (int j = i + 1; j < n; j++) {
            if (!test(CLOSED[i], j)) setb(p, j);
        }
        if (AIM <= 1) {
            C[i] = 1;
            if (C[i] > LOWER) LOWER = C[i];
            if (C[i] >= target) {
                *nodes_out = NODES;
                *lower_out = LOWER;
                *timed_out = 0;
                return 1;
            }
            continue;
        }
        rec(p, 1); /* already took i */
        if (TIMED_OUT) break;
        C[i] = FOUND ? C[i + 1] + 1 : C[i + 1];
        if (C[i] > LOWER) LOWER = C[i];
        if (C[i] >= target) {
            *nodes_out = NODES;
            *lower_out = LOWER;
            *timed_out = 0;
            return 1;
        }
        FOUND = 0;
    }

    *nodes_out = NODES;
    *lower_out = LOWER;
    *timed_out = TIMED_OUT;
    /* FOUND here is leftover from last doll; α = LOWER. Beat target? */
    return LOWER >= target;
}
