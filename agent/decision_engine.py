# =========================================================
# REVIVEAI DECISION ENGINE
# =========================================================
#
# AI probability
#       +
# transaction context
#       ↓
# policy decision
#       ↓
# action + status + reason
#
# =========================================================


# =========================================================
# POLICY CONFIGURATION
# =========================================================

MAX_RETRIES = 2

HIGH_VALUE_THRESHOLD = 50000


# =========================================================
# DECISION BUILDER
# =========================================================

def build_decision(
    transaction,
    recovery_probability,
    action,
    policy_status
):
    """
    Build the decision object consumed by recovery_agent.py.
    """

    reason = explain_decision(
        transaction,
        recovery_probability,
        action,
        policy_status
    )

    return {
        "action": action,
        "policy_status": policy_status,
        "status": policy_status,
        "reason": reason
    }


# =========================================================
# MAIN DECISION FUNCTION
# =========================================================

def decide_action(transaction, recovery_probability):

    failure_reason = transaction.get(
        "failure_reason",
        "UNKNOWN"
    )

    retry_count = int(
        transaction.get(
            "retry_count",
            0
        )
    )

    amount = float(
        transaction.get(
            "amount",
            0
        )
    )

    probability = float(
        recovery_probability
    )

    probability = max(
        0.0,
        min(probability, 1.0)
    )

    # =====================================================
    # HARD GUARDRAILS
    # =====================================================

    # Fraud must never be automatically recovered.

    if failure_reason == "FRAUD_SUSPECTED":

        return build_decision(
            transaction,
            probability,
            "ESCALATE",
            "BLOCKED"
        )

    # Maximum retry protection.

    if retry_count >= MAX_RETRIES:

        return build_decision(
            transaction,
            probability,
            "ESCALATE",
            "BLOCKED"
        )

    # High-value transactions require merchant approval.

    if amount >= HIGH_VALUE_THRESHOLD:

        return build_decision(
            transaction,
            probability,
            "ESCALATE",
            "APPROVAL_REQUIRED"
        )

    # =====================================================
    # NETWORK ERROR
    # =====================================================

    if failure_reason == "NETWORK_ERROR":

        if probability >= 0.70:

            return build_decision(
                transaction,
                probability,
                "RETRY_PAYMENT",
                "ALLOWED"
            )

        if probability >= 0.50:

            return build_decision(
                transaction,
                probability,
                "CREATE_PAYMENT_LINK",
                "ALLOWED"
            )

        return build_decision(
            transaction,
            probability,
            "ESCALATE",
            "ALLOWED"
        )

    # =====================================================
    # TIMEOUT
    # =====================================================

    if failure_reason == "TIMEOUT":

        if probability >= 0.70:

            return build_decision(
                transaction,
                probability,
                "RETRY_PAYMENT",
                "ALLOWED"
            )

        if probability >= 0.50:

            return build_decision(
                transaction,
                probability,
                "CREATE_PAYMENT_LINK",
                "ALLOWED"
            )

        return build_decision(
            transaction,
            probability,
            "ESCALATE",
            "ALLOWED"
        )

    # =====================================================
    # BANK DECLINE
    # =====================================================

    if failure_reason == "BANK_DECLINE":

        if probability >= 0.50:

            return build_decision(
                transaction,
                probability,
                "CREATE_PAYMENT_LINK",
                "ALLOWED"
            )

        if probability >= 0.30:

            return build_decision(
                transaction,
                probability,
                "ESCALATE",
                "ALLOWED"
            )

        return build_decision(
            transaction,
            probability,
            "NO_ACTION",
            "ALLOWED"
        )

    # =====================================================
    # INSUFFICIENT FUNDS
    # =====================================================

    if failure_reason == "INSUFFICIENT_FUNDS":

        return build_decision(
            transaction,
            probability,
            "ESCALATE",
            "ALLOWED"
        )

    # =====================================================
    # EXPIRED CARD
    # =====================================================

    if failure_reason == "EXPIRED_CARD":

        return build_decision(
            transaction,
            probability,
            "ESCALATE",
            "ALLOWED"
        )

    # =====================================================
    # FALLBACK
    # =====================================================

    if probability >= 0.80:

        return build_decision(
            transaction,
            probability,
            "RETRY_PAYMENT",
            "ALLOWED"
        )

    if probability >= 0.60:

        return build_decision(
            transaction,
            probability,
            "CREATE_PAYMENT_LINK",
            "ALLOWED"
        )

    if probability >= 0.30:

        return build_decision(
            transaction,
            probability,
            "ESCALATE",
            "ALLOWED"
        )

    return build_decision(
        transaction,
        probability,
        "NO_ACTION",
        "ALLOWED"
    )


