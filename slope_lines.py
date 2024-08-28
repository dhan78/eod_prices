import pandas as pd
import numpy as np

purchases_df = pd.DataFrame({"user_id": [100, 101, 100, 101, 200],
                             "date": ['2022-01-01', '2022-01-01','2022-01-01','2022-01-01', '2022-01-01'],
                             "purchase": ['cookies', 'jam', 'jam', 'jam', np.nan]})

purchases_df.groupby(['date','user_id']).agg(lambda x: x.mode().max())

agg_mode = purchases_df.groupby(['date', 'user_id'])['purchase'].agg(lambda x: x.mode().tolist())
