import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

NUM_CUSTOMERS = 1000
NUM_TRANSACTIONS = 5000

SEED = 42

random.seed(SEED)
np.random.seed(SEED)


# ============================================================
# CUSTOMER BEHAVIOR
# ============================================================

CUSTOMER_SEGMENTS = {
    "RELIABLE": {
        "success_rate": 0.92,
        "recovery_rate": 0.85,
    },
    "NORMAL": {
        "success_rate": 0.80,
        "recovery_rate": 0.65,
    },
    "RISKY": {
        "success_rate": 0.60,
        "recovery_rate": 0.35,
    },
}


# ============================================================
# PAYMENT DATA
# ============================================================

PAYMENT_METHODS = [
    "UPI",
    "CARD",
    "NETBANKING",
    "WALLET",
]


FAILURE_REASONS = [
    "NETWORK_ERROR",
    "TIMEOUT",
    "BANK_DECLINE",
    "INSUFFICIENT_FUNDS",
    "EXPIRED_CARD",
    "FRAUD_SUSPECTED",
]


# ============================================================
# SYNTHETIC GROUND-TRUTH RECOVERY RATES
# ============================================================
#
# These are assumptions for our synthetic dataset.
# They are NOT real Razorpay statistics.
#
# They allow us to create known recovery outcomes so that
# we can later evaluate our AI model.
# ============================================================

RECOVERY_BASE_RATES = {
    "NETWORK_ERROR": 0.90,
    "TIMEOUT": 0.85,
    "BANK_DECLINE": 0.55,
    "INSUFFICIENT_FUNDS": 0.45,
    "EXPIRED_CARD": 0.20,
    "FRAUD_SUSPECTED": 0.03,
}


# ============================================================
# CUSTOMER GENERATOR
# ============================================================

def generate_customers():
    customers = []

    for i in range(1, NUM_CUSTOMERS + 1):

        customer_id = f"C{i:04d}"

        # Select a customer behavior segment.
        segment = random.choices(
            ["RELIABLE", "NORMAL", "RISKY"],
            weights=[0.30, 0.50, 0.20],
            k=1
        )[0]

        segment_data = CUSTOMER_SEGMENTS[segment]

        # Generate historical transaction count.
        total_transactions = random.randint(5, 30)

        # Estimate historical successful/failed transactions.
        successful_transactions = int(
            total_transactions * segment_data["success_rate"]
        )

        failed_transactions = (
            total_transactions - successful_transactions
        )

        # Average amount spent by the customer.
        average_transaction_value = round(
            random.uniform(500, 10000),
            2
        )

        # Approximate customer lifetime value.
        lifetime_value = round(
            successful_transactions
            * average_transaction_value,
            2
        )

        # Customer's preferred payment method.
        preferred_payment_method = random.choice(
            PAYMENT_METHODS
        )

        # Historical recovery behavior.
        previous_recovery_successes = int(
            failed_transactions
            * segment_data["recovery_rate"]
        )

        previous_recovery_failures = (
            failed_transactions
            - previous_recovery_successes
        )

        customers.append({
            "customer_id": customer_id,
            "customer_segment": segment,
            "total_transactions": total_transactions,
            "successful_transactions": successful_transactions,
            "failed_transactions": failed_transactions,
            "average_transaction_value": average_transaction_value,
            "lifetime_value": lifetime_value,
            "preferred_payment_method": preferred_payment_method,
            "previous_recovery_successes": previous_recovery_successes,
            "previous_recovery_failures": previous_recovery_failures,
        })

    return pd.DataFrame(customers)


# ============================================================
# RECOVERY GROUND TRUTH
# ============================================================

def calculate_recovery_outcome(
    segment,
    failure_reason,
    retry_count
):
    """
    Calculate the synthetic ground-truth recovery probability
    and outcome for a failed transaction.

    This represents the simulated world against which our
    future AI model will be evaluated.
    """

    base_rate = RECOVERY_BASE_RATES[failure_reason]

    # Customer behavior adjustment.
    if segment == "RELIABLE":
        customer_adjustment = 0.08

    elif segment == "RISKY":
        customer_adjustment = -0.12

    else:
        customer_adjustment = 0.0

    # Multiple previous retries reduce recovery likelihood.
    retry_penalty = retry_count * 0.10

    recovery_probability = (
        base_rate
        + customer_adjustment
        - retry_penalty
    )

    # Keep probability between 1% and 99%.
    recovery_probability = max(
        0.01,
        min(0.99, recovery_probability)
    )

    # Simulate whether the recovery actually succeeds.
    recovery_outcome = (
        random.random() < recovery_probability
    )

    return recovery_probability, recovery_outcome


# ============================================================
# TRANSACTION GENERATOR
# ============================================================

