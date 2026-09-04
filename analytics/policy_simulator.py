import os
import sys
import pandas as pd


# =========================================================
# REVIVEAI POLICY SIMULATOR
# =========================================================
#
# Compares:
#   1. Current policy
#   2. Aggressive failure-specific policy
#   3. Conservative failure-specific policy
#
# Also evaluates the ECONOMIC/RISK tradeoff of each policy.
#
# IMPORTANT:
# - No payment/recovery tools are executed.
# - recovery_probability drives policy decisions.
# - ground_truth_recovery is used ONLY for evaluation.
# - retry_count comes from transactions.csv.
# =========================================================


# ---------------------------------------------------------
# PROJECT ROOT
# ---------------------------------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------
# DATA FILES
# ---------------------------------------------------------

TRANSACTIONS_PATH = os.path.join(
    PROJECT_ROOT,
    "data",
    "transactions.csv"
)

RECOVERY_RESULTS_PATH = os.path.join(
    PROJECT_ROOT,
    "data",
    "recovery_results.csv"
)


# ---------------------------------------------------------
# GLOBAL POLICY THRESHOLDS
# ---------------------------------------------------------

CURRENT_RETRY_THRESHOLD = 0.80
CURRENT_PAYMENT_LINK_THRESHOLD = 0.60
CURRENT_ESCALATE_THRESHOLD = 0.30


# =========================================================
# LOAD DATA
# =========================================================

def load_simulation_data():

    if not os.path.exists(TRANSACTIONS_PATH):
        raise FileNotFoundError(
            f"Could not find transactions.csv:\n"
            f"{TRANSACTIONS_PATH}"
        )

    if not os.path.exists(RECOVERY_RESULTS_PATH):
        raise FileNotFoundError(
            f"Could not find recovery_results.csv:\n"
            f"{RECOVERY_RESULTS_PATH}"
        )

    transactions = pd.read_csv(
        TRANSACTIONS_PATH
    )

    results = pd.read_csv(
        RECOVERY_RESULTS_PATH
    )

    required_transaction_columns = {
        "transaction_id",
        "amount",
        "failure_reason",
        "retry_count"
    }

    missing_transaction_columns = (
        required_transaction_columns
        - set(transactions.columns)
    )

    if missing_transaction_columns:
        raise ValueError(
            "transactions.csv is missing required columns: "
            f"{sorted(missing_transaction_columns)}"
        )

    required_result_columns = {
        "transaction_id",
        "recovery_probability",
        "ground_truth_recovery"
    }

    missing_result_columns = (
        required_result_columns
        - set(results.columns)
    )

    if missing_result_columns:
        raise ValueError(
            "recovery_results.csv is missing required columns: "
            f"{sorted(missing_result_columns)}"
        )

    transaction_data = transactions[
        [
            "transaction_id",
            "amount",
            "failure_reason",
            "retry_count"
        ]
    ].copy()

    transaction_data = transaction_data.drop_duplicates(
        subset=["transaction_id"],
        keep="first"
    )

    result_data = results[
        [
            "transaction_id",
            "recovery_probability",
            "ground_truth_recovery"
        ]
    ].copy()

    result_data = result_data.drop_duplicates(
        subset=["transaction_id"],
        keep="first"
    )

    simulated = transaction_data.merge(
        result_data,
        on="transaction_id",
        how="inner"
    )

    if simulated.empty:
        raise ValueError(
            "No transactions could be matched using "
            "transaction_id."
        )

    simulated["amount"] = pd.to_numeric(
        simulated["amount"],
        errors="coerce"
    )

    simulated["retry_count"] = pd.to_numeric(
        simulated["retry_count"],
        errors="coerce"
    )

    simulated["recovery_probability"] = pd.to_numeric(
        simulated["recovery_probability"],
        errors="coerce"
    )

    simulated["ground_truth_recovery"] = (
        simulated["ground_truth_recovery"]
        .astype(bool)
    )

    simulated = simulated.dropna(
        subset=[
            "amount",
            "retry_count",
            "recovery_probability"
        ]
    ).copy()

    return simulated


