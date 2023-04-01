import pycaret
from pycaret.regression import *
from pycaret.datasets import get_data
import os
import imgkit
import pandas as pd
# data_set = get_data('diamond')


def save_test(df, target, name):
    print('test')
    exp = setup(df, target=target, silent=True)
    best_model = compare_models()
    pd.set_option('display.max_columns', 100)
    df = pd.DataFrame(pull(best_model))
    print(df)
    save_model(best_model, model_name=name)


def load_test(df):
    load_tuned_model = load_model(model_name='test_model')
    # print(load_tuned_model)
    predictions = predict_model(load_tuned_model, data=df)
    print(predictions)


def tune_test():
    print('start tuning')
    exp = setup(df, target=target, silent=True)
    model = load_model(model_name='test_model')
    evaluate_model(model)