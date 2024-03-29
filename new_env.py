import random
import pyglet
import numpy as np
from enum import Enum
from math import floor


def value_to_tuple(value):
    return (value % 5, floor(value / 5))

def tuple_to_value(tuple):
    return tuple[0] + (tuple[1] * 5)


class Actions(Enum):
    FORWARD = 1
    TURN_LEFT = 2
    TURN_RIGHT = 3
    PICKUP = 4
    DROPOFF = 5


class SquareType(Enum):
    EMPTY = 1
    PICKUP = 2
    DROPOFF = 3


class TaxiDriverBoard:
    def __init__(self, size):
        self.size = size
        self.init_binary_to_index()
        self.init_reward_table()
        self.reset()

    def init_binary_to_index(self):
        self.binary_to_index = {}
        for taxiLoc in range(25):
            for taxiDir in range(4):
                for pickupLoc in range(25):
                    for dropoffLoc in range(25):
                        self.binary_to_index[self.values_to_binary(taxiLoc, taxiDir, pickupLoc, dropoffLoc)] = len(self.binary_to_index)

    def values_to_binary(self, taxiLoc, taxiDir, pickupLoc, dropoffLoc):
        return taxiLoc + (taxiDir << 5) + (pickupLoc << 7) + (dropoffLoc << 12)
    
    def values_to_index(self, taxiLoc, taxiDir, pickupLoc, dropoffLoc):
        return self.binary_to_index[self.values_to_binary(taxiLoc, taxiDir, pickupLoc, dropoffLoc)]

    def do_action(self, action):
        if action == Actions.FORWARD:
            loc = self.taxi.get_forward()
            if loc[0] > -1 and loc[0] < self.size[0] and \
                loc[1] > -1 and loc[1] < self.size[1]:
                self.taxi.move_to(loc)
        elif action == Actions.TURN_LEFT:
            self.taxi.turn_left()
        elif action == Actions.TURN_RIGHT:
            self.taxi.turn_right()
        elif action == Actions.PICKUP:
            if self.taxi.location == self.pickup:
                self.taxi.pickup()
                self.pickup = None
        elif action == Actions.DROPOFF:
            if self.taxi.location == self.dropoff and self.taxi.has_pickup:
                return True
        return False
    
    def set_state(self, state):
        self.taxi.location = value_to_tuple(state[0])
        self.taxi.direction = Direction(state[1])
        self.pickup = state[2]
        self.dropoff = state[3]
    
    def get_state(self):
        return self.values_to_index(tuple_to_value(self.taxi.location), self.taxi.direction.value, self.pickup, self.dropoff)

    def init_reward_table(self):
        self.reward_table = np.empty([len(self.binary_to_index)], dtype=object)
        for taxiLoc in range(25):
            for taxiDir in range(4):
                for pickupLoc in range(25):
                    for dropoffLoc in range(25):
                        current_state = self.values_to_index(taxiLoc, taxiDir, pickupLoc, dropoffLoc)
                        forward_state = current_state
                        turn_right_state = self.values_to_index(taxiLoc, (taxiDir - 1) % 4, pickupLoc, dropoffLoc)
                        turn_left_state = self.values_to_index(taxiLoc, (taxiDir + 1) % 4, pickupLoc, dropoffLoc)
                        pickup_state = current_state
                        pickup_reward = -10
                        dropoff_successful = False
                        dropoff_reward = -10
                        if taxiDir == 0 and taxiLoc - 5 > -1:
                            forward_state = self.values_to_index(taxiLoc - 5, taxiDir, pickupLoc, dropoffLoc)
                        if taxiDir == 1 and taxiLoc % 5 != 0:
                            forward_state = self.values_to_index(taxiLoc - 1, taxiDir, pickupLoc, dropoffLoc)
                        if taxiDir == 2 and taxiLoc + 5 < 25:
                            forward_state = self.values_to_index(taxiLoc + 5, taxiDir, pickupLoc, dropoffLoc)
                        if taxiDir == 3 and taxiLoc % 5 != 4:
                            forward_state = self.values_to_index(taxiLoc + 1, taxiDir, pickupLoc, dropoffLoc)
                        if pickupLoc == taxiLoc and not (pickupLoc == dropoffLoc):
                            pickup_state = self.values_to_index(taxiLoc, taxiDir, dropoffLoc, dropoffLoc)
                            pickup_reward = 10
                        if taxiLoc == dropoffLoc and pickupLoc == dropoffLoc:
                            dropoff_successful = True
                            dropoff_reward = 10
                        self.reward_table[current_state] = {
                            0: (1.0, forward_state, -1, False),
                            1: (1.0, turn_left_state, -1, False),
                            2: (1.0, turn_right_state, -1, False),
                            3: (1.0, pickup_state, pickup_reward, False),
                            4: (1.0, current_state, dropoff_reward, dropoff_successful)
                        }

    def reset(self):
        self.taxi = Taxi((random.randint(0, self.size[1] - 1), random.randint(0, self.size[1] - 1)))
        self.pickup = (random.randint(0, self.size[1] - 1), random.randint(0, self.size[1] - 1))
        while self.pickup == self.taxi.location:
            self.pickup = (random.randint(0, self.size[1] - 1), random.randint(0, self.size[1] - 1))
        self.dropoff = (random.randint(0, self.size[1] - 1), random.randint(0, self.size[1] - 1))
        while self.pickup == self.dropoff and self.dropoff == self.taxi.location:
            self.dropoff = (random.randint(0, self.size[1] - 1), random.randint(0, self.size[1] - 1))


