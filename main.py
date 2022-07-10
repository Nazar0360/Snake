import pygame as pg
import numpy as np
from os import system
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
        self.__boosts = None
        self.__field = np.zeros(shape, dtype=np.int8)

    def __str__(self) -> str:
        return f'{self.__field}'

    def __repr__(self) -> str:
        return f'Field({self.__field.shape})'

    def update(self):
        self.__field[:] = np.zeros(self.__field.shape, dtype=np.int8)

        if self.boosts is not None:
            for boost in self.boosts.boosts:
                if all(boost[:-1] != np.array([-1, -1])):
                    self.field[boost[0], boost[1]] = boost[2] + 4

        for head in self.__snake_heads:
            self.field[head.pos[0], head.pos[1]] = 1

            for element_pos in head.tail.tail_elements_pos:
                if all(element_pos != np.array([-1, -1])):
                    self.field[element_pos[0], element_pos[1]] = 2

    def print(self, pretty_print=True, debug=False):
        if pretty_print:
            # hint: here you can change the design {0: ' ', 1: '#', 2: '$', 3: '%'...}
            character_replacement = {0: '.', 1: '@', 2: '*', 3: '#', 4: '+', 5: '-', 6: '?'}
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
        It checks if there is a snake head, snake tail, or boost at the position

        :param pos: the position to check
        :param exclude_head: The head to exclude from the check
        :return: A dictionary with the keys head, tail, and boost.
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

        is_here_boost = False
        if self.boosts is not None:
            for i in range(self.boosts.boost_types_number):
                is_here_boost = in_array(self.boosts.boosts, np.append(pos, [i], 0))
                if is_here_boost:
                    break

        return dict(head=is_here_head, tail=is_here_tail, boost=is_here_boost)

    def print_debug_info(self):
        print({x: x.__dict__ for x in [self.__boosts]+self.__snake_heads})

    @property
    def field(self):
        return self.__field

    @field.setter
    def field(self, value: np.array):
        self.__field = value

    @property
    def boosts(self):
        return self.__boosts

    @boosts.setter
    def boosts(self, boosts):
        if isinstance(boosts, Boosts):
            self.__boosts = boosts
        else:
            raise TypeError("boosts must be an instance of Boosts")

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
        self.__score = 0

        self.__tail = Tail(self)

        self.__controls = list(controls)

    def move(self, move_anyway=False):
        fps = min(clock.get_fps(), 10_000)

        if fps > 0 == time % (fps // min(self.moves_per_second, int(fps))) or move_anyway:
            next_pos = self.pos + self.movement
            if not self.check_for_obstacle(next_pos) and self.is_alive and any(self.movement != 0):
                self.pos = self.pos + self.movement
            elif self.check_for_obstacle(next_pos):
                self.__is_alive = False

    def change_movement_direction(self, key):
        directions = {x: y for x, y in zip(self.__controls, [[-1, 0], [1, 0], [0, -1], [0, 1]])}
        if key in directions:
            if any(self.pos + directions[key] != self.previous_pos) or not len(self.tail.tail_elements_pos):
                self.movement = directions[key]

    def check_for_obstacle(self, pos: Sequence) -> bool:
        pos = np.array(pos)
        pos_is_head = self.field.check_for_objects_at_the_position(pos, self)['head']
        pos_is_tail = self.field.check_for_objects_at_the_position(pos)['tail']
        return any(pos + 1 > self.field.field.shape) or any(pos < 0) or pos_is_tail or pos_is_head

    def eat(self, create_boost=True, increase_speed=0, increase_score=1):
        if self.field.check_for_objects_at_the_position(self.pos)['boost']:
            self.__score += increase_score

            boost_type = self.boosts.destroy_boost_at_pos(self.pos)
            match boost_type:
                case 0:
                    self.tail.add_new_element()

                case 1:
                    self.tail.delete_last_element()

                case 2:
                    self.tail.add_new_element(np.random.randint(-2, 2))

            if create_boost:
                self.boosts.create_boost()

            self.moves_per_second = self.moves_per_second + increase_speed

    @property
    def pos(self):
        return self.__pos

    @pos.setter
    def pos(self, value):
        self.__previous_pos = self.pos
        self.__pos = np.array(value)

        '''
        hint: here you can turn off the creating boosts, you can also set the value by which
        the head speed (moves per second [integer]) or score increases each time when the snake eats (False, 1, 5)
        '''

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
    def boosts(self):
        return self.__field.boosts

    @property
    def moves_per_second(self):
        return self.__moves_per_second

    @moves_per_second.setter
    def moves_per_second(self, value):
        if isinstance(value, int) and value > 0:
            self.__moves_per_second = value

    @property
    def score(self):
        return self.__score


class Tail:
    def __init__(self, _head: Head):
        self.__head = _head
        self.__tail_elements_pos: np.array = np.array([[-1, -1]])

    def add_new_element(self, amount=1):
        if amount < 0:
            self.delete_last_element(abs(amount))
            return

        for _ in range(amount):
            self.__tail_elements_pos = np.append([[-1, -1]], self.__tail_elements_pos, 0)

    def delete_last_element(self, amount=1):
        if amount < 0:
            self.add_new_element(abs(amount))
            return

        for _ in range(amount):
            if len(self.tail_elements_pos) > 0:
                self.__tail_elements_pos = np.delete(self.tail_elements_pos, 0, 0)

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


class Boosts:
    def __init__(self, _field: Field):
        self.__field = _field
        self.__field.boosts = self
        self.__boosts = np.array([[-1, -1, -1]], dtype=int)
        self.__boost_types_number = 3

    def create_boost(self, amount=1, pos=None, boost_type=None):
        for _ in range(amount):
            if not boost_type:
                boost_type = np.random.choice(self.__boost_types_number, 1, p=[.7, .2, .1])

            if not pos:
                _boost_pos = np.random.randint(self.__field.field.shape)
                while any(self.__field.check_for_objects_at_the_position(_boost_pos).values()):
                    _boost_pos = np.random.randint(self.__field.field.shape)
            else:
                _boost_pos = np.array(pos)

            self.__boosts = np.append(self.__boosts, np.array([[*_boost_pos, boost_type]]), 0)

    def destroy_boost_at_pos(self, pos):
        for i in range(self.boost_types_number):
            if index := find(self.boosts, np.append(pos, i)):
                self.__boosts = np.delete(self.boosts, index, 0)
                return i

    @property
    def boosts(self):
        return self.__boosts

    @property
    def boost_types_number(self):
        return self.__boost_types_number


def main(use_console=True):
    global time

    # the screen variable for a future
    screen = pg.display.set_mode((1, 1))

    # hint: here you can change the field size (10, 10)
    field = Field((21, 21))

    # 2+ player mode have some bugs
    '''
    hint: here you can change the head position and its control (field, (0, 0), (pg.K_i, pg.K_k, pg.K_j, pg.K_l)).
    You can also add a new snake (Head(field, (11, 10), (pg.K_w, pg.K_s, pg.K_a, pg.K_d))).
    '''
    Head(field, (10, 10))

    boosts = Boosts(field)

    # hint: here you can change the amount of the boosts, they position and boost type (5, (6, 9), 0)
    boosts.create_boost(3)

    while True:
        for event in pg.event.get():
            [exit() for _ in ' ' if event.type == pg.QUIT]
            if event.type == pg.KEYDOWN:
                for head in field.snake_heads:
                    head.change_movement_direction(event.key)

        [head.move() for head in field.snake_heads]
        field.update()

        pg.display.set_caption(f'FPS: {clock.get_fps()}')

        if use_console:
            system('cls')

            for head in field.snake_heads:
                print(f'Score: {head.score}\n'
                      f'Tail length: {len(head.tail.tail_elements_pos)}\n')

            # hint: here you can turn off the pretty print and turn on the debug print (False, True)
            field.print()

        time += 1
        clock.tick()


if __name__ == '__main__':
    main()
