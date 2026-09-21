from sklearn.metrics import f1_score, roc_curve, auc


def get_auc_score(y, pred):
    fpr, tpr, _ = roc_curve(y, pred)
    return auc(fpr, tpr)


def get_f1_score(y, pred, average='weighted'):
    return f1_score(y, pred, average=average)
