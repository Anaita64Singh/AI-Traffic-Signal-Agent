
import streamlit as st
import streamlit.components.v1 as components


def render_intersection(state, signal_state=None):

    vehicles = state["vehicles"]
    current_road = state["current_road"]

    if signal_state is None:
        phase = "GREEN" if current_road else "RED"
        signal_road = current_road
    else:
        phase = signal_state["phase"]
        signal_road = signal_state["current_road"]

    def make_cars(road):
        count = min(vehicles[road], 8)
        return "".join(
            '<span class="car">🚗</span>'
            for _ in range(count)
        )

    def signal(road):
        if signal_road != road:
            return '<div class="light red">●</div>'

        if phase == "GREEN":
            return '<div class="light green">●</div>'

        if phase == "YELLOW":
            return '<div class="light yellow">●</div>'

        return '<div class="light red">●</div>'

    north_cars = make_cars("North")
    south_cars = make_cars("South")
    east_cars = make_cars("East")
    west_cars = make_cars("West")

    north_signal = signal("North")
    south_signal = signal("South")
    east_signal = signal("East")
    west_signal = signal("West")

    active = signal_road or "None"

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>

    * {{
        box-sizing: border-box;
    }}

    body {{
        margin: 0;
        padding: 10px;
        background: #0b1120;
        font-family: Arial, sans-serif;
        color: #e8f0fa;
    }}

    .scene {{
        position: relative;
        width: 100%;
        height: 510px;
        max-width: 850px;
        margin: auto;
        overflow: hidden;
        background: #111c2c;
        border: 1px solid #26364b;
        border-radius: 18px;
    }}

    .road {{
        position: absolute;
        background: #303c4d;
    }}

    .vertical {{
        left: 39%;
        width: 22%;
        top: 0;
        height: 100%;
    }}

    .horizontal {{
        top: 34%;
        height: 32%;
        left: 0;
        width: 100%;
    }}

    .vertical::after {{
        content: "";
        position: absolute;
        left: 50%;
        height: 100%;
        border-left: 3px dashed #d4d9df;
        opacity: 0.7;
    }}

    .horizontal::after {{
        content: "";
        position: absolute;
        top: 50%;
        width: 100%;
        border-top: 3px dashed #d4d9df;
        opacity: 0.7;
    }}

    .crosswalk {{
        position: absolute;
        z-index: 2;
        display: flex;
        gap: 5px;
    }}

    .crosswalk span {{
        background: #dce3ec;
        opacity: 0.85;
    }}

    .crosswalk.top,
    .crosswalk.bottom {{
        left: 39%;
        width: 22%;
        height: 13px;
        flex-direction: row;
    }}

    .crosswalk.top {{
        top: 29%;
    }}

    .crosswalk.bottom {{
        bottom: 29%;
    }}

    .crosswalk.left,
    .crosswalk.right {{
        top: 34%;
        height: 32%;
        width: 13px;
        flex-direction: column;
    }}

    .crosswalk.left {{
        left: 35%;
    }}

    .crosswalk.right {{
        right: 35%;
    }}

    .crosswalk span {{
        flex: 1;
    }}

    .road-label {{
        position: absolute;
        font-size: 12px;
        font-weight: bold;
        color: #aabbd0;
        z-index: 5;
    }}

    .north-label {{
        top: 8px;
        left: 50%;
        transform: translateX(-50%);
    }}

    .south-label {{
        bottom: 8px;
        left: 50%;
        transform: translateX(-50%);
    }}

    .west-label {{
        left: 8px;
        top: 50%;
    }}

    .east-label {{
        right: 8px;
        top: 50%;
    }}

    .queue {{
        position: absolute;
        z-index: 5;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
        flex-wrap: wrap;
        max-width: 180px;
    }}

    .north-queue {{
        top: 65px;
        left: 42%;
        width: 16%;
        flex-direction: column;
    }}

    .south-queue {{
        bottom: 65px;
        left: 42%;
        width: 16%;
        flex-direction: column;
    }}

    .west-queue {{
        left: 15px;
        top: 42%;
        width: 18%;
    }}

    .east-queue {{
        right: 15px;
        top: 42%;
        width: 18%;
    }}

    .car {{
        font-size: 19px;
        line-height: 1.1;
    }}

    .signal-box {{
        position: absolute;
        z-index: 10;
        background: #131e30;
        border: 1px solid #45566d;
        border-radius: 10px;
        padding: 5px 10px;
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 11px;
        font-weight: bold;
    }}

    .north-signal {{
        top: 35%;
        left: 62%;
    }}

    .south-signal {{
        bottom: 35%;
        right: 62%;
    }}

    .west-signal {{
        top: 25%;
        left: 30%;
    }}

    .east-signal {{
        bottom: 25%;
        right: 30%;
    }}

    .light {{
        font-size: 21px;
        line-height: 1;
    }}

    .red {{
        color: #ff5d6c;
        text-shadow: 0 0 9px #ff5d6c;
    }}

    .green {{
        color: #20c997;
        text-shadow: 0 0 12px #20c997;
        animation: pulse 1.2s infinite;
    }}

    .yellow {{
        color: #ffc857;
        text-shadow: 0 0 12px #ffc857;
        animation: pulse 0.7s infinite;
    }}

    .intersection-center {{
        position: absolute;
        z-index: 3;
        left: 39%;
        top: 34%;
        width: 22%;
        height: 32%;
        border: 2px solid rgba(255,255,255,0.15);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-size: 12px;
        font-weight: bold;
        text-align: center;
    }}

    .active-banner {{
        position: absolute;
        top: 12px;
        right: 12px;
        z-index: 15;
        background: #123b36;
        color: #20c997;
        padding: 9px 12px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: bold;
    }}

    @keyframes pulse {{
        50% {{ opacity: 0.45; }}
    }}

    @media(max-width: 550px) {{
        .scene {{
            height: 440px;
        }}

        .car {{
            font-size: 14px;
        }}

        .signal-box {{
            font-size: 9px;
            padding: 4px;
        }}

        .light {{
            font-size: 16px;
        }}
    }}

    </style>
    </head>

    <body>
    <div class="scene">

        <div class="road vertical"></div>
        <div class="road horizontal"></div>

        <div class="crosswalk top">
            <span></span><span></span><span></span>
            <span></span><span></span>
        </div>

        <div class="crosswalk bottom">
            <span></span><span></span><span></span>
            <span></span><span></span>
        </div>

        <div class="crosswalk left">
            <span></span><span></span><span></span>
            <span></span>
        </div>

        <div class="crosswalk right">
            <span></span><span></span><span></span>
            <span></span>
        </div>

        <div class="intersection-center">
            SMARTFLOW<br>AI
        </div>

        <div class="road-label north-label">NORTH</div>
        <div class="road-label south-label">SOUTH</div>
        <div class="road-label west-label">WEST</div>
        <div class="road-label east-label">EAST</div>

        <div class="queue north-queue">{north_cars}</div>
        <div class="queue south-queue">{south_cars}</div>
        <div class="queue west-queue">{west_cars}</div>
        <div class="queue east-queue">{east_cars}</div>

        <div class="signal-box north-signal">
            NORTH {north_signal}
        </div>

        <div class="signal-box south-signal">
            SOUTH {south_signal}
        </div>

        <div class="signal-box west-signal">
            WEST {west_signal}
        </div>

        <div class="signal-box east-signal">
            EAST {east_signal}
        </div>

        <div class="active-banner">
            ACTIVE: {active.upper()}
        </div>

    </div>
    </body>
    </html>
    """

    components.html(
        html_code,
        height=540,
        scrolling=False
    )
