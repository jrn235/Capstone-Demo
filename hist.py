import pymongo
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import rcParams
import time

constring = "mongodb://mjl79:NxMswiyz0oGQ4kT2XdqM@cmp4818.computers.nau.edu:27017/?authSource=admin"

start = time.time()
client = pymongo.MongoClient(constring)

ztf_pym = client.ztf.ztf

start = time.time()
ssnamenr_obs = ztf_pym.aggregate([
    {"$group": {"_id": "$ssnamenr", "observations": {"$sum": 1}}}
])

df = pd.DataFrame(ssnamenr_obs).sort_values("observations")

print(df)

df = df[-1000:]

hist = sns.barplot(x='_id', y="observations", data = df, order = df["_id"])
hist.set_xticklabels([])
sns.set(rc = {"figure.figsize": (5, 11)})
fig = hist.get_figure()
fig.savefig("hist.png", dpi = 300)
end = time.time()
print(f'{end - start}')