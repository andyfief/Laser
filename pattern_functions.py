# === Pattern Functions ===
# Each function renders a single frame and maintains its own state
# Should be called repeatedly from the persistent pattern runner

import random
import time
import math

# Global state for each pattern function
dotLR_state = {'i': 33}
dotRL_state = {'i': 96}
sideToSideDot_state = {'direction': 'RL', 'i': 96}
horizontalLineRL_state = {'i': 33}
horizontalLineLR_state = {'i': 96}
horizontalLineSideToSide_state = {'direction': 'RL', 'i': 33}
circleZoomIn_state = {'i': 0, 'direction': 1}
wiggleLine_state = {'i': 40, 'direction': 1}
crazyDots_state = {'count': 0}
crazyDots2_state = {'initialized': False}
spazzCircle_state = {'initialized': False}
spotlight_state = {'x': 0, 'y': 0, 'dx': 0, 'dy': 0, 'start_time': 0, 'duration': 0, 'initialized': False}
driftingDot_state = {'x': 0, 'y': 0, 'angle': 0, 'initialized': False}
stillBeam_state = {'x': 0, 'y': 0, 'initialized': False}
lineWithDotsRL_state = {'y': 33, 'y_direction': 1, 'x': 0, 'x_direction': 1}
twoCircleSpin_state = {'initialized': False}
voiceWave_state = {'initialized': False}

def calculateSpeedForRange(start, stop, speed):
    """
    Calculate movement speed for auto movement patterns.
    Maps speed (0-10) to DMX range (start-stop).
    """
    difference = stop - start
    movementSpeed = start + speed * (difference / 10)
    return math.floor(movementSpeed)

def dotLR(dmx, speed):
    """
    Advances one step left-to-right across DMX channel 8.
    Should be called repeatedly from outer loop.
    """
    dmx.set_channel(4, 16)
    dmx.set_channel(8, dotLR_state['i'])
    dotLR_state['i'] += 1
    
    # Wrap/reset when done
    if dotLR_state['i'] > 95:
        dotLR_state['i'] = 33
    
    time.sleep(1 / (50 * speed))

def dotRL(dmx, speed):
    """Moves a dot from right to left, one step per call."""
    dmx.set_channel(4, 16)
    dmx.set_channel(8, dotRL_state['i'])
    dotRL_state['i'] -= 1
    
    # Wrap/reset when done
    if dotRL_state['i'] < 33:
        dotRL_state['i'] = 96
    
    time.sleep(1 / (50 * speed))

def sideToSideDot(dmx, speed):
    """Oscillates a dot back and forth, one step per call."""
    dmx.set_channel(4, 16)
    
    if sideToSideDot_state['direction'] == 'RL':
        dmx.set_channel(8, sideToSideDot_state['i'])
        sideToSideDot_state['i'] -= 1
        if sideToSideDot_state['i'] < 33:
            sideToSideDot_state['direction'] = 'LR'
            sideToSideDot_state['i'] = 33
    else:  # direction == 'LR'
        dmx.set_channel(8, sideToSideDot_state['i'])
        sideToSideDot_state['i'] += 1
        if sideToSideDot_state['i'] > 95:
            sideToSideDot_state['direction'] = 'RL'
            sideToSideDot_state['i'] = 95
    
    time.sleep(1 / (50 * speed))

def horizontalLineRL(dmx, speed):
    """Sweeps a horizontal line from right to left, one step per call."""
    dmx.set_channel(4, 45)
    dmx.set_channel(8, horizontalLineRL_state['i'])
    horizontalLineRL_state['i'] += 1
    
    # Wrap/reset when done
    if horizontalLineRL_state['i'] > 95:
        horizontalLineRL_state['i'] = 33
    
    time.sleep(1 / (100 * speed))

def horizontalLineLR(dmx, speed):
    """Sweeps a horizontal line from left to right, one step per call."""
    dmx.set_channel(4, 45)
    dmx.set_channel(8, horizontalLineLR_state['i'])
    horizontalLineLR_state['i'] -= 1
    
    # Wrap/reset when done
    if horizontalLineLR_state['i'] < 33:
        horizontalLineLR_state['i'] = 96
    
    time.sleep(1 / (100 * speed))