class Taxi:
    def __init__(self, loc):
        self.location = loc
        self.direction = Direction.NORTH
        self.has_pickup = False
    
    def get_forward(self):
        if self.direction == Direction.NORTH:
            return (self.location[0], self.location[1] + 1)
        elif self.direction == Direction.WEST:
            return (self.location[0] - 1, self.location[1])
        elif self.direction == Direction.SOUTH:
            return (self.location[0], self.location[1] - 1)
        else:
            return (self.location[0] + 1, self.location[1])
    
    def move_to(self, loc):
        self.location = loc
    
    def turn_left(self):
        if self.direction == Direction.NORTH:
            self.direction = Direction.WEST
        elif self.direction == Direction.WEST:
            self.direction = Direction.SOUTH
        elif self.direction == Direction.SOUTH:
            self.direction = Direction.EAST
        else:
            self.direction = Direction.NORTH
    
    def turn_right(self):
        if self.direction == Direction.NORTH:
            self.direction = Direction.EAST
        elif self.direction == Direction.EAST:
            self.direction = Direction.SOUTH
        elif self.direction == Direction.SOUTH:
            self.direction = Direction.WEST
        else:
            self.direction = Direction.NORTH

    def pickup(self):
        self.has_pickup = True
            

class Direction(Enum):
    NORTH = 0
    WEST = 1
    SOUTH = 2
    EAST = 3


class Square:
    def __init__(self):
        ran = random.uniform(0, 1)
        if ran < 0.1:
            self.type = SquareType.PICKUP
        elif ran < 0.2:
            self.type = SquareType.DROPOFF
        else:
            self.type = SquareType.EMPTY
    
    def set_type(self, squareType):
        self.type = squareType


window = pyglet.window.Window(500, 500)
taxiPic = pyglet.image.load("images/taxi.png")
pickupPic = pyglet.image.load("images/pickup.png")
dropoffPic = pyglet.image.load("images/dropoff.png")

# taxi * taxi_directions * pickups * dropoffs
states = 25 * 4 * 25 * 24

def center_anchor(image):
    image.anchor_x = image.width // 2
    image.anchor_y = image.height // 2

center_anchor(taxiPic)
center_anchor(pickupPic)
center_anchor(dropoffPic)

boardPic = pyglet.image.load('images/board.png')

offsetX = 125
offsetY = 125

batch = pyglet.graphics.Batch()

taxiSprite = pyglet.sprite.Sprite(taxiPic, batch=batch)
pickupSprite = pyglet.sprite.Sprite(pickupPic, batch=batch)
dropoffSprite = pyglet.sprite.Sprite(dropoffPic, batch=batch)

game = TaxiDriverBoard((5, 5))

game.set_state((18, 3, 5, 8))
print(game.reward_table[game.values_to_index(18, 3, 5, 8)])

def set_assets():
    taxiSprite.x = game.taxi.location[0] * 50 + offsetX + 25
    taxiSprite.y = game.taxi.location[1] * 50 + offsetY + 25
    taxiSprite.rotation = -90 * game.taxi.direction.value
    if game.pickup:
        pickupSprite.x = value_to_tuple(game.pickup)[0] * 50 + offsetX + 25
        pickupSprite.y = value_to_tuple(game.pickup)[1] * 50 + offsetY + 25
    if game.dropoff:
        dropoffSprite.x = value_to_tuple(game.dropoff)[0] * 50 + offsetX + 25
        dropoffSprite.y = value_to_tuple(game.dropoff)[1] * 50 + offsetY + 25


@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.UP:
        game.do_action(Actions.FORWARD)
    elif symbol == pyglet.window.key.LEFT:
        game.do_action(Actions.TURN_LEFT)
    elif symbol == pyglet.window.key.RIGHT:
        game.do_action(Actions.TURN_RIGHT)
    elif symbol == pyglet.window.key.P:
        game.do_action(Actions.PICKUP)
    elif symbol == pyglet.window.key.D:
        if game.do_action(Actions.DROPOFF):
            print("You won!")
            game.reset()
    elif symbol == pyglet.window.key.ESCAPE:
        pyglet.app.exit()
    elif symbol == pyglet.window.key.I:
        print(game.get_state())


@window.event
def on_draw():
    set_assets()
    window.clear()
    boardPic.blit(offsetX, offsetY)
    taxiSprite.draw()
    if game.pickup:
        pickupSprite.draw()
    if game.dropoff:
        dropoffSprite.draw()



pyglet.app.run()