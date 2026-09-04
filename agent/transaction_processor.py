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
# IMPORT AGENT
# --------------------------------------------------

from agent.recovery_agent import (
    recover_transaction
)


# --------------------------------------------------
# LOAD TRANSACTIONS
# --------------------------------------------------

def load_transactions():
    """
    Load the transaction dataset.
    """

    path = os.path.join(
        PROJECT_ROOT,
        "data",
        "transactions.csv"
    )

    transactions = pd.read_csv(path)

    return transactions


# --------------------------------------------------
# PREPARE TRANSACTION
# --------------------------------------------------

def prepare_transaction(row):
    """
    Convert a dataframe row into the dictionary
    expected by the recovery agent.
    """

    return {
        "transaction_id":
            row["transaction_id"],

        "amount":
            float(row["amount"]),

        "payment_method":
            row["payment_method"],

        "failure_reason":
            row["failure_reason"],

        "retry_count":
            int(row["retry_count"]),

        "subscription":
            bool(row["subscription"]),

        "status":
            row["status"],

        # IMPORTANT:
        # This is NOT passed into the ML model.
        # It is retained only for evaluation.
        "recovery_outcome":
            row["recovery_outcome"],
    }


# --------------------------------------------------
# PROCESS TRANSACTIONS
# --------------------------------------------------

def process_transactions(
    transactions,
    limit=None,
    verbose=False
):
    """
    Process failed transactions through ReviveAI.

    Parameters
    ----------
    transactions : pandas.DataFrame
        Complete transaction dataset.

    limit : int or None
        Number of failed transactions to process.
        None = process all.

    verbose : bool
        Whether to print every transaction's
        detailed agent output.

    Returns
    -------
    list
        Audit records.
    """

    failed_transactions = transactions[
        transactions["status"] == "FAILED"
    ].copy()

    # --------------------------------------------------
    # APPLY OPTIONAL LIMIT
    # --------------------------------------------------

    if limit is not None:
        failed_transactions = (
            failed_transactions.head(limit)
        )

    audit_records = []

    total = len(failed_transactions)

    print("\n" + "=" * 70)
    print("REVIVEAI TRANSACTION PROCESSOR")
    print("=" * 70)

    print(
        f"\nFailed transactions to process: {total}"
    )

    # --------------------------------------------------
    # PROCESS EACH TRANSACTION
    # --------------------------------------------------

    for index, (_, row) in enumerate(
        failed_transactions.iterrows(),
        start=1
    ):

        transaction = prepare_transaction(row)

        # Keep terminal output manageable
        if not verbose:

            print(
                f"\rProcessing: "
                f"{index}/{total}",
                end=""
            )

        # Run the recovery agent
        audit_record = recover_transaction(
            transaction
        )

        # --------------------------------------------------
        # EVALUATION
        # --------------------------------------------------

        # Store synthetic ground truth separately.
        #
        # This value was NEVER provided to the
        # recovery prediction model.
        audit_record["ground_truth_recovery"] = (
            bool(row["recovery_outcome"])
            if pd.notna(row["recovery_outcome"])
            else False
        )

        audit_record["original_retry_count"] = (
            int(row["retry_count"])
        )

        audit_records.append(
            audit_record
        )

    if not verbose:
        print()

    return audit_records


# --------------------------------------------------
# CALCULATE METRICS
# --------------------------------------------------

def calculate_metrics(
    transactions,
    audit_records
):
    """
    Calculate business-level recovery metrics.
    """

    results = pd.DataFrame(
        audit_records
    )

    if results.empty:
        return {
            "transactions_analyzed": 0,
            "revenue_at_risk": 0,
            "revenue_recovered": 0,
            "recovery_rate": 0,
            "successful_recoveries": 0,
            "retry_actions": 0,
            "payment_links": 0,
            "escalations": 0,
            "no_actions": 0,
            "blocked_actions": 0,
        }

    # --------------------------------------------------
    # REVENUE AT RISK
    # --------------------------------------------------

    revenue_at_risk = results[
        "amount"
    ].sum()

    # --------------------------------------------------
    # REVENUE RECOVERED
    # --------------------------------------------------

    revenue_recovered = results[
        "recovered_amount"
    ].sum()

    # --------------------------------------------------
    # RECOVERY RATE
    # --------------------------------------------------

    recovery_rate = (
        revenue_recovered / revenue_at_risk
        if revenue_at_risk > 0
        else 0
    )

    # --------------------------------------------------
    # ACTION COUNTS
    # --------------------------------------------------

    retry_actions = (
        results["action"]
        == "RETRY_PAYMENT"
    ).sum()

    payment_links = (
        results["action"]
        == "CREATE_PAYMENT_LINK"
    ).sum()

    escalations = (
        results["action"]
        == "ESCALATE"
    ).sum()

    no_actions = (
        results["action"]
        == "NO_ACTION"
    ).sum()

    # --------------------------------------------------
    # BLOCKED ACTIONS
    # --------------------------------------------------

    blocked_actions = (
        results["policy_status"]
        == "BLOCKED"
    ).sum()

    # --------------------------------------------------
    # SUCCESSFUL RECOVERIES
    # --------------------------------------------------

    successful_recoveries = (
        results["verification_status"]
        == "SUCCESS"
    ).sum()

    return {
        "transactions_analyzed":
            len(results),

        "revenue_at_risk":
            revenue_at_risk,

        "revenue_recovered":
            revenue_recovered,

        "recovery_rate":
            recovery_rate,

        "successful_recoveries":
            successful_recoveries,

        "retry_actions":
            retry_actions,

        "payment_links":
            payment_links,

        "escalations":
            escalations,

        "no_actions":
            no_actions,

        "blocked_actions":
            blocked_actions,
    }


# --------------------------------------------------
# PRINT METRICS
# --------------------------------------------------

def print_metrics(metrics):

    print("\n" + "=" * 70)
    print("REVIVEAI RECOVERY RESULTS")
    print("=" * 70)

    print(
        f"\nTransactions Analyzed : "
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

    print("\nActions")
    print("-" * 30)

    print(
        f"Retry Payments        : "
        f"{metrics['retry_actions']}"
    )

    print(
        f"Payment Links         : "
        f"{metrics['payment_links']}"
    )

    print(
        f"Escalations           : "
        f"{metrics['escalations']}"
    )

    print(
        f"No Action             : "
        f"{metrics['no_actions']}"
    )

    print(
        f"Blocked Actions       : "
        f"{metrics['blocked_actions']}"
    )

    print("\n" + "=" * 70)


# --------------------------------------------------
# SAVE AUDIT RESULTS
# --------------------------------------------------

def save_results(audit_records):

    output_path = os.path.join(
        PROJECT_ROOT,
        "data",
        "recovery_results.csv"
    )

    results = pd.DataFrame(
        audit_records
    )

    results.to_csv(
        output_path,
        index=False
    )

    print(
        f"\nAudit results saved to:"
    )

    print(
        output_path
    )


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":

    transactions = load_transactions()

    # --------------------------------------------------
    # IMPORTANT:
    # Start with only 10 transactions.
    #
    # This lets us verify the complete pipeline
    # before processing all 978 failed payments.
    # --------------------------------------------------

    audit_records = process_transactions(
        transactions,
        limit=None,
        verbose=False
    )

    metrics = calculate_metrics(
        transactions,
        audit_records
    )

    print_metrics(metrics)

    save_results(
        audit_records
    )