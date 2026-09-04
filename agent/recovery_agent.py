import os
import sys
from datetime import datetime


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
# IMPORT REVIVEAI COMPONENTS
# --------------------------------------------------

from models.recovery_model import (
    predict_recovery_probability
)

from agent.decision_engine import (
    decide_action
)


# --------------------------------------------------
# SIMULATED RECOVERY TOOLS
# --------------------------------------------------

def retry_payment(transaction):
    """
    Simulate a payment retry.

    The transaction's synthetic recovery_outcome is used
    ONLY to simulate the response from the payment provider.

    It is NOT used by the ML model to make its prediction.
    """

    print("  [TOOL] retry_payment()")

    ground_truth = transaction.get(
        "recovery_outcome"
    )

    # Convert dataset value safely
    if isinstance(ground_truth, str):
        ground_truth = ground_truth.lower() == "true"

    success = bool(ground_truth)

    if success:

        return {
            "success": True,
            "message": "Payment retry succeeded."
        }

    return {
        "success": False,
        "message": "Payment retry failed."
    }


def create_payment_link(transaction):
    """
    Simulate payment-link creation and the customer's
    subsequent payment attempt.

    recovery_outcome is used ONLY to simulate the
    external payment result. It is never supplied
    to the ML prediction model.
    """

    print("  [TOOL] create_payment_link()")

    payment_link = (
        "https://reviveai.example/pay/"
        + transaction["transaction_id"]
    )

    ground_truth = transaction.get(
        "recovery_outcome"
    )

    if isinstance(ground_truth, str):
        ground_truth = (
            ground_truth.lower() == "true"
        )

    customer_payment_success = bool(
        ground_truth
    )

    return {
        "success": True,
        "payment_link": payment_link,
        "customer_payment_success":
            customer_payment_success,
        "message":
            "Payment link created successfully.",
    }


def send_recovery_message(
    transaction,
    action
):
    """
    Simulate sending a recovery message
    to the customer.
    """

    print(
        "  [TOOL] send_recovery_message()"
    )

    return {
        "success": True,
        "message": (
            f"Recovery message sent for {action}."
        )
    }


def escalate_to_merchant(
    transaction,
    reason
):
    """
    Simulate merchant escalation.
    """

    print(
        "  [TOOL] escalate_to_merchant()"
    )

    return {
        "success": True,
        "message": (
            "Transaction escalated to merchant."
        ),
        "reason": reason,
    }


def verify_payment(
    transaction,
    payment_success
):
    """
    Verify the final payment status.

    In production, this would query the
    payment provider.
    """

    print(
        "  [TOOL] verify_payment()"
    )

    if payment_success:

        return {
            "verified": True,
            "status": "SUCCESS",
        }

    return {
        "verified": False,
        "status": "FAILED",
    }


# --------------------------------------------------
# AUDIT LOG
# --------------------------------------------------

def record_outcome(
    transaction,
    probability,
    decision,
    execution_result,
    verification_result,
):
    """
    Create a complete audit record.
    """

    recovered_amount = 0

    if verification_result["verified"]:

        recovered_amount = transaction[
            "amount"
        ]

    return {

        "timestamp": datetime.now().isoformat(),

        "transaction_id":
            transaction["transaction_id"],

        "amount":
            transaction["amount"],

        "failure_reason":
            transaction["failure_reason"],

        "recovery_probability":
            round(probability, 4),

        "action":
            decision["action"],

        "policy_status":
            decision["policy_status"],

        "decision_reason":
            decision["reason"],

        "execution_success":
            execution_result.get(
                "success",
                False
            ),

        "execution_message":
            execution_result.get(
                "message",
                ""
            ),

        "verification_status":
            verification_result["status"],

        "recovered_amount":
            recovered_amount,
    }


# --------------------------------------------------
# MAIN RECOVERY AGENT
# --------------------------------------------------

