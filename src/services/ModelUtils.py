from sklearn.base import BaseEstimator, TransformerMixin

class TargetEncoder(BaseEstimator, TransformerMixin):
    def __init__(self, cols):
        self.cols = cols
        self.mapping = {}
        self.global_mean = None

    def fit(self, X, y):
        self.global_mean = y.mean()
        df = X.copy()
        df['target'] = y

        for col in self.cols:
            self.mapping[col] = df.groupby(col)['target'].mean()

        return self

    def transform(self, X):
        X = X.copy()

        for col in self.cols:
            X[col] = X[col].map(self.mapping[col])
            X[col] = X[col].fillna(self.global_mean)

        return X

def encode_gender(X):
    X = X.copy()
    X['gender'] = X['gender'].map({'M': 0, 'F': 1})
    return X