# =========================================================
# CURRENT POLICY
# =========================================================

def current_policy(transaction, probability):

    if transaction["failure_reason"] == "FRAUD_SUSPECTED":
        return "ESCALATE", "BLOCKED"

    if transaction["retry_count"] >= 2:
        return "ESCALATE", "BLOCKED"

    if transaction["amount"] >= 50000:
        return "ESCALATE", "APPROVAL_REQUIRED"

    if probability >= CURRENT_RETRY_THRESHOLD:
        return "RETRY_PAYMENT", "ALLOWED"

    if probability >= CURRENT_PAYMENT_LINK_THRESHOLD:
        return "CREATE_PAYMENT_LINK", "ALLOWED"

    if probability >= CURRENT_ESCALATE_THRESHOLD:
        return "ESCALATE", "ALLOWED"

    return "NO_ACTION", "ALLOWED"


# =========================================================
# AGGRESSIVE FAILURE-SPECIFIC POLICY
# =========================================================

def aggressive_policy(transaction, probability):

    if transaction["failure_reason"] == "FRAUD_SUSPECTED":
        return "ESCALATE", "BLOCKED"

    if transaction["retry_count"] >= 2:
        return "ESCALATE", "BLOCKED"

    if transaction["amount"] >= 50000:
        return "ESCALATE", "APPROVAL_REQUIRED"

    failure_reason = transaction["failure_reason"]

    if failure_reason in [
        "NETWORK_ERROR",
        "TIMEOUT"
    ]:

        if probability >= 0.60:
            return "RETRY_PAYMENT", "ALLOWED"

        if probability >= 0.40:
            return "CREATE_PAYMENT_LINK", "ALLOWED"

        return "ESCALATE", "ALLOWED"

    if failure_reason in [
        "BANK_DECLINE",
        "INSUFFICIENT_FUNDS"
    ]:

        if probability >= 0.50:
            return "CREATE_PAYMENT_LINK", "ALLOWED"

        if probability >= 0.30:
            return "ESCALATE", "ALLOWED"

        return "NO_ACTION", "ALLOWED"

    if failure_reason == "EXPIRED_CARD":
        return "ESCALATE", "ALLOWED"

    if probability >= 0.80:
        return "RETRY_PAYMENT", "ALLOWED"

    if probability >= 0.60:
        return "CREATE_PAYMENT_LINK", "ALLOWED"

    if probability >= 0.30:
        return "ESCALATE", "ALLOWED"

    return "NO_ACTION", "ALLOWED"


# =========================================================
# CONSERVATIVE FAILURE-SPECIFIC POLICY
# =========================================================

def conservative_policy(transaction, probability):

    if transaction["failure_reason"] == "FRAUD_SUSPECTED":
        return "ESCALATE", "BLOCKED"

    if transaction["retry_count"] >= 2:
        return "ESCALATE", "BLOCKED"

    if transaction["amount"] >= 50000:
        return "ESCALATE", "APPROVAL_REQUIRED"

    failure_reason = transaction["failure_reason"]

    if failure_reason in [
        "NETWORK_ERROR",
        "TIMEOUT"
    ]:

        if probability >= 0.70:
            return "RETRY_PAYMENT", "ALLOWED"

        if probability >= 0.50:
            return "CREATE_PAYMENT_LINK", "ALLOWED"

        return "ESCALATE", "ALLOWED"

    if failure_reason in [
        "BANK_DECLINE",
        "INSUFFICIENT_FUNDS"
    ]:

        if probability >= 0.50:
            return "CREATE_PAYMENT_LINK", "ALLOWED"

        if probability >= 0.30:
            return "ESCALATE", "ALLOWED"

        return "NO_ACTION", "ALLOWED"

    if failure_reason == "EXPIRED_CARD":
        return "ESCALATE", "ALLOWED"

    if probability >= 0.80:
        return "RETRY_PAYMENT", "ALLOWED"

    if probability >= 0.60:
        return "CREATE_PAYMENT_LINK", "ALLOWED"

    if probability >= 0.30:
        return "ESCALATE", "ALLOWED"

    return "NO_ACTION", "ALLOWED"


