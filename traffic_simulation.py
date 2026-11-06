
import random

ROADS = ["North", "South", "East", "West"]

MAX_QUEUE = 30
MAX_WAIT = 120
MAX_GREEN_WAIT = 60
VEHICLES_PER_CYCLE = 5


class TrafficSimulation:
    def __init__(self, seed=42):
        random.seed(seed)

        self.vehicles = {
            road: random.randint(5, 20)
            for road in ROADS
        }

        self.waiting_time = {
            road: 0 for road in ROADS
        }

        self.road_wait = {
            road: 0 for road in ROADS
        }

        self.current_road = None
        self.current_green_time = 0
        self.cycle = 0

        self.total_arrived = sum(self.vehicles.values())
        self.total_served = 0

    def get_normalized_data(self):
        data = {}

        for road in ROADS:
            data[road] = {
                "vehicles": round(
                    min(self.vehicles[road] / MAX_QUEUE, 1) * 100
                ),
                "waiting_time": round(
                    min(self.waiting_time[road] / MAX_WAIT, 1) * 100
                ),
                "road_wait": round(
                    min(self.road_wait[road] / MAX_GREEN_WAIT, 1) * 100
                )
            }

        return data

    def step(self, selected_road):
        self.cycle += 1

        self.current_road = selected_road
        self.current_green_time = 1

        # Vehicles pass through the green signal.
        served = min(
            self.vehicles[selected_road],
            VEHICLES_PER_CYCLE
        )

        self.vehicles[selected_road] -= served
        self.total_served += served

        # Other vehicles continue to wait.
        for road in ROADS:
            if road != selected_road and self.vehicles[road] > 0:
                self.waiting_time[road] = min(
                    self.waiting_time[road] + 5,
                    MAX_WAIT
                )

        # The selected road has just received green.
        self.waiting_time[selected_road] = 0
        self.road_wait[selected_road] = 0

        # Roads without green accumulate road waiting time.
        for road in ROADS:
            if road != selected_road:
                self.road_wait[road] = min(
                    self.road_wait[road] + 5,
                    MAX_GREEN_WAIT
                )

        # New vehicles arrive after the signal action.
        for road in ROADS:
            arrivals = random.randint(0, 4)

            self.vehicles[road] = min(
                self.vehicles[road] + arrivals,
                MAX_QUEUE
            )

            self.total_arrived += arrivals

    def get_state(self):
        return {
            "vehicles": self.vehicles.copy(),
            "waiting_time": self.waiting_time.copy(),
            "road_wait": self.road_wait.copy(),
            "current_road": self.current_road,
            "cycle": self.cycle,
            "total_arrived": self.total_arrived,
            "total_served": self.total_served
        }
