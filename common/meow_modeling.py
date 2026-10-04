import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from catboost import CatBoostClassifier

from sklearn.metrics import accuracy_score, roc_auc_score, average_precision_score, f1_score, recall_score, precision_score
from sklearn.model_selection import StratifiedKFold

from .utils import reset_seeds


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
        cat_cols:list=None, cat_hp:dict={}
    ) -> None:
        self.__features = x_tr.copy()
        self.__target = y_tr
        self.__valid_features_targets()

        self.__cat_hp = cat_hp
        self.__cat_cols = cat_cols
        if cat_cols is None:
            self.__cat_cols = x_tr.select_dtypes(
                exclude=[np.number, "bool", "boolean"]
            ).columns.tolist()
        self.__convert_dtype(self.__features)

        self.__meow_model = None
        self.__test_pred = None
        self.__test_proba = None
    

    def __valid_features_targets(
        self, x_te:pd.DataFrame = None, y_te:pd.DataFrame = None
    ) -> None:
        train_str = self.__features.select_dtypes(exclude=np.number)
        assert train_str.isnull().sum().sum() == 0, "[학습용] 수치를 제외한 features에 결측치가 있습니다."
        assert len(self.__features) == len(self.__target), "[학습용] features와 targets의 데이터 수가 다릅니다."

        if x_te is not None and y_te is not None:
            test_str = x_te.select_dtypes(exclude=np.number)
            assert test_str.isnull().sum().sum() == 0, "[평가용] 수치를 제외한 features에 결측치가 있습니다."
            assert len(x_te) == len(y_te), "[평가용] features와 targets의 데이터 수가 다릅니다."
            assert list(self.__features.columns) == list(x_te.columns), "[평가용] features의 컬럼명 또는 순서가 학습용과 다릅니다."

    def __convert_dtype(self, features):
        # bool -> int8, 범주형 컬럼 -> category
        bool_cols = features.select_dtypes(include=["bool", "boolean"]).columns
        features[bool_cols] = features[bool_cols].astype("int8")

        for col in self.__cat_cols:
            features[col] = features[col].astype("category")


    def __make_meow_model(self):
        return CatBoostClassifier(
            random_seed=42,                 # 시드 고정
            verbose=0,                      # 부스팅 단계 출력 안보이게 하기
            cat_features=self.__cat_cols,   # 범주형 데이터 알려주기
            allow_writing_files=False,      # 학습 내용 파일로 저장 금지
            **self.__cat_hp
        )
    
    def run_strat_kfold(self, n_splits:int=5) -> None:
        # 교차 검증 (타겟 클래스 비율을 맞춰 KFold하는 CV)
        skf = StratifiedKFold(n_splits, shuffle=True, random_state=42)

        CV_scores = []

        for fold, (tr_idx, va_idx) in enumerate(skf.split(self.__features, self.__target), 1):
            # skf가 분리해준대로 train과 val 생성
            X_tr, X_va = self.__features.iloc[tr_idx], self.__features.iloc[va_idx]
            Y_tr, Y_va = self.__target.iloc[tr_idx], self.__target.iloc[va_idx]

            # 모델 학습
            model = self.__make_meow_model()
            model.fit(X_tr, Y_tr)

            # 평가
            proba = model.predict_proba(X_va)[:, 1]
            pred = (proba >= 0.5).astype(int)
            scores = {
                "ROC-AUC": roc_auc_score(Y_va, proba),
                "PR-AUC": average_precision_score(Y_va, proba),
                "F1": f1_score(Y_va, pred),
                "Recall": recall_score(Y_va, pred),
                "Precision": precision_score(Y_va, pred)
            }
            CV_scores.append(scores)
            print(f"{fold}번째 Stratified K-Fold: " + ", ".join(
                f"{name}={score:.5f}" for name, score in scores.items()
            ))

        cv_scores = pd.DataFrame(CV_scores)
        print('-'*50)
        print("5-Fold 평균\n", cv_scores.mean().round(5))
        print("5-Fold 표준편차\n", cv_scores.std().round(5))


    def __fit(self):
        # train 데이터 학습
        self.__meow_model = self.__make_meow_model()
        self.__meow_model.fit(self.__features, self.__target)
        # 예측 데이터 반환
        return self.__meow_model.predict(self.__features).astype(int)

    @reset_seeds()
    def fit_evaluation(self, X_test:pd.DataFrame, Y_test:pd.DataFrame) -> None:
        # train 데이터 평가
        train_pred = self.__fit()
        print(f"Train Accuracy : {accuracy_score(self.__target, train_pred):.5f}")

        # test 데이터 평가
        self.__test_pred = self.__meow_model.predict(X_test).astype(int)
        self.__test_proba = self.__meow_model.predict_proba(X_test)[:, 1]

        accuracy = accuracy_score(Y_test, self.__test_pred)
        precision = precision_score(Y_test, self.__test_pred)
        recall = recall_score(Y_test, self.__test_pred)
        f1 = f1_score(Y_test, self.__test_pred)
        roc_auc = roc_auc_score(Y_test, self.__test_proba)
        pr_auc = average_precision_score(Y_test, self.__test_proba)

        overall_score = np.mean([precision, recall, f1, roc_auc, pr_auc])


        print(f"Valid Accuracy : {accuracy:.5f}")
        print(f"Precision      : {precision:.5f}")
        print(f"Recall         : {recall:.5f}")
        print(f"F1-score       : {f1:.5f}")
        print(f"ROC-AUC        : {roc_auc:.5f}")
        print(f"PR-AUC         : {pr_auc:.5f}")
        print(f"Overall Score  : {overall_score:.5f}")


    def get_model(self) -> CatBoostClassifier:
        return self.__meow_model

    def get_test_pred_proba(self) -> tuple:
        return self.__test_pred, self.__test_proba