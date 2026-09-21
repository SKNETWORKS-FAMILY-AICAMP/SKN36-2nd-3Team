import numpy as np
import pandas as pd

import shap


class ShapAnalyzer:
    def __init__(self, X_test:pd.DataFrame, model):
        self.X_test = X_test.copy()
        self.model = model

        # 학습된 모델을 넣는다.
        explainer = shap.TreeExplainer(model)
        # 학습된 모델을 갖고 X_test를 분석
        shap_values = explainer.shap_values(X_test)
        if isinstance(shap_values, list):
            shap_values = shap_values[-1]
        
        self.shap_values = np.asarray(shap_values)


    def show_summary(self, show_type:str="all", plot_bar:bool=False) -> None:
        """show_type list : ['all', 'num', 'str']"""
        if plot_bar:
            shap.summary_plot(self.shap_values, self.X_test, plot_type="bar")
        else:
            if show_type == "all":
                selected_features = self.X_test.columns.tolist()
            elif show_type == "num":
                selected_features = self.X_test.select_dtypes(
                    include=[np.number, "bool", "boolean"]
                ).columns.tolist()
            elif show_type == "str":
                selected_features = self.X_test.select_dtypes(
                    exclude=[np.number, "bool", "boolean"]
                ).columns.tolist()
            else:
                print("잘못된 show_type 입니다.")
                print("show_type list : ['all', 'num', 'str']")
                return

            # 해당 feature의 위치
            selected_idx = [self.X_test.columns.get_loc(col) for col in selected_features]

            # 원하는 feature만 SHAP plot
            shap.summary_plot(
                self.shap_values[:, selected_idx],
                self.X_test[selected_features]
            )


    def get_mean_abs(self, head_num:int=20) -> pd.DataFrame:
        shap_rank = pd.DataFrame({
            'feature':self.X_test.columns,
            'mean_abs_shap':np.abs(self.shap_values).mean(axis=0)
        }).sort_values('mean_abs_shap', ascending=False)

        return shap_rank.head(head_num)
