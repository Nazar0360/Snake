import pygame as pg
import numpy as np
from os import system
from os.path import exists
from typing import *

time = 0

pg.init()
clock = pg.time.Clock()


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
        self.__snake_heads = []
        self.__food = None
        self.__field = np.zeros(shape, dtype=np.int8)

    def __str__(self) -> str:
        return f'{self.__field}'

    def __repr__(self) -> str:
        return f'Field({self.__field.shape})'

    def update(self):
        self.__field[:] = np.zeros(self.__field.shape, dtype=np.int8)

        for head in self.__snake_heads:
            self.field[head.pos[0], head.pos[1]] = 1

            for element_pos in head.tail.tail_elements_pos:
                if all(element_pos != np.array([-1, -1])):
                    self.field[element_pos[0], element_pos[1]] = 2

        if self.food is not None:
            for element_pos in self.food.food_pos:
                if all(element_pos != np.array([-1, -1])):
                    self.field[element_pos[0], element_pos[1]] = 3

    def print(self, pretty_print=True, debug=False):
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

        if debug:
            self.print_debug_info()

    def add_snake(self, head):
        if isinstance(head, Head):
            self.__snake_heads.append(head)
        else:
            raise TypeError('head must be an instance of Head')

    def check_for_objects_at_the_position(self, pos, exclude_head=None) -> dict:
        """
        It checks if there is a snake head, snake tail, or food at the position

        :param pos: The position to check for objects
        :param exclude_head: This is the head of the snake that is currently moving. We don't want to check if the head
        is in the position of the head that is currently moving
        :return: A dictionary with the keys head, tail, and food.
        """

        pos = np.array(pos)
        is_here_head = is_here_tail = False
        for head in self.__snake_heads:
            if head is not exclude_head:
                is_here_head = all(head.pos == pos) or is_here_head
            tail_elements_pos = head.tail.tail_elements_pos
            if head.is_alive:
                tail_elements_pos = tail_elements_pos[1:]
            is_here_tail = in_array(tail_elements_pos, pos) or is_here_tail

        if self.food is not None:
            is_here_food = in_array(self.food.food_pos, pos)
        else:
            is_here_food = False
        return dict(head=is_here_head, tail=is_here_tail, food=is_here_food)

    def print_debug_info(self):
        print({x: x.__dict__ for x in [self.__food]+self.__snake_heads})

    @property
    def field(self):
        return self.__field

    @field.setter
    def field(self, value: np.array):
        self.__field = value

    @property
    def food(self):
        return self.__food

    @food.setter
    def food(self, food):
        if isinstance(food, Food):
            self.__food = food
        else:
            raise TypeError("food must be an instance of Food")

    @property
    def snake_heads(self):
        return self.__snake_heads


class Head:
    def __init__(self, _field: Field, pos=(0, 0), controls=(pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT)):
        self.__moves_per_second = 5
        self.__field = _field
        self.__field.add_snake(self)

        self.__pos: np.array = np.array(pos)
        self.__previous_pos = np.array([-1, -1])
        self.__movement: np.array = np.zeros(2, dtype=np.int8)

        self.__is_alive = True
        self.__tail = Tail(self)

        self.__controls = list(controls)

    def move(self, move_anyway=False):
        fps = min(clock.get_fps(), 120)

        if fps > 0 == time % (fps // min(self.moves_per_second, int(clock.get_fps()))) or move_anyway:
            next_pos = self.pos + self.movement
            if not self.check_for_obstacle(next_pos) and self.is_alive and any(self.movement != 0):
                self.pos = self.pos + self.movement
            elif self.check_for_obstacle(next_pos):
                self.__is_alive = False

    def change_movement_direction(self, key):
        directions = {x: y for x, y in zip(self.__controls, [[-1, 0], [1, 0], [0, -1], [0, 1]])}
        if key in directions:
            if any(self.pos + directions[key] != self.previous_pos):
                self.movement = directions[key]

    def check_for_obstacle(self, pos: Sequence) -> bool:
        pos = np.array(pos)
        pos_is_head = self.field.check_for_objects_at_the_position(pos, self)['head']
        pos_is_tail = self.field.check_for_objects_at_the_position(pos)['tail']
        return any(pos + 1 > self.field.field.shape) or any(pos < 0) or pos_is_tail or pos_is_head

    def eat(self, increase_tail_length=True, create_food=True, increase_speed=None):
        if self.field.check_for_objects_at_the_position(self.pos)['food']:
            if increase_tail_length:
                self.__tail.add_new_element()
            self.food.destroy_food_at_pos(self.pos)
            if create_food:
                self.food.create_food()
            if increase_speed:
                self.moves_per_second = self.moves_per_second + increase_speed

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
        return self.__field.food

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
            unprepared_array = np.append([-1, -1], self.__tail_elements_pos)
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

    @property
    def tail_elements_pos(self):
        return self.__tail_elements_pos


class Food:
    def __init__(self, _field: Field):
        self.__field = _field
        self.__field.food = self
        self.__food_pos = np.array([[-1, -1]], dtype=int)

    def create_food(self, amount=1, pos=None):
        for _ in range(amount):
            if not pos:
                _food_pos = np.random.randint(self.__field.field.shape)
                while any(self.__field.check_for_objects_at_the_position(_food_pos).values()):
                    _food_pos = np.random.randint(self.__field.field.shape)
            else:
                _food_pos = np.array(pos)
            self.__food_pos = np.append(self.__food_pos, np.array([_food_pos]), 0)

    def destroy_food_at_pos(self, pos):
        self.__food_pos = np.delete(self.food_pos, find(self.food_pos, pos), 0)

    @property
    def food_pos(self):
        return self.__food_pos


def main():
    global time

    # this will be needed when the pygame screen is added
    use_console = exists('.\\main.py')

    # the screen variable for a future
    screen = pg.display.set_mode((1, 1))

    field = Field((21, 21))

    # 2+ player mode have some bugs
    Head(field, (9, 10))
    Head(field, (11, 10), (pg.K_w, pg.K_s, pg.K_a, pg.K_d))

    food = Food(field)
    food.create_food(3)

    while True:
        for event in pg.event.get():
            [exit() for _ in ' ' if event.type == pg.QUIT]
            if event.type == pg.KEYDOWN:
                for head in field.snake_heads:
                    head.change_movement_direction(event.key)

        [head.move() for head in field.snake_heads]
        field.update()

        if use_console:
            system('cls')
            field.print()

        time += 1
        clock.tick()


if __name__ == '__main__':
    main()
