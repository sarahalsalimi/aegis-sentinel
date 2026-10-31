import shutil
import streamlit as st

# Reset config to stable state on initial app load
if "app_bootstrapped" not in st.session_state:
    try:
        shutil.copy("stable_config.json", "current_config.json")
    except Exception:
        pass
    st.session_state.app_bootstrapped = True
    st.session_state.audit_results = {
        "accuracy": 100.0,
        "passed": 25,
        "total": 25,
        "avg_latency": 33,
        "max_latency": 35,
        "sla_breaches": 0,
        "status": "HEALTHY"
    }

import streamlit as st
import json
import model_service
import recovery_agent

st.set_page_config(
    page_title="Aegis Sentinel | AI Recovery Center",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    .hero {
        background: linear-gradient(120deg, #0F172A, #1E3A5F);
        padding: 26px 30px;
        border-radius: 14px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .hero h1 {
        color: white;
        font-size: 2.2rem;
        margin-bottom: 5px;
    }
    .hero p {
        color: #CBD5E1;
        margin-bottom: 0;
    }
    .section-title {
        font-size: 1.2rem;
        font-weight: 700;
        margin-top: 12px;
        margin-bottom: 12px;
    }
    .stage {
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #334155;
        background: #111827;
        text-align: center;
        min-height: 90px;
    }
    .stage-active {
        border: 2px solid #38BDF8;
        background: #172554;
    }
    .stage-done {
        border: 1px solid #16A34A;
        background: #052E1A;
    }
    .stage-label {
        font-size: 0.8rem;
        color: #94A3B8;
    }
    .stage-name {
        font-weight: 700;
        margin-top: 6px;
        color: white;
        font-size: 0.95rem;
    }
    .muted {
        color: #94A3B8;
        font-size: 0.85rem;
    }
    div[data-testid="stMetric"] {
        background: rgba(128, 128, 128, 0.05);
        padding: 12px;
        border-radius: 10px;
        border: 1px solid rgba(128, 128, 128, 0.15);
    }
</style>
""", unsafe_allow_html=True)

if "coordinator" not in st.session_state:
    st.session_state.coordinator = recovery_agent.AegisCoordinator()

if "telemetry" not in st.session_state or st.session_state.telemetry is None:
    st.session_state.telemetry = st.session_state.coordinator.run_telemetry()
    st.session_state.forensics = st.session_state.coordinator.run_forensics()
    st.session_state.lifecycle_stage = "AUDITED" 

defaults = {
    "telemetry": None,
    "forensics": None,
    "recovery_result": None,
    "lifecycle_stage": "READY"
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

def safe_config():
    try:
        return model_service.get_current_config()
    except Exception:
        return {}

def get_system_status(telemetry):
    if telemetry is None:
        return "NOT AUDITED"
    if (
        telemetry["semantic_score"] < 100
        or telemetry["sla_breaches"] > 0
        or not telemetry["all_http_ok"]
    ):
        return "DEGRADED"
    return "HEALTHY"

def render_stage(number, title, description, completed=False, active=False):
    css_class = "stage"
    if completed:
        css_class += " stage-done"
    elif active:
        css_class += " stage-active"

    symbol = "✓" if completed else str(number)

    st.markdown(f"""
        <div class="{css_class}">
            <div class="stage-label">{symbol} · {description}</div>
            <div class="stage-name">{title}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>🛡️ AEGIS SENTINEL</h1>
    <p>Autonomous AI Failure Detection · Cryptographic Investigation · Governed Recovery</p>
    <p class="muted">Multi-Agent SRE Architecture | Local Sovereign AI | Zero Data-Leakage</p>
</div>
""", unsafe_allow_html=True)

current_cfg = safe_config()
telemetry = st.session_state.telemetry
forensics = st.session_state.forensics
recovery = st.session_state.recovery_result
system_status = get_system_status(telemetry)

with st.sidebar:
    st.title("🎮 Control Center")
    st.caption("Manage autonomous governance & recovery cycle.")
    st.markdown("---")

    if st.button("🚨 Inject System Fault", use_container_width=True):
        try:
            with st.spinner("Injecting configuration entropy..."):
                model_service.inject_fault()
                st.session_state.telemetry = st.session_state.coordinator.run_telemetry()
                st.session_state.forensics = st.session_state.coordinator.run_forensics()
                st.session_state.recovery_result = None
                st.session_state.lifecycle_stage = "DETECTED"
            st.rerun()
        except Exception as e:
            st.error(f"Fault injection failed: {e}")

    if st.button("🔍 Run Semantic Audit", use_container_width=True):
        try:
            with st.spinner("Auditing 25 Sovereign Benchmarks (Zero Data-Leakage)..."):
                st.session_state.telemetry = st.session_state.coordinator.run_telemetry()
                st.session_state.forensics = st.session_state.coordinator.run_forensics()
                st.session_state.lifecycle_stage = "AUDITED"
            st.rerun()
        except Exception as e:
            st.error(f"Audit failed: {e}")

    st.markdown("---")
    st.subheader("🔐 Human Authorization")

    admin_grant = st.checkbox(
        "Admin Explicit Authorization",
        value=False,
        help="Required before configuration rollback."
    )

    st.write("")

    if st.button("🔄 Execute Recovery", type="primary", use_container_width=True):
        if st.session_state.telemetry is None:
            st.warning("Run an audit before recovery.")
        else:
            try:
                with st.spinner("Verifying SHA-256 & executing rollback..."):
                    result = st.session_state.coordinator.run_recovery_lifecycle(
                        pre_telemetry=st.session_state.telemetry,
                        admin_authorized=admin_grant
                    )
                    st.session_state.recovery_result = result
                    st.session_state.telemetry = result["telemetry"]
                    st.session_state.forensics = st.session_state.coordinator.run_forensics()

                    if result["verified"]:
                        st.session_state.lifecycle_stage = "RECOVERED"
                    elif result["requires_approval"]:
                        st.session_state.lifecycle_stage = "BLOCKED"
                    else:
                        st.session_state.lifecycle_stage = "RECOVERY_FAILED"

                st.rerun()
            except Exception as e:
                st.error(f"Recovery failed: {e}")

    st.markdown("---")
    st.markdown("### ⚙️ Runtime Parameters")
    st.caption("Inference Engine")
    st.code("Ollama / qwen2.5-coder:latest")
    st.caption("Integrity Baseline")
    sha_short = model_service.EXPECTED_STABLE_HASH[:12] + "..." if model_service.EXPECTED_STABLE_HASH else "Not set"
    st.code(f"SHA-256: {sha_short}")
    st.caption("SLA Cap")
    st.code("15,000 ms")

status_col, version_col = st.columns([2, 1])

with status_col:
    if system_status == "HEALTHY":
        st.success("🟢 SYSTEM HEALTHY — All benchmark checks compliant & validated.")
    elif system_status == "DEGRADED":
        st.error("🔴 SYSTEM DEGRADED — Semantic drift detected despite HTTP 200.")
    else:
        st.info("⚪ SYSTEM READY — Waiting for initial audit.")

with version_col:
    active_v = current_cfg.get("version", "Unknown")
    st.metric(
        "Active Configuration",
        active_v,
        delta="Verified Clean" if active_v == "v1.0-stable" else "Config Tampered",
        delta_color="normal" if active_v == "v1.0-stable" else "inverse"
    )

st.markdown('<div class="section-title">🔄 Recovery Lifecycle</div>', unsafe_allow_html=True)

stage = st.session_state.lifecycle_stage
stage_map = {
    "READY": 0,
    "AUDITED": 1,
    "DETECTED": 2,
    "BLOCKED": 3,
    "RECOVERY_FAILED": 3,
    "RECOVERED": 5
}
progress = stage_map.get(stage, 0)
stages = [
    ("DETECTION", "Failure Detection"),
    ("INVESTIGATION", "Differential Analysis"),
    ("APPROVAL", "Human Authorization"),
    ("RECOVERY", "Cryptographic Rollback"),
    ("VERIFICATION", "Post-Audit Verification")
]

cols = st.columns(5)
for i, (description, title) in enumerate(stages):
    completed = progress > i
    active = progress == i and stage not in ("READY", "RECOVERED")
    with cols[i]:
        render_stage(i + 1, title, description, completed=completed, active=active)

st.markdown("---")

if telemetry is None:
    score_text = "—"
    avg_text = "—"
    max_text = "—"
    sla_text = "—"
    sla_breaches = 0
    score = 0.0
else:
    score = telemetry["semantic_score"]
    score_text = f"{score:.1f}%"
    avg_text = f'{telemetry["avg_latency"]:.0f} ms'
    max_text = f'{telemetry["max_latency"]:.0f} ms'
    sla_breaches = telemetry.get("sla_breaches", 0)
    sla_text = str(sla_breaches)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Semantic Accuracy",
        score_text,
        delta="100% Verified" if score == 100 else ("Degraded State" if telemetry is not None else "Not audited"),
        delta_color="normal" if score == 100 else "inverse"
    )

with c2:
    st.metric("Average Latency", avg_text)

with c3:
    st.metric("Max Latency", max_text)

with c4:
    delta_val = f"{sla_breaches} breaches" if telemetry is not None else None
    st.metric("SLA Breaches (>15s)", sla_text, delta=delta_val, delta_color="inverse" if sla_breaches > 0 else "normal")

if telemetry is not None:
    st.progress(min(score / 100, 1.0))
    st.caption(f'{telemetry["passed_cases"]} of {telemetry["total_cases"]} sovereign benchmark cases passed.')

st.markdown("---")

tab_audit, tab_forensics, tab_governance = st.tabs([
    "📊 Audit & Test Records",
    "🔬 Forensic Differential Traces",
    "📜 Recovery & Governance Attestation"
])

with tab_audit:
    st.subheader("Golden Dataset Audit (Zero Data-Leakage)")
    if telemetry is None:
        st.info("Run an audit to view benchmark results.")
    else:
        records = telemetry["audit_records"]
        passed = [r for r in records if r["valid"]]
        failed = [r for r in records if not r["valid"]]

        a, b, c = st.columns(3)
        a.metric("Passed Cases", len(passed))
        b.metric("Failed Cases", len(failed))
        c.metric("Total Cases", len(records))

        if failed:
            st.error(f"🚨 Silent Failure Confirmed: {len(failed)} cases failed semantic validation while HTTP server reports healthy.")
        else:
            st.success("✅ All benchmark cases validated without semantic or SLA breaches.")

        st.markdown("### Individual Forensic Records")
        for record in records:
            label = "PASS" if record["valid"] else "FAIL"
            with st.expander(f'{record["id"]} | {record["category"]} | Status: {label} ({record["latency"]:.0f}ms)'):
                left, right = st.columns(2)
                with left:
                    st.caption("Expected Sovereign Output")
                    st.json(record["expected"])
                with right:
                    st.caption("Actual Model Output")
                    try:
                        st.json(json.loads(record["output"]))
                    except (json.JSONDecodeError, TypeError):
                        st.code(str(record["output"]), language="text")

                st.markdown(f'**Latency:** {record["latency"]:.1f} ms | **HTTP Response:** {record["status_code"]}')
                if record["valid"]:
                    st.success("Semantic verification passed.")
                else:
                    st.error(f'Rejection Reason: {record["reason"]}')

with tab_forensics:
    st.subheader("Root Cause Differential Attribution")
    if forensics is None:
        st.info("Run an audit to isolate root-cause evidence.")
    else:
        if forensics["anomaly_isolated"]:
            st.error("🚨 Configuration Drift & Inference Entropy Isolated")
            for evidence in forensics["attribution_evidence"]:
                st.warning(f"• {evidence}")
        else:
            st.success("✅ System Clean: Runtime configuration matches verified baseline.")

        st.markdown("### Configuration Differencing")
        stable_cfg = {}
        try:
            with open("stable_config.json", "r", encoding="utf-8") as f:
                stable_cfg = json.load(f)
        except (OSError, json.JSONDecodeError):
            st.error("Stable baseline unreadable.")

        left, right = st.columns(2)
        with left:
            st.markdown("**Active Environment Config:**")
            st.json(current_cfg)
        with right:
            st.markdown("**Stable Baseline:**")
            st.json(stable_cfg)

with tab_governance:
    st.subheader("Human-in-the-Loop Governance & Attestation")
    if recovery is None:
        st.info("No recovery action recorded in this cycle.")
    else:
        if recovery["verified"]:
            st.success("🎉 SYSTEM RECOVERED & CRYPTOGRAPHICALLY VERIFIED")
            st.markdown(f'### {recovery["certificate"]}')
            x, y, z = st.columns(3)
            x.metric("Pre-Recovery Score", f'{recovery["pre_score"]:.1f}%')
            y.metric("Post-Recovery Score", f'{recovery["post_score"]:.1f}%')
            z.metric("Restored Cases", recovery["cases_restored"])
            st.info(f"🔒 **Cryptographic Integrity:** SHA-256 match confirmed (`{model_service.EXPECTED_STABLE_HASH[:16]}...`) prior to atomic replacement.")
        elif recovery["requires_approval"]:
            st.warning("🛑 GOVERNANCE POLICY GATE TRIGGERED")
            st.markdown(f'### {recovery["certificate"]}')
            st.error("The Autonomous Agent is restricted from mutating production state without explicit human approval.")
        else:
            st.error("❌ RECOVERY INCOMPLETE")
            st.markdown(f'### {recovery["certificate"]}')

st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#94A3B8; padding:10px;">
    <b>AEGIS SENTINEL</b> · Sovereign AI Governance & Autonomous SRE<br>
    <small>Local Ollama Engine · SHA-256 Verified · Policy Gated · Closed-Loop Recovery</small>
</div>
""", unsafe_allow_html=True)
