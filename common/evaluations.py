from sklearn.metrics import roc_auc_score, f1_score, roc_curve, auc
from sklearn.model_selection import StratifiedKFold

from .preprocessing import smotenc_sampling

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .meow_modeling import MeowModeling


def run_strat_kfold(
    skf:StratifiedKFold,
    model:"MeowModeling",
    use_smotenc:bool=False,
    sampling_strategy:str="auto",
    k_neighbors:int=5
) -> list:
    AUC_scores = []
    X_data, Y_data = model.features, model.target
    cat_cols = model.cat_cols

    for fold, (tr_idx, va_idx) in enumerate(skf.split(X_data, Y_data), 1):
        # skf가 분리해준대로 train과 val 생성
        X_tr, X_va = X_data.iloc[tr_idx], X_data.iloc[va_idx]
        Y_tr, Y_va = Y_data.iloc[tr_idx], Y_data.iloc[va_idx]

        # Smote-NC
        if use_smotenc:
            X_tr, Y_tr = smotenc_sampling(
                X_tr, Y_tr, cat_cols,
                sampling_strategy=sampling_strategy,
                k_neighbors=k_neighbors
            )
        
        fold_model = model.make_model()  # fold마다 새 모델 생성
        fold_model.fit(X_tr, Y_tr)       # 학습

        pred = fold_model.predict_proba(X_va)[:, 1]  # 예측
        auc_score = roc_auc_score(Y_va, pred)   # ROC-AUC 로 평가
        AUC_scores.append(auc_score)            # AUC_scores에 추가
        print(f"{fold}번째 Stratified K-Fold의 AUC 점수: {auc_score}")  # 점수 반환

    return AUC_scores


def get_auc_score(y, pred):
    fpr, tpr, _ = roc_curve(y, pred)
    return auc(fpr, tpr)


def get_f1_score(y, pred, average='weighted'):
    return f1_score(y, pred, average=average)
