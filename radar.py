import asyncio
import aioesphomeapi
import math

# The room, in meters
ROOM_LENGTH = 5.49
ROOM_DEPTH = 3.60

SENSOR_X = 2.02
SENSOR_Y = 0.0
SIDE = 1

def sensor_to_room(x_mm, y_mm):
    room_x = SENSOR_X + SIDE * (x_mm / 1000)
    room_y = SENSOR_Y + SIDE * (y_mm / 1000)
    return round(room_x, 2), round(room_y, 2)

def in_room(x, y):
    return 0 <= x <= ROOM_LENGTH and 0 <= y <= ROOM_DEPTH
    

class RadarNode:
    def __init__(self, address, key):
        self.address = address
        self.key = key
        self.connected = False
        self.present = False
        self.moving = False
        self.still = False
        self.still_distance = 0.0
        self.target_x = [math.nan, math.nan, math.nan]
        self.target_y = [math.nan, math.nan, math.nan]

    def snapshot(self):
        return {
            "connected": self.connected,
            "present": self.present,
            "moving": self.moving,
            "still": self.still,
            "still_distance": self.still_distance
        }

    def people(self):
        found = []
        for i in range(3):
            x_mm = self.target_x[i]
            y_mm = self.target_y[i]
            if math.isnan(x_mm) or math.isnan(y_mm):
                continue
            room_x, room_y = sensor_to_room(x_mm, y_mm)
            if not in_room(room_x, room_y):
                continue
            found.append({"x": room_x, "y": room_y, "held": False})
        return found
        
    async def run(self):
        while True:
            try:
                api=aioesphomeapi.APIClient(self.address, 6053, None,  noise_psk=self.key)
                stopped = asyncio.Event()
    
                async def on_stop(expected_disconnect):
                    stopped.set()

                await api.connect(on_stop=on_stop, login=True)

                entities, services = await api.list_entities_services()
                names = {e.key: e.name for e in entities}
                
                def on_state(state):
                    name = names.get(state.key)
                    value = getattr(state, "state", None)
                    if name == "Presence":
                        self.present = bool(value)
                    elif name == "Moving target":
                        self.moving = bool(value)
                    elif name == "Still target":
                        self.still = bool(value)
                    elif name == "Still distance":
                        self.still_distance = float(value)
                    elif name in ("T1 x", "T2 x", "T3 x"):
                        self.target_x[int(name[1]) - 1] = float(value)
                    elif name in ("T1 y", "T2 y", "T3 y"):
                        self.target_y[int(name[1]) - 1] = float(value)


                api.subscribe_states(on_state)
                self.connected = True
                print("radar connected")
                await stopped.wait()

            except Exception as e:
                print(f"radar", e)
            self.connected = False
            await asyncio.sleep(5)