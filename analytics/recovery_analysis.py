import os
import sys

import pandas as pd


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
# FILE PATHS
# --------------------------------------------------

RESULTS_PATH = os.path.join(
    PROJECT_ROOT,
    "data",
    "recovery_results.csv"
)


# --------------------------------------------------
# LOAD RESULTS
# --------------------------------------------------

def load_results():
    """
    Load the recovery audit results.
    """

    if not os.path.exists(RESULTS_PATH):
        raise FileNotFoundError(
            "recovery_results.csv not found. "
            "Run transaction_processor.py first."
        )

    results = pd.read_csv(
        RESULTS_PATH
    )

    return results


# --------------------------------------------------
# BASIC METRICS
# --------------------------------------------------

def calculate_basic_metrics(results):

    transactions_analyzed = len(results)

    revenue_at_risk = results[
        "amount"
    ].sum()

    revenue_recovered = results[
        "recovered_amount"
    ].sum()

    recovery_rate = (
        revenue_recovered / revenue_at_risk
        if revenue_at_risk > 0
        else 0
    )

    successful_recoveries = (
        results["verification_status"]
        == "SUCCESS"
    ).sum()

    return {
        "transactions_analyzed":
            transactions_analyzed,

        "revenue_at_risk":
            revenue_at_risk,

        "revenue_recovered":
            revenue_recovered,

        "recovery_rate":
            recovery_rate,

        "successful_recoveries":
            successful_recoveries,
    }


# --------------------------------------------------
# ACTION ANALYSIS
# --------------------------------------------------

def analyze_actions(results):

    action_summary = (
        results
        .groupby("action")
        .agg(
            transactions=(
                "transaction_id",
                "count"
            ),
            revenue_at_risk=(
                "amount",
                "sum"
            ),
            revenue_recovered=(
                "recovered_amount",
                "sum"
            ),
        )
        .reset_index()
    )

    action_summary["recovery_rate"] = (
        action_summary["revenue_recovered"]
        /
        action_summary["revenue_at_risk"]
    )

    return action_summary


# --------------------------------------------------
# FAILURE REASON ANALYSIS
# --------------------------------------------------

def analyze_failure_reasons(results):

    failure_summary = (
        results
        .groupby("failure_reason")
        .agg(
            transactions=(
                "transaction_id",
                "count"
            ),
            revenue_at_risk=(
                "amount",
                "sum"
            ),
            revenue_recovered=(
                "recovered_amount",
                "sum"
            ),
            successful_recoveries=(
                "recovered_amount",
                lambda x: (x > 0).sum()
            ),
        )
        .reset_index()
    )

    failure_summary["recovery_rate"] = (
        failure_summary["revenue_recovered"]
        /
        failure_summary["revenue_at_risk"]
    )

    return failure_summary.sort_values(
        "revenue_at_risk",
        ascending=False
    )


# --------------------------------------------------
# POLICY ANALYSIS
# --------------------------------------------------

def analyze_policy(results):

    policy_summary = (
        results
        .groupby("policy_status")
        .agg(
            transactions=(
                "transaction_id",
                "count"
            ),
            revenue_at_risk=(
                "amount",
                "sum"
            ),
            revenue_recovered=(
                "recovered_amount",
                "sum"
            ),
        )
        .reset_index()
    )

    policy_summary["recovery_rate"] = (
        policy_summary["revenue_recovered"]
        /
        policy_summary["revenue_at_risk"]
    )

    return policy_summary


# --------------------------------------------------
# FRAUD PROTECTION ANALYSIS
# --------------------------------------------------

def analyze_fraud_protection(results):

    fraud = results[
        results["failure_reason"]
        == "FRAUD_SUSPECTED"
    ]

    blocked = fraud[
        fraud["policy_status"]
        == "BLOCKED"
    ]

    return {
        "fraud_transactions":
            len(fraud),

        "fraud_blocked":
            len(blocked),

        "fraud_recovery_attempts":
            len(fraud) - len(blocked),

        "fraud_recovered":
            fraud["recovered_amount"].sum(),
    }


# --------------------------------------------------
# MODEL DECISION ANALYSIS
# --------------------------------------------------

def analyze_predictions(results):

    # Actual recovery outcome
    actual = (
        results["ground_truth_recovery"]
        .astype(bool)
    )

    # AI's decision to attempt automatic recovery
    predicted_recoverable = results[
        "action"
    ].isin(
        [
            "RETRY_PAYMENT",
            "CREATE_PAYMENT_LINK",
        ]
    )

    true_positive = (
        predicted_recoverable & actual
    ).sum()

    false_positive = (
        predicted_recoverable & ~actual
    ).sum()

    false_negative = (
        ~predicted_recoverable & actual
    ).sum()

    true_negative = (
        ~predicted_recoverable & ~actual
    ).sum()

    precision = (
        true_positive
        /
        (true_positive + false_positive)
        if (true_positive + false_positive) > 0
        else 0
    )

    recall = (
        true_positive
        /
        (true_positive + false_negative)
        if (true_positive + false_negative) > 0
        else 0
    )

    return {
        "true_positive":
            true_positive,

        "false_positive":
            false_positive,

        "false_negative":
            false_negative,

        "true_negative":
            true_negative,

        "precision":
            precision,

        "recall":
            recall,
    }


# --------------------------------------------------
# PRINT BASIC METRICS
# --------------------------------------------------

def print_basic_metrics(metrics):

    print("\n" + "=" * 70)
    print("REVIVEAI ANALYTICS")
    print("=" * 70)

    print("\nOverall Performance")
    print("-" * 30)

    print(
        f"Transactions Analyzed : "
        f"{metrics['transactions_analyzed']}"
    )

    print(
        f"Revenue at Risk       : "
        f"₹{metrics['revenue_at_risk']:,.2f}"
    )

    print(
        f"Revenue Recovered     : "
        f"₹{metrics['revenue_recovered']:,.2f}"
    )

    print(
        f"Recovery Rate         : "
        f"{metrics['recovery_rate']:.2%}"
    )

    print(
        f"Successful Recoveries : "
        f"{metrics['successful_recoveries']}"
    )


# --------------------------------------------------
# PRINT ACTION ANALYSIS
# --------------------------------------------------

def print_action_analysis(action_summary):

    print("\nAction Performance")
    print("-" * 30)

    for _, row in action_summary.iterrows():

        print(
            f"\n{row['action']}"
        )

        print(
            f"  Transactions: "
            f"{int(row['transactions'])}"
        )

        print(
            f"  Revenue at Risk: "
            f"₹{row['revenue_at_risk']:,.2f}"
        )

        print(
            f"  Revenue Recovered: "
            f"₹{row['revenue_recovered']:,.2f}"
        )

        print(
            f"  Recovery Rate: "
            f"{row['recovery_rate']:.2%}"
        )


# --------------------------------------------------
# PRINT FAILURE ANALYSIS
# --------------------------------------------------

def print_failure_analysis(failure_summary):

    print("\nFailure Reason Analysis")
    print("-" * 30)

    for _, row in failure_summary.iterrows():

        print(
            f"\n{row['failure_reason']}"
        )

        print(
            f"  Transactions: "
            f"{int(row['transactions'])}"
        )

        print(
            f"  Revenue at Risk: "
            f"₹{row['revenue_at_risk']:,.2f}"
        )

        print(
            f"  Revenue Recovered: "
            f"₹{row['revenue_recovered']:,.2f}"
        )

        print(
            f"  Recovery Rate: "
            f"{row['recovery_rate']:.2%}"
        )


# --------------------------------------------------
# PRINT POLICY ANALYSIS
# --------------------------------------------------

def print_policy_analysis(policy_summary):

    print("\nPolicy Analysis")
    print("-" * 30)

    for _, row in policy_summary.iterrows():

        print(
            f"\n{row['policy_status']}"
        )

        print(
            f"  Transactions: "
            f"{int(row['transactions'])}"
        )

        print(
            f"  Revenue at Risk: "
            f"₹{row['revenue_at_risk']:,.2f}"
        )

        print(
            f"  Revenue Recovered: "
            f"₹{row['revenue_recovered']:,.2f}"
        )

        print(
            f"  Recovery Rate: "
            f"{row['recovery_rate']:.2%}"
        )


# --------------------------------------------------
# PRINT FRAUD ANALYSIS
# --------------------------------------------------

def print_fraud_analysis(fraud):

    print("\nFraud Protection")
    print("-" * 30)

    print(
        f"Fraud Transactions: "
        f"{fraud['fraud_transactions']}"
    )

    print(
        f"Automated Actions Blocked: "
        f"{fraud['fraud_blocked']}"
    )

    print(
        f"Recovery Attempts: "
        f"{fraud['fraud_recovery_attempts']}"
    )

    print(
        f"Fraud Revenue Recovered: "
        f"₹{fraud['fraud_recovered']:,.2f}"
    )


