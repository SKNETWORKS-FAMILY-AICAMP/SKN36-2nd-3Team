import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

import enum
from tqdm.auto import tqdm

from xgboost import XGBClassifier
from xgboost import plot_importance as xgb_plot_importance
from lightgbm import LGBMClassifier
from lightgbm import plot_importance as lgb_plot_importance
from catboost import CatBoostClassifier

from .utils import reset_seeds
from .evaluations import get_auc_score

def cat_plot_importance(cat):
    feature_importance = cat.feature_importances_
    feature_names = np.array(cat.feature_names_)
    sorted_idx = np.argsort(feature_importance)

    plt.figure(figsize=(12, 6))
    plt.barh(
        range(len(sorted_idx)),
        feature_importance[sorted_idx]
    )
    plt.yticks(
        range(len(sorted_idx)),
        feature_names[sorted_idx]
    )
    plt.title("Feature Importance")
    plt.xlabel("Importance")
    plt.show()


class BoostModelType(enum.Enum):
    xgb = (
        enum.auto(), XGBClassifier,
        {
            "tree_method": "hist",
            "enable_categorical": True,
            "random_state": 42,
        },
        xgb_plot_importance
    )
    lgb = (
        enum.auto(), LGBMClassifier,
        {
            "verbose": -1,
            "random_state": 42,
        },
        lgb_plot_importance,
    )
    cat = (
        enum.auto(), CatBoostClassifier,
        {
            "verbose": 0,
            "random_seed": 42,
        },
        cat_plot_importance,
    )

    @classmethod
    def show_plot_importance(cls, model):
        for model_type in BoostModelType:
            if isinstance(model, model_type.value[1]):
                model_type.value[3](model)
                plt.show()



class Modeling:
    def __init__(
        self, x_tr:pd.DataFrame, y_tr:pd.DataFrame, 
        cat_cols:list, vali_func=get_auc_score, use_proba:bool=True
    ) -> None:
        self.__features = x_tr.copy()
        self.__targets = y_tr
        self.__valid_features_targets()

        self.__cat_cols = cat_cols
        self.__cat_levels = {}          # 범주형 컬럼별 train의 카테고리 목록
        self.__convert_dtype(self.__features, fit=True)
        
        self.__best_model = {
            "model": None,
            'model_name': None,
            'hpo': None,
            'train_score': 0.0,
            'test_score': 0.0,
            'score_type': None
        }
        self.__vali_func = vali_func
        self.__use_proba = use_proba    # True: 확률값으로 평가 (AUC), False: 클래스 예측값으로 평가 (F1 등)


    def __convert_dtype(self, features, fit=False):
        # bool -> int8, 범주형 컬럼 -> category (train의 카테고리 기준, 처음 보는 값은 'unknown')
        bool_cols = features.select_dtypes(include=["bool", "boolean"]).columns
        features[bool_cols] = features[bool_cols].astype("int8")

        for col in self.__cat_cols:
            values = features[col].astype(str)

            if fit:
                levels = values.unique().tolist()
                if "unknown" not in levels:
                    levels.append("unknown")
                self.__cat_levels[col] = levels
            else:
                levels = self.__cat_levels[col]
                values = values.where(values.isin(levels), "unknown")

            features[col] = pd.Categorical(values, categories=levels)

    def __valid_features_targets(self, x_te:pd.DataFrame=None, y_te:pd.DataFrame=None) -> None:
        assert self.__features.isnull().sum().sum() == 0, "[학습용] features에 결측치가 있습니다."
        assert len(self.__features) == len(self.__targets), "[학습용] features와 targets의 데이터 수가 다릅니다."

        if x_te is not None and y_te is not None:
            assert x_te.isnull().sum().sum() == 0, "[평가용] features에 결측치가 있습니다."
            assert len(x_te) == len(y_te), "[평가용] features와 targets의 데이터 수가 다릅니다."
            assert list(self.__features.columns) == list(x_te.columns), "[평가용] features의 컬럼명 또는 순서가 학습용과 다릅니다."



    def get_best_model(self):
        return self.__best_model

    def __fit(self, model_type:BoostModelType, add_hpo:dict):

        # 하이퍼 파라미터 정의 (모델별 기본값 + add_hpo에서 해당 모델의 추가값)
        hpo = model_type.value[2] | add_hpo.get(model_type.name, {})
        if model_type is BoostModelType.cat:
            hpo = hpo | {'cat_features': self.__cat_cols}

        # 모델 생성 
        model = model_type.value[1](**hpo)

        # 모델 학습 
        model.fit(self.__features, self.__targets) 

        return model, hpo 

    def __predict_for_score(self, model, features):
        # 점수 계산용 예측값
        if self.__use_proba:
            return model.predict_proba(features)[:, 1]
        return model.predict(features)

    def __evaluation(self, model, hpo, y_te, x_te):
        # 모델 평가 
        test_score = self.__vali_func(
            y=y_te, pred=self.__predict_for_score(model, x_te)
        )

        if self.__best_model['test_score'] < test_score:
            self.__best_model = {
                'model':model,
                'model_name': model.__class__.__name__,
                'hpo': hpo,
                'train_score': self.__vali_func(
                    y=self.__targets, pred=self.__predict_for_score(model, self.__features)
                ),
                'test_score': test_score,
                'score_type': self.__vali_func.__name__
            }


    @reset_seeds()
    def fit_evaluation(
        self, y_te:pd.DataFrame, x_te:pd.DataFrame, add_hpo:dict=None) -> None:
        """ add_hpo 예시: {'xgb': {'max_depth': 6}, 'lgb': {'num_leaves': 31}, 'cat': {'depth': 6}} """
        
        self.__valid_features_targets(x_te, y_te)
        x_te = x_te.copy()
        self.__convert_dtype(x_te)

        add_hpo = add_hpo or {}

        for model_type in tqdm(
            BoostModelType, desc="training.."):

            model, hpo = self.__fit(model_type, add_hpo)
            self.__evaluation(model, hpo, y_te, x_te)
        
    def predict_by_best_model(self, features:pd.DataFrame):
        features = features[self.__features.columns].copy()   # 학습 때와 같은 컬럼 순서로 맞춤
        self.__convert_dtype(features)

        return self.__best_model['model'].predict(features)