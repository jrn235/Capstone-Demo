import pandas as pd
import pymongo
import seaborn as sns
from constring import *
import numpy as np

client = pymongo.MongoClient(con_string)

# number of observations per object
ast = client.ztf.asteroids
total = ast.find({}, {"observationCounts":1})
df_obs = pd.DataFrame(total)

hist = sns.histplot(x='observationCounts', data = df_obs, bins = 100, log_scale=(False, True))
hist.set_xlabel("Number of Observations")
hist.set_ylabel("Number of Objects")
sns.set(rc = {"figure.figsize": (5, 11)})
fig = hist.get_figure()
fig.savefig("obs_hist.png", dpi = 300)
fig.clf()



# LC rotation period solutions: lcper
lc = client.ztf["Light Curve Objects"]
lcrot = lc.find({}, {"lcper":1})
df_rot = pd.DataFrame(lcrot)

hist_lc = sns.histplot(x='lcper', data = df_rot, bins = 100, log_scale=(False, True))
hist_lc.set_xlabel("Light Curve Rotation Periods")
hist_lc.set_ylabel("Number of Objects")
fig = hist_lc.get_figure()
fig.savefig("lc_hist.png", dpi = 300)
fig.clf()



# LC amplitudes for each object: lcamp
lcamp = lc.find({}, {"lcamp":1})
df_amp = pd.DataFrame(lcamp)

hist_lcamp = sns.histplot(x='lcamp', data = df_amp, bins = 100)
hist_lcamp.set_xlabel("Light Curve Amplitude")
hist_lcamp.set_ylabel("Number of Objects")
fig = hist_lcamp.get_figure()
fig.savefig("lcamp_hist.png", dpi = 300)
fig.clf()



# asteroid color distribution: grColor
gr_color = lc.find({}, {"grColor": 1})
df_gr = pd.DataFrame(gr_color)

gr_color_hist = sns.histplot(x = "grColor", data = df_gr, bins = 200)
gr_color_hist.set_xlabel("g-r Color")
gr_color_hist.set_ylabel("Number of Objects")
fig = gr_color_hist.get_figure()
fig.savefig("grColor_hist.png", dpi = 300)
fig.clf()
