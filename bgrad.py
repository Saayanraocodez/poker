"""Batched exact gradient du_owner/dx for a stack of profiles, via the tree."""
import numpy as np, tree as T

ND, NPOS, KAP = T.ND, T.NPOS, T.KAP
INT = list(T.INTERNAL); LEAF = list(T.LEAFPOS)
AGGC, PASC, COORD, PAYT = T.AGGC, T.PASC, T.COORD, T.PAYT
OWN_PL = [T.OWNER[p][0] for p in INT]
S = np.zeros((len(INT) * ND, 48))
for a, pos in enumerate(INT):
    for d in range(ND):
        S[a * ND + d, COORD[d, pos]] = 1.0

def grads_own(P):
    P = np.asarray(P, float); B = P.shape[0]
    V = np.zeros((B, ND, NPOS, 3))
    V[:, :, LEAF] = PAYT[:, LEAF][None]
    for pos in INT[::-1]:
        x = P[:, COORD[:, pos]][:, :, None]
        V[:, :, pos] = x * V[:, :, AGGC[pos]] + (1 - x) * V[:, :, PASC[pos]]
    R = np.zeros((B, ND, NPOS)); R[:, :, 0] = 1.0
    for pos in INT:
        x = P[:, COORD[:, pos]]
        R[:, :, AGGC[pos]] = R[:, :, pos] * x
        R[:, :, PASC[pos]] = R[:, :, pos] * (1 - x)
    d = np.empty((B, len(INT), ND))
    for a, pos in enumerate(INT):
        i = OWN_PL[a]
        d[:, a] = R[:, :, pos] * (V[:, :, AGGC[pos], i] - V[:, :, PASC[pos], i])
    return KAP * (d.reshape(B, -1) @ S)

def utils(P):
    P = np.asarray(P, float); B = P.shape[0]
    V = np.zeros((B, ND, NPOS, 3))
    V[:, :, LEAF] = PAYT[:, LEAF][None]
    for pos in INT[::-1]:
        x = P[:, COORD[:, pos]][:, :, None]
        V[:, :, pos] = x * V[:, :, AGGC[pos]] + (1 - x) * V[:, :, PASC[pos]]
    return KAP * V[:, :, 0].sum(axis=1)

def reaches(P):
    P = np.asarray(P, float); B = P.shape[0]
    R = np.zeros((B, ND, NPOS)); R[:, :, 0] = 1.0
    for pos in INT:
        x = P[:, COORD[:, pos]]
        R[:, :, AGGC[pos]] = R[:, :, pos] * x
        R[:, :, PASC[pos]] = R[:, :, pos] * (1 - x)
    return (R[:, :, INT].transpose(0, 2, 1).reshape(B, -1) @ S) * KAP
