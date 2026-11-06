
# ==========================================
# TRAFFIC SIGNAL PHASE CONTROLLER
# WITH PEDESTRIAN SAFETY INTERLOCK
# ==========================================

class SignalController:

    def __init__(self):

        self.phase = "RED"
        self.current_road = None

        self.remaining_seconds = 0
        self.green_duration = 0

        self.yellow_duration = 3
        self.all_red_duration = 1

        self.pedestrian_walk_duration = 15
        self.pedestrian_request_pending = False

        self.is_running = False

    def start(self, road, green_seconds):

        """
        Start a new green signal phase for a road.
        """

        if self.is_running:
            return False

        if self.pedestrian_request_pending:
            return False

        self.current_road = road

        self.green_duration = max(
            10,
            min(60, int(green_seconds))
        )

        self.remaining_seconds = self.green_duration

        self.phase = "GREEN"
        self.is_running = True

        return True

    def request_pedestrian_crossing(self, duration=15):

        """
        Request a pedestrian crossing.

        Vehicle signals transition safely:
        GREEN -> YELLOW -> ALL-RED -> PED-WALK -> RED
        """

        if self.phase == "PED-WALK":
            return False

        if self.pedestrian_request_pending:
            return False

        self.pedestrian_walk_duration = max(5, int(duration))
        self.pedestrian_request_pending = True

        if self.phase == "GREEN":

            # Give vehicles a yellow warning first.
            self.phase = "YELLOW"
            self.remaining_seconds = self.yellow_duration

        elif self.phase == "YELLOW":

            # Finish the existing yellow phase.
            pass

        elif self.phase == "ALL-RED":

            # Wait for the all-red phase to finish.
            pass

        else:

            # If traffic is stopped, create an all-red phase.
            self.phase = "ALL-RED"
            self.current_road = None
            self.remaining_seconds = self.all_red_duration
            self.is_running = True

        return True

    def advance_one_second(self):

        """
        Advance the simulation clock by one second.
        """

        if not self.is_running:
            return self.get_state()

        self.remaining_seconds -= 1

        if self.remaining_seconds <= 0:

            if self.phase == "GREEN":

                self.phase = "YELLOW"
                self.remaining_seconds = self.yellow_duration

            elif self.phase == "YELLOW":

                self.phase = "ALL-RED"
                self.current_road = None
                self.remaining_seconds = self.all_red_duration

            elif self.phase == "ALL-RED":

                if self.pedestrian_request_pending:

                    # All vehicle signals remain RED.
                    self.phase = "PED-WALK"
                    self.remaining_seconds = (
                        self.pedestrian_walk_duration
                    )

                    self.pedestrian_request_pending = False

                else:

                    self.phase = "RED"
                    self.current_road = None
                    self.remaining_seconds = 0
                    self.is_running = False

            elif self.phase == "PED-WALK":

                # Crossing period completed.
                self.phase = "RED"
                self.current_road = None
                self.remaining_seconds = 0
                self.is_running = False

        return self.get_state()

    def get_state(self):

        """
        Return the current signal controller status.
        """

        return {
            "phase": self.phase,
            "current_road": self.current_road,
            "remaining_seconds": self.remaining_seconds,
            "green_duration": self.green_duration,
            "is_running": self.is_running,
            "pedestrian_request_pending": (
                self.pedestrian_request_pending
            ),
            "pedestrian_walk_active": (
                self.phase == "PED-WALK"
            )
        }
