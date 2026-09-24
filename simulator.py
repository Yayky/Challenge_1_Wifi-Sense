class Simulator:
    def __init__(self):
        self.x = 2.5
        self.y = 2.0
        self.step_x = 0.04
        self.step_y = 0.02
        self.frames_until_sit = 100
        self.sit_frames_left = 0

    def next_frame(self):
        # Simulate the next frame of movement and sitting behavior
        if self.sit_frames_left > 0:
            self.sit_frames_left -= 1
            return[]
        # If the person is not sitting, update their position and check for boundaries
        else:
            self.x += self.step_x
            self.y += self.step_y
        # Check if the person has moved out of bounds and reverse direction if necessary
            if self.x < 0 or self.x >5:
                self.step_x = -self.step_x
            if self.y < 0 or self.y >4:
                self.step_y = -self.step_y                
            self.frames_until_sit -= 1
        # If it's time for the person to sit, reset the sitting frames and countdown
            if self.frames_until_sit <= 0:
                self.sit_frames_left = 50
                self.frames_until_sit = 10
        # Create a list of people with their current position and held status
            # single person sim
            #return[{"x":round(self.x, 2),"y":round(self.y,2)}]
            
            # for multiple people sim 
            return[{"x": round(self.x, 2), "y": round(self.y, 2)}, {"x": round(5 - self.x, 2), "y": round(4 - self.y, 2)}]