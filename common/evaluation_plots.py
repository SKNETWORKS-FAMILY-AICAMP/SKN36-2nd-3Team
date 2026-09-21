import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import confusion_matrix, RocCurveDisplay, PrecisionRecallDisplay
from sklearn.dummy import DummyClassifier


def show_norm_conf_mx(y, pred):
    norm_conf_mx = confusion_matrix(y, pred, normalize="true")

    plt.figure(figsize=(7,5))
    sns.heatmap(norm_conf_mx, annot=True, cmap="coolwarm", linewidth=0.5)
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.show()


def show_roc_curve(X_train, Y_train, X_test, Y_test, test_proba):
    # Dummy 모델
    dummy = DummyClassifier(strategy='most_frequent')
    dummy.fit(X_train, Y_train)
    pred_dummy = dummy.predict_proba(X_test)[:, 1]

    fig, ax = plt.subplots(figsize=(5, 5))
    RocCurveDisplay.from_predictions(Y_test, test_proba, name='CatBoost',ax=ax)
    RocCurveDisplay.from_predictions(Y_test, pred_dummy, name='dummy', ax=ax)
    plt.title("Validation ROC Curve")
    plt.show()

def show_pr_curve(Y_test, test_proba):
    fig, ax = plt.subplots(figsize=(5, 5))
    PrecisionRecallDisplay.from_predictions(Y_test, test_proba, name="CatBoost", ax=ax)
    plt.title("Validation PR Curve")
    plt.show()