def generate_transactions(customers_df):

    transactions = []

    start_date = (
        datetime.now()
        - timedelta(days=90)
    )

    for transaction_number in range(
        1,
        NUM_TRANSACTIONS + 1
    ):

        # Select a random customer.
        customer = customers_df.sample(
            n=1
        ).iloc[0]

        customer_id = customer["customer_id"]
        segment = customer["customer_segment"]

        # Use customer's preferred payment method.
        payment_method = (
            customer["preferred_payment_method"]
        )

        # Customer segment determines base payment success rate.
        success_probability = (
            CUSTOMER_SEGMENTS[segment]["success_rate"]
        )

        is_successful = (
            random.random()
            < success_probability
        )

        # Transaction amount.
        amount = round(
            random.uniform(300, 15000),
            2
        )

        # Transaction timestamp within the previous 90 days.
        timestamp = (
            start_date
            + timedelta(
                minutes=random.randint(
                    0,
                    90 * 24 * 60
                )
            )
        )

        # ----------------------------------------------------
        # SUCCESSFUL PAYMENT
        # ----------------------------------------------------

        if is_successful:

            status = "SUCCESS"

            failure_reason = None

            retry_count = 0

            checkout_completed = True

            recovery_eligible = False

            recovery_probability = None

            recovery_outcome = None

        # ----------------------------------------------------
        # FAILED PAYMENT
        # ----------------------------------------------------

        else:

            status = "FAILED"

            # Select failure reason.
            failure_reason = random.choices(
                FAILURE_REASONS,
                weights=[
                    0.25,  # NETWORK_ERROR
                    0.20,  # TIMEOUT
                    0.20,  # BANK_DECLINE
                    0.15,  # INSUFFICIENT_FUNDS
                    0.12,  # EXPIRED_CARD
                    0.08,  # FRAUD_SUSPECTED
                ],
                k=1
            )[0]

            # Number of previous retry attempts.
            retry_count = random.randint(
                0,
                2
            )

            # Whether checkout was completed.
            checkout_completed = (
                random.random() < 0.85
            )

            # Fraud-suspected transactions should not receive
            # automatic recovery.
            recovery_eligible = (
                failure_reason
                != "FRAUD_SUSPECTED"
            )

            # Calculate synthetic ground truth.
            recovery_probability, recovery_outcome = (
                calculate_recovery_outcome(
                    segment,
                    failure_reason,
                    retry_count
                )
            )

        # Whether this is a subscription transaction.
        is_subscription = (
            random.random() < 0.25
        )

        # Add transaction to dataset.
        transactions.append({

            "transaction_id": (
                f"TX{transaction_number:05d}"
            ),

            "customer_id": customer_id,

            "amount": amount,

            "timestamp": timestamp,

            "payment_method": payment_method,

            "status": status,

            "failure_reason": failure_reason,

            "retry_count": retry_count,

            "checkout_completed": checkout_completed,

            "subscription": is_subscription,

            "recovery_eligible": recovery_eligible,

            "recovery_probability_ground_truth": (
                recovery_probability
            ),

            "recovery_outcome": recovery_outcome,
        })

    return pd.DataFrame(transactions)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("REVIVEAI DATASET GENERATOR")
    print("=" * 60)

    print()

    # --------------------------------------------------------
    # Generate customers
    # --------------------------------------------------------

    customers_df = generate_customers()

    customers_df.to_csv(
        "data/customers.csv",
        index=False
    )

    print(
        "Customer dataset generated successfully."
    )

    print(
        f"Customers: {len(customers_df)}"
    )

    print()

    # --------------------------------------------------------
    # Generate transactions
    # --------------------------------------------------------

    transactions_df = generate_transactions(
        customers_df
    )

    transactions_df.to_csv(
        "data/transactions.csv",
        index=False
    )

    print(
        "Transaction dataset generated successfully."
    )

    print(
        f"Transactions: {len(transactions_df)}"
    )

    print()

    # --------------------------------------------------------
    # Transaction status
    # --------------------------------------------------------

    print(
        "Transaction status distribution:"
    )

    print(
        transactions_df["status"].value_counts()
    )

    print()

    # --------------------------------------------------------
    # Failure reasons
    # --------------------------------------------------------

    print(
        "Failure reason distribution:"
    )

    print(
        transactions_df[
            "failure_reason"
        ].value_counts(
            dropna=True
        )
    )

    print()

    # --------------------------------------------------------
    # Recovery eligibility
    # --------------------------------------------------------

    print(
        "Recovery eligibility:"
    )

    print(
        transactions_df[
            "recovery_eligible"
        ].value_counts(
            dropna=False
        )
    )

    print()

    # --------------------------------------------------------
    # Recovery outcomes
    # --------------------------------------------------------

    print(
        "Recovery outcomes:"
    )

    print(
        transactions_df[
            "recovery_outcome"
        ].value_counts(
            dropna=False
        )
    )

    print()

    # --------------------------------------------------------
    # Failed transaction summary
    # --------------------------------------------------------

    failed_transactions = (
        transactions_df[
            transactions_df["status"] == "FAILED"
        ]
    )

    recoverable_transactions = (
        failed_transactions[
            failed_transactions[
                "recovery_outcome"
            ] == True
        ]
    )

    print(
        f"Failed transactions: "
        f"{len(failed_transactions)}"
    )

    print(
        f"Recoverable transactions: "
        f"{len(recoverable_transactions)}"
    )

    print()

    # --------------------------------------------------------
    # Revenue at risk
    # --------------------------------------------------------

    revenue_at_risk = (
        failed_transactions["amount"].sum()
    )

    print(
        f"Revenue at risk: "
        f"₹{revenue_at_risk:,.2f}"
    )

    print()

    # --------------------------------------------------------
    # Sample transactions
    # --------------------------------------------------------

    print(
        "Sample transactions:"
    )

    print(
        transactions_df.head()
    )

    print()

    print("=" * 60)
    print("DATASET GENERATION COMPLETE")
    print("=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()