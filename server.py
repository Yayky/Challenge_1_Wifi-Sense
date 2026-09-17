from fastapi import FastAPI, WebSocket,WebSocketDisconnect
from fastapi.responses import FileResponse
import asyncio
from simulator  import Simulator


app = FastAPI()

@app.get("/")
async def dashboard():
    return FileResponse("dashboard.html")

@app.get("/status")
async def read_status():
    return {"people":0}

@app.get("/api/state")
async def read_state():
    return {"occupied":False,"people":0,"source":"placeholder"}

# 1.The target dissapears after 100 frames, and in the middle of the room (not within the door or window zones) it should still stay visible on that same spot becuase they could not have left the room.
# 2.If they dissapear within the door or window zones (though the widow zone is to be viewed a bit differently since the chance of a person going out trough the window is less likely), then they should be considered to have left the room.
# 3.If we hold them forever, if there is an error and the target is actually gone, then we are filling up the radar and pinging the server for no reason that someone is still in there. If we hold them until something elese happens then we also can abandom the presence that is actually in there for a possbile curtain movement, fan movement, or other person even though there is already another one in there.
# 4.we can put change their color to yellow and a little timer on them or next to them that says how long they have been there.

# The reason behind the 5 min hold is that its not too short or too long, also if the person is in the room and they are not moving, then they are still there. If they are moving, then they are still there. If they are sitting, then they are still there. If they are standing, then they are still there. If they are walking, then they are still there. If they are running, then they are still there. If they are jumping, then they are still there. If they are falling, then they are still there. If they are flying, then they are still there. If they are swimming, then they are still there. If they are driving, then they are still there. If they are biking, then they are still there. If they are skating, then they are still there. If they are skiing, then they are still there. If they are snowboarding, then they are still there. If they are surfing, then they are still there. If they are skateboarding, then they are still there. If they are rollerblading, then they are still there. If they are horseback riding, then they are still there. If they are paragliding, then they are still there. If they are hang gliding, then they are still there. If they are skydiving, then they are still there. If they are bungee jumping, then they are still there. If they are rock climbing, then they are still there. If they are ice climbing, then they are still there. If they are mountaineering, then they are still there. If they are caving, then they are still there. If they are spelunking, then they are still there. If they are kayaking, then they are still there. If they are canoeing, then they are still there. If they are rafting, then they are still there. If they are sailing, then they are still there. If they are windsurfing, then they are still there. If they are kitesurfing, then they are still there. If they are wakeboarding, then they are still there. If they are waterskiing, then they are still there. If they are tubing, then they are still there. If they are parasailing, then they are still there. If they are jet skiing, then they are still there. If they are scuba diving, then they are still there. If they are snorkeling, then they are still there. If they are freediving, then they are still there. If they are spearfishing, then they are still there.
MAX_HOLD_FRAMES = 3000

def is_in_door_zone(x, y):
    return 3.0<= x <= 4.0 and 3.4<= y <= 4.0

def is_in_window_zone(x, y):
    return 0.6 <= x <= 1.4 and 0.0 <= y <= 0.6

def hold_frames(x, y):
    if is_in_door_zone(x, y):
        return 0 
    if is_in_window_zone(x, y):
        return 150
    return MAX_HOLD_FRAMES

@app.websocket("/ws")
async def stream(websocket: WebSocket):
    await websocket.accept()

    sim = Simulator()
    last_x = None
    last_y = None
    held_frames = 0

    try:
        while True:
            people = sim.next_frame()

            if len(people) > 0:
                last_x = people[0]["x"]
                last_y = people[0]["y"]
                held_frames = 0
                people[0]["held"] = False
            elif last_x is not None :
                if held_frames < hold_frames(last_x, last_y):
                    held_frames += 1
                    people = [{"x":round(last_x, 2),"y":round(last_y,2),"held":True, "held_seconds":round(held_frames/10,1)}]
                else: 
                    last_x = None
                    last_y = None
                    
            await websocket.send_json({"people":people})
            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        print("dashboard disconnected")