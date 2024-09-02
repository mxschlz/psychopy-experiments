import numpy as np


def levenshtein(a, b, ratio=False, print_matrix=False, lowercase=False):
    if not isinstance(a, str):
        raise TypeError('First argument is not a string!')
    if not isinstance(b, str):
        raise TypeError('Second argument is not a string!')
    if a == '':
        return len(b)
    if b == '':
        return len(a)
    if lowercase:
        a = a.lower()
        b = b.lower()

    n = len(a)
    m = len(b)
    lev = np.zeros((n+1, m+1))

    for i in range(0, n+1):
        lev[i, 0] = i
    for i in range(0, m+1):
        lev[0, i] = i

    for i in range(1, n+1):
        for j in range(1, m+1):
            insertion = lev[i-1, j] + 1
            deletion = lev[i, j-1] + 1
            substitution = lev[i-1, j-1] + (1 if a[i-1] != b[j-1] else 0)
            lev[i, j] = min(insertion,deletion,substitution)

    if print_matrix:
        print(lev)

    if ratio:
        return (n+m-lev[n, m])/(n+m)
    else:
        return lev[n, m]


if __name__ == "__main__":
    import pandas as pd
    from Levenshtein import distance
    import random
    df1 = pd.read_excel("C:\PycharmProjects\psychopy-experiments\SPACEPRIME\sequences\sub-999_block_0.xlsx")
    df2 = pd.read_excel("C:\PycharmProjects\psychopy-experiments\SPACEPRIME\sequences\sub-999_block_1.xlsx")
    sequence1 = list()
    for i, row in df1.iterrows():
        element = row["Priming"]
        if row["SingletonPresent"] == 1:
            element += 10
        sequence1.append(element)
    sequence2 = list()
    for i, row in df2.iterrows():
        element = row["Priming"]
        if row["SingletonPresent"] == 1:
            element += 10
        sequence2.append(element)

    total_distance = distance(sequence1, sequence2)
    # compare randomness
    pool = [-1, 0, 1, 9, 10, 11]
    random_sequence1 = list()
    random_sequence2 = list()
    for trial in range(225):
        random_sequence1.append(random.choice(pool))
        random_sequence2.append(random.choice(pool))
    total_random_distance = distance(random_sequence1, random_sequence2)

    print(f"Total distance: {total_distance/len(sequence1)}% \n"
          f"Total distance of a completely random sequence: {total_random_distance/len(random_sequence1)}%")
