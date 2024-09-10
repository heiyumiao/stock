import pandas as pd

# data = pd.read_pickle(r'D:\something\finance\stock\instock\cache\hist\201308\20130826\000002qfq.gzip.pickle', compression='gzip')
# data = pd.read_pickle(r'D:\something\finance\stock\instock\cache\hist\202408\20240830\000002qfq.gzip.pickle', compression='gzip')
# data = pd.read_pickle(r'D:\something\finance\stock\instock\cache\etf_hist\202409\159533qfq.gzip.pickle', compression='gzip')
data = pd.read_pickle(r'D:\something\finance\stock\instock\cache\hist_stock\daily\300287qfq.gzip.pickle', compression='gzip')

data.to_csv('data.csv',index=False)