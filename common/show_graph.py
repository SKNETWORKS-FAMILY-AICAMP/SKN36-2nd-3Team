import numpy as np
import pandas as pd
import seaborn as sns

def show_corr_map(
    X_train:pd.DataFrame, Y_train:pd.DataFrame,
    drop_columns:list=None
):
    features = X_train.copy()
    if drop_columns:
        features.drop(columns=drop_columns, inplace=True)
    
    df = pd.concat([Y_train, features], axis=1)

    for col in df.select_dtypes(exclude=np.number).columns:
        df[col] = pd.factorize(df[col])[0]

    sns.heatmap(
        df.corr(),
        annot=True,
        vmin=-1, vmax=1,
        linewidths=0.2,
        cmap='coolwarm'
    )