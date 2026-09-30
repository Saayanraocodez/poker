import os, sys, time
os.environ["KUHN_MODE"] = "nash"; os.environ["KUHN_ORDER"] = "bet"
import numpy as np
import treesize6 as T6, enumc3 as E3, certbox, treebound as TB
U, MIX, DC = 9, 2, 3
spec = "a11:0,a21:MIX,a31:0,a41:MIX"
rng = np.random.default_rng(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
root_lab, LO, HI = T6.root_of(spec)
L2, A2, B2, al = T6.propagate(root_lab[None], LO[None], HI[None], False)
lab = root_lab.copy(); lab[(lab == U) & (L2[0] == DC)] = DC; LO, HI = A2[0], B2[0]
cbox = None; depth = 0
tc = tk = 0.0; unsure_plain = unsure_inh = 0; tried = 0
while depth < 40:
    u = [x for x in E3.ORDER if lab[x] == U]
    if not u: break
    v = u[0]
    t0 = time.time(); st, rec, cbox2 = E3.contract_node(lab, cbox); tc += time.time() - t0
    if st == "dead": print("depth %d: node dead by inherited contraction" % depth); break
    cbox = cbox2
    kids = []
    for l in (0, 1, MIX):
        l2 = lab.copy(); a2 = LO.copy(); b2 = HI.copy(); l2[v] = l
        if l == 0: b2[v] = 0.0
        elif l == 1: a2[v] = 1.0
        kids.append((l2, a2, b2))
    Lk = np.array([q[0] for q in kids]); Ak = np.array([q[1] for q in kids]); Bk = np.array([q[2] for q in kids])
    L3, A3, B3, al3 = T6.propagate(Lk, Ak, Bk, False)
    allowed = [LO[v] <= 0.0, HI[v] >= 1.0, HI[v] > 0.0 and LO[v] < 1.0]
    for t, l in enumerate((0, 1, MIX)):
        if not (allowed[t] and al3[t]):
            tried += 1
            t0 = time.time(); kp = E3.kill_cert(kids[t][0], None); t_plain = time.time() - t0
            t0 = time.time(); ki = E3.kill_cert(kids[t][0], E3.child_cbox(cbox, v, l)); t_inh = time.time() - t0
            tk += t_plain + t_inh
            unsure_plain += kp is None; unsure_inh += ki is None
            print("depth %2d child %s float-dead: label-box cert %-4s (%.1fs)  inherited-box cert %-4s (%.1fs)" % (
                depth, l, "OK" if kp else "FAIL", t_plain, "OK" if ki else "FAIL", t_inh), flush=True)
    live = [t for t in range(3) if allowed[t] and al3[t]]
    if not live: print("depth %d: all children float-dead" % depth); break
    t = live[rng.integers(len(live))]
    lab = kids[t][0].copy(); lab[(lab == U) & (L3[t] == DC)] = DC; LO, HI = A3[t], B3[t]
    cbox = E3.child_cbox(cbox, v, (0, 1, MIX)[t]); depth += 1
print("path depth %d: contraction %.1fs total; float-dead children %d: uncertifiable from label box %d, from inherited box %d" % (
    depth, tc, tried, unsure_plain, unsure_inh))
