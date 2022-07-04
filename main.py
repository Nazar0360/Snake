import pygame as pg
import numpy as np
from os import system
from os.path import exists
from typing import *


def find(array, value):
    for index, element in enumerate(array):
        if list(element) == list(value):
            return index
    return []


# just “in” doesn't work correctly
def in_array(array, value):
    return list(value) in list(map(lambda x: list(x), array))


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
            character_replacement = {0: '.', 1: '@', 2: '*', 3: '+'}
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

    @staticmethod
    def check_for_objects_at_the_position(head, pos) -> dict:
        """
        It checks if the head is at the position, if the tail is at the position, and if the food is at the position

        :param head: the head of the snake
        :param pos: the position to check
        :return: A dictionary with the keys head, tail and food.
        """
        pos = np.array(pos)
        is_here_head = all(head.pos == pos)
        is_here_tail = in_array(head.tail.tail_elements_pos[1:], pos)
        is_here_food = in_array(head.food.food_pos, pos)
        return dict(head=is_here_head, tail=is_here_tail, food=is_here_food)

    @property
    def field(self):
        return self.__field

    @field.setter
    def field(self, value: np.array):
        self.__field = value


class Head:
    def __init__(self, _field: Field, pos):
        self.__moves_per_second = 10
        self.__field = _field

        self.__pos: np.array = np.array(pos)
        self.__previous_pos = np.array([-1, -1])
        self.__movement: np.array = np.zeros(2, dtype=np.int8)

        self.__is_alive = True
        self.__tail = Tail(self)

        self.__food = Food(self)
        self.__food.create_food(3)

        self.put_on_the_field()

    def move(self):
        next_pos = self.pos + self.movement
        if not self.check_for_obstacle(next_pos) and self.is_alive and any(self.movement != 0):
            self.pos = self.pos + self.movement
        elif self.check_for_obstacle(next_pos):
            self.__is_alive = False

        self.__tail.put_on_the_field()
        self.put_on_the_field()

    def change_movement_direction(self, key: Literal[pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT]):
        directions = {pg.K_UP: [-1, 0], pg.K_DOWN: [1, 0], pg.K_LEFT: [0, -1], pg.K_RIGHT: [0, 1]}
        if key in directions:
            if any(self.pos + directions[key] != self.previous_pos):
                self.movement = directions[key]

    def check_for_obstacle(self, pos: Sequence) -> bool:
        pos = np.array(pos)
        pos_is_tail = self.field.check_for_objects_at_the_position(self, pos)['tail']
        return any(pos + 1 > self.field.field.shape) or any(pos < 0) or pos_is_tail

    def eat(self, increase_tail_length=True, create_food=True, increase_speed=None):
        if self.field.check_for_objects_at_the_position(self, self.pos)['food']:
            if increase_tail_length:
                self.__tail.add_new_element()
            self.food.destroy_food_at_pos(self.pos)
            if create_food:
                self.food.create_food()
            if increase_speed:
                self.moves_per_second = self.moves_per_second + increase_speed

    def put_on_the_field(self):
        self.field.field[self.pos[0], self.pos[1]] = 1

    def print_debug_info(self):
        print(f'pos: {self.pos}, '
              f'previous_pos: {self.previous_pos}, '
              f'movement: {self.movement}, '
              f'is_alive: {self.is_alive}, '
              f'moves_per_second: {self.moves_per_second}\n'
              f'tail_elements_pos: {list(self.tail.tail_elements_pos)}\n'
              f'food_pos: {list(self.food.food_pos)}')

    @property
    def pos(self):
        return self.__pos

    @pos.setter
    def pos(self, value):
        self.__previous_pos = self.pos
        self.__pos = np.array(value)
        self.eat()
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

    @property
    def food(self):
        return self.__food

    @property
    def moves_per_second(self):
        return self.__moves_per_second

    @moves_per_second.setter
    def moves_per_second(self, value):
        if isinstance(value, int) and value > 0:
            self.__moves_per_second = value


class Tail:
    def __init__(self, _head: Head):
        self.__head = _head
        self.__tail_elements_pos: np.array = np.array([[-1, -1]])

    def add_new_element(self, amount=1):
        for _ in range(amount):
            unprepared_array = np.append([-1, -1], self.__tail_elements_pos, )
            self.__tail_elements_pos = unprepared_array.reshape((unprepared_array.shape[0] // 2, 2))

    def update_pos(self):
        """
        If the head's position is different from the previous position, then the last element of the
        tail_elements_pos list is set to the previous position of the head, and the rest of the elements are set to
        the next element in the list
        """
        if any(self.__head.pos != self.__head.previous_pos):
            for index in range(len(self.__tail_elements_pos)):
                if index == len(self.__tail_elements_pos) - 1:
                    self.__tail_elements_pos[index] = self.__head.previous_pos
                else:
                    self.__tail_elements_pos[index] = self.__tail_elements_pos[index + 1]

        self.put_on_the_field()

    def put_on_the_field(self):
        for element_pos in self.__tail_elements_pos:
            if all(element_pos != np.array([-1, -1])):
                self.__head.field.field[element_pos[0], element_pos[1]] = 2

    @property
    def tail_elements_pos(self):
        return self.__tail_elements_pos


class Food:
    def __init__(self, _head: Head):
        self.__head = _head
        self.__food_pos = np.array([[-1, -1]], dtype=int)

    def create_food(self, amount=1, pos=None):
        for _ in range(amount):
            if not pos:
                _food_pos = np.random.randint(self.__head.field.field.shape)
                while any(self.__head.field.check_for_objects_at_the_position(self.__head, _food_pos).values()):
                    _food_pos = np.random.randint(self.__head.field.field.shape)
            else:
                _food_pos = np.array(pos)
            self.__food_pos = np.append(self.__food_pos, np.array([_food_pos]), 0)

        self.put_on_the_field()

    def destroy_food_at_pos(self, pos):
        self.__food_pos = np.delete(self.food_pos, find(self.food_pos, pos), 0)

    def put_on_the_field(self):
        for element_pos in self.__food_pos:
            if all(element_pos != np.array([-1, -1])):
                self.__head.field.field[element_pos[0], element_pos[1]] = 3

    @property
    def food_pos(self):
        return self.__food_pos


def main(print_debug_info=True):
    # this will be needed when the pygame screen is added
    use_console = exists('.\\main.py')

    pg.init()
    clock = pg.time.Clock()

    # the screen variable for a future
    screen = pg.display.set_mode((1, 1))

    field = Field((21, 21))
    head = Head(field, (10, 10))
    time = 0

    while True:
        for event in pg.event.get():
            [exit() for _ in ' ' if event.type == pg.QUIT]
            if event.type == pg.KEYDOWN:
                head.change_movement_direction(event.key)

        if float('inf') != clock.get_fps() > 0 == time % (
                clock.get_fps() // min(head.moves_per_second, int(clock.get_fps()))):
            field.clear()
            head.food.put_on_the_field()
            head.move()

        if use_console:
            system('cls')
            field.print()
            if print_debug_info:
                head.print_debug_info()

        time += 1
        clock.tick()


if __name__ == '__main__':
    main(False)
