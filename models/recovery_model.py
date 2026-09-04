import os
import sys

import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)


# --------------------------------------------------
# PROJECT PATH
# --------------------------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

transactions_path = os.path.join(
    PROJECT_ROOT,
    "data",
    "transactions.csv"
)

transactions = pd.read_csv(transactions_path)


# --------------------------------------------------
# FILTER FAILED TRANSACTIONS
# --------------------------------------------------

failed_transactions = transactions[
    transactions["status"] == "FAILED"
].copy()


# --------------------------------------------------
# FEATURES
# --------------------------------------------------

FEATURES = [
    "amount",
    "payment_method",
    "failure_reason",
    "retry_count",
    "subscription",
]

TARGET = "recovery_outcome"


X = failed_transactions[FEATURES]

y = failed_transactions[TARGET].astype(int)


# --------------------------------------------------
# TRAIN / TEST SPLIT
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)


# --------------------------------------------------
# PREPROCESSING
# --------------------------------------------------

numeric_features = [
    "amount",
    "retry_count",
]

categorical_features = [
    "payment_method",
    "failure_reason",
    "subscription",
]


preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            StandardScaler(),
            numeric_features,
        ),
        (
            "categorical",
            OneHotEncoder(
                handle_unknown="ignore"
            ),
            categorical_features,
        ),
    ]
)


# --------------------------------------------------
# MODEL
# --------------------------------------------------

model = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor
        ),
        (
            "classifier",
            LogisticRegression(
                random_state=42,
                max_iter=1000,
            )
        ),
    ]
)


# --------------------------------------------------
# TRAIN MODEL
# --------------------------------------------------

model.fit(
    X_train,
    y_train
)


# --------------------------------------------------
# PREDICTION FUNCTION
# --------------------------------------------------

def predict_recovery_probability(transaction):
    """
    Predict the probability that a failed transaction
    can be successfully recovered.

    Parameters
    ----------
    transaction : dict
        Transaction information.

    Returns
    -------
    float
        Recovery probability between 0 and 1.
    """

    input_data = pd.DataFrame(
        [
            {
                "amount": transaction["amount"],
                "payment_method": transaction["payment_method"],
                "failure_reason": transaction["failure_reason"],
                "retry_count": transaction["retry_count"],
                "subscription": transaction["subscription"],
            }
        ]
    )

    probability = model.predict_proba(
        input_data
    )[0][1]

    return probability


# --------------------------------------------------
# MODEL EVALUATION
# --------------------------------------------------

def evaluate_model():
    """
    Evaluate the trained model on the test dataset.
    """

    y_pred = model.predict(X_test)

    y_probability = model.predict_proba(
        X_test
    )[:, 1]

    accuracy = accuracy_score(
        y_test,
        y_pred
    )

    precision = precision_score(
        y_test,
        y_pred
    )

    recall = recall_score(
        y_test,
        y_pred
    )

    f1 = f1_score(
        y_test,
        y_pred
    )

    roc_auc = roc_auc_score(
        y_test,
        y_probability
    )

    matrix = confusion_matrix(
        y_test,
        y_pred
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": roc_auc,
        "confusion_matrix": matrix,
    }


# --------------------------------------------------
# DEMO
# --------------------------------------------------

def run_model_demo():

    metrics = evaluate_model()

    print("\n" + "=" * 50)
    print("REVIVEAI RECOVERY PREDICTION MODEL")
    print("=" * 50)

    print(
        f"\nTraining samples : {len(X_train)}"
    )

    print(
        f"Testing samples  : {len(X_test)}"
    )

    print("\nModel Performance")
    print("-" * 30)

    print(
        f"Accuracy  : {metrics['accuracy']:.4f}"
    )

    print(
        f"Precision : {metrics['precision']:.4f}"
    )

    print(
        f"Recall    : {metrics['recall']:.4f}"
    )

    print(
        f"F1 Score  : {metrics['f1']:.4f}"
    )

    print(
        f"ROC-AUC   : {metrics['roc_auc']:.4f}"
    )

    print("\nConfusion Matrix")

    print(
        metrics["confusion_matrix"]
    )

    # --------------------------------------------------
    # SAMPLE TRANSACTION
    # --------------------------------------------------

    sample_transaction = {
        "transaction_id": "SAMPLE_TXN",
        "amount": 2500,
        "payment_method": "UPI",
        "failure_reason": "NETWORK_ERROR",
        "retry_count": 0,
        "subscription": False,
        "status": "FAILED",
    }

    probability = predict_recovery_probability(
        sample_transaction
    )

    print("\nSample Transaction")
    print("-" * 30)

    print(
        "Recovery Probability:",
        f"{probability:.2%}"
    )

    print("=" * 50)


# --------------------------------------------------
# RUN ONLY WHEN FILE IS EXECUTED DIRECTLY
# --------------------------------------------------

if __name__ == "__main__":
    run_model_demo()