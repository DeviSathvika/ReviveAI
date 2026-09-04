# ReviveAI

### AI-powered, policy-controlled revenue recovery for failed payments

ReviveAI is an AI revenue recovery agent that identifies failed payments worth recovering, predicts the probability of successful recovery, selects a bounded intervention, executes the approved action, verifies the outcome, and records the result.

> **Detect → Diagnose → Decide → Act → Verify → Measure**

## Why ReviveAI?

Failed payments are not all the same. A transient network error may be worth retrying immediately, while an expired card, suspected fraud event, or high-value transaction requires a different response.

ReviveAI treats recovery as a **decisioning and controlled-execution problem**, not simply a retry loop.

The system combines:

- Machine-learning recovery prediction
- Failure-specific recovery policies
- Hard safety guardrails
- Bounded execution tools
- Outcome verification
- Recovery and audit analytics

## System Architecture

```text
Merchant Transaction Data
          │
          ▼
┌──────────────────────────┐
│ Revenue-at-Risk Detector │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ AI Recovery Prediction   │
│ Logistic Regression      │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Policy / Guardrail Layer │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Recovery Agent           │
│ Retry / Link / Escalate  │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Provider Simulation      │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Verify + Audit + Measure │
└──────────────────────────┘
```

### Core design principle

**AI recommends. Policy authorizes. Tool executes. Agent verifies. Audit trail records.**

This separation keeps probabilistic model output from directly authorizing money-moving actions.

## Recovery Decisioning

ReviveAI uses a failure-specific policy rather than applying one threshold to every payment failure.

| Failure reason | Recovery strategy |
|---|---|
| `NETWORK_ERROR` | High confidence → retry; medium confidence → payment link; otherwise escalate |
| `TIMEOUT` | High confidence → retry; medium confidence → payment link; otherwise escalate |
| `BANK_DECLINE` | Higher confidence → payment link; otherwise escalate |
| `INSUFFICIENT_FUNDS` | Escalate |
| `EXPIRED_CARD` | Escalate |
| `FRAUD_SUSPECTED` | Block automated recovery and escalate |

### Hard guardrails

- Maximum retry count: **2**
- Transactions above **₹50,000** require merchant approval
- Suspected fraud cannot trigger automated recovery
- Successful transactions cannot enter the recovery path
- Unknown failure types fall back to conservative policy behavior
- Failed execution is verified and escalated rather than repeatedly retried

## Machine Learning

The current baseline is a **Logistic Regression** classifier trained only on failed payments.

Features:

- Transaction amount
- Payment method
- Failure reason
- Previous retry count
- Subscription indicator

The synthetic ground-truth recovery outcome is used only as the training/evaluation target and provider-simulation result; it is **not used as an ML feature**.

### Model evaluation

| Metric | Result |
|---|---:|
| Accuracy | 69.90% |
| Precision | 66.00% |
| Recall | 72.53% |
| F1 | 69.11% |
| ROC-AUC | 79.12% |

The model is intentionally treated as a decision input rather than an unrestricted autonomous authority.

## Batch Results

The included synthetic dataset contains **5,000 transactions**, of which **978 failed payments** entered the recovery workflow.

| Metric | Result |
|---|---:|
| Failed payments analyzed | **978** |
| Revenue at risk | **₹72.58 lakh** |
| Revenue recovered | **₹17.15 lakh** |
| Recovery rate | **23.63%** |
| Successful recoveries | **239** |
| Automated actions | **328** |
| Suspected fraud cases blocked | **69** |

These figures come from the included deterministic synthetic-data simulation and are intended to demonstrate the product workflow, decisioning, and measurement pipeline—not production payment performance.

## Example: A Recoverable Payment

For a failed payment such as `TX00018`:

```text
Amount:              ₹887.13
Failure:             TIMEOUT
AI recovery score:   83.94%
Decision:             RETRY_PAYMENT
Policy status:        ALLOWED
Verification:         SUCCESS
Recovered:            ₹887.13
```

The important behavior is that the agent does not stop at prediction. It executes a permitted action, verifies the resulting payment state, and records the recovered amount.

## Graceful Failure

Recovery actions can fail. ReviveAI handles this explicitly.

