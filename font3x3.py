A = """
010
111
101
"""
B = """
110
111
110
"""
C = """
011
100
011
"""
D = """
110
101
110
"""
E = """
111
110
111
"""
F = """
111
110
100
"""
G = """
110
101
111
"""
H = """
101
111
101
"""
I = """
111
010
111
"""
J = """
001
001
110
"""
K = """
101
110
101
"""
L = """
100
100
111
"""
M = """
111
111
101
"""
N = """
110
101
101
"""
O = """
111
101
111
"""
P = """
111
111
100
"""
Q = """
111
101
110
"""
R = """
110
111
101
"""
S = """
011
010
110
"""
T = """
111
010
010
"""
U = """
101
101
111
"""
V = """
101
101
010
"""
W = """
101
111
111
"""
X = """
101
010
101
"""
Y = """
101
010
010
"""
Z = """
110
010
011
"""

ATLAS = {}
for i in range(65, 91):
    ATLAS[chr(i)] = locals()[chr(i)]


def concat(bms):
    result = []
    for lino in range(3):
        line = ""
        for l in range(len(bms)):
            line += bms[l].strip().split("\n")[lino]
        result.append(line)
    return "\n".join(result)


def print3r(text, blankzero=False):
    bms = []
    for idx, c in enumerate(text):
        bms.append(ATLAS[c.upper()].replace("1", str(1 + (idx % 9))))
    if blankzero:
        return concat(bms).replace("0", " ")
    else:
        return concat(bms)