# =========================================================
# EVALUATE POLICY
# =========================================================

def evaluate_policy(results, policy_function):

    simulated = results.copy()

    actions = []
    policy_statuses = []

    for _, transaction in simulated.iterrows():

        probability = float(
            transaction["recovery_probability"]
        )

        action, policy_status = policy_function(
            transaction,
            probability
        )

        actions.append(action)
        policy_statuses.append(policy_status)

    simulated["simulated_action"] = actions

    simulated["simulated_policy_status"] = (
        policy_statuses
    )

    automated_actions = simulated[
        "simulated_action"
    ].isin(
        [
            "RETRY_PAYMENT",
            "CREATE_PAYMENT_LINK"
        ]
    )

    ground_truth = simulated[
        "ground_truth_recovery"
    ].astype(bool)

    # -----------------------------------------------------
    # Confusion matrix
    # -----------------------------------------------------

    true_positive = int(
        (
            automated_actions
            & ground_truth
        ).sum()
    )

    false_positive = int(
        (
            automated_actions
            & ~ground_truth
        ).sum()
    )

    false_negative = int(
        (
            ~automated_actions
            & ground_truth
        ).sum()
    )

    true_negative = int(
        (
            ~automated_actions
            & ~ground_truth
        ).sum()
    )

    # -----------------------------------------------------
    # Revenue
    # -----------------------------------------------------

    revenue_at_risk = float(
        simulated["amount"].sum()
    )

    successful_recovery = (
        automated_actions
        & ground_truth
    )

    false_positive_mask = (
        automated_actions
        & ~ground_truth
    )

    revenue_recovered = float(
        simulated.loc[
            successful_recovery,
            "amount"
        ].sum()
    )

    false_positive_revenue = float(
        simulated.loc[
            false_positive_mask,
            "amount"
        ].sum()
    )

    recovery_rate = (
        revenue_recovered / revenue_at_risk
        if revenue_at_risk > 0
        else 0.0
    )

    # -----------------------------------------------------
    # Precision / Recall
    # -----------------------------------------------------

    precision = (
        true_positive
        / (true_positive + false_positive)
        if true_positive + false_positive > 0
        else 0.0
    )

    recall = (
        true_positive
        / (true_positive + false_negative)
        if true_positive + false_negative > 0
        else 0.0
    )

    # -----------------------------------------------------
    # Action counts
    # -----------------------------------------------------

    action_counts = (
        simulated[
            "simulated_action"
        ]
        .value_counts()
        .to_dict()
    )

    retry_count = action_counts.get(
        "RETRY_PAYMENT",
        0
    )

    payment_link_count = action_counts.get(
        "CREATE_PAYMENT_LINK",
        0
    )

    automated_action_count = (
        retry_count
        + payment_link_count
    )

    blocked_actions = int(
        simulated[
            "simulated_policy_status"
        ]
        .eq("BLOCKED")
        .sum()
    )

    approval_required = int(
        simulated[
            "simulated_policy_status"
        ]
        .eq("APPROVAL_REQUIRED")
        .sum()
    )

    # -----------------------------------------------------
    # Economic metrics
    # -----------------------------------------------------

    automated_action_rate = (
        automated_action_count
        / len(simulated)
        if len(simulated) > 0
        else 0.0
    )

    revenue_per_automated_action = (
        revenue_recovered
        / automated_action_count
        if automated_action_count > 0
        else 0.0
    )

    average_false_positive_amount = (
        false_positive_revenue
        / false_positive
        if false_positive > 0
        else 0.0
    )

    average_successful_recovery_amount = (
        revenue_recovered
        / true_positive
        if true_positive > 0
        else 0.0
    )

    # Revenue exposed to automation as a false positive
    false_positive_revenue_rate = (
        false_positive_revenue
        / revenue_at_risk
        if revenue_at_risk > 0
        else 0.0
    )

    # A simple efficiency ratio:
    #
    # recovered revenue / false-positive revenue exposed
    #
    # Higher is better.
    risk_adjusted_efficiency = (
        revenue_recovered
        / false_positive_revenue
        if false_positive_revenue > 0
        else float("inf")
    )

    # -----------------------------------------------------
    # Fraud protection
    # -----------------------------------------------------

    fraud_transactions = (
        simulated["failure_reason"]
        == "FRAUD_SUSPECTED"
    )

    fraud_automated_actions = int(
        (
            fraud_transactions
            & automated_actions
        ).sum()
    )

    fraud_revenue_recovered = float(
        simulated.loc[
            fraud_transactions
            & successful_recovery,
            "amount"
        ].sum()
    )

    return {
        "transactions":
            len(simulated),

        "revenue_at_risk":
            revenue_at_risk,

        "revenue_recovered":
            revenue_recovered,

        "recovery_rate":
            recovery_rate,

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

        "retry_payments":
            retry_count,

        "payment_links":
            payment_link_count,

        "automated_actions":
            automated_action_count,

        "automated_action_rate":
            automated_action_rate,

        "escalations":
            action_counts.get(
                "ESCALATE",
                0
            ),

        "no_actions":
            action_counts.get(
                "NO_ACTION",
                0
            ),

        "blocked_actions":
            blocked_actions,

        "approval_required":
            approval_required,

        "false_positive_revenue":
            false_positive_revenue,

        "false_positive_revenue_rate":
            false_positive_revenue_rate,

        "average_false_positive_amount":
            average_false_positive_amount,

        "average_successful_recovery_amount":
            average_successful_recovery_amount,

        "revenue_per_automated_action":
            revenue_per_automated_action,

        "risk_adjusted_efficiency":
            risk_adjusted_efficiency,

        "fraud_transactions":
            int(
                fraud_transactions.sum()
            ),

        "fraud_automated_actions":
            fraud_automated_actions,

        "fraud_revenue_recovered":
            fraud_revenue_recovered
    }


