import random
import time
import threading
import pygame
import sys
from Vehicle_Detection import image_uploader, vehicle_counter

# ------------------------------
# CONFIGURATION & GLOBAL VARIABLES
# ------------------------------

# Default timer values
defaultGreen = {0: 10, 1: 10, 2: 10, 3: 10}
defaultRed = 150
defaultYellow = 2

signals = []
noOfSignals = 4

# Paired signals setup:
# Original mapping: 0: right, 1: down, 2: left, 3: up
# We group:
#   Pair 0 (east–west): right (index 0) and left (index 2)
#   Pair 1 (north–south): down (index 1) and up (index 3)
pairMapping = {
    0: [0, 2], 
    1: [1, 3]
}
activePair = 0  # start with east–west active

# Global phase for the active pair. For vehicles in the active directions, this tells them if the light is green or yellow.
# (For inactive directions, the phase is always "red".)
currentPhase = "green"  # will be updated within the signal cycle

# Direction mapping used in vehicles (unchanged)
directionNumbers = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}

# Vehicle speeds and starting coordinates
speeds = {'car': 2.25, 'bus': 1.8, 'truck': 1.8, 'bike': 2.5}
x = {
    'right': [0, 0, 0],
    'down': [755, 727, 697],
    'left': [1400, 1400, 1400],
    'up': [602, 627, 657]
}    
y = {
    'right': [348, 370, 398],
    'down': [0, 0, 0],
    'left': [498, 466, 436],
    'up': [800, 800, 800]
}

# Vehicles structure: each direction has 3 lanes (list indexes 0,1,2); 'crossed' flag is ignored here.
vehicles = {
    'right': {0: [], 1: [], 2: []},
    'down':  {0: [], 1: [], 2: []},
    'left':  {0: [], 1: [], 2: []},
    'up':    {0: [], 1: [], 2: []}
}
vehicleTypes = {0: 'car', 1: 'bus', 2: 'truck', 3: 'bike'}

# Coordinates for signals on screen
signalCoods = [(530,230), (810,230), (810,570), (530,570)]
signalTimerCoods = [(530,210), (810,210), (810,550), (530,550)]

# Stop lines (the line vehicles must not cross in red/yellow)
stopLines = {
    'right': 590,  # vehicles moving right must stop before x reaches 590
    'down':  330,  # vehicles moving down must stop before y reaches 330
    'left':  800,  # vehicles moving left must not go below x = 800 (they approach from the right)
    'up':    535   # vehicles moving up must not go above y = 535
}
# (Adjust these values to match your intersection.)

# Gap values (in pixels) to allow between vehicles
stoppingGap = 15    # gap when vehicles are stopped
movingGap = 15      # minimal gap when moving

pygame.init()
simulation = pygame.sprite.Group()

# ------------------------------
# CLASS DEFINITIONS
# ------------------------------

class TrafficSignal:
    def __init__(self, red, yellow, green):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.signalText = ""