# =========================================================
# DECISION EXPLANATION
# =========================================================

def explain_decision(
    transaction,
    recovery_probability,
    action,
    policy_status
):

    failure_reason = transaction.get(
        "failure_reason",
        "UNKNOWN"
    )

    retry_count = int(
        transaction.get(
            "retry_count",
            0
        )
    )

    amount = float(
        transaction.get(
            "amount",
            0
        )
    )

    probability_percent = (
        float(recovery_probability) * 100
    )

    # -----------------------------------------------------
    # BLOCKED
    # -----------------------------------------------------

    if policy_status == "BLOCKED":

        if failure_reason == "FRAUD_SUSPECTED":

            return (
                "Automated recovery blocked because "
                "fraud was suspected."
            )

        if retry_count >= MAX_RETRIES:

            return (
                f"Automated recovery blocked because "
                f"maximum retry limit of {MAX_RETRIES} "
                "has been reached."
            )

        return (
            "Automated recovery blocked by policy."
        )

    # -----------------------------------------------------
    # APPROVAL REQUIRED
    # -----------------------------------------------------

    if policy_status == "APPROVAL_REQUIRED":

        return (
            f"Transaction amount ₹{amount:,.2f} exceeds "
            f"the automatic recovery threshold of "
            f"₹{HIGH_VALUE_THRESHOLD:,.2f}. "
            "Merchant approval is required."
        )

    # -----------------------------------------------------
    # NETWORK ERROR
    # -----------------------------------------------------

    if failure_reason == "NETWORK_ERROR":

        if action == "RETRY_PAYMENT":

            return (
                f"Network failure with "
                f"{probability_percent:.2f}% predicted "
                "recovery probability. Automatic retry "
                "is permitted."
            )

        if action == "CREATE_PAYMENT_LINK":

            return (
                f"Network failure with "
                f"{probability_percent:.2f}% predicted "
                "recovery probability. A payment link "
                "is safer than an automatic retry."
            )

        return (
            f"Network failure with "
            f"{probability_percent:.2f}% predicted "
            "recovery probability. Confidence is below "
            "the automatic recovery threshold, so the "
            "case is escalated."
        )

    # -----------------------------------------------------
    # TIMEOUT
    # -----------------------------------------------------

    if failure_reason == "TIMEOUT":

        if action == "RETRY_PAYMENT":

            return (
                f"Timeout with "
                f"{probability_percent:.2f}% predicted "
                "recovery probability. Automatic retry "
                "is permitted."
            )

        if action == "CREATE_PAYMENT_LINK":

            return (
                f"Timeout with "
                f"{probability_percent:.2f}% predicted "
                "recovery probability. A payment link "
                "provides a safer recovery path."
            )

        return (
            f"Timeout with "
            f"{probability_percent:.2f}% predicted "
            "recovery probability. Escalation is preferred."
        )

    # -----------------------------------------------------
    # BANK DECLINE
    # -----------------------------------------------------

    if failure_reason == "BANK_DECLINE":

        if action == "CREATE_PAYMENT_LINK":

            return (
                f"Bank decline with "
                f"{probability_percent:.2f}% predicted "
                "recovery probability. A payment link "
                "provides an alternative payment path "
                "without blindly retrying the decline."
            )

        if action == "ESCALATE":

            return (
                f"Bank decline with "
                f"{probability_percent:.2f}% predicted "
                "recovery probability. Merchant/customer "
                "intervention is recommended."
            )

        return (
            f"Bank decline with only "
            f"{probability_percent:.2f}% predicted "
            "recovery probability. No automated recovery "
            "action is justified."
        )

    # -----------------------------------------------------
    # INSUFFICIENT FUNDS
    # -----------------------------------------------------

    if failure_reason == "INSUFFICIENT_FUNDS":

        return (
            "Insufficient funds detected. Automated "
            "collection is intentionally avoided and "
            "the transaction is escalated."
        )

    # -----------------------------------------------------
    # EXPIRED CARD
    # -----------------------------------------------------

    if failure_reason == "EXPIRED_CARD":

        return (
            "Expired card detected. The payment method "
            "must be updated before recovery."
        )

    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------

    return (
        f"Policy selected {action} with "
        f"{probability_percent:.2f}% predicted "
        "recovery probability."
    )


