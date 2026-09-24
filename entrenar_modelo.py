"""Reproduce el pipeline del notebook PA1 y guarda random_forest_titanic.pkl"""
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

URL = "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv"


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    d = df.drop(columns=["PassengerId", "Name", "Ticket", "Cabin"])
    d["Age"] = d.groupby(["Pclass", "Sex"])["Age"].transform(lambda s: s.fillna(s.median()))
    d["Embarked"] = d["Embarked"].fillna(d["Embarked"].mode()[0])
    d["FamilySize"] = d["SibSp"] + d["Parch"] + 1
    d["IsAlone"] = (d["FamilySize"] == 1).astype(int)
    d["Sex"] = d["Sex"].map({"male": 0, "female": 1})
    return pd.get_dummies(d, columns=["Embarked"], prefix="Emb", drop_first=True, dtype=int)


def entrenar(df: pd.DataFrame):
    d = preparar(df)
    X, y = d.drop("Survived", axis=1), d["Survived"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)
    model.fit(X_train, y_train)
    return model, X_train, X_test, y_train, y_test


if __name__ == "__main__":
    model, *_ = entrenar(pd.read_csv(URL))
    joblib.dump(model, "random_forest_titanic.pkl")
    print("Modelo guardado:", list(model.feature_names_in_))