class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        # The spawn coordinate for this vehicle
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        # crossed == 0 means not yet entered the intersection (has not passed the stop line)
        # crossed == 1 means vehicle has entered the intersection.
        self.crossed = 0  
        # Append self to the appropriate lane for gap checking.
        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1  # position in the lane
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.image = pygame.image.load(path)
        
        # Adjust spawn positions slightly so vehicles do not overlap.
        if direction == 'right':
            delta = self.image.get_rect().width + stoppingGap
            x[direction][lane] -= delta
        elif direction == 'left':
            delta = self.image.get_rect().width + stoppingGap
            x[direction][lane] += delta
        elif direction == 'down':
            delta = self.image.get_rect().height + stoppingGap
            y[direction][lane] -= delta
        elif direction == 'up':
            delta = self.image.get_rect().height + stoppingGap
            y[direction][lane] += delta
            
        simulation.add(self)

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def gapAvailable(self):
        """Check if the gap to the preceding vehicle is sufficient.
           Returns True if no vehicle ahead or gap >= movingGap; otherwise False.
        """
        if self.index == 0:
            return True  # first vehicle in lane—nothing ahead
        # Get the preceding vehicle in the same lane & direction
        prev = vehicles[self.direction][self.lane][self.index - 1]
        if self.direction == 'right':
            gap = prev.x - (self.x + self.image.get_rect().width)
        elif self.direction == 'left':
            gap = self.x - (prev.x + prev.image.get_rect().width)
        elif self.direction == 'down':
            gap = prev.y - (self.y + self.image.get_rect().height)
        elif self.direction == 'up':
            gap = self.y - (prev.y + prev.image.get_rect().height)
        return gap >= movingGap

    def move(self):
        global currentPhase
        
        # Determine if this vehicle's direction is currently active (its signal is controlled by activePair)
        activeDirections = [directionNumbers[idx] for idx in pairMapping[activePair]]
        # For vehicles in inactive directions, phase is considered "red"
        phase = currentPhase if (self.direction in activeDirections) else "red"
        
        # --- BEFORE THE INTERSECTION (has not yet crossed) ---
        if self.crossed == 0:
            # If the phase is green, the vehicle is allowed to cross.
            if phase == "green":
                # If gap allows, move forward.
                if self.gapAvailable():
                    self.advance()
                # Check if we now cross the stop line. (For each direction, use the appropriate coordinate.)
                if self.direction == 'right' and (self.x + self.image.get_rect().width >= stopLines['right']):
                    self.crossed = 1
                elif self.direction == 'down' and (self.y + self.image.get_rect().height >= stopLines['down']):
                    self.crossed = 1
                elif self.direction == 'left' and (self.x <= stopLines['left']):
                    self.crossed = 1
                elif self.direction == 'up' and (self.y <= stopLines['up']):
                    self.crossed = 1
                    
            # For red or yellow phases, the vehicle should approach the stop line but not cross.
            else:
                # Move forward only if not already at (or past) the stop line.
                if self.direction == 'right':
                    if self.x + self.image.get_rect().width < stopLines['right']:
                        if self.gapAvailable():
                            self.advance()
                        # Clamp the position so that it does not cross the stop line.
                        if self.x + self.image.get_rect().width > stopLines['right']:
                            self.x = stopLines['right'] - self.image.get_rect().width
                elif self.direction == 'down':
                    if self.y + self.image.get_rect().height < stopLines['down']:
                        if self.gapAvailable():
                            self.advance()
                        if self.y + self.image.get_rect().height > stopLines['down']:
                            self.y = stopLines['down'] - self.image.get_rect().height
                elif self.direction == 'left':
                    if self.x > stopLines['left']:
                        if self.gapAvailable():
                            self.advance()
                        if self.x < stopLines['left']:
                            self.x = stopLines['left']
                elif self.direction == 'up':
                    if self.y > stopLines['up']:
                        if self.gapAvailable():
                            self.advance()
                        if self.y < stopLines['up']:
                            self.y = stopLines['up']
        else:
            # --- INSIDE THE INTERSECTION ---
            # If the vehicle has already crossed, it continues moving regardless of signal.
            self.advance()

    def advance(self):
        """Advance the vehicle by its speed along its direction."""
        if self.direction == 'right':
            self.x += self.speed
        elif self.direction == 'down':
            self.y += self.speed
        elif self.direction == 'left':
            self.x -= self.speed
        elif self.direction == 'up':
            self.y -= self.speed

# ------------------------------
# SIGNAL MANAGEMENT & VEHICLE GENERATION
# ------------------------------

def initializeSignals():
    # Create signals in order: index 0: right, 1: down, 2: left, 3: up.
    ts0 = TrafficSignal(0, defaultYellow, defaultGreen[0])   # right
    signals.append(ts0)
    ts1 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[1])  # down
    signals.append(ts1)
    ts2 = TrafficSignal(0, defaultYellow, defaultGreen[2])   # left
    signals.append(ts2)
    ts3 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[3])  # up
    signals.append(ts3)
    # Start the signal cycle in a separate thread.
    threading.Thread(target=repeat, daemon=True).start()

def repeat():
    global activePair, currentPhase
    # For active pair directions, set them to a starting green phase.
    for idx in pairMapping[activePair]:
        signals[idx].green = defaultGreen[idx]
        signals[idx].yellow = defaultYellow
        signals[idx].red = 0
    # For the inactive pair, force red.
    inactivePair = 1 - activePair
    for idx in pairMapping[inactivePair]:
        signals[idx].red = defaultRed
        signals[idx].green = 0
        signals[idx].yellow = 0

    # --- GREEN PHASE ---
    currentPhase = "green"
    t = defaultGreen[pairMapping[activePair][0]]
    while t > 0:
        for idx in pairMapping[activePair]:
            signals[idx].green = t
        time.sleep(1)
        t -= 1

    # --- YELLOW PHASE ---
    currentPhase = "yellow"
    t = defaultYellow
    for idx in pairMapping[activePair]:
        signals[idx].yellow = t
        signals[idx].green = 0
    while t > 0:
        for idx in pairMapping[activePair]:
            signals[idx].yellow = t
        time.sleep(1)
        t -= 1

    # End of active phase: reset active pair to defaults (red)
    for idx in pairMapping[activePair]:
        signals[idx].red = defaultRed
        signals[idx].green = defaultGreen[idx]
        signals[idx].yellow = defaultYellow

    # Switch active pair; the new active pair will have its phase set when its cycle begins.
    activePair = inactivePair
    # Set currentPhase for new active pair as green for the next cycle.
    currentPhase = "green"
    repeat()  # Recursively continue the cycle.

def generateVehicles():
    while True:
        vehicle_type = random.randint(0,3)
        lane_number = random.randint(1,2)
        dice = random.randint(0,99)
        direction_number = 0
        # Use probability ranges to assign direction based on dice roll.
        if dice < 25:
            direction_number = 0
        elif dice < 50:
            direction_number = 1
        elif dice < 75:
            direction_number = 2
        else:
            direction_number = 3
        Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number])
        time.sleep(1)  # Adjust spawn rate as needed

# ------------------------------
# MAIN LOOP & RENDERING
# ------------------------------ 

class Main:
    def __init__(self):
        # Start the signal initialization thread.
        threading.Thread(target=initializeSignals, daemon=True).start()
        # Start vehicle generation thread.
        threading.Thread(target=generateVehicles, daemon=True).start()
        self.run()

    def run(self):
        black = (0, 0, 0)
        white = (255, 255, 255)
        screenWidth = 1400
        screenHeight = 800
        screenSize = (screenWidth, screenHeight)

        background = pygame.image.load('images/intersection.png')
        screen = pygame.display.set_mode(screenSize)
        pygame.display.set_caption("SIMULATION")

        redSignal = pygame.image.load('images/signals/red.png')
        yellowSignal = pygame.image.load('images/signals/yellow.png')
        greenSignal = pygame.image.load('images/signals/green.png')
        font = pygame.font.Font(None, 30)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

            screen.blit(background, (0, 0))
            # Render signals for each index
            for i in range(noOfSignals):
                # For signals that belong to the active pair, display their green or yellow timer.
                if i in pairMapping[activePair]:
                    if signals[i].green > 0:
                        signals[i].signalText = signals[i].green
                        screen.blit(greenSignal, signalCoods[i])
                    elif signals[i].yellow > 0:
                        signals[i].signalText = signals[i].yellow
                        screen.blit(yellowSignal, signalCoods[i])
                else:
                    # Inactive signals display red.
                    if signals[i].red <= 10:
                        signals[i].signalText = signals[i].red
                    else:
                        signals[i].signalText = "---"
                    screen.blit(redSignal, signalCoods[i])
                textRendered = font.render(str(signals[i].signalText), True, white, black)
                screen.blit(textRendered, signalTimerCoods[i])
            # Update and draw vehicles.
            for vehicle in simulation:
                vehicle.move()
                screen.blit(vehicle.image, (vehicle.x, vehicle.y))

            pygame.display.update()

# ------------------------------
# LAUNCH THE SIMULATION
# ------------------------------

if __name__ == '__main__':
    image_uploader()
    vehicle_counter()
    Main()