def horizontalLineSideToSide(dmx, speed):
    """Oscillates a horizontal line back and forth, one step per call."""
    dmx.set_channel(4, 45)
    
    if horizontalLineSideToSide_state['direction'] == 'RL':
        dmx.set_channel(8, horizontalLineSideToSide_state['i'])
        horizontalLineSideToSide_state['i'] += 1
        if horizontalLineSideToSide_state['i'] > 95:
            horizontalLineSideToSide_state['direction'] = 'LR'
            horizontalLineSideToSide_state['i'] = 95
    else:  # direction == 'LR'
        dmx.set_channel(8, horizontalLineSideToSide_state['i'])
        horizontalLineSideToSide_state['i'] -= 1
        if horizontalLineSideToSide_state['i'] < 33:
            horizontalLineSideToSide_state['direction'] = 'RL'
            horizontalLineSideToSide_state['i'] = 33
    
    time.sleep(1 / (100 * speed))

def circleZoomIn(dmx, speed):
    """Zooms a circle pattern, one step per call."""
    dmx.set_channel(4, 5)
    dmx.set_channel(5, circleZoomIn_state['i'])
    
    circleZoomIn_state['i'] += 4 * circleZoomIn_state['direction']
    
    # Reverse direction at boundaries
    if circleZoomIn_state['i'] >= 127:
        circleZoomIn_state['direction'] = -1
        circleZoomIn_state['i'] = 127
    elif circleZoomIn_state['i'] <= 0:
        circleZoomIn_state['direction'] = 1
        circleZoomIn_state['i'] = 0
    
    time.sleep(1 / (100 * speed))

def crazyDots(dmx, speed):
    """Flashes dots at random positions, one flash per call."""
    dmx.set_channel(4, 16)
    dmx.set_channel(7, random.randint(0, 127))
    dmx.set_channel(8, random.randint(0, 127))
    
    crazyDots_state['count'] += 1
    if crazyDots_state['count'] > 20:
        crazyDots_state['count'] = 0
    
    time.sleep(1 / speed)

def randomSingleDot(dmx, speed):
    """Displays one random dot briefly, one position per call."""
    dmx.set_channel(4, 16)
    dmx.set_channel(7, random.randint(0, 127))
    dmx.set_channel(8, random.randint(0, 127))
    time.sleep(0.1)

def wiggleLine(dmx, speed):
    """Creates a waving line motion, one step per call."""
    dmx.set_channel(4, 51)
    dmx.set_channel(6, 33)
    dmx.set_channel(10, wiggleLine_state['i'])
    
    wiggleLine_state['i'] += wiggleLine_state['direction']
    
    # Reverse direction at boundaries
    if wiggleLine_state['i'] >= 100:
        wiggleLine_state['direction'] = -1
        wiggleLine_state['i'] = 100
    elif wiggleLine_state['i'] <= 40:
        wiggleLine_state['direction'] = 1
        wiggleLine_state['i'] = 40
    
    time.sleep(1 / (50 * speed))

def spazzCircle(dmx, speed):
    """Random circle positions, one frame per call."""
    if not spazzCircle_state['initialized']:
        dmx.set_channel(4, 5)  # Circle
        spazzCircle_state['initialized'] = True
    
    dmx.set_channel(7, random.randint(0, 127))
    dmx.set_channel(8, random.randint(0, 127))
    time.sleep(1 / (50 * speed))

