
# ==========================================
# ADAPTIVE TRAFFIC SIGNAL TIMING
# ==========================================

MIN_GREEN_TIME = 10
MAX_GREEN_TIME = 60


def calculate_green_time(congestion_score):
    """
    Calculate adaptive green signal duration.

    Higher congestion receives longer green time.

    Input:
        congestion_score: 0 to 100

    Output:
        Green signal duration in seconds.
    """

    congestion_score = max(
        0,
        min(100, congestion_score)
    )

    green_time = (
        MIN_GREEN_TIME
        + (congestion_score / 100)
        * (MAX_GREEN_TIME - MIN_GREEN_TIME)
    )

    return round(green_time)


def get_signal_timing(scores, selected_road):
    """
    Return the adaptive green duration for a selected road.
    """

    if selected_road not in scores:
        return MIN_GREEN_TIME

    return calculate_green_time(
        scores[selected_road]
    )
