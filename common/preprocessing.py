import numpy as np
import pandas as pd
from pandas import DataFrame as DF, Series

from imblearn.over_sampling import SMOTENC
from sklearn.model_selection import train_test_split

from .utils import reset_seeds


@reset_seeds()
def train_test_split_by_target(
    df:DF, target_name:str,
    test_size:float=0.25, split_target:bool=True
) -> tuple:
    """ Return (default)

    **train_features, test_features, train_target, test_target**

    If split_target is set to False :

    **train, test**
    """
    features = df.drop(columns=target_name)
    target = df[target_name]

    if split_target:
        return train_test_split(
            features, target,
            test_size=test_size,
            stratify=target
        )
    
    return train_test_split(
        df,
        test_size=test_size,
        stratify=target
    )


def soft_cleansing(
    train:DF, test:DF,
    fill_in_num:Series|int|float|None=None, fill_in_str:Series|str="unknown"
) -> tuple:
    """fill_in_num : 수치형 결측치를 채울 값 (기본 : median)

    fill_in_str : 범주형 결측치를 채울 값 (기본 : "unknown")

    **Return**
    - cleansed_train, cleansed_test
    """
    cleansed_train = train.copy()
    cleansed_test = test.copy()
    num_cols = train.select_dtypes(include=np.number).columns
    str_cols = train.select_dtypes(exclude=np.number).columns

    if fill_in_num is None:
        fill_in_num = cleansed_train[num_cols].median()

    
    print(f"수정 전 train: {cleansed_train.isnull().sum().sum()}, "
        f"test: {cleansed_test.isnull().sum().sum()}")

    for df_tmp in [cleansed_train, cleansed_test]:
        df_tmp[num_cols] = df_tmp[num_cols].fillna(fill_in_num)
        df_tmp[str_cols] = df_tmp[str_cols].fillna(fill_in_str)

    print(f"수정 후 train: {cleansed_train.isnull().sum().sum()}, "
        f"test: {cleansed_test.isnull().sum().sum()}")

    return cleansed_train, cleansed_test


# Smote는 범주형 데이터를 처리하지 못해서, One-Hot-Encoding 등을 해야함
# Smote-NC 는 범주형 데이터도 같이 처리해줌
@reset_seeds()
def smotenc_sampling(
    features:DF, target:DF, cat_features:list,
    sampling_strategy:str="auto",  # 샘플링 균형도
    k_neighbors:int=5           # 이웃 섞는 정도
) -> tuple:
    features = features.copy()
    for col in cat_features:
        features[col] = features[col].astype("category")  # category형으로 변환

    sampler = SMOTENC(
        categorical_features=cat_features,
        sampling_strategy=sampling_strategy,
        k_neighbors=k_neighbors
    )
    features_samp, target_samp = sampler.fit_resample(features, target)     # Smote-NC 적용

    # CatBoost categorical 입력은 문자열로 통일
    for col in cat_features:
        features_samp[col] = features_samp[col].astype(str)

    return features_samp, target_samp