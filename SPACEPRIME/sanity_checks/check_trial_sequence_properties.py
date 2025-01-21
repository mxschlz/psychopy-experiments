import pandas as pd


dfs = [pd.read_csv(f"C:\\Users\Max\PycharmProjects\psychopy-experiments\SPACEPRIME\sequences\sub-999_block_{block}.csv") for block in range(10)]
df = pd.concat(dfs)

# check proportions of c, np and pp trials
nr_c = []
nr_pp = []
nr_np = []
# check proportion of singleton present trials
nr_sp = []
