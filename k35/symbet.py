"""Is there structure in du1/da_j1 -- the derivative that decides whether P1 bets?

Every numerical route to the betting branch is now closed by measurement:
support enumeration is 10^9-10^10 patterns per branch, box refinement grows
1.44x per level needing ~104 more, and singleton look-ahead -- the strongest
generic propagation strengthening -- leaves the estimate unchanged at 2.42e10
with 100 % of paths still surviving.  So the obstruction is the BOUND, and no
amount of branching or budget touches it.

What settled the silent branch was not compute but a factorisation: s15.6 found
du2/db21 = 0 collapsing to b23*(2*c11 - 1) = 0, and that single factorisation is
the origin of SGS's three sub-families.  This asks the same question of the
derivative that governs P1 betting.

Two computations, cheapest first:

  1. du1/da_j1 with ONLY Table 2 substituted (21 coordinates forced, 27 free).
     Print it factored.  A factorisation here would do for the bet branch what
     s15.6's did for the silent one.
  2. du1/da_j1 against a general FAMILY opponent -- P2 and P3 built from
     family.make_profile with its 7 free parameters, P1 free.  This is small
     enough to reason about, and it answers "how much does P1 lose by betting
     card j against any member of the family, as a function of that member".

Reports degree and term count before printing anything, because a 27-variable
multilinear expansion can be enormous and an unreadable blob is not a result.
"""
import sys, time
import sympy as sp
import tree as T
import kuhn3p as K

I = K.NAME_IDX
NAME = K.PARAM_NAME

T2_ZERO = ("a12", "a13", "a14", "a24", "b12", "b13", "b14", "b24",
           "c12", "c13", "c14", "c24")
T2_ONE = ("a42", "a43", "a44", "b42", "b43", "b44", "c42", "c43", "c44")
OPEN = ("a11", "a21", "a31", "a41")


def build(Xvals):
    """Symbolic tree pass -> (G, U): own-gradients per coordinate, utilities."""
    V = [[None] * T.NPOS for _ in range(T.ND)]
    for d in range(T.ND):
        for pos in T.LEAFPOS:
            V[d][pos] = [sp.Integer(int(T.PAYT[d, pos, i])) for i in range(3)]
        for pos in list(T.INTERNAL)[::-1]:
            x = Xvals[T.COORD[d, pos]]
            V[d][pos] = [sp.expand(x * V[d][T.AGGC[pos]][i]
                                   + (1 - x) * V[d][T.PASC[pos]][i])
                         for i in range(3)]
    R = [[sp.Integer(0)] * T.NPOS for _ in range(T.ND)]
    for d in range(T.ND):
        R[d][0] = sp.Integer(1)
        for pos in T.INTERNAL:
            x = Xvals[T.COORD[d, pos]]
            R[d][T.AGGC[pos]] = sp.expand(R[d][pos] * x)
            R[d][T.PASC[pos]] = sp.expand(R[d][pos] * (1 - x))
    G = [sp.Integer(0)] * K.NPARAM
    for d in range(T.ND):
        for pos in T.INTERNAL:
            i = T.OWNER[pos][0]
            G[T.COORD[d, pos]] += sp.Rational(1, 24) * R[d][pos] * (
                V[d][T.AGGC[pos]][i] - V[d][T.PASC[pos]][i])
    U = [sp.expand(sp.Rational(1, 24) * sum(V[d][0][i] for d in range(T.ND)))
         for i in range(3)]
    return G, U


def build_D(Xvals):
    """Own-reach-stripped gradients:  D_i = (1/24) sum_n R_{-i}(n) * Delta_n over
    the nodes n of coordinate i's information set, where R_{-i} multiplies only
    the OTHER players' coordinates along the path (own earlier choices set to 1).

    Why: a Nash strategy must be optimal at every information set the player
    could reach by their OWN deviation (one-deviation principle over the
    player's own decision tree), with beliefs proportional to the opponents'
    reach.  Where the set is reached, D_i and G_i have the same sign (the own
    factor is common to the whole set); where only the player's own choice
    keeps it unreached, G_i = 0 says nothing while D_i is the real condition.
    Where an OPPONENT's zero-probability action makes it unreached, D_i = 0 and
    Nash indeed requires nothing.  Sequential rationality of every coordinate
    with respect to D is therefore equivalent to Nash -- up to re-choosing
    own-unreached coordinates, which never changes on-path play."""
    V = [[None] * T.NPOS for _ in range(T.ND)]
    for d in range(T.ND):
        for pos in T.LEAFPOS:
            V[d][pos] = [sp.Integer(int(T.PAYT[d, pos, i])) for i in range(3)]
        for pos in list(T.INTERNAL)[::-1]:
            x = Xvals[T.COORD[d, pos]]
            V[d][pos] = [sp.expand(x * V[d][T.AGGC[pos]][i]
                                   + (1 - x) * V[d][T.PASC[pos]][i])
                         for i in range(3)]
    # R[d][pos][player]: reach of pos with player's own coordinates stripped
    R = [[None] * T.NPOS for _ in range(T.ND)]
    for d in range(T.ND):
        R[d][0] = [sp.Integer(1)] * 3
        for pos in T.INTERNAL:
            x = Xvals[T.COORD[d, pos]]
            own = T.OWNER[pos][0]
            R[d][T.AGGC[pos]] = [R[d][pos][i] if i == own else sp.expand(R[d][pos][i] * x) for i in range(3)]
            R[d][T.PASC[pos]] = [R[d][pos][i] if i == own else sp.expand(R[d][pos][i] * (1 - x)) for i in range(3)]
    D = [sp.Integer(0)] * K.NPARAM
    for d in range(T.ND):
        for pos in T.INTERNAL:
            i = T.OWNER[pos][0]
            D[T.COORD[d, pos]] += sp.Rational(1, 24) * R[d][pos][i] * (
                V[d][T.AGGC[pos]][i] - V[d][T.PASC[pos]][i])
    return [sp.expand(g) for g in D]


def table2_only():
    """21 coordinates forced by Table 2; the other 27 symbolic."""
    X = [None] * K.NPARAM
    for n in T2_ZERO:
        X[I[n]] = sp.Integer(0)
    for n in T2_ONE:
        X[I[n]] = sp.Integer(1)
    syms = {}
    for i in range(K.NPARAM):
        if X[i] is None:
            syms[NAME[i]] = sp.Symbol(NAME[i], nonnegative=True)
            X[i] = syms[NAME[i]]
    return X, syms


def report(expr, label):
    e = sp.expand(expr)
    terms = len(e.args) if e.is_Add else 1
    dg = sp.total_degree(e) if e != 0 else 0
    print("   %-10s terms %-7d total degree %-3s" % (label, terms, dg), flush=True)
    if terms <= 40:
        print("      = %s" % sp.factor(e), flush=True)
    else:
        f = sp.factor(e)
        # only worth printing if factoring actually found structure
        if f.is_Mul and len(f.args) > 1:
            print("      FACTORS: %s" % f, flush=True)
        else:
            print("      (does not factor; %d terms suppressed)" % terms, flush=True)
    return e


if __name__ == "__main__":
    t0 = time.time()
    print("=== 1. du1/da_j1 with only Table 2 substituted (27 free) ===\n", flush=True)
    X, syms = table2_only()
    G, U = build(X)
    for n in OPEN:
        report(G[I[n]], "du1/d%s" % n)
    print("\n   %.0fs" % (time.time() - t0), flush=True)
