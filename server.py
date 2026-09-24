from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
import asyncio
from simulator  import Simulator
from contextlib import asynccontextmanager
import yaml
from radar import RadarNode

secrets = yaml.safe_load(open("firmware/secrets.yaml"))
RADAR_KEY=secrets["api_key"]
RADAR_ADDRESS=secrets["radar_address"]

# Door zone: in front of the door
DOOR_X1, DOOR_X2 = 4.80, 5.49     
DOOR_Y1, DOOR_Y2 = 1.80, 3.00     

# Window zone:
WINDOW_X1, WINDOW_X2 = 0.00, 0.60  
WINDOW_Y1, WINDOW_Y2 = 0.00, 1.50

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(radar.run())
    yield
    task.cancel()

radar = RadarNode(RADAR_ADDRESS, RADAR_KEY)
app = FastAPI(lifespan=lifespan)

# HTTP GET for the dashbaord updates
@app.get("/")
async def dashboard():
    return FileResponse("dashboard.html")

# HTTP GET for status updates
@app.get("/status")
async def read_status():
    return {"people":0}

# HTTP GET for the API state
@app.get("/api/state")
async def read_state():
    return {"occupied":False,"people":0,"source":"placeholder"}



# 1.The target dissapears after 100 frames, and in the middle of the room (not within the door or window zones) it should still stay visible on that same spot becuase they could not have left the room.
# 2.If they dissapear within the door or window zones (though the widow zone is to be viewed a bit differently since the chance of a person going out trough the window is less likely), then they should be considered to have left the room.
# 3.If we hold them forever, if there is an error and the target is actually gone, then we are filling up the radar and pinging the server for no reason that someone is still in there. If we hold them until something elese happens then we also can abandom the presence that is actually in there for a possbile curtain movement, fan movement, or other person even though there is already another one in there.
# 4.we can put change their color to yellow and a little timer on them or next to them that says how long they have been there.

# The reason behind the 5 min hold is that its not too short or too long, because no one really sits 100% still for more that 5 minutes if not less.
MAX_HOLD_FRAMES = 3000

# def for checking if the person is in the door zone or window zone
def is_in_door_zone(x, y):
    return DOOR_X1 <= x <= DOOR_X2 and DOOR_Y1 <= y <= DOOR_Y2

# def for checking if the person is in the window zone
def is_in_window_zone(x, y):
    return WINDOW_X1 <= x <= WINDOW_X2 and WINDOW_Y1 <= y <= WINDOW_Y2

# def for checking how many frames to hold the person based on their position
def hold_frames(x, y):
    if is_in_door_zone(x, y):
        return 0 
    if is_in_window_zone(x, y):
        return 150
    return MAX_HOLD_FRAMES

#websocket for streaming the simulator data to the dashboard (contains all the logic for holding the person in the room)
@app.websocket("/ws")
async def stream(websocket: WebSocket):
    await websocket.accept()

# pull the simulator.py for the simulation part of the project
    sim = Simulator()

# initialize the last known position and held frames
    last_x = None
    last_y = None
    held_frames = 0

# start the websocket loop for streaming the simulator data to the dashboard
    try:
        while True:
            if radar.connected:
                people = radar.people()
                source = "radar"
            else:
                people = sim.next_frame()
                source = "simulator"

# Check if there are any people in the current frame
            if len(people) > 0:
                last_x = people[0]["x"]
                last_y = people[0]["y"]
                held_frames = 0
                people[0]["held"] = False
# If there are no people in the current frame, check if there was a last known position and if the held frames is less than the hold frames for that position
            elif last_x is not None :
                if held_frames < hold_frames(last_x, last_y):
                    held_frames += 1
                    people = [{"x":round(last_x, 2),"y":round(last_y,2),"held":True, "held_seconds":round(held_frames/10,1)}]
                else: 
                    last_x = None
                    last_y = None
                    
            await websocket.send_json({
                "source":source,
                "people":people,
                "radar":radar.snapshot()
                })
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        print("dashboard disconnected")