def spotlight(dmx, speed):
    """Bouncing spotlight with random direction changes, one frame per call."""
    state = spotlight_state
    
    # Initialize if needed
    if not state['initialized']:
        min_bound = 47
        max_bound = 80
        state['x'] = random.uniform(min_bound, max_bound)
        state['y'] = random.uniform(min_bound, max_bound)
        
        dmx.set_channel(2, 29)  # smaller pattern size
        dmx.set_channel(4, 5)   # Circle or movement mode
        
        # Pick initial direction
        angle = random.uniform(0, 2 * math.pi)
        state['dx'] = math.cos(angle)
        state['dy'] = math.sin(angle)
        state['start_time'] = time.time()
        state['duration'] = random.uniform(1, 3)
        state['initialized'] = True
    
    # Check if we need a new direction
    if time.time() - state['start_time'] > state['duration']:
        angle = random.uniform(0, 2 * math.pi)
        state['dx'] = math.cos(angle)
        state['dy'] = math.sin(angle)
        state['start_time'] = time.time()
        state['duration'] = random.uniform(1, 3)
    
    # Update position
    min_bound = 47
    max_bound = 80
    state['x'] += state['dx'] * speed
    state['y'] += state['dy'] * speed
    
    # Bounce off edges
    if state['x'] <= min_bound:
        state['dx'] *= -1
        state['x'] = min_bound
    elif state['x'] >= max_bound:
        state['dx'] *= -1
        state['x'] = max_bound
    
    if state['y'] <= min_bound:
        state['dy'] *= -1
        state['y'] = min_bound
    elif state['y'] >= max_bound:
        state['dy'] *= -1
        state['y'] = max_bound
    
    # Send to DMX
    dmx.set_channel(7, int(state['x']))
    dmx.set_channel(8, int(state['y']))
    
    time.sleep(0.1 / speed)

def driftingDot(dmx, speed):
    """Drifting dot with organic movement, one frame per call."""
    state = driftingDot_state
    
    # Initialize if needed
    if not state['initialized']:
        min_bound = 33
        max_bound = 96
        center_x = (min_bound + max_bound) / 2
        center_y = (min_bound + max_bound) / 2
        
        state['x'] = center_x
        state['y'] = center_y
        state['angle'] = random.uniform(0, 2 * math.pi)
        state['initialized'] = True
        
        dmx.set_channel(4, 16)  # dot
    
    # Limit speed
    if speed > 3:
        speed = 3
    
    # Control parameters
    drift_strength = 0.1 * speed
    movement_speed = 2 * speed
    
    # Drift the angle slightly
    state['angle'] += random.uniform(-drift_strength, drift_strength)
    
    # Propose new position
    dx = math.cos(state['angle']) * movement_speed
    dy = math.sin(state['angle']) * movement_speed
    new_x = state['x'] + dx
    new_y = state['y'] + dy
    
    # Reflect angle if hitting bounds
    min_bound = 33
    max_bound = 96
    
    if new_x < min_bound or new_x > max_bound:
        state['angle'] = math.pi - state['angle']
        new_x = state['x']  # cancel movement in x
    if new_y < min_bound or new_y > max_bound:
        state['angle'] = -state['angle']
        new_y = state['y']  # cancel movement in y
    
    # Commit new position
    state['x'] = new_x
    state['y'] = new_y
    
    # Send to DMX
    dmx.set_channel(7, int(state['x']))
    dmx.set_channel(8, int(state['y']))
    
    time.sleep(0.05)

def stillBeam(dmx, speed):
    """Static beam at random position, sets once then holds."""
    if not stillBeam_state['initialized']:
        dmx.set_channel(4, 16)  # dot
        stillBeam_state['x'] = random.randint(0, 127)
        stillBeam_state['y'] = random.randint(0, 127)
        dmx.set_channel(7, stillBeam_state['x'])
        dmx.set_channel(8, stillBeam_state['y'])
        stillBeam_state['initialized'] = True
    
    # Just maintain the position
    dmx.set_channel(7, stillBeam_state['x'])
    dmx.set_channel(8, stillBeam_state['y'])
    time.sleep(0.1)

def lineWithDotsRL(dmx, speed):
    """Horizontal line with dots moving within it, one frame per call."""
    state = lineWithDotsRL_state
    speed = 1/10 * speed
    
    # Setup channels for line and dots
    dmx.set_channel(4, 45)   # vertical line
    dmx.set_channel(6, 32)   # rotate 90 degrees
    dmx.set_channel(18, 23)  # laser 2 on
    dmx.set_channel(19, 0)   # pattern size 100%
    dmx.set_channel(21, 57)  # spaced dots, laser 2
    dmx.set_channel(23, 32)  # rotate 90 degrees
    
    # Define bounds
    min_y = 33
    max_y = 95
    min_x = 0
    max_x = 127
    
    # Update vertical pan position (slower)
    state['y'] += state['y_direction']
    if state['y'] >= max_y:
        state['y'] = max_y
        state['y_direction'] = -1
    elif state['y'] <= min_y:
        state['y'] = min_y
        state['y_direction'] = 1
    
    # Update horizontal dot position (faster)
    state['x'] += state['x_direction'] * 3
    if state['x'] >= max_x:
        state['x'] = 0
    
    # Apply positions to DMX
    dmx.set_channel(7, state['y'])   # vertical pan main line
    dmx.set_channel(24, state['y'])  # move line down/up together
    dmx.set_channel(25, state['x'])  # dots side to side inside the line
    
    time.sleep(0.02 / speed)

