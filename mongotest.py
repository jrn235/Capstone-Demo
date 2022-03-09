import pandas as pd
import pymongo
from constring import *

constring = con_string

client = pymongo.MongoClient(constring)
ztf = client.ztf.ztf

scatter_mong = ztf.find( {}, {"jd": 1, "H": 1} )

df = pd.DataFrame(scatter_mong)

print(df)