# =========================================================
# TESTS
# =========================================================

if __name__ == "__main__":

    test_cases = [

        {
            "name": "High-confidence network error",
            "transaction": {
                "transaction_id": "TEST001",
                "amount": 2500,
                "failure_reason": "NETWORK_ERROR",
                "retry_count": 0
            },
            "probability": 0.85
        },

        {
            "name": "Medium-confidence network error",
            "transaction": {
                "transaction_id": "TEST002",
                "amount": 2500,
                "failure_reason": "NETWORK_ERROR",
                "retry_count": 0
            },
            "probability": 0.60
        },

        {
            "name": "Low-confidence timeout",
            "transaction": {
                "transaction_id": "TEST003",
                "amount": 2500,
                "failure_reason": "TIMEOUT",
                "retry_count": 0
            },
            "probability": 0.35
        },

        {
            "name": "High-confidence bank decline",
            "transaction": {
                "transaction_id": "TEST004",
                "amount": 5000,
                "failure_reason": "BANK_DECLINE",
                "retry_count": 0
            },
            "probability": 0.70
        },

        {
            "name": "Medium-confidence bank decline",
            "transaction": {
                "transaction_id": "TEST005",
                "amount": 5000,
                "failure_reason": "BANK_DECLINE",
                "retry_count": 0
            },
            "probability": 0.40
        },

        {
            "name": "Low-confidence bank decline",
            "transaction": {
                "transaction_id": "TEST006",
                "amount": 5000,
                "failure_reason": "BANK_DECLINE",
                "retry_count": 0
            },
            "probability": 0.20
        },

        {
            "name": "Insufficient funds",
            "transaction": {
                "transaction_id": "TEST007",
                "amount": 3000,
                "failure_reason": "INSUFFICIENT_FUNDS",
                "retry_count": 0
            },
            "probability": 0.90
        },

        {
            "name": "Expired card",
            "transaction": {
                "transaction_id": "TEST008",
                "amount": 3000,
                "failure_reason": "EXPIRED_CARD",
                "retry_count": 0
            },
            "probability": 0.90
        },

        {
            "name": "Fraud suspected",
            "transaction": {
                "transaction_id": "TEST009",
                "amount": 3000,
                "failure_reason": "FRAUD_SUSPECTED",
                "retry_count": 0
            },
            "probability": 0.95
        },

        {
            "name": "Maximum retries reached",
            "transaction": {
                "transaction_id": "TEST010",
                "amount": 3000,
                "failure_reason": "NETWORK_ERROR",
                "retry_count": 2
            },
            "probability": 0.95
        },

        {
            "name": "High-value transaction",
            "transaction": {
                "transaction_id": "TEST011",
                "amount": 75000,
                "failure_reason": "NETWORK_ERROR",
                "retry_count": 0
            },
            "probability": 0.95
        },

        {
            "name": "Unknown failure reason",
            "transaction": {
                "transaction_id": "TEST012",
                "amount": 3000,
                "failure_reason": "UNKNOWN_FAILURE",
                "retry_count": 0
            },
            "probability": 0.75
        }
    ]

    print("=" * 70)
    print("REVIVEAI DECISION ENGINE TEST")
    print("=" * 70)

    for test in test_cases:

        decision = decide_action(
            test["transaction"],
            test["probability"]
        )

        print()

        print(test["name"])

        print(
            f"  Failure Reason : "
            f"{test['transaction']['failure_reason']}"
        )

        print(
            f"  Probability    : "
            f"{test['probability']:.0%}"
        )

        print(
            f"  Action         : "
            f"{decision['action']}"
        )

        print(
            f"  Policy Status  : "
            f"{decision['policy_status']}"
        )

        print(
            f"  Reason         : "
            f"{decision['reason']}"
        )