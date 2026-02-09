"""Reduced-round Rijndael (3 rounds) for Samsung TV SamyGO key transform.

NOT standard AES (which uses 10 rounds for 128-bit keys).
Ported from SmartCrypto/IPRemote py3rijndael.
"""

import copy

# --- Constants (generated once at import) ---

shifts = [[[0, 0], [1, 3], [2, 2], [3, 1]],
          [[0, 0], [1, 5], [2, 4], [3, 3]],
          [[0, 0], [1, 7], [3, 5], [4, 4]]]

num_rounds = {16: {16: 3}}

a_log = [1]
for _i in range(255):
    _j = (a_log[-1] << 1) ^ a_log[-1]
    if _j & 0x100 != 0:
        _j ^= 0x11B
    a_log.append(_j)

log = [0] * 256
for _i in range(1, 255):
    log[a_log[_i]] = _i


def _mul(a, b):
    if a == 0 or b == 0:
        return 0
    return a_log[(log[a & 0xFF] + log[b & 0xFF]) % 255]


_A = [[1, 1, 1, 1, 1, 0, 0, 0],
      [0, 1, 1, 1, 1, 1, 0, 0],
      [0, 0, 1, 1, 1, 1, 1, 0],
      [0, 0, 0, 1, 1, 1, 1, 1],
      [1, 0, 0, 0, 1, 1, 1, 1],
      [1, 1, 0, 0, 0, 1, 1, 1],
      [1, 1, 1, 0, 0, 0, 1, 1],
      [1, 1, 1, 1, 0, 0, 0, 1]]

_box = [[0] * 8 for _ in range(256)]
_box[1][7] = 1
for _i in range(2, 256):
    _j = a_log[255 - log[_i]]
    for _t in range(8):
        _box[_i][_t] = (_j >> (7 - _t)) & 0x01

_B = [0, 1, 1, 0, 0, 0, 1, 1]
_cox = [[0] * 8 for _ in range(256)]
for _i in range(256):
    for _t in range(8):
        _cox[_i][_t] = _B[_t]
        for _j2 in range(8):
            _cox[_i][_t] ^= _A[_t][_j2] * _box[_i][_j2]

S = [0] * 256
for _i in range(256):
    S[_i] = _cox[_i][0] << 7
    for _t in range(1, 8):
        S[_i] ^= _cox[_i][_t] << (7 - _t)

_G = [[2, 1, 1, 3], [3, 2, 1, 1], [1, 3, 2, 1], [1, 1, 3, 2]]


def _mul4(a, bs):
    if a == 0:
        return 0
    rr = 0
    for b in bs:
        rr <<= 8
        if b != 0:
            rr = rr | _mul(a, b)
    return rr


T1, T2, T3, T4 = [], [], [], []
for _t in range(256):
    _s = S[_t]
    T1.append(_mul4(_s, _G[0]))
    T2.append(_mul4(_s, _G[1]))
    T3.append(_mul4(_s, _G[2]))
    T4.append(_mul4(_s, _G[3]))

r_con = [1]
_r = 1
for _ in range(1, 30):
    _r = _mul(2, _r)
    r_con.append(_r)


# --- Encrypt ---

def encrypt(key: bytes, source: bytes) -> bytes:
    """Rijndael-128 encrypt with 3 rounds (NOT standard AES)."""
    block_size = 16
    b_c = block_size // 4
    rounds = num_rounds[len(key)][block_size]
    k_e = [[0] * b_c for _ in range(rounds + 1)]
    round_key_count = (rounds + 1) * b_c
    k_c = len(key) // 4

    tk = []
    for i in range(k_c):
        tk.append(
            (ord(key[i * 4:i * 4 + 1]) << 24) |
            (ord(key[i * 4 + 1:i * 4 + 2]) << 16) |
            (ord(key[i * 4 + 2:i * 4 + 3]) << 8) |
            ord(key[i * 4 + 3:i * 4 + 4])
        )

    t = 0
    j = 0
    while j < k_c and t < round_key_count:
        k_e[t // b_c][t % b_c] = tk[j]
        j += 1
        t += 1

    r_con_pointer = 0
    while t < round_key_count:
        tt = tk[k_c - 1]
        tk[0] ^= (
            (S[(tt >> 16) & 0xFF] & 0xFF) << 24 ^
            (S[(tt >> 8) & 0xFF] & 0xFF) << 16 ^
            (S[tt & 0xFF] & 0xFF) << 8 ^
            (S[(tt >> 24) & 0xFF] & 0xFF) ^
            (r_con[r_con_pointer] & 0xFF) << 24
        )
        r_con_pointer += 1
        for i in range(1, k_c):
            tk[i] ^= tk[i - 1]
        j = 0
        while j < k_c and t < round_key_count:
            k_e[t // b_c][t % b_c] = tk[j]
            j += 1
            t += 1

    s1 = shifts[0][1][0]
    s2 = shifts[0][2][0]
    s3 = shifts[0][3][0]
    a = [0] * b_c
    t_arr = []
    for i in range(b_c):
        t_arr.append(
            (ord(source[i * 4:i * 4 + 1]) << 24 |
             ord(source[i * 4 + 1:i * 4 + 2]) << 16 |
             ord(source[i * 4 + 2:i * 4 + 3]) << 8 |
             ord(source[i * 4 + 3:i * 4 + 4])) ^ k_e[0][i]
        )

    for r in range(1, rounds):
        for i in range(b_c):
            a[i] = (
                T1[(t_arr[i] >> 24) & 0xFF] ^
                T2[(t_arr[(i + s1) % b_c] >> 16) & 0xFF] ^
                T3[(t_arr[(i + s2) % b_c] >> 8) & 0xFF] ^
                T4[t_arr[(i + s3) % b_c] & 0xFF]
            ) ^ k_e[r][i]
        t_arr = copy.copy(a)

    result = []
    for i in range(b_c):
        tt = k_e[rounds][i]
        result.append((S[(t_arr[i] >> 24) & 0xFF] ^ (tt >> 24)) & 0xFF)
        result.append((S[(t_arr[(i + s1) % b_c] >> 16) & 0xFF] ^ (tt >> 16)) & 0xFF)
        result.append((S[(t_arr[(i + s2) % b_c] >> 8) & 0xFF] ^ (tt >> 8)) & 0xFF)
        result.append((S[t_arr[(i + s3) % b_c] & 0xFF] ^ tt) & 0xFF)

    out = b''
    for xx in result:
        out += bytes([xx])
    return out
