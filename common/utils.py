import os
import numpy as np
import random

from functools import wraps


def reset_seeds(seed=42):
    """ Python random / NumPy RNG를 함수 호출 직전에 초기화한다.
    - XGBoost / LightGBM / CatBoost의 seed는 각 모델 생성자에도 명시해야 한다.
    """
    def decorator(func):        # 데코레이션 대상 함수 받기
        @wraps(func)
        def wrapper_func(*args, **kwargs):  # 함수 실행 시 인자 받기
            random.seed(seed)
            os.environ["PYTHONHASHSEED"] = str(seed)
            np.random.seed(seed)
            return func(*args, **kwargs)

        return wrapper_func
    return decorator
