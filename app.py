from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from signal_controller import SignalController
from agent import choose_road
from traffic_simulation import TrafficSimulation, ROADS
from components.intersection import render_intersection
from adaptive_timing import get_signal_timing


# =========================================================
# 1. PAGE CONFIGURATION AND STYLING
# =========================================================

st.set_page_config(
    page_title="SmartFlow AI | Traffic Management",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

css_path = Path(__file__).parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )


# =========================================================
# 2. SESSION STATE
# =========================================================

def initialize_state():
    defaults = {
        "simulation": TrafficSimulation(),
        "history": [],
        "active_emergency": None,
        "pedestrian_count": 0,
        "signal_controller": SignalController(),
        "control_mode": "AI Automatic Mode",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


initialize_state()

simulation = st.session_state.simulation
controller = st.session_state.signal_controller


# =========================================================
# 3. COMMON HELPER FUNCTIONS
# =========================================================

def page_header(title, subtitle):
    st.markdown(
        f"""
        <div style="margin-bottom:25px;">
            <div style="font-size:30px;font-weight:800;color:#e8f0fa;">
                {title}
            </div>
            <div style="font-size:14px;color:#91a4ba;margin-top:6px;">
                {subtitle}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card(title, body):
    st.markdown(
        f"""
        <div class="sf-card">
            <div style="font-size:17px;font-weight:700;color:#e8f0fa;">
                {title}
            </div>
            <div class="sf-muted" style="margin-top:8px;">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_scores():
    data = simulation.get_normalized_data()
    _, scores = choose_road(data, simulation.current_road)
    return scores


def record_cycle(selected_road, scores, green_time=None, emergency=None):
    """Advance the traffic simulation and save a snapshot for analytics."""
    simulation.step(selected_road)
    snapshot = simulation.get_state()
    snapshot["scores"] = scores
    if green_time is not None:
        snapshot["green_time"] = green_time
    if emergency is not None:
        snapshot["emergency"] = emergency
    st.session_state.history.append(snapshot)


def reset_project():
    st.session_state.simulation = TrafficSimulation()
    st.session_state.history = []
    st.session_state.active_emergency = None
    st.session_state.pedestrian_count = 0
    st.session_state.signal_controller = SignalController()


# =========================================================
# 4. SIDEBAR NAVIGATION
# =========================================================

with st.sidebar:
    st.markdown(
        """
        <div style="padding:12px 4px 22px 4px;">
            <div style="font-size:27px;font-weight:800;color:#20c9b0;">
                🚦 SMARTFLOW AI
            </div>
            <div style="color:#91a4ba;font-size:12px;margin-top:5px;">
                INTELLIGENT TRAFFIC MANAGEMENT
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    st.caption("MAIN MENU")

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Live Simulation",
            "Signal Control",
            "Emergency Management",
            "Pedestrian Management",
            "AI Decision Engine",
            "Analytics & Reports",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown(
        """
        <div style="padding:10px 4px;">
            <div style="color:#20c997;font-weight:700;font-size:13px;">
                ● SYSTEM ONLINE
            </div>
            <div style="color:#91a4ba;font-size:11px;margin-top:5px;">
                SmartFlow AI v3.0
            </div>
            <div style="color:#91a4ba;font-size:11px;">
                Four-way intersection · Simulation mode
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 5. CENTRAL SIGNAL TIMER
#    The controller advances in ONE place only. This avoids
#    multiple pages accidentally advancing it twice.
# =========================================================

if controller.is_running:
    st_autorefresh(interval=1000, key="smartflow_global_signal_clock")
    controller.advance_one_second()

# Pedestrian WALK is true only during the actual PED-WALK phase.
st.session_state.pedestrian_crossing_active = (
    controller.phase == "PED-WALK"
)
st.session_state.pedestrian_crossing_timer = (
    controller.remaining_seconds if controller.phase == "PED-WALK" else 0
)

# When the walk phase finishes, clear the waiting pedestrian group.
if (
    not controller.is_running
    and not controller.pedestrian_request_pending
    and not st.session_state.pedestrian_crossing_active
    and controller.phase == "RED"
):
    # Only clear after a crossing has actually been completed.
    if st.session_state.get("pedestrian_crossing_was_active", False):
        st.session_state.pedestrian_count = 0
        st.session_state.pedestrian_crossing_was_active = False

if controller.phase == "PED-WALK":
    st.session_state.pedestrian_crossing_was_active = True


# Refresh current references after any reset/action.
simulation = st.session_state.simulation
controller = st.session_state.signal_controller
state = simulation.get_state()
traffic_data = simulation.get_normalized_data()
current_scores = get_scores()


# =========================================================
# 6. OVERVIEW
# =========================================================

if page == "Overview":
    page_header(
        "Traffic Overview",
        "Monitor the four-way intersection and intelligent traffic conditions.",
    )

    st.markdown(
        """
        <div class="sf-card">
            <div style="font-size:13px;color:#91a4ba;">INTERSECTION STATUS</div>
            <div style="font-size:23px;font-weight:800;color:#20c997;margin-top:7px;">
                ● SYSTEM OPERATIONAL
            </div>
            <div class="sf-muted" style="margin-top:5px;">
                Monitoring North, South, East and West roads
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("System Statistics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Simulation Cycle", state["cycle"])
    c2.metric("Vehicles in Queue", sum(state["vehicles"].values()))
    c3.metric("Vehicles Arrived", state["total_arrived"])
    c4.metric("Vehicles Served", state["total_served"])

    st.divider()
    st.subheader("Live Road Conditions")
    cols = st.columns(4)

    signal_state = controller.get_state()
    for index, road in enumerate(ROADS):
        with cols[index]:
            phase = signal_state["phase"]
            active = signal_state["current_road"] == road
            if active and phase == "GREEN":
                signal_label, signal_color = "🟢 GREEN", "#20c997"
            elif active and phase == "YELLOW":
                signal_label, signal_color = "🟡 YELLOW", "#ffc857"
            else:
                signal_label, signal_color = "🔴 RED", "#ff5d6c"

            st.markdown(
                f"""
                <div class="sf-card">
                    <div style="color:#91a4ba;font-size:12px;">{road.upper()} ROAD</div>
                    <div style="font-size:25px;font-weight:800;color:#e8f0fa;margin-top:10px;">
                        {state['vehicles'][road]}
                    </div>
                    <div class="sf-muted">Vehicles waiting</div>
                    <div style="font-weight:700;color:{signal_color};margin-top:12px;">
                        {signal_label}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.progress(
                min(max(current_scores[road] / 100, 0.0), 1.0),
                text=f"Congestion: {current_scores[road]:.1f}/100",
            )
            st.caption(f"Waiting time: {state['waiting_time'][road]} seconds")

    st.divider()
    st.subheader("Quick Simulation Controls")
    left, right = st.columns(2)

    with left:
        if st.button("▶ Run Next Cycle", type="primary", use_container_width=True):
            if controller.is_running:
                st.warning("Wait for the current signal sequence to finish.")
            else:
                selected, scores = choose_road(
                    simulation.get_normalized_data(),
                    simulation.current_road,
                    emergency=st.session_state.active_emergency,
                    pedestrian_count=st.session_state.pedestrian_count,
                )
                record_cycle(selected, scores)
                st.rerun()

    with right:
        if st.button("↻ Reset Simulation", use_container_width=True):
            reset_project()
            st.rerun()

    st.divider()
    st.subheader("Current Signal Decision")
    if signal_state["is_running"]:
        st.info(
            f"{signal_state['phase']} phase — "
            f"{signal_state['current_road'] or 'Pedestrian crossing'} — "
            f"{signal_state['remaining_seconds']} seconds remaining."
        )
    else:
        st.info("The controller is idle. Open Signal Control to start a signal cycle.")


# =========================================================
# 7. LIVE SIMULATION
# =========================================================

elif page == "Live Simulation":
    page_header(
        "Live Traffic Simulation",
        "Visual monitoring of signal phases and vehicle queues.",
    )

    st.subheader("Live Intersection View")
    render_intersection(state, controller.get_state())

    signal_state = controller.get_state()
    c1, c2, c3 = st.columns(3)
    c1.metric("Signal Phase", signal_state["phase"])
    c2.metric("Active Road", signal_state["current_road"] or "None")
    c3.metric("Time Remaining", f"{signal_state['remaining_seconds']} sec")

    st.divider()
    st.subheader("Current Vehicle Queues")
    queue_cols = st.columns(4)
    for index, road in enumerate(ROADS):
        with queue_cols[index]:
            st.metric(f"{road} Road", state["vehicles"][road], "vehicles waiting")

    st.subheader("Simulation Information")
    st.write(f"Current simulation cycle: **{state['cycle']}**")
    st.write(f"Total vehicles served: **{state['total_served']}**")
    st.write(f"Total vehicles arrived: **{state['total_arrived']}**")


# =========================================================
# 8. SIGNAL CONTROL
# =========================================================

elif page == "Signal Control":
    page_header(
        "Traffic Signal Control",
        "Choose AI-based or manual control and monitor the timed signal sequence.",
    )

    st.subheader("Signal Control Mode")
    control_mode = st.radio(
        "Choose control mode:",
        ["AI Automatic Mode", "Manual Mode"],
        horizontal=True,
        key="control_mode",
    )

    if control_mode == "AI Automatic Mode":
        selected_road, scores = choose_road(
            simulation.get_normalized_data(),
            simulation.current_road,
            emergency=st.session_state.active_emergency,
            pedestrian_count=st.session_state.pedestrian_count,
        )
    else:
        selected_road = st.selectbox("Select Road", ROADS)
        scores = get_scores()

    green_time = get_signal_timing(scores, selected_road)

    st.divider()
    st.subheader("AI Signal Recommendation")
    col1, col2 = st.columns(2)
    col1.metric("Selected Road", selected_road)
    col2.metric("Recommended Green Time", f"{green_time} sec")

    signal_state = controller.get_state()

    if not signal_state["is_running"]:
        if st.button(
            "▶ Start Signal",
            type="primary",
            use_container_width=True,
        ):
            if controller.start(selected_road, green_time):
                record_cycle(selected_road, scores, green_time=green_time)
                st.rerun()
            else:
                st.warning("The signal controller is not ready. Please try again.")
    else:
        st.subheader("Live Signal Countdown")
        phase = signal_state["phase"]
        phase_colors = {
            "GREEN": "#16A34A",
            "YELLOW": "#EAB308",
            "ALL-RED": "#DC2626",
            "PED-WALK": "#20c997",
            "RED": "#DC2626",
        }
        phase_color = phase_colors.get(phase, "#DC2626")
        label = signal_state["current_road"] or (
            "Pedestrian Crossing" if phase == "PED-WALK" else "Intersection"
        )

        st.markdown(
            f"""
            <div class="sf-card" style="text-align:center;">
                <h2 style="color:{phase_color};">{phase}</h2>
                <h3>{label}</h3>
                <h1>{signal_state['remaining_seconds']} SEC</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

        duration_by_phase = {
            "GREEN": signal_state["green_duration"],
            "YELLOW": controller.yellow_duration,
            "ALL-RED": controller.all_red_duration,
            "PED-WALK": controller.pedestrian_walk_duration,
        }
        total_duration = duration_by_phase.get(phase, 1)
        progress = (
            signal_state["remaining_seconds"] / total_duration
            if total_duration > 0 else 0
        )
        st.progress(min(max(progress, 0.0), 1.0))

        if phase == "PED-WALK":
            st.success("Pedestrians have the right of way. All vehicle roads remain RED.")
        elif phase == "ALL-RED":
            st.warning("All vehicle signals are RED for the safety clearance interval.")
        elif phase == "YELLOW":
            st.warning("Yellow phase: prepare to stop before the next phase.")

    st.divider()
    st.subheader("Road Signal Status")
    signal_state = controller.get_state()

    for road in ROADS:
        if road == signal_state["current_road"] and signal_state["phase"] == "GREEN":
            status = "🟢 GREEN"
        elif road == signal_state["current_road"] and signal_state["phase"] == "YELLOW":
            status = "🟡 YELLOW"
        else:
            status = "🔴 RED"
        st.write(f"**{road} Road:** {status}")

    st.caption(
        "The controller uses GREEN → YELLOW → ALL-RED transitions. "
        "Pedestrian requests add a protected PED-WALK phase. This is a software simulation."
    )


# =========================================================
# 9. EMERGENCY MANAGEMENT
# =========================================================

elif page == "Emergency Management":
    page_header(
        "Emergency Vehicle Management",
        "Simulate priority handling for ambulances, fire trucks and police vehicles.",
    )

    st.info(
        "Choose an emergency vehicle and its incoming road. "
        "The AI decision function will prioritize that road during the next selection."
    )

    col1, col2 = st.columns(2)
    with col1:
        emergency_type = st.selectbox(
            "Emergency Vehicle Type",
            ["🚑 Ambulance", "🚒 Fire Truck", "🚓 Police Vehicle"],
        )
    with col2:
        emergency_road = st.selectbox("Incoming Road", ROADS)

    if st.button(
        "🚨 Activate Emergency Priority",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.active_emergency = {
            "type": emergency_type,
            "road": emergency_road,
        }
        st.success(f"Emergency priority set for {emergency_road} Road.")
        st.rerun()

    st.divider()
    if st.session_state.active_emergency:
        emergency = st.session_state.active_emergency
        st.markdown(
            f"""
            <div class="sf-card">
                <h3>{emergency['type']}</h3>
                <h2 style="color:#20c997;">{emergency['road'].upper()} ROAD PRIORITY</h2>
                <p class="sf-muted">
                    The next AI road selection will prioritize this approach.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Clear Emergency", use_container_width=True):
            st.session_state.active_emergency = None
            st.rerun()
    else:
        st.warning("No active emergency.")

    st.subheader("Current Road Queues")
    for road in ROADS:
        st.write(f"**{road} Road:** {state['vehicles'][road]} vehicles")

    st.caption(
        "This is simulated emergency priority. The project does not detect real emergency vehicles "
        "through cameras, GPS or roadside sensors."
    )


# =========================================================
# 10. PEDESTRIAN MANAGEMENT
# =========================================================

elif page == "Pedestrian Management":
    page_header(
        "Pedestrian Crossing Management",
        "Manage pedestrian demand with a protected crossing sequence.",
    )

    signal_state = controller.get_state()
    crossing_active = signal_state["phase"] == "PED-WALK"
    request_pending = signal_state["pedestrian_request_pending"]

    c1, c2 = st.columns(2)
    c1.metric("Waiting Pedestrians", st.session_state.pedestrian_count)
    if crossing_active:
        crossing_status = "WALK"
    elif request_pending:
        crossing_status = "REQUESTED"
    else:
        crossing_status = "WAIT"
    c2.metric("Crossing Status", crossing_status)

    st.divider()
    st.subheader("Pedestrian Controls")
    add_col, remove_col = st.columns(2)

    with add_col:
        if st.button("➕ Add 5 Pedestrians", use_container_width=True):
            if crossing_active or request_pending:
                st.warning("Please wait until the current crossing sequence finishes.")
            else:
                st.session_state.pedestrian_count += 5
                st.rerun()

    with remove_col:
        if st.button("➖ Remove 5 Pedestrians", use_container_width=True):
            if crossing_active or request_pending:
                st.warning("Pedestrian count cannot be changed during a crossing sequence.")
            else:
                st.session_state.pedestrian_count = max(
                    0, st.session_state.pedestrian_count - 5
                )
                st.rerun()

    st.divider()
    if not crossing_active and not request_pending:
        if st.button(
            "🚶 Request Pedestrian Crossing",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.pedestrian_count == 0,
        ):
            if controller.request_pedestrian_crossing(duration=15):
                st.success(
                    "Crossing requested. Vehicle signals will safely transition "
                    "through YELLOW and ALL-RED before WALK begins."
                )
                st.rerun()
            else:
                st.warning("The controller cannot accept a crossing request right now.")
    elif request_pending:
        st.warning(
            "Crossing request accepted. Please wait while the vehicle signal "
            "moves through its safety-clearance phases."
        )
        st.metric("Current Vehicle Phase", signal_state["phase"])
        st.metric("Phase Time Remaining", f"{signal_state['remaining_seconds']} sec")
    else:
        st.success("🟢 WALK SIGNAL ACTIVE")
        st.metric(
            "Crossing Time Remaining",
            f"{signal_state['remaining_seconds']} seconds",
        )
        st.info(
            "The WALK phase ends automatically. The user cannot manually skip "
            "the protected crossing timer."
        )

    st.divider()
    st.subheader("Pedestrian Signal")
    if crossing_active:
        st.markdown(
            """
            <div class="sf-card" style="text-align:center;">
                <h1 style="color:#20c997;">🟢 WALK</h1>
                <p>Pedestrians may cross. All vehicle approaches are RED.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="sf-card" style="text-align:center;">
                <h1 style="color:#ff5c70;">🔴 WAIT</h1>
                <p>Pedestrians must wait until the protected WALK phase begins.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.caption(
        "The crossing phase is simulated in software and is not connected to real traffic hardware."
    )


# =========================================================
# 11. AI DECISION ENGINE
# =========================================================

elif page == "AI Decision Engine":
    page_header(
        "AI Decision Engine",
        "Inspect the congestion-based logic used to select the next road.",
    )

    score_df = pd.DataFrame(
        [
            {
                "Road": road,
                "Congestion Score": round(current_scores[road], 2),
                "Vehicles": state["vehicles"][road],
                "Waiting Time (sec)": state["waiting_time"][road],
                "Road Wait (sec)": state["road_wait"][road],
            }
            for road in ROADS
        ]
    )

    st.subheader("Current Congestion Scores")
    st.dataframe(score_df, use_container_width=True, hide_index=True)

    st.subheader("Decision-Making Formula")
    st.latex(r"S = 0.5V + 0.3W + 0.2R")
    st.write(
        "**V** = normalized vehicle count, **W** = normalized waiting time, "
        "**R** = normalized road waiting time."
    )

    recommended_road, recommendation_scores = choose_road(
        simulation.get_normalized_data(),
        simulation.current_road,
        emergency=st.session_state.active_emergency,
        pedestrian_count=st.session_state.pedestrian_count,
    )

    st.success(f"Current AI recommendation: **{recommended_road} Road**")

    if st.session_state.active_emergency:
        st.warning(
            f"Emergency override is active for "
            f"{st.session_state.active_emergency['road']} Road."
        )
    else:
        st.info("No emergency override is currently active.")

    st.caption(
        "This project uses a rule-based weighted decision algorithm, not a model "
        "trained on a machine-learning dataset. Adaptive green timing is calculated "
        "from the selected road's congestion score."
    )


# =========================================================
# 12. ANALYTICS AND REPORTS
# =========================================================

elif page == "Analytics & Reports":
    page_header(
        "Analytics & Reports",
        "Review recorded simulation cycles and export the results.",
    )

    if st.session_state.history:
        rows = []
        for item in st.session_state.history:
            for road in ROADS:
                rows.append(
                    {
                        "Cycle": item["cycle"],
                        "Road": road,
                        "Vehicles": item["vehicles"][road],
                        "Waiting Time": item["waiting_time"][road],
                        "Road Wait": item["road_wait"][road],
                        "Congestion Score": round(item["scores"][road], 2),
                        "Selected Green Road": item["current_road"] or "None",
                        "Green Time (sec)": item.get("green_time", "N/A"),
                        "Emergency": item.get("emergency", "No"),
                    }
                )

        results_df = pd.DataFrame(rows)
        st.subheader("Simulation Results")
        st.dataframe(results_df, use_container_width=True, hide_index=True)

        st.download_button(
            "⬇ Download Results (CSV)",
            data=results_df.to_csv(index=False),
            file_name="smartflow_traffic_results.csv",
            mime="text/csv",
        )

        st.divider()
        st.subheader("Vehicle Queue Comparison")
        queue_df = pd.DataFrame(
            [{"Cycle": item["cycle"], **item["vehicles"]}
             for item in st.session_state.history]
        ).set_index("Cycle")
        st.line_chart(queue_df)

        st.subheader("Waiting Time Comparison")
        wait_df = pd.DataFrame(
            [{"Cycle": item["cycle"], **item["waiting_time"]}
             for item in st.session_state.history]
        ).set_index("Cycle")
        st.line_chart(wait_df)

        st.metric("Recorded Cycles", len(st.session_state.history))
    else:
        st.info(
            "No analytics available yet. Start signal cycles or run simulation "
            "cycles from the Overview page to collect data."
        )


# =========================================================
# 13. FOOTER
# =========================================================

st.divider()
st.markdown(
    """
    <div style="text-align:center;padding:12px;color:#91a4ba;font-size:12px;">
        SMARTFLOW AI · Intelligent Traffic Management System<br>
        Academic Software Simulation Project
    </div>
    """,
    unsafe_allow_html=True,
)