def recover_transaction(transaction):
    """
    Execute the complete ReviveAI recovery workflow.

    Workflow:

    Transaction
        ↓
    AI Prediction
        ↓
    Policy Decision
        ↓
    Recovery Action
        ↓
    Verification
        ↓
    Escalation if Recovery Fails
        ↓
    Audit Record
    """

    print("\\n" + "=" * 60)
    print("REVIVEAI RECOVERY AGENT")
    print("=" * 60)

    print(
        f"\\nTransaction: "
        f"{transaction['transaction_id']}"
    )

    print(
        f"Amount: "
        f"₹{transaction['amount']:,.2f}"
    )

    print(
        f"Failure Reason: "
        f"{transaction['failure_reason']}"
    )

    # --------------------------------------------------
    # STEP 1: AI PREDICTION
    # --------------------------------------------------

    probability = predict_recovery_probability(
        transaction
    )

    print(
        f"\\n[AI] Recovery Probability: "
        f"{probability:.2%}"
    )

    # --------------------------------------------------
    # STEP 2: POLICY DECISION
    # --------------------------------------------------

    decision = decide_action(
        transaction,
        probability
    )

    print(
        f"[POLICY] Action: "
        f"{decision['action']}"
    )

    print(
        f"[POLICY] Status: "
        f"{decision['policy_status']}"
    )

    print(
        f"[POLICY] Reason: "
        f"{decision['reason']}"
    )

    # --------------------------------------------------
    # STEP 3: BLOCKED
    # --------------------------------------------------

    if decision["policy_status"] == "BLOCKED":

        print(
            "\\n[AGENT] Automated action blocked."
        )

        execution_result = escalate_to_merchant(
            transaction,
            decision["reason"]
        )

        verification_result = {
            "verified": False,
            "status": "ESCALATED",
        }

    # --------------------------------------------------
    # STEP 4: APPROVAL REQUIRED
    # --------------------------------------------------

    elif decision["policy_status"] == "APPROVAL_REQUIRED":

        print(
            "\\n[AGENT] Merchant approval required."
        )

        execution_result = escalate_to_merchant(
            transaction,
            decision["reason"]
        )

        verification_result = {
            "verified": False,
            "status": "AWAITING_APPROVAL",
        }

    # --------------------------------------------------
    # STEP 5: RETRY PAYMENT
    # --------------------------------------------------

    elif decision["action"] == "RETRY_PAYMENT":

        execution_result = retry_payment(
            transaction
        )

        if execution_result["success"]:

            print(
                "\\n[AGENT] Retry succeeded."
            )

            verification_result = verify_payment(
                transaction,
                True
            )

        else:

            print(
                "\\n[AGENT] Retry failed."
            )

            verification_result = verify_payment(
                transaction,
                False
            )

            if verification_result["status"] == "FAILED":

                print(
                    "\\n[AGENT] Recovery attempt failed."
                )

                print(
                    "[AGENT] Escalating to merchant."
                )

                escalation_result = escalate_to_merchant(
                    transaction,
                    "Automated payment retry failed after policy-approved recovery attempt."
                )

                execution_result = {
                    "success": False,
                    "message": (
                        execution_result.get(
                            "message",
                            "Payment retry failed."
                        )
                        + " "
                        + escalation_result.get(
                            "message",
                            "Merchant escalation created."
                        )
                    ),
                }

                verification_result = {
                    "verified": False,
                    "status": "ESCALATED",
                }

    # --------------------------------------------------
    # STEP 6: PAYMENT LINK
    # --------------------------------------------------

    elif decision["action"] == "CREATE_PAYMENT_LINK":

        execution_result = create_payment_link(
            transaction
        )

        if execution_result["success"]:

            send_recovery_message(
                transaction,
                "CREATE_PAYMENT_LINK"
            )

            verification_result = verify_payment(
                transaction,
                execution_result["customer_payment_success"]
            )

            if verification_result["status"] == "FAILED":

                print(
                    "\\n[AGENT] Payment link recovery failed."
                )

                print(
                    "[AGENT] Escalating to merchant."
                )

                escalation_result = escalate_to_merchant(
                    transaction,
                    "Customer did not complete payment through the recovery link."
                )

                execution_result["message"] = (
                    execution_result.get(
                        "message",
                        "Payment link created."
                    )
                    + " "
                    + escalation_result.get(
                        "message",
                        "Merchant escalation created."
                    )
                )

                verification_result = {
                    "verified": False,
                    "status": "ESCALATED",
                }

        else:

            print(
                "\\n[AGENT] Payment link creation failed."
            )

            print(
                "[AGENT] Escalating to merchant."
            )

            escalation_result = escalate_to_merchant(
                transaction,
                "Payment link creation failed."
            )

            execution_result["message"] = (
                execution_result.get(
                    "message",
                    "Payment link creation failed."
                )
                + " "
                + escalation_result.get(
                    "message",
                    "Merchant escalation created."
                )
            )

            verification_result = {
                "verified": False,
                "status": "ESCALATED",
            }

    # --------------------------------------------------
    # STEP 7: DIRECT ESCALATION
    # --------------------------------------------------

    elif decision["action"] == "ESCALATE":

        execution_result = escalate_to_merchant(
            transaction,
            decision["reason"]
        )

        verification_result = {
            "verified": False,
            "status": "ESCALATED",
        }

    # --------------------------------------------------
    # STEP 8: NO ACTION
    # --------------------------------------------------

    else:

        execution_result = {
            "success": True,
            "message": "No recovery action taken."
        }

        verification_result = {
            "verified": False,
            "status": "NO_ACTION",
        }

    # --------------------------------------------------
    # STEP 9: RECORD AUDIT
    # --------------------------------------------------

    audit_record = record_outcome(
        transaction,
        probability,
        decision,
        execution_result,
        verification_result,
    )

    print(
        "\\n[VERIFY] Status:",
        verification_result["status"]
    )

    print(
        f"[RESULT] Recovered: "
        f"₹{audit_record['recovered_amount']:,.2f}"
    )

    print(
        "\\n[AUDIT] Recovery record created."
    )

    print("=" * 60)

    return audit_record


# --------------------------------------------------
# DEMO
# --------------------------------------------------

if __name__ == "__main__":

    demo_transaction = {

        "transaction_id":
            "DEMO_TXN_001",

        "amount":
            2500,

        "payment_method":
            "UPI",

        "failure_reason":
            "NETWORK_ERROR",

        "retry_count":
            0,

        "subscription":
            False,

        "status":
            "FAILED",
        "recovery_outcome":
             True,
    }

    result = recover_transaction(
        demo_transaction
    )

    print("\nFINAL AUDIT RECORD")
    print("-" * 60)

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )