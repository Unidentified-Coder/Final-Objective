import random
import time
import threading
import pygame
import sys
from Vehicle_Detection import image_uploader, vehicle_counter

# Default timer values
defaultGreen = {0: 10, 1: 10, 2: 10, 3: 10}
defaultRed = 150
defaultYellow = 5  # Change this to 2 if desired (e.g., defaultYellow = 2)

signals = []
noOfSignals = 4

# --- Paired signals setup ---
# Using original mapping:
# index 0: right, index 1: down, index 2: left, index 3: up
# We want east–west (right & left) to move together and north–south (down & up) to move together.
pairMapping = {
    0: [0, 2],  # Pair 0: east–west (right and left)
    1: [1, 3]   # Pair 1: north–south (down and up)
}
activePair = 0  # Start with east–west active

# Mapping for directions (unchanged)
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

vehicles = {
    'right': {0: [], 1: [], 2: [], 'crossed': 0},
    'down':  {0: [], 1: [], 2: [], 'crossed': 0},
    'left':  {0: [], 1: [], 2: [], 'crossed': 0},
    'up':    {0: [], 1: [], 2: [], 'crossed': 0}
}
vehicleTypes = {0: 'car', 1: 'bus', 2: 'truck', 3: 'bike'}

# Signal image coordinates on screen
signalCoods = [(530,230), (810,230), (810,570), (530,570)]
signalTimerCoods = [(530,210), (810,210), (810,550), (530,550)]

# Stop line and default stop positions (not used on green phase now)
stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

stoppingGap = 15  # gap between vehicles when stopping
movingGap = 15    # gap between vehicles when moving

pygame.init()
simulation = pygame.sprite.Group()

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
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.crossed = 0
        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.image = pygame.image.load(path)

        # Determine the stop coordinate when created
        if len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index - 1].crossed == 0:
            if direction == 'right':
                self.stop = vehicles[direction][lane][self.index - 1].stop - vehicles[direction][lane][self.index - 1].image.get_rect().width - stoppingGap
            elif direction == 'left':
                self.stop = vehicles[direction][lane][self.index - 1].stop + vehicles[direction][lane][self.index - 1].image.get_rect().width + stoppingGap
            elif direction == 'down':
                self.stop = vehicles[direction][lane][self.index - 1].stop - vehicles[direction][lane][self.index - 1].image.get_rect().height - stoppingGap
            elif direction == 'up':
                self.stop = vehicles[direction][lane][self.index - 1].stop + vehicles[direction][lane][self.index - 1].image.get_rect().height + stoppingGap
        else:
            self.stop = defaultStop[direction]
            
        # Adjust starting coordinates to avoid overlap
        if direction == 'right':
            temp = self.image.get_rect().width + stoppingGap    
            x[direction][lane] -= temp
        elif direction == 'left':
            temp = self.image.get_rect().width + stoppingGap
            x[direction][lane] += temp
        elif direction == 'down':
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] -= temp
        elif direction == 'up':
            temp = self.image.get_rect().height + stoppingGap
            y[direction][lane] += temp
        simulation.add(self)

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def move(self):
        # Get list of directions that are active (green/yellow)
        activeDirections = [directionNumbers[idx] for idx in pairMapping[activePair]]
        # Only move if this vehicle's direction is in the active group.
        if self.direction in activeDirections:
            # Check if vehicle has crossed its stop line to update its "crossed" status.
            if self.direction == 'right':
                if self.crossed == 0 and self.x + self.image.get_rect().width > stopLines[self.direction]:
                    self.crossed = 1
                # On green, simply move forward if there's sufficient gap to the preceding vehicle.
                if self.index == 0 or self.x + self.image.get_rect().width < (vehicles[self.direction][self.lane][self.index - 1].x - movingGap):
                    self.x += self.speed
            elif self.direction == 'down':
                if self.crossed == 0 and self.y + self.image.get_rect().height > stopLines[self.direction]:
                    self.crossed = 1
                if self.index == 0 or self.y + self.image.get_rect().height < (vehicles[self.direction][self.lane][self.index - 1].y - movingGap):
                    self.y += self.speed
            elif self.direction == 'left':
                if self.crossed == 0 and self.x < stopLines[self.direction]:
                    self.crossed = 1
                if self.index == 0 or self.x > (vehicles[self.direction][self.lane][self.index - 1].x + vehicles[self.direction][self.lane][self.index - 1].image.get_rect().width + movingGap):
                    self.x -= self.speed
            elif self.direction == 'up':
                if self.crossed == 0 and self.y < stopLines[self.direction]:
                    self.crossed = 1
                if self.index == 0 or self.y > (vehicles[self.direction][self.lane][self.index - 1].y + vehicles[self.direction][self.lane][self.index - 1].image.get_rect().height + movingGap):
                    self.y -= self.speed
        # When not active, vehicles remain still.

