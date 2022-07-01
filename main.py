import pygame as pg
import numpy as np
import os
from typing import *


class Field:
    def __init__(self, shape: tuple[int, int]):
        self.__field = np.zeros(shape, dtype=np.int8)

    def __str__(self) -> str:
        return f'{self.__field}'

    def __repr__(self) -> str:
        return f'Field({self.__field.shape})'

    def clear(self):
        self.__field[:] = np.zeros(self.__field.shape, dtype=np.int8)

    def print(self, pretty_print=True):
        if pretty_print:
            character_replacement = {0: '*', 1: '@', 2: '#'}
            for index in range(self.__field.shape[0]):
                for _index in range(self.__field.shape[1]):
                    value = self.__field[index, _index]
                    if value in character_replacement:
                        print(character_replacement[value], end=' ')
                    else:
                        print(value, end=' ')
                print()
        else:
            print(self)

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
        self.__previous_pos = np.array([-1, -1])
        self.__movement: np.array = np.zeros(2, dtype=np.int8)
        self.__is_alive = True
        self.__tail = Tail(self)
        self.write_to_array()

    def move(self):
        next_pos = self.pos + self.movement
        if not self.check_for_obstacle(next_pos) and self.is_alive and any(self.movement != 0):
            self.pos = self.pos + self.movement
        elif self.check_for_obstacle(next_pos):
            self.__is_alive = False
        self.write_to_array()
        self.__tail.write_to_array()

    def change_movement_direction(self, key: Literal[pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT]):
        directions = {pg.K_UP: [-1, 0], pg.K_DOWN: [1, 0], pg.K_LEFT: [0, -1], pg.K_RIGHT: [0, 1]}
        if key in directions and not all(self.__movement == -np.array(directions[key])):
            self.movement = directions[key]

    def check_for_obstacle(self, pos: Sequence) -> bool:
        pos = np.array(pos)
        return not (all(pos + 1 <= self.field.field.shape) and all(pos >= 0))

    def write_to_array(self):
        self.field.field[self.pos[0], self.pos[1]] = 1

    def print_debug_info(self):
        print(f'pos: {self.pos}\n'
              f'previous_pos: {self.previous_pos}\n'
              f'movement: {self.movement}\n'
              f'is_alive: {self.is_alive}\n'
              f'tail_elements_pos: {self.tail.tail_elements_pos}')

    @property
    def pos(self):
        return self.__pos

    @pos.setter
    def pos(self, value):
        self.__previous_pos = self.pos
        self.__pos = np.array(value)
        self.__tail.update_pos()

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

    @property
    def tail(self):
        return self.__tail


class Tail:
    def __init__(self, _head: Head):
        self.__head = _head
        self.__tail_elements_pos: np.array = np.array([[-1, -1]])

    def add_new_element(self, amount=1):
        for _ in range(amount):
            unprepared_array = np.append(self.__tail_elements_pos, [-1, -1])
            self.__tail_elements_pos = unprepared_array.reshape((unprepared_array.shape[0] // 2, 2))

    def update_pos(self):
        if any(self.__head.pos != self.__tail_elements_pos[0]):
            for index in range(len(self.__tail_elements_pos)):
                if index != len(self.__tail_elements_pos) - 1:
                    self.__tail_elements_pos[index] = self.__tail_elements_pos[index + 1]
                else:
                    self.__tail_elements_pos[index] = self.__head.previous_pos[:]
        self.write_to_array()

    def write_to_array(self):
        for element_pos in self.__tail_elements_pos:
            if all(element_pos != np.array([-1, -1])):
                self.__head.field.field[element_pos[0], element_pos[1]] = 2

    @property
    def tail_elements_pos(self):
        return self.__tail_elements_pos


def main():
    pg.init()
    clock = pg.time.Clock()
    # the screen variable for a future
    screen = pg.display.set_mode((1, 1))

    field = Field((21, 21))
    head = Head(field, (10, 10))
    head.tail.add_new_element(3)
    time = 0

    while True:
        head.print_debug_info()
        for event in pg.event.get():
            [exit() for _ in ' ' if event.type == pg.QUIT]
            if event.type == pg.KEYDOWN:
                head.change_movement_direction(event.key)
        os.system('cls')
        if time % 5 == 0:
            field.clear()
            head.move()
        field.print()
        clock.tick(60)
        time += 1


if __name__ == '__main__':
    main()
