import pygame as pg
import numpy as np
import os
from typing import *

pg.init()
clock = pg.time.Clock()
screen = pg.display.set_mode((1, 1))


class Field:

    def __init__(self, shape: tuple[int, int]):
        self.__field = np.zeros(shape, dtype=np.int8)

    def __str__(self) -> str:
        return f'{self.__field}'

    def __repr__(self) -> str:
        return f'Field({self.__field.shape})'

    def reload(self):
        self.__field[:] = np.zeros(self.__field.shape, dtype=np.int8)

    @property
    def field(self):
        return self.__field

    @field.setter
    def field(self, value: np.array):
        self.__field = value


class Head:
    def __init__(self, _field: Field, pos):
        self.__field = _field
        self.__pos: np.array = np.array(pos)
        self.__previous_pos = None
        self.__movement: np.array = np.zeros(2, dtype=np.int8)
        self.__is_alive = True
        self.__tail = Tail(self)
        self.write_to_array()

    def move(self):
        next_pos = self.pos + self.movement
        if not self.check_for_obstacle(next_pos) and self.is_alive and any(self.movement != 0):
            self.pos = self.pos + self.movement
            if self.check_for_obstacle(next_pos):
                self.__is_alive = False
        self.__field.field[self.__pos[0], self.__pos[1]] = 1

    def change_movement_direction(self, key: Literal[pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT]):
        directions = {pg.K_UP: [-1, 0], pg.K_DOWN: [1, 0], pg.K_LEFT: [0, -1], pg.K_RIGHT: [0, 1]}
        if key in directions.keys() and not all(self.__movement == -np.array(directions[key])):
            self.movement = directions[key]

    def check_for_obstacle(self, pos: Sequence) -> bool:
        pos = np.array(pos)
        return not all(pos + 1 <= self.field.field.shape) and all(pos >= 0)

    def write_to_array(self):
        self.field.field[self.pos[0], self.pos[1]] = 1

    @property
    def pos(self):
        return self.__pos

    @pos.setter
    def pos(self, value):
        self.__previous_pos = self.pos
        self.__pos = np.array(value)
        self.__tail.move()

    @property
    def movement(self):
        return self.__movement

    @movement.setter
    def movement(self, value):
        self.__movement = np.array(value)

    @property
    def is_alive(self):
        return self.__is_alive

    @property
    def field(self):
        return self.__field

    @property
    def previous_pos(self):
        return self.__previous_pos


class Tail:
    def __init__(self, next_part):
        self.__pos = None
        self.__previous_pos = None
        self.__next_part: Tail | Head = next_part
        self.__previous_part: Tail | None = None
        part: Tail | Head = next_part
        _id = 0
        while not isinstance(part, Head):
            part = part.next_part
            _id += 1
        self.__head: Head = part
        self.__id = _id

    def add_new_tail(self):
        last_part: Tail | None = self.__previous_part
        if last_part is not None:
            while True:
                if last_part.__previous_part is None:
                    break
                last_part = last_part.__previous_part
        if last_part is None:
            last_part = self
        with open('f.txt', 'w') as f:
            f.write(f'{last_part=}, {last_part.__previous_part=}')
        last_part.__previous_part = Tail(last_part)

    def move(self):
        self.pos = self.__next_part.previous_pos
        if self.__previous_part is not None:
            self.__previous_part.move()

    @property
    def next_part(self):
        return self.__next_part

    @property
    def pos(self):
        return self.__pos

    @pos.setter
    def pos(self, value):
        self.__previous_pos = self.pos
        self.__pos = value
        if self.__pos is not None:
            self.__head.field.field[self.pos[0], self.pos[1]] = 2

    @property
    def previous_pos(self):
        return self.__previous_pos


field = Field((21, 21))
head = Head(field, (10, 10))
time = 0

while True:
    print(f'pos: {head.pos}\n'f'movement: {head.movement}\nis_alive: {head.is_alive}\n'
          f'previous_pos: {head.previous_pos}')
    for event in pg.event.get():
        [exit() for _ in ' ' if event.type == pg.QUIT]
        if event.type == pg.KEYDOWN:
            head.change_movement_direction(event.key)
    os.system('cls')
    if time % 5 == 0:
        field.reload()
        head.move()
    print(field)
    clock.tick(60)
    time += 1