# (Optional helper if needed)
def count_waiting_vehicles(direction):
    count = 0
    for lane in range(3):
        count += len(vehicles[direction][lane])
    return count

# Initialize signals for each direction
def initialize():
    # Create signals in the order: 0:right, 1:down, 2:left, 3:up.
    ts0 = TrafficSignal(0, defaultYellow, defaultGreen[0])    # right
    signals.append(ts0)
    ts1 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[1])  # down
    signals.append(ts1)
    ts2 = TrafficSignal(0, defaultYellow, defaultGreen[2])    # left
    signals.append(ts2)
    ts3 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[3])  # up
    signals.append(ts3)
    repeat()

# Signal cycle: alternate between active pairs.
def repeat():
    global activePair
    # For the active pair, set signals to green phase; for the inactive pair, set red.
    for idx in pairMapping[activePair]:
        signals[idx].green = defaultGreen[idx]
        signals[idx].yellow = defaultYellow
        signals[idx].red = 0
    inactivePair = 1 - activePair
    for idx in pairMapping[inactivePair]:
        signals[idx].red = defaultRed
        signals[idx].green = 0
        signals[idx].yellow = 0

    # GREEN phase: countdown for active pair
    t = defaultGreen[pairMapping[activePair][0]]  # assuming same green time for both signals in pair
    while t > 0:
        for idx in pairMapping[activePair]:
            signals[idx].green = t
        time.sleep(1)
        t -= 1

    # YELLOW phase: active pair goes yellow
    t = defaultYellow
    for idx in pairMapping[activePair]:
        signals[idx].yellow = t
        signals[idx].green = 0
    while t > 0:
        for idx in pairMapping[activePair]:
            signals[idx].yellow = t
        time.sleep(1)
        t -= 1

    # After yellow, reset active pair to red and restore defaults.
    for idx in pairMapping[activePair]:
        signals[idx].red = defaultRed
        signals[idx].green = defaultGreen[idx]
        signals[idx].yellow = defaultYellow

    # Switch active pair
    activePair = inactivePair
    repeat()

# In this paired system, updateValues() is not used.
def updateValues():
    pass

# Generate vehicles continuously (adjust sleep for spawn rate)
def generateVehicles():
    while True:
        vehicle_type = random.randint(0, 3)
        lane_number = random.randint(1, 2)
        temp = random.randint(0, 99)
        direction_number = 0
        dist = [25, 50, 75, 100]
        if temp < dist[0]:
            direction_number = 0
        elif temp < dist[1]:
            direction_number = 1
        elif temp < dist[2]:
            direction_number = 2
        elif temp < dist[3]:
            direction_number = 3
        Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number])
        time.sleep(1)  # Adjust this if you need to spawn vehicles faster

class Main:
    thread1 = threading.Thread(name="initialization", target=initialize, args=())
    thread1.daemon = True
    thread1.start()

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

    thread2 = threading.Thread(name="generateVehicles", target=generateVehicles, args=())
    thread2.daemon = True
    thread2.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        screen.blit(background, (0, 0))
        # Draw signals
        for i in range(noOfSignals):
            # Active pair signals display green or yellow, inactive show red.
            if i in pairMapping[activePair]:
                if signals[i].green > 0:
                    signals[i].signalText = signals[i].green
                    screen.blit(greenSignal, signalCoods[i])
                elif signals[i].yellow > 0:
                    signals[i].signalText = signals[i].yellow
                    screen.blit(yellowSignal, signalCoods[i])
            else:
                if signals[i].red <= 10:
                    signals[i].signalText = signals[i].red
                else:
                    signals[i].signalText = "---"
                screen.blit(redSignal, signalCoods[i])
            textRendered = font.render(str(signals[i].signalText), True, white, black)
            screen.blit(textRendered, signalTimerCoods[i])
        # Draw vehicles
        for vehicle in simulation:
            screen.blit(vehicle.image, (vehicle.x, vehicle.y))
            vehicle.move()
        pygame.display.update()

if __name__ == '__main__':
    image_uploader()
    vehicle_counter()
    Main()
