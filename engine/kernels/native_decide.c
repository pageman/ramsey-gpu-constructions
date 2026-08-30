/* Decision MIS: does G have an independent set of size AIM?
 * No Russian-doll exact-α (that is why native_mis.c timed out on Yu 186).
 * Optional OpenMP flatten of the first two branches.
 *
 * gcc -O3 -shared -fPIC -fopenmp -o native_decide.so native_decide.c
 * gcc -O3 -shared -fPIC -o native_decide.so native_decide.c   # fallback
 */
#include <stdint.h>
#include <string.h>
#include <time.h>

#ifdef _OPENMP
#include <omp.h>
#endif

#define WORDS 4
#define MAXN 256

typedef uint64_t word;

static int N, AIM;
static word NBR[MAXN][WORDS];
static word CLOSED[MAXN][WORDS];
static long NODES;
static int FOUND, TIMED_OUT;
static double DEADLINE;

static inline double wall_now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + 1e-9 * (double)ts.tv_nsec;
}

static inline int popc(const word *b) {
    return __builtin_popcountll(b[0]) + __builtin_popcountll(b[1])
         + __builtin_popcountll(b[2]) + __builtin_popcountll(b[3]);
}

static inline int empty(const word *b) {
    return !(b[0] | b[1] | b[2] | b[3]);
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
#ifdef _OPENMP
    #pragma omp atomic
#endif
    NODES++;
    if ((NODES & 262143) == 0 && wall_now() > DEADLINE) {
        TIMED_OUT = 1;
        return;
    }
    if (size >= AIM) {
        FOUND = 1;
        return;
    }
    if (size + popc(p) < AIM) return;
    if (empty(p)) return;
    /* α(G[P]) ≤ |P| − ν(G[P]); greedy matching is O(|P|). */
    {
        word used[WORDS] = {0};
        int matched = 0;
        for (int w = 0; w < WORDS; w++) {
            word bits = p[w];
            while (bits) {
                int v = (w << 6) + __builtin_ctzll(bits);
                bits &= bits - 1;
                if ((used[w] >> (v & 63)) & 1u) continue;
                for (int i = 0; i < WORDS; i++) {
                    word cand = p[i] & NBR[v][i] & ~used[i];
                    if (!cand) continue;
                    int u = (i << 6) + __builtin_ctzll(cand);
                    used[v >> 6] |= (word)1 << (v & 63);
                    used[u >> 6] |= (word)1 << (u & 63);
                    matched++;
                    goto next_v;
                }
            next_v:
                ;
            }
        }
        if (size + popc(p) - matched < AIM) return;
    }
    /* Clique-cover / colouring of the complement: α(G[P]) ≤ χ(¯G[P]).
     * Yu's "matching colour bound on the complement". Helps once |P| shrinks. */
    {
        int col[MAXN];
        for (int i = 0; i < N; i++) col[i] = -1;
        int ncolors = 0;
        for (int w = 0; w < WORDS; w++) {
            word bits = p[w];
            while (bits) {
                int v = (w << 6) + __builtin_ctzll(bits);
                bits &= bits - 1;
                unsigned long long forbid = 0;
                for (int i = 0; i < WORDS; i++) {
                    word nonadj = p[i] & ~NBR[v][i];
                    if (i == (v >> 6)) nonadj &= ~((word)1 << (v & 63));
                    while (nonadj) {
                        int u = (i << 6) + __builtin_ctzll(nonadj);
                        nonadj &= nonadj - 1;
                        int c = col[u];
                        if (c >= 0 && c < 63) forbid |= 1ULL << (unsigned)c;
                    }
                }
                int c = 0;
                while (c < 63 && ((forbid >> c) & 1ULL)) c++;
                col[v] = c;
                if (c + 1 > ncolors) ncolors = c + 1;
            }
        }
        if (size + ncolors < AIM) return;
    }

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

/* Collect (mask, size) after two take/skip choices, then solve in parallel. */
typedef struct {
    word p[WORDS];
    int size;
} subprob;

static void push_subs(word *p, int size, int depth, subprob *out, int *nout, int cap) {
    if (FOUND || *nout >= cap) return;
    if (size >= AIM) {
        FOUND = 1;
        return;
    }
    if (size + popc(p) < AIM || empty(p)) return;
    if (depth >= 2) {
        memcpy(out[*nout].p, p, sizeof(word) * WORDS);
        out[*nout].size = size;
        (*nout)++;
        return;
    }
    int best_v = first_bit(p);
    if (best_v < 0) return;
    word q[WORDS];
    for (int i = 0; i < WORDS; i++) q[i] = p[i] & ~CLOSED[best_v][i];
    push_subs(q, size + 1, depth + 1, out, nout, cap);
    memcpy(q, p, sizeof(q));
    clrb(q, best_v);
    push_subs(q, size, depth + 1, out, nout, cap);
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

int mis_decide_aim(int n, const uint64_t *nbr_flat, int target, double seconds,
                   int greedy_lower, long *nodes_out, int *lower_out, int *timed_out) {
    if (n <= 0 || n > MAXN) {
        if (nodes_out) *nodes_out = 0;
        if (lower_out) *lower_out = greedy_lower;
        if (timed_out) *timed_out = 1;
        return 0;
    }
    FOUND = 0;
    TIMED_OUT = 0;
    NODES = 0;
    AIM = target;
    N = n;
    if (greedy_lower >= target) {
        *nodes_out = 0;
        *lower_out = greedy_lower;
        *timed_out = 0;
        return 1;
    }
    int perm[MAXN], inv[MAXN];
    degeneracy_relabel(n, nbr_flat, perm);
    for (int i = 0; i < n; i++) inv[perm[i]] = i;
    memset(NBR, 0, sizeof(NBR));
    memset(CLOSED, 0, sizeof(CLOSED));
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
    DEADLINE = wall_now() + seconds;

    word full[WORDS] = {0};
    for (int v = 0; v < n; v++) setb(full, v);

    subprob subs[8];
    int nsub = 0;
    push_subs(full, 0, 0, subs, &nsub, 8);
    if (FOUND) {
        *nodes_out = NODES;
        *lower_out = target;
        *timed_out = 0;
        return 1;
    }
#ifdef _OPENMP
    #pragma omp parallel for schedule(dynamic, 1) shared(FOUND, TIMED_OUT, NODES)
    for (int s = 0; s < nsub; s++) {
        if (FOUND || TIMED_OUT) continue;
        rec(subs[s].p, subs[s].size);
    }
#else
    for (int s = 0; s < nsub; s++) {
        if (FOUND || TIMED_OUT) break;
        rec(subs[s].p, subs[s].size);
    }
#endif

    *nodes_out = NODES;
    *lower_out = FOUND ? target : greedy_lower;
    *timed_out = TIMED_OUT;
    return FOUND;
}
