import os
import sys

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


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
# REVIVEAI IMPORTS
# --------------------------------------------------

from models.recovery_model import (
    predict_recovery_probability
)

from agent.decision_engine import (
    decide_action
)

from agent.recovery_agent import (
    recover_transaction
)


# --------------------------------------------------
# FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="ReviveAI API",
    description=(
        "AI-powered revenue recovery system "
        "for failed payments."
    ),
    version="1.0.0"
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# FILE PATHS
# --------------------------------------------------

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


# --------------------------------------------------
# DATA HELPERS
# --------------------------------------------------

def get_transactions():
    """Load the source transaction dataset."""

    if not os.path.exists(TRANSACTIONS_PATH):
        raise FileNotFoundError(
            "transactions.csv not found."
        )

    return pd.read_csv(
        TRANSACTIONS_PATH
    )


def get_recovery_results():
    """Load generated recovery/audit results."""

    if not os.path.exists(
        RECOVERY_RESULTS_PATH
    ):
        return None

    return pd.read_csv(
        RECOVERY_RESULTS_PATH
    )


def prepare_transaction(row):
    """
    Convert a dataframe row into the transaction
    structure expected by ReviveAI.

    recovery_outcome is retained internally for
    simulator/provider behavior only. It is never
    exposed by the public analysis response.
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

        "recovery_outcome":
            row["recovery_outcome"],
    }


def public_transaction(transaction):
    """
    Remove internal evaluation/provider data before
    returning a transaction to the frontend.
    """

    return {
        key: value
        for key, value in transaction.items()
        if key != "recovery_outcome"
    }


def serialize_value(value):
    """Convert pandas/numpy values into JSON-safe values."""

    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value


def serialize_record(record):
    """Convert a pandas row into a JSON-safe dictionary."""

    return {
        key: serialize_value(value)
        for key, value in record.items()
    }


# --------------------------------------------------
# REQUEST MODEL
# --------------------------------------------------

class RecoveryRequest(BaseModel):
    transaction_id: str


# --------------------------------------------------
# HEALTH / ROOT
# --------------------------------------------------

@app.get("/")
def root():

    return {
        "name": "ReviveAI",
        "description": (
            "AI Revenue Recovery Agent"
        ),
        "status": "online",
        "workflow": [
            "Detect",
            "Diagnose",
            "Decide",
            "Act",
            "Verify",
            "Measure",
        ],
    }


@app.get("/api/health")
def health():

    return {
        "status": "healthy",
        "service": "reviveai-api",
        "version": "1.0.0",
    }


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.get("/api/dashboard")
def dashboard():

    try:
        results = get_recovery_results()

        if results is None:
            return {
                "status": "no_results",
                "message": (
                    "Run transaction_processor.py "
                    "to generate recovery_results.csv."
                ),
            }

        transactions_analyzed = len(results)

        revenue_at_risk = float(
            results["amount"].sum()
        )

        revenue_recovered = float(
            results["recovered_amount"].sum()
        )

        recovery_rate = (
            revenue_recovered /
            revenue_at_risk
            if revenue_at_risk > 0
            else 0
        )

        successful_recoveries = int(
            (
                results["verification_status"]
                == "SUCCESS"
            ).sum()
        )

        automated_actions = int(
            results["action"].isin(
                [
                    "RETRY_PAYMENT",
                    "CREATE_PAYMENT_LINK",
                ]
            ).sum()
        )

        escalations = int(
            (
                results["verification_status"]
                == "ESCALATED"
            ).sum()
        )

        blocked_actions = int(
            (
                results["policy_status"]
                == "BLOCKED"
            ).sum()
        )

        approval_required = int(
            (
                results["policy_status"]
                == "APPROVAL_REQUIRED"
            ).sum()
        )

        return {
            "status": "ready",

            "transactions_analyzed":
                transactions_analyzed,

            "revenue_at_risk":
                round(revenue_at_risk, 2),

            "revenue_recovered":
                round(revenue_recovered, 2),

            "recovery_rate":
                round(recovery_rate, 4),

            "recovery_rate_percent":
                round(
                    recovery_rate * 100,
                    2
                ),

            "successful_recoveries":
                successful_recoveries,

            "automated_actions":
                automated_actions,

            "escalations":
                escalations,

            "blocked_actions":
                blocked_actions,

            "approval_required":
                approval_required,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# TRANSACTION LIST
# --------------------------------------------------

@app.get("/api/transactions")
def transactions(
    limit: int = 100,
    offset: int = 0,
):

    try:

        if limit < 1 or limit > 1000:
            raise HTTPException(
                status_code=400,
                detail="limit must be between 1 and 1000."
            )

        if offset < 0:
            raise HTTPException(
                status_code=400,
                detail="offset cannot be negative."
            )

        results = get_recovery_results()

        if results is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Recovery results not found. "
                    "Run transaction_processor.py first."
                )
            )

        columns = [
            "transaction_id",
            "amount",
            "failure_reason",
            "recovery_probability",
            "action",
            "policy_status",
            "verification_status",
            "recovered_amount",
        ]

        available_columns = [
            column
            for column in columns
            if column in results.columns
        ]

        data = results[
            available_columns
        ].iloc[
            offset: offset + limit
        ].copy()

        data = data.fillna("")

        return {
            "count": len(results),
            "limit": limit,
            "offset": offset,
            "transactions":
                data.to_dict(
                    orient="records"
                ),
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# SINGLE TRANSACTION
# --------------------------------------------------

@app.get(
    "/api/transactions/{transaction_id}"
)
def transaction_detail(
    transaction_id: str
):

    try:

        results = get_recovery_results()

        if results is None:
            raise HTTPException(
                status_code=404,
                detail="Recovery results not found."
            )

        matches = results[
            results["transaction_id"].astype(str)
            == str(transaction_id)
        ]

        if matches.empty:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Transaction "
                    f"{transaction_id} not found."
                )
            )

        return serialize_record(
            matches.iloc[0]
        )

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# AI ANALYSIS
# --------------------------------------------------

@app.post(
    "/api/recovery/analyze"
)
def analyze_recovery(
    request: RecoveryRequest
):

    try:

        transactions = get_transactions()

        matches = transactions[
            transactions[
                "transaction_id"
            ].astype(str)
            == str(request.transaction_id)
        ]

        if matches.empty:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Transaction "
                    f"{request.transaction_id} "
                    f"not found."
                )
            )

        row = matches.iloc[0]

        transaction = prepare_transaction(
            row
        )

        probability = (
            predict_recovery_probability(
                transaction
            )
        )

        decision = decide_action(
            transaction,
            probability
        )

        return {
            "transaction":
                public_transaction(
                    transaction
                ),

            "recovery_probability":
                round(probability, 4),

            "recovery_probability_percent":
                round(
                    probability * 100,
                    2
                ),

            "action":
                decision["action"],

            "policy_status":
                decision["policy_status"],

            "reason":
                decision["reason"],
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# EXECUTE RECOVERY
# --------------------------------------------------

@app.post(
    "/api/recovery/execute"
)
def execute_recovery(
    request: RecoveryRequest
):

    try:

        transactions = get_transactions()

        matches = transactions[
            transactions[
                "transaction_id"
            ].astype(str)
            == str(request.transaction_id)
        ]

        if matches.empty:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Transaction "
                    f"{request.transaction_id} "
                    f"not found."
                )
            )

        row = matches.iloc[0]

        transaction = prepare_transaction(
            row
        )

        audit_record = recover_transaction(
            transaction
        )

        return {
            "success": True,
            "audit_record":
                audit_record,
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# ACTION ANALYTICS
# --------------------------------------------------

@app.get(
    "/api/analytics/actions"
)
def action_analytics():

    try:

        results = get_recovery_results()

        if results is None:
            raise HTTPException(
                status_code=404,
                detail="Recovery results not found."
            )

        grouped = (
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
                )
            )
            .reset_index()
        )

        grouped["recovery_rate"] = (
            grouped["revenue_recovered"]
            /
            grouped["revenue_at_risk"]
        ).fillna(0)

        grouped = grouped.fillna(0)

        return {
            "actions":
                grouped.to_dict(
                    orient="records"
                )
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# FAILURE-REASON ANALYTICS
# --------------------------------------------------

@app.get(
    "/api/analytics/failure-reasons"
)
def failure_reason_analytics():

    try:

        results = get_recovery_results()

        if results is None:
            raise HTTPException(
                status_code=404,
                detail="Recovery results not found."
            )

        grouped = (
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
                    lambda x: int(
                        (x > 0).sum()
                    )
                )
            )
            .reset_index()
        )

        grouped["recovery_rate"] = (
            grouped["revenue_recovered"]
            /
            grouped["revenue_at_risk"]
        ).fillna(0)

        grouped = grouped.fillna(0)

        return {
            "failure_reasons":
                grouped.to_dict(
                    orient="records"
                )
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# POLICY ANALYTICS
# --------------------------------------------------

@app.get(
    "/api/analytics/policy"
)
def policy_analytics():

    try:

        results = get_recovery_results()

        if results is None:
            raise HTTPException(
                status_code=404,
                detail="Recovery results not found."
            )

        grouped = (
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
                )
            )
            .reset_index()
        )

        grouped["recovery_rate"] = (
            grouped["revenue_recovered"]
            /
            grouped["revenue_at_risk"]
        ).fillna(0)

        grouped = grouped.fillna(0)

        return {
            "policy":
                grouped.to_dict(
                    orient="records"
                )
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# FRAUD ANALYTICS
# --------------------------------------------------

@app.get(
    "/api/analytics/fraud"
)
def fraud_analytics():

    try:

        results = get_recovery_results()

        if results is None:
            raise HTTPException(
                status_code=404,
                detail="Recovery results not found."
            )

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
                int(len(fraud)),

            "fraud_blocked":
                int(len(blocked)),

            "fraud_recovery_attempts":
                int(
                    len(fraud) - len(blocked)
                ),

            "fraud_recovered":
                round(
                    float(
                        fraud[
                            "recovered_amount"
                        ].sum()
                    ),
                    2
                ),
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# START DEVELOPMENT SERVER
# --------------------------------------------------

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