# --------------------------------------------------
# PRINT PREDICTION ANALYSIS
# --------------------------------------------------

def print_prediction_analysis(predictions):

    print("\nRecovery Decision Quality")
    print("-" * 30)

    print(
        f"True Positives : "
        f"{predictions['true_positive']}"
    )

    print(
        f"False Positives: "
        f"{predictions['false_positive']}"
    )

    print(
        f"False Negatives: "
        f"{predictions['false_negative']}"
    )

    print(
        f"True Negatives : "
        f"{predictions['true_negative']}"
    )

    print(
        f"\nDecision Precision: "
        f"{predictions['precision']:.2%}"
    )

    print(
        f"Decision Recall   : "
        f"{predictions['recall']:.2%}"
    )

# --------------------------------------------------
# MISSED RECOVERY ANALYSIS
# --------------------------------------------------

def analyze_missed_recoveries(results):
    """
    Analyze recoverable transactions that the current policy
    did not attempt to recover automatically.

    A missed recovery is:
    - Ground truth says the transaction was recoverable
    - Agent did NOT choose RETRY_PAYMENT
    - Agent did NOT choose CREATE_PAYMENT_LINK
    """

    automated_actions = results["action"].isin(
        ["RETRY_PAYMENT", "CREATE_PAYMENT_LINK"]
    )

    missed = results[
        (~automated_actions)
        & (results["ground_truth_recovery"] == True)
    ].copy()

    print("\nMissed Recovery Opportunities")
    print("-" * 30)

    total_missed = len(missed)
    missed_revenue = missed["amount"].sum()

    print(
        f"Total missed recoverable transactions: "
        f"{total_missed}"
    )

    print(
        f"Missed recoverable revenue: "
        f"₹{missed_revenue:,.2f}"
    )

    # ---------------------------------------------------------
    # Breakdown by failure reason
    # ---------------------------------------------------------

    if total_missed > 0:

        grouped = (
            missed.groupby("failure_reason")
            .agg(
                missed_transactions=("transaction_id", "count"),
                missed_revenue=("amount", "sum"),
                average_probability=("recovery_probability", "mean"),
            )
            .sort_values(
                "missed_revenue",
                ascending=False
            )
        )

        for reason, row in grouped.iterrows():

            print(f"\n{reason}")

            print(
                f"  Missed Transactions: "
                f"{int(row['missed_transactions'])}"
            )

            print(
                f"  Missed Revenue: "
                f"₹{row['missed_revenue']:,.2f}"
            )

            print(
                f"  Average AI Probability: "
                f"{row['average_probability']:.2%}"
            )

        # -----------------------------------------------------
        # Probability distribution
        # -----------------------------------------------------

        print("\nMissed Recovery Probability Distribution")
        print("-" * 30)

        bins = [
            0,
            0.30,
            0.40,
            0.50,
            0.60,
            0.70,
            0.80,
            1.01,
        ]

        labels = [
            "<30%",
            "30–39%",
            "40–49%",
            "50–59%",
            "60–69%",
            "70–79%",
            "80%+",
        ]

        missed["probability_band"] = pd.cut(
            missed["recovery_probability"],
            bins=bins,
            labels=labels,
            right=False,
        )

        distribution = (
            missed["probability_band"]
            .value_counts()
            .sort_index()
        )

        for band, count in distribution.items():
            print(
                f"{band}: {count}"
            )

    return missed
# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":

    results = load_results()

    metrics = calculate_basic_metrics(
        results
    )

    action_summary = analyze_actions(
        results
    )

    failure_summary = analyze_failure_reasons(
        results
    )

    policy_summary = analyze_policy(
        results
    )

    fraud_summary = analyze_fraud_protection(
        results
    )

    prediction_summary = analyze_predictions(
        results
    )

    missed_recoveries = analyze_missed_recoveries(
        results 
    )

    print_basic_metrics(
        metrics
    )

    print_action_analysis(
        action_summary
    )

    print_failure_analysis(
        failure_summary
    )

    print_policy_analysis(
        policy_summary
    )

    print_fraud_analysis(
        fraud_summary
    )

    print_prediction_analysis(
        prediction_summary
    )

    print("\n" + "=" * 70)