# =========================================================
# PRINT POLICY RESULTS
# =========================================================

def print_policy_results(name, metrics):

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    print("\nPerformance")
    print("-" * 30)

    print(
        f"Transactions Analyzed : "
        f"{metrics['transactions']}"
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

    print("\nActions")
    print("-" * 30)

    print(
        f"Retry Payments        : "
        f"{metrics['retry_payments']}"
    )

    print(
        f"Payment Links         : "
        f"{metrics['payment_links']}"
    )

    print(
        f"Automated Actions     : "
        f"{metrics['automated_actions']}"
    )

    print(
        f"Automated Action Rate : "
        f"{metrics['automated_action_rate']:.2%}"
    )

    print(
        f"Escalations           : "
        f"{metrics['escalations']}"
    )

    print(
        f"No Actions            : "
        f"{metrics['no_actions']}"
    )

    print(
        f"Blocked Actions       : "
        f"{metrics['blocked_actions']}"
    )

    print(
        f"Approval Required     : "
        f"{metrics['approval_required']}"
    )

    print("\nDecision Quality")
    print("-" * 30)

    print(
        f"True Positives        : "
        f"{metrics['true_positive']}"
    )

    print(
        f"False Positives       : "
        f"{metrics['false_positive']}"
    )

    print(
        f"False Negatives       : "
        f"{metrics['false_negative']}"
    )

    print(
        f"True Negatives        : "
        f"{metrics['true_negative']}"
    )

    print(
        f"Decision Precision    : "
        f"{metrics['precision']:.2%}"
    )

    print(
        f"Decision Recall       : "
        f"{metrics['recall']:.2%}"
    )

    print("\nEconomic / Risk Analysis")
    print("-" * 30)

    print(
        f"Recovered / Auto Act. : "
        f"₹{metrics['revenue_per_automated_action']:,.2f}"
    )

    print(
        f"False-Positive Revenue: "
        f"₹{metrics['false_positive_revenue']:,.2f}"
    )

    print(
        f"FP Revenue Exposure   : "
        f"{metrics['false_positive_revenue_rate']:.2%}"
    )

    print(
        f"Avg FP Action Amount  : "
        f"₹{metrics['average_false_positive_amount']:,.2f}"
    )

    print(
        f"Avg Successful Amount : "
        f"₹{metrics['average_successful_recovery_amount']:,.2f}"
    )

    efficiency = metrics[
        "risk_adjusted_efficiency"
    ]

    if efficiency == float("inf"):
        print(
            "Risk-Adjusted Efficiency: INF"
        )
    else:
        print(
            f"Risk-Adjusted Efficiency: "
            f"{efficiency:.2f}x"
        )

    print("\nFraud Protection")
    print("-" * 30)

    print(
        f"Fraud Transactions    : "
        f"{metrics['fraud_transactions']}"
    )

    print(
        f"Fraud Automated Acts  : "
        f"{metrics['fraud_automated_actions']}"
    )

    print(
        f"Fraud Revenue Rec.    : "
        f"₹{metrics['fraud_revenue_recovered']:,.2f}"
    )


# =========================================================
# FAILURE-REASON ECONOMIC ANALYSIS
# =========================================================

def failure_reason_analysis(
    results,
    policy_name,
    policy_function
):

    simulated = results.copy()

    actions = []

    for _, transaction in simulated.iterrows():

        probability = float(
            transaction["recovery_probability"]
        )

        action, _ = policy_function(
            transaction,
            probability
        )

        actions.append(action)

    simulated["simulated_action"] = actions

    automated = simulated[
        "simulated_action"
    ].isin(
        [
            "RETRY_PAYMENT",
            "CREATE_PAYMENT_LINK"
        ]
    )

    successful = (
        automated
        & simulated["ground_truth_recovery"]
    )

    false_positive = (
        automated
        & ~simulated["ground_truth_recovery"]
    )

    grouped_rows = []

    for failure_reason, group in simulated.groupby(
        "failure_reason"
    ):

        group_automated = group[
            "simulated_action"
        ].isin(
            [
                "RETRY_PAYMENT",
                "CREATE_PAYMENT_LINK"
            ]
        )

        group_successful = (
            group_automated
            & group["ground_truth_recovery"]
        )

        group_fp = (
            group_automated
            & ~group["ground_truth_recovery"]
        )

        risk = float(
            group["amount"].sum()
        )

        recovered = float(
            group.loc[
                group_successful,
                "amount"
            ].sum()
        )

        fp_revenue = float(
            group.loc[
                group_fp,
                "amount"
            ].sum()
        )

        grouped_rows.append(
            {
                "failure_reason":
                    failure_reason,

                "transactions":
                    len(group),

                "automated_actions":
                    int(group_automated.sum()),

                "successful_recoveries":
                    int(group_successful.sum()),

                "false_positives":
                    int(group_fp.sum()),

                "risk":
                    risk,

                "recovered":
                    recovered,

                "false_positive_revenue":
                    fp_revenue
            }
        )

    analysis = pd.DataFrame(
        grouped_rows
    )

    analysis = analysis.sort_values(
        "recovered",
        ascending=False
    )

    print("\n" + "=" * 70)
    print(
        f"FAILURE-REASON ECONOMIC ANALYSIS — {policy_name}"
    )
    print("=" * 70)

    for _, row in analysis.iterrows():

        print(
            f"\n{row['failure_reason']}"
        )

        print(
            f"  Transactions          : "
            f"{int(row['transactions'])}"
        )

        print(
            f"  Automated Actions     : "
            f"{int(row['automated_actions'])}"
        )

        print(
            f"  Successful Recoveries : "
            f"{int(row['successful_recoveries'])}"
        )

        print(
            f"  False Positives       : "
            f"{int(row['false_positives'])}"
        )

        print(
            f"  Revenue at Risk       : "
            f"₹{row['risk']:,.2f}"
        )

        print(
            f"  Revenue Recovered     : "
            f"₹{row['recovered']:,.2f}"
        )

        print(
            f"  FP Revenue Exposure   : "
            f"₹{row['false_positive_revenue']:,.2f}"
        )


# =========================================================
# THREE-WAY COMPARISON
# =========================================================

def print_comparison(
    current,
    aggressive,
    conservative
):

    print("\n" + "=" * 70)
    print("THREE-WAY POLICY COMPARISON")
    print("=" * 70)

    print(
        "\nMetric                     Current       Aggressive    Conservative"
    )

    print("-" * 78)

    rows = [
        (
            "Revenue Recovered",
            "revenue_recovered",
            "currency"
        ),
        (
            "Recovery Rate",
            "recovery_rate",
            "percent"
        ),
        (
            "Precision",
            "precision",
            "percent"
        ),
        (
            "Recall",
            "recall",
            "percent"
        ),
        (
            "False Positives",
            "false_positive",
            "integer"
        ),
        (
            "False Negatives",
            "false_negative",
            "integer"
        ),
        (
            "Automated Actions",
            "automated_actions",
            "integer"
        ),
        (
            "Retry Payments",
            "retry_payments",
            "integer"
        ),
        (
            "Payment Links",
            "payment_links",
            "integer"
        ),
        (
            "FP Revenue Exposure",
            "false_positive_revenue",
            "currency"
        ),
        (
            "Recovered / Auto Act.",
            "revenue_per_automated_action",
            "currency"
        ),
        (
            "Avg FP Amount",
            "average_false_positive_amount",
            "currency"
        ),
        (
            "Avg Successful Amount",
            "average_successful_recovery_amount",
            "currency"
        ),
        (
            "Risk-Adjusted Efficiency",
            "risk_adjusted_efficiency",
            "ratio"
        )
    ]

    for label, key, value_type in rows:

        c = current[key]
        a = aggressive[key]
        conservative_value = conservative[key]

        if value_type == "currency":

            print(
                f"{label:<26}"
                f"₹{c:>10,.2f}   "
                f"₹{a:>10,.2f}   "
                f"₹{conservative_value:>10,.2f}"
            )

        elif value_type == "percent":

            print(
                f"{label:<26}"
                f"{c:>10.2%}   "
                f"{a:>10.2%}   "
                f"{conservative_value:>10.2%}"
            )

        elif value_type == "ratio":

            def format_ratio(value):
                if value == float("inf"):
                    return "INF"
                return f"{value:.2f}x"

            print(
                f"{label:<26}"
                f"{format_ratio(c):>12}   "
                f"{format_ratio(a):>12}   "
                f"{format_ratio(conservative_value):>12}"
            )

        else:

            print(
                f"{label:<26}"
                f"{c:>10d}   "
                f"{a:>10d}   "
                f"{conservative_value:>10d}"
            )


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    print(
        "Loading transaction and recovery results..."
    )

    results = load_simulation_data()

    print(
        f"Loaded {len(results)} matched transactions."
    )

    # -----------------------------------------------------
    # Evaluate policies
    # -----------------------------------------------------

    current_metrics = evaluate_policy(
        results,
        current_policy
    )

    aggressive_metrics = evaluate_policy(
        results,
        aggressive_policy
    )

    conservative_metrics = evaluate_policy(
        results,
        conservative_policy
    )

    # -----------------------------------------------------
    # Individual results
    # -----------------------------------------------------

    print_policy_results(
        "CURRENT POLICY",
        current_metrics
    )

    print_policy_results(
        "AGGRESSIVE FAILURE-SPECIFIC POLICY",
        aggressive_metrics
    )

    print_policy_results(
        "CONSERVATIVE FAILURE-SPECIFIC POLICY",
        conservative_metrics
    )

    # -----------------------------------------------------
    # Three-way comparison
    # -----------------------------------------------------

    print_comparison(
        current_metrics,
        aggressive_metrics,
        conservative_metrics
    )

    # -----------------------------------------------------
    # Failure reason analysis
    # -----------------------------------------------------

    failure_reason_analysis(
        results,
        "CURRENT POLICY",
        current_policy
    )

    failure_reason_analysis(
        results,
        "CONSERVATIVE FAILURE-SPECIFIC POLICY",
        conservative_policy
    )