```text
AI decision
    ↓
Retry / Payment Link
    ↓
Execution fails
    ↓
Verify → FAILED
    ↓
Escalate to merchant
    ↓
₹0 recovered + audit record
```

This prevents the agent from blindly repeating an unsuccessful money action.

## Auditability

Each recovery decision records information including:

- Transaction ID
- Amount
- Failure reason
- Model recovery probability
- Selected action
- Policy status
- Decision reason
- Execution result
- Verification status
- Recovered amount
- Timestamp

This makes each automated recovery decision explainable after the fact.

## Dashboard

The React dashboard provides:

- Revenue-at-risk and recovered-revenue metrics
- Recovery queue
- Transaction-level AI decisions
- Expected recovery value
- Recovery execution controls
- Action distribution analytics
- Failure-reason analytics
- Policy and safety views
- Audit trail

## Tech Stack

**Frontend**
- React
- Vite
- Recharts

**Backend**
- Python
- FastAPI
- Uvicorn

**AI / Analytics**
- scikit-learn
- Logistic Regression
- pandas
- NumPy

**Data**
- Deterministic synthetic transaction dataset
- CSV-based local persistence for the buildathon prototype

## Project Structure

```text
ReviveAI/
├── agent/
│   ├── decision_engine.py
│   ├── recovery_agent.py
│   └── transaction_processor.py
├── analytics/
│   ├── policy_simulator.py
│   └── recovery_analysis.py
├── api/
│   └── main.py
├── data/
│   ├── customers.csv
│   ├── generate_dataset.py
│   ├── recovery_results.csv
│   └── transactions.csv
├── models/
│   └── recovery_model.py
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── App.css
    │   └── api/reviveApi.js
    │   └── ...
    └── package.json
```

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/DeviSathvika/ReviveAI.git
cd ReviveAI
```

### 2. Create and activate the Python environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install backend dependencies

```bash
pip install fastapi uvicorn pandas numpy scikit-learn
```

### 4. Start the API

```bash
uvicorn api.main:app --reload
```

The API runs on `http://127.0.0.1:8000` by default.

### 5. Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite will provide the local dashboard URL.

## API Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Backend health check |
| `GET /api/dashboard` | Dashboard metrics |
| `GET /api/transactions` | Recovery queue |
| `GET /api/transactions/{transaction_id}` | Transaction details |
| `POST /api/recovery/analyze` | Predict and select a policy action |
| `POST /api/recovery/execute` | Execute the bounded recovery workflow |
| `GET /api/analytics/actions` | Action distribution |
| `GET /api/analytics/failure-reasons` | Failure analysis |
| `GET /api/analytics/policy` | Policy metrics |
| `GET /api/analytics/fraud` | Fraud-safety metrics |

## What Broke at 2 AM?

One of the most important engineering lessons in this prototype was that **a recovery prediction is not the same thing as a safe recovery action**.

The recovery model can produce a high probability, but the system still needs independent controls around retries, fraud, transaction value, and execution outcomes.

The resulting architecture deliberately separates prediction from authorization:

```text
Model score ≠ permission to move money

Model → Policy → Guardrails → Tool → Verification
```

This also gives the system a clean failure mode: if an execution attempt fails, the agent verifies the failure and escalates instead of entering an uncontrolled retry loop.

## Limitations and Production Next Steps

This is a buildathon prototype. The transaction provider is simulated and the dataset is synthetic.

A production implementation would add:

- Real payment-provider webhooks and idempotency controls
- Persistent PostgreSQL-backed transaction and audit storage
- Merchant-configurable recovery policies
- Real customer communication channels
- Model monitoring and drift detection
- Offline policy evaluation and A/B testing
- Stronger fraud/risk signals
- Role-based approval workflows for high-value actions
- Production authentication, authorization, secrets management, and observability

## Why the Approach Matters

ReviveAI is designed around a simple operational objective:

> **Recover more revenue without giving an AI unrestricted permission to move money.**

The prototype demonstrates the complete closed loop:

**Detect → Diagnose → Decide → Act → Verify → Measure**

---

Built for the **Razorpay AI Buildathon 2026 — Track 03: AI Revenue Recovery**.