def crazyDots2(dmx, speed):
    """Less random but funky movement using auto patterns."""
    if not crazyDots2_state['initialized']:
        dmx.set_channel(4, 78)
        crazyDots2_state['initialized'] = True
    
    movementSpeed = calculateSpeedForRange(128, 159, speed)
    if movementSpeed > 159:
        movementSpeed = 159
    
    dmx.set_channel(9, movementSpeed)
    dmx.set_channel(10, movementSpeed)
    time.sleep(0.05)

def twoCircleSpin(dmx, speed):
    """Two circles spinning pattern."""
    if not twoCircleSpin_state['initialized']:
        dmx.set_channel(4, 83)
        twoCircleSpin_state['initialized'] = True
    
    movementSpeed = calculateSpeedForRange(192, 223, speed)
    dmx.set_channel(6, movementSpeed)
    time.sleep(0.05)

def voiceWave(dmx, speed):
    """Voice wave pattern using circle with auto movement."""
    if not voiceWave_state['initialized']:
        dmx.set_channel(4, 5)  # circle
        voiceWave_state['initialized'] = True
    
    movementSpeed = calculateSpeedForRange(128, 159, speed)
    dmx.set_channel(9, movementSpeed)
    time.sleep(0.05)

# Reset functions to initialize pattern states
def reset_pattern_states():
    """Reset all pattern states to their initial values."""
    global dotLR_state, dotRL_state, sideToSideDot_state
    global horizontalLineRL_state, horizontalLineLR_state, horizontalLineSideToSide_state
    global circleZoomIn_state, wiggleLine_state, crazyDots_state, crazyDots2_state
    global spazzCircle_state, spotlight_state, driftingDot_state, stillBeam_state
    global lineWithDotsRL_state, twoCircleSpin_state, voiceWave_state
    
    dotLR_state = {'i': 33}
    dotRL_state = {'i': 96}
    sideToSideDot_state = {'direction': 'RL', 'i': 96}
    horizontalLineRL_state = {'i': 33}
    horizontalLineLR_state = {'i': 96}
    horizontalLineSideToSide_state = {'direction': 'RL', 'i': 33}
    circleZoomIn_state = {'i': 0, 'direction': 1}
    wiggleLine_state = {'i': 40, 'direction': 1}
    crazyDots_state = {'count': 0}
    crazyDots2_state = {'initialized': False}
    spazzCircle_state = {'initialized': False}
    spotlight_state = {'x': 0, 'y': 0, 'dx': 0, 'dy': 0, 'start_time': 0, 'duration': 0, 'initialized': False}
    driftingDot_state = {'x': 0, 'y': 0, 'angle': 0, 'initialized': False}
    stillBeam_state = {'x': 0, 'y': 0, 'initialized': False}
    lineWithDotsRL_state = {'y': 33, 'y_direction': 1, 'x': 0, 'x_direction': 1}
    twoCircleSpin_state = {'initialized': False}
    voiceWave_state = {'initialized': False}

# All available pattern functions:
# dotLR, dotRL, sideToSideDot, horizontalLineRL, horizontalLineLR, horizontalLineSideToSide,
# circleZoomIn, crazyDots, randomSingleDot, wiggleLine, spazzCircle, spotlight, driftingDot,
# stillBeam, lineWithDotsRL, crazyDots2, twoCircleSpin, voiceWave

# Pattern groups dictionary - fill in the functions as needed
pattern_groups = {
    1: [stillBeam, dotLR, dotRL, sideToSideDot, randomSingleDot, horizontalLineRL, horizontalLineLR, horizontalLineSideToSide],  # Fill with desired functions
    2: [circleZoomIn, crazyDots, crazyDots2, lineWithDotsRL, spazzCircle],  # Fill with desired functions  
    3: [wiggleLine, spotlight, driftingDot, voiceWave, twoCircleSpin],  # Fill with desired functions
}