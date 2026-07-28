# Airplane Ticket Concierge Agent (SkyConcierge)

An enterprise-grade autonomous AI travel concierge system built with the [Google Antigravity (AGY) SDK](file:///usr/local/google/home/gaowen/.gemini/config/plugins/google-antigravity-sdk/skills/google-antigravity-sdk/SKILL.md).

SkyConcierge features **Infrastructure as Code (IaC) via Terraform**, **OpenTelemetry-compatible distributed tracing**, **multi-agent orchestration**, **task-based model routing**, **declarative security guardrails**, **human-in-the-loop (HITL) hooks**, **persistent SQLite database storage**, **history context compaction**, and **async memory operations**.

---

## Key Architectural Capabilities

### 🏗️ 1. Infrastructure as Code (IaC) via Terraform
- **Complete GCP Provisioning (`terraform/`)**: Automated resource provisioning using Terraform (`main.tf`, `variables.tf`, `outputs.tf`).
- **GCP Resources Managed**:
  - **Cloud Run v2**: Serverless container execution with auto-scaling.
  - **Secret Manager**: Secure API key storage and IAM secret accessor bindings.
  - **Artifact Registry**: Docker container image repository (`skyconcierge-repo`).
  - **Cloud Storage Bucket**: Versioned GCS bucket for persistent agent state and backups.
  - **IAM & Least-Privilege**: Dedicated Service Account (`skyconcierge-agent-sa`).

### 🌐 2. OpenTelemetry Distributed Tracing & Span Linkage
- **Trace Context Propagation**: Propagates a root `trace_id` across turns, subagents, and tool calls using Python `contextvars`.
- **Parent-Child Span Linkage (`TraceSpan`)**: Automatically links `parent_span_id` -> `span_id` across nested execution blocks (Orchestrator -> Subagent -> Tool).
- **Intent vs. Outcome Observability**: Every log entry records `intent`, `action`, `outcome`, `duration_ms`, `trace_id`, `span_id`, and `parent_span_id`.
- **PII Redactor (`PIIRedactor`)**: Masks passport numbers (`P123****`), credit cards, and SSNs in log outputs.

### 💾 3. Persistent SQLite Database Storage
- **Database Backend (`concierge.db`)**: Replaces transient in-memory dictionaries with a persistent, thread-safe SQLite database handled asynchronously via `database.py`.
- **Survives Restart**: Flight inventories, seat allocations, PNR booking records, traveler profiles, and compaction summaries survive application restarts.

### 🧠 4. History Context Compaction & Trajectory Persistence
- **Context Compaction Hook (`@hooks.on_compaction`)**: Listens to context window compaction events.
- **Trajectory Persistence (`save_dir` & `conversation_id`)**: Persists conversation trajectories to disk for session resumption.
- **Memory Compaction Tool (`compact_conversation_memory`)**: Summarizes long turn histories into structured state memory.

### 🤖 5. Multi-Agent Delegation Pattern
- **Main Orchestrator (`SkyConcierge`)**: Coordinates specialized subagent workers.
- **Flight Search Specialist (`FlightSearchSpecialist`)**: Subagent for querying schedules, seat maps, and baggage allowances.
- **Booking Specialist (`BookingSpecialist`)**: Subagent for passenger identity verification, PNR creation, and cancellation.

### 🎯 6. Model Routing & Security Guardrails
- **Fast Tier (`gemini-3.5-flash`)**: Low-latency model for read-only lookups.
- **Reasoning Tier (`gemini-3.5-pro`)**: High-precision model for identity validation and reservations.
- **Human-In-The-Loop (HITL) Approval Hooks**: Intercepts high-stakes transactions (`reserve_ticket`, `cancel_booking`) for explicit user confirmation.

---

## Project Structure

```text
.
├── README.md           # Architecture, IaC, tracing, & usage guide
├── requirements.txt    # Package dependencies
├── agent.py            # Main SkyConcierge orchestrator & interactive CLI entry point
├── database.py         # Persistent SQLite database storage & async CRUD queries
├── memory.py           # Async user memory persistence & history context compaction
├── subagents.py        # Search and Booking specialist subagents & model router
├── security.py         # Declarative policy rules, passport & PNR guardrails
├── logging_tracing.py  # OpenTelemetry distributed tracing, TraceSpan context propagation, & PII redactor
├── secrets_manager.py  # GCP Secret Manager & env credential store
├── hooks.py            # Compaction hook, HITL approval handler, LLM recovery hooks
├── tools.py            # Database-backed flight search, seat map, reservation, & baggage tools
├── test_eval_suite.py  # Automated 6-category evaluation test suite
├── terraform/          # Infrastructure as Code (IaC) Terraform configurations
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tfvars.example
│   └── README.md
└── example_usage.py    # Feature demonstration script
```

---

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Gemini API Key

```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

### 3. Deploy Infrastructure via Terraform (Optional)

```bash
cd terraform
terraform init
terraform apply
```

---

## License

Built with Google Antigravity SDK. Internal Project Template.
