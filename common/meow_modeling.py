import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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


class MeowModeling:
    def __init__(
        self, x_tr: pd.DataFrame, y_tr: pd.DataFrame,
        cat_cols:list=None, vali_func=get_auc_score, use_proba:bool=True
    ) -> None:
        self.__features = x_tr.copy()
        self.__targets = y_tr
        self.__valid_features_targets()

        self.__cat_cols = cat_cols
        if cat_cols is None:
            self.__cat_cols = x_tr.select_dtypes(exclude=np.number).columns.tolist()

        self.__convert_dtype(self.__features)

        self.__model = None
        self.__model_info = None

        self.__vali_func = vali_func
        self.__use_proba = use_proba  # True: 확률값으로 평가 (AUC), False: 클래스 예측값으로 평가 (F1 등)

    def __convert_dtype(self, features):
        # bool -> int8, 범주형 컬럼 -> category
        bool_cols = features.select_dtypes(
            include=["bool", "boolean"]
        ).columns
        features[bool_cols] = features[bool_cols].astype("int8")

        for col in self.__cat_cols:
            features[col] = features[col].astype("category")

    def __valid_features_targets(
        self, x_te: pd.DataFrame = None, y_te: pd.DataFrame = None
    ) -> None:
        assert self.__features.isnull().sum().sum() == 0, "[학습용] features에 결측치가 있습니다."
        assert len(self.__features) == len(self.__targets), "[학습용] features와 targets의 데이터 수가 다릅니다."

        if x_te is not None and y_te is not None:
            assert x_te.isnull().sum().sum() == 0, "[평가용] features에 결측치가 있습니다."
            assert len(x_te) == len(y_te), "[평가용] features와 targets의 데이터 수가 다릅니다."
            assert list(self.__features.columns) == list(x_te.columns), "[평가용] features의 컬럼명 또는 순서가 학습용과 다릅니다."

    def get_model_info(self):
        return self.__model_info

    def __fit(self, add_hpo: dict):
        # CatBoost 기본 하이퍼파라미터 + 추가 하이퍼파라미터
        hpo = {
            "verbose": 0,
            "random_seed": 42,
        } | add_hpo

        hpo["cat_features"] = self.__cat_cols

        # 모델 생성 및 학습
        self.__model = CatBoostClassifier(**hpo)
        self.__model.fit(self.__features, self.__targets)

        return hpo

    def __predict_for_score(self, features):
        # 점수 계산용 예측값
        if self.__use_proba:
            return self.__model.predict_proba(features)[:, 1]

        return self.__model.predict(features)

    def __evaluation(self, hpo, y_te, x_te):
        # 모델 평가
        test_score = self.__vali_func(
            y=y_te,
            pred=self.__predict_for_score(x_te)
        )

        self.__model_info = {
            "model": self.__model,
            "model_name": self.__model.__class__.__name__,
            "hpo": hpo,
            "train_score": self.__vali_func(
                y=self.__targets,
                pred=self.__predict_for_score(self.__features)
            ),
            "test_score": test_score,
            "score_type": self.__vali_func.__name__
        }


    def make_meow_model(self, add_hp:dict={}):
        return CatBoostClassifier(
            random_seed=42,                 # 시드 고정
            verbose=0,                      # 부스팅 단계 출력 안보이게 하기
            cat_features=self.__cat_cols,   # 범주형 데이터 알려주기
            allow_writing_files=False,      # 학습 내용 파일로 저장 금지
            **add_hp
        )
    

    @reset_seeds()
    def fit_evaluation(
        self, y_te: pd.DataFrame, x_te: pd.DataFrame,
        add_hpo: dict = None
    ) -> None:
        """add_hpo 예시: {"depth": 6, "learning_rate": 0.05}"""

        self.__valid_features_targets(x_te, y_te)

        x_te = x_te.copy()
        self.__convert_dtype(x_te)

        add_hpo = add_hpo or {}

        hpo = self.__fit(add_hpo)
        self.__evaluation(hpo, y_te, x_te)

    def predict_by_model(self, features: pd.DataFrame):
        features = features[self.__features.columns].copy()
        self.__convert_dtype(features)

        return self.__model.predict(features)