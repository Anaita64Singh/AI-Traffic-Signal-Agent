
ROADS = ["North", "South", "East", "West"]


def calculate_congestion_score(vehicles, waiting_time, road_wait):
    """
    Calculate congestion score using weighted traffic parameters.
    All inputs are normalized between 0 and 100.
    """

    return (
        0.5 * vehicles
        + 0.3 * waiting_time
        + 0.2 * road_wait
    )


def choose_road(
    traffic_data,
    current_road=None,
    emergency=None,
    pedestrian_count=0
):
    """
    Select the best road using congestion and priority factors.

    Emergency priority overrides normal congestion scoring.
    Pedestrian demand is considered when choosing a road.
    """

    scores = {}

    for road in ROADS:

        data = traffic_data[road]

        score = calculate_congestion_score(
            data["vehicles"],
            data["waiting_time"],
            data["road_wait"]
        )

        # Additional priority for pedestrian demand.
        if pedestrian_count > 0:
            score += min(pedestrian_count * 0.5, 15)

        scores[road] = score

    # Emergency vehicles receive priority.
    if emergency and emergency["road"] in ROADS:

        selected_road = emergency["road"]

        return selected_road, scores

    # Avoid selecting the currently active road again.
    candidates = [
        road for road in ROADS
        if road != current_road
    ]

    if not candidates:
        candidates = ROADS

    selected_road = max(
        candidates,
        key=lambda road: scores[road]
    )

    return selected_road, scores
