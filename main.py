from os import system
from typing import *
import pygame as pg
import numpy as np
import sys

time = 0
pause = False

pg.init()
clock = pg.time.Clock()


def find(array, value, _slice=None):
    if _slice is None:
        _slice = (0, array.shape[1])
    for index, element in enumerate(array):
        if list(element)[_slice[0]:_slice[1]] == list(value):
            return index
    return []


# just “in” doesn't work correctly
def in_array(array, value):
    return list(value) in list(map(lambda x: list(x), array))


def colored(r, g, b, text):
    text = str(text)
    r, g, b = int(r), int(g), int(b)
    return f"\033[38;2;{r};{g};{b}m{text}\033[38;2;255;255;255m"


class Field:
    # hint: here you can change the empty space symbol and its color
    empty_space_color = (127, 127, 127)
    empty_space_character = '.'

    def __init__(self, shape: tuple[int, int], field_boundaries_is_deadly=False):
        """
        The function initializes the game field, the snake heads, the boosts, and the walls

        :param shape: The shape of the field
        :type shape: tuple[int, int]
        :param field_boundaries_is_deadly: If True, the snake will die if it hits the field boundaries,
        defaults to False (optional)
        """
        self.__snake_heads = []
        self.__boosts = None
        self.__walls = None

        self.__field_dtype = np.dtype([('color', int, (3,)), ('character', str, 1)])
        self.__field = np.zeros(shape, dtype=self.__field_dtype)

        self.__field_boundaries_is_deadly = bool(field_boundaries_is_deadly)

    def __str__(self) -> str:
        return f'{self.__field}'

    def __repr__(self) -> str:
        return f'Field({self.__field.shape})'

    def update(self):
        self.__field[:] = np.zeros(self.__field.shape, dtype=self.__field_dtype)

        if self.boosts is not None:
            for boost in self.boosts.boosts:
                if all(boost[:-1] != np.array([-1, -1])):
                    self.field[boost[0], boost[1]][0] = Boosts.colors[boost[2]]
                    self.field[boost[0], boost[1]][1] = Boosts.characters[boost[2]]

        for head in self.__snake_heads:
            if head.is_alive:
                for element_pos in head.tail.tail_elements_pos:
                    if all(element_pos != np.array([-1, -1])):
                        self.field[element_pos[0], element_pos[1]][0] = head.tail.color
                        self.field[element_pos[0], element_pos[1]][1] = Tail.character

        for head in self.__snake_heads:
            self.field[head.pos[0], head.pos[1]][0] = head.color
            self.field[head.pos[0], head.pos[1]][1] = Head.character

        if self.walls is not None:
            for wall in self.walls.walls_pos:
                if all(wall != np.array([-1, -1])):
                    self.field[wall[0], wall[1]][0] = Walls.color
                    self.field[wall[0], wall[1]][1] = Walls.character

        for index in range(self.__field.shape[0]):
            for _index in range(self.__field.shape[1]):
                if self.__field[index, _index][1] == '':
                    self.__field[index, _index] = ([*Field.empty_space_color], Field.empty_space_character)

    def print(self, pretty_print=True, debug=False):
        if pretty_print:
            str_field = '\n'
            for index in range(self.__field.shape[0]):
                for _index in range(self.__field.shape[1]):
                    value = self.__field[index, _index]
                    str_field = str_field + colored(*value[0], value[1]) + ' '
                str_field += '\n'
            sys.stdout.writelines(str_field)

        else:
            print(self)

        if debug:
            self.print_debug_info()

    def add_snake(self, head):
        if isinstance(head, Head):
            self.__snake_heads.append(head)
        else:
            raise TypeError('head must be an instance of Head')

    def check_for_objects_at_the_position(self, pos, current_snake=None) -> dict:
        """
        It checks if there's a snake head, tail, boost or wall at the given position

        :param pos: the position to check
        :param current_snake: the snake that is currently being checked for collisions
        :return: A dictionary with the following keys: head, tail, boost, wall.
        """

        pos = np.array(pos)
        is_here_head = is_here_tail = False
        for head in self.__snake_heads:
            if (current_snake is not None and current_snake.contact_with_other_snakes) and head is not current_snake:
                is_here_head = all(head.pos == pos) or is_here_head

            if current_snake is None or current_snake.contact_with_other_snakes:
                tail_elements_pos = head.tail.tail_elements_pos
                if head.is_alive:
                    tail_elements_pos = tail_elements_pos[1:]
                is_here_tail = is_here_tail or in_array(tail_elements_pos, pos)
            else:
                tail_elements_pos = current_snake.tail.tail_elements_pos[1:]
                is_here_tail = is_here_tail or in_array(tail_elements_pos, pos)

        is_here_boost = False
        if self.boosts is not None:
            for i in range(self.boosts.boost_types_number):
                is_here_boost = in_array(self.boosts.boosts, np.append(pos, [i], 0))
                if is_here_boost:
                    break

        is_here_wall = False
        if self.walls is not None:
            is_here_wall = in_array(self.walls.walls_pos, pos)

        return dict(head=is_here_head, tail=is_here_tail, boost=is_here_boost, wall=is_here_wall)

    def field_is_filled(self):
        for y in range(self.__field.shape[0]):
            for x in range(self.__field.shape[1]):
                if not any(self.check_for_objects_at_the_position((y, x)).values()):
                    return False
        return True

    def find_random_free_pos(self):
        pos = np.random.randint(self.field.shape)

        if self.field_is_filled():
            return np.array([-1, -1], dtype=int)

        while any(self.check_for_objects_at_the_position(pos).values()):
            pos = np.random.randint(self.field.shape)
        return pos

    def is_out_of_field(self, pos):
        """
        If the position is out of the field, return the direction in which it is out of the field

        :param pos: the position of the agent
        :return: A tuple of two values, one for each axis.
        """

        pos = np.array(pos)
        direction: list[int, int] = [0, 0]

        for i in range(2):
            if pos[i] + 1 > self.field.shape[i]:
                direction[i] = 1
            elif pos[i] < 0:
                direction[i] = -1

        return tuple(direction)

    def print_debug_info(self):
        print({x: x.__dict__ for x in [self.__boosts] + self.__snake_heads})

    def reset_all(self):
        for head in self.snake_heads:
            head.reset()

        self.boosts.reset()
        self.walls.reset()

    def normalized_pos(self, pos) -> np.array:
        pos = np.array(pos)

        if any(directions := self.is_out_of_field(pos)):
            for i in range(2):
                _ = {1: 0, -1: self.field.shape[i] - 1}
                pos[i] = _.get(directions[i], pos[i])

        return pos

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

    @property
    def walls(self):
        return self.__walls

    @walls.setter
    def walls(self, value):
        if isinstance(value, Walls):
            self.__walls = value

    @property
    def field_boundaries_is_deadly(self):
        return self.__field_boundaries_is_deadly

    @field_boundaries_is_deadly.setter
    def field_boundaries_is_deadly(self, value):
        self.__field_boundaries_is_deadly = bool(value)


class Head:
    __snakes_number: int = 0

    # hint: here you can change the head symbol
    character = '@'

    @staticmethod
    def generate_head_color():
        random_color = np.random.randint(0, 255, 3, dtype=int)
        while not 510 >= np.sum(random_color) >= 255:
            random_color = np.random.randint(0, 255, 3, dtype=int)

        return tuple(random_color)

    def __init__(self, _field: Field, pos=(0, 0), moves_per_second=4,
                 controls=(pg.K_w, pg.K_s, pg.K_a, pg.K_d), name=None, color=None, contact_with_other_snakes=False):
        """
        The function takes in a field, position, moves per second, controls, name, and color.

        The function then creates a snake with the given parameters.

        The function also creates a tail for the snake.

        The function then returns the snake.

        :param _field: Field - the field on which the snake is located
        :type _field: Field
        :param pos: the position of the head
        :param moves_per_second: How many times the snake moves per second, defaults to 4 (optional)
        :param controls: a tuple of 4 keys, which are used to control the snake
        :param name: The name of the snake
        :param color: The color of the snake's head
        :param contact_with_other_snakes: If True, the snake will die if it touches another snake, defaults to False
        (optional)
        """
        if name is None:
            name = f'Snake{Head.__snakes_number}'
        else:
            name = str(name)
        self.__name = name

        if color is None:
            color = Head.generate_head_color()
        else:
            color = tuple(color)
        self.__color = color

        Head.__snakes_number += 1

        self.__moves_per_second = moves_per_second
        self.__field = _field
        self.__field.add_snake(self)

        self.__pos: np.array = np.array(pos)
        self.__previous_pos = np.array([-1, -1])
        self.__start_pos = self.__pos
        self.__movement: np.array = np.zeros(2, dtype=np.int8)

        self.__contact_with_other_snakes = contact_with_other_snakes

        self.__is_alive = True
        self.__score = 0

        self.__tail = Tail(self)

        self.__controls = list(controls)

    def next_pos(self) -> np.array:
        return self.field.normalized_pos(self.pos + self.movement)

    def move(self, move_anyway=False):
        fps = min(clock.get_fps(), 10_000)

        if fps > 0 == time % (fps // min(self.moves_per_second, int(fps))) or move_anyway:
            if not self.check_for_obstacle(self.next_pos()) and self.is_alive and any(self.movement != 0):
                self.pos = (self.pos + self.movement)
            elif self.check_for_obstacle(self.next_pos()):
                self.__is_alive = False

    def change_movement_direction(self, key):
        directions = {x: y for x, y in zip(self.__controls, [[-1, 0], [1, 0], [0, -1], [0, 1]])}

        if key in directions:
            next_pos = self.field.normalized_pos(self.pos + directions[key])

            if any(next_pos != self.previous_pos):
                self.movement = directions[key]

    def check_for_obstacle(self, pos: Sequence) -> bool:
        pos = np.array(pos)
        pos_is_obstacle = [self.field.check_for_objects_at_the_position(pos, self)['head'],
                           self.field.check_for_objects_at_the_position(pos, self)['tail'],
                           self.field.check_for_objects_at_the_position(pos, self)['wall']]
        return ((any(pos + 1 > self.field.field.shape) or any(pos < 0))
                and self.field.field_boundaries_is_deadly) or any(pos_is_obstacle)

    def eat(self, boost_amount_to_be_created=1, wall_amount_to_be_created=1, increase_speed=0, increase_score=1):
        if self.field.check_for_objects_at_the_position(self.pos)['boost']:

            boost_type = self.boosts.destroy_boost_at_pos(self.pos)
            match boost_type:
                case 0:
                    self.tail.add_new_element()
                    self.__score += increase_score

                case 1:
                    self.tail.delete_last_element()

                case 2:
                    efficiency = np.random.randint(-1, 1)
                    elements_number = np.random.randint(-2, 2)
                    self.tail.add_new_element(elements_number)
                    self.__score += elements_number * increase_score + efficiency

                case 3:
                    wall_amount_to_be_destroyed = self.walls.walls_pos.size // 4
                    self.walls.delete_random_wall(wall_amount_to_be_destroyed)

                    self.__score -= wall_amount_to_be_destroyed // 2

            self.boosts.create_boost(boost_amount_to_be_created)

            if boost_type in range(3):
                chance = (((self.field.field.size - self.field.walls.walls_pos.shape[0])
                           / self.field.field.size)
                          ** (len(self.field.snake_heads) + 1))
                if np.random.choice([0, 1], 1, p=[1 - chance, chance]):
                    self.walls.create_wall(wall_amount_to_be_created)

            self.moves_per_second += increase_speed

    def reset(self):
        self.__is_alive = True
        self.__score = 0

        self.__pos = self.start_pos
        self.__previous_pos = np.array([-1, -1])
        self.__movement = np.zeros(2, dtype=np.int8)

        self.tail.reset()

    @property
    def pos(self):
        return self.__pos

    @pos.setter
    def pos(self, value):
        value = np.array(value)

        if not self.check_for_obstacle(value):
            self.__previous_pos = self.pos
            self.__pos = self.field.normalized_pos(value)
        else:
            self.__is_alive = False

        '''
        hint: here you can set the value by which the number of boosts or walls or the head speed (moves per 
        second [integer]) or score increases each time when the snake eats (2, 3, 1, 5)
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
    def walls(self):
        return self.field.walls

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

    @property
    def start_pos(self):
        return self.__start_pos

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, new_name):
        self.__name = str(new_name)

    @property
    def contact_with_other_snakes(self):
        return self.__contact_with_other_snakes

    @property
    def color(self):
        return self.__color


class Tail:
    # hint: here you can change the tail symbol
    character = '*'

    def __init__(self, _head: Head):
        self.__head = _head
        self.__tail_elements_pos: np.array = np.array([[-1, -1]])

        color = list(self.__head.color)

        for index in range(3):
            if color[index] + 64 > 255:
                color[index] -= 64
            else:
                color[index] += 64

        self.__color = tuple(color)

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
            if len(self.tail_elements_pos) > 1:
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

    def reset(self):
        self.__tail_elements_pos = np.array([[-1, -1]])

    @property
    def tail_elements_pos(self):
        return self.__tail_elements_pos

    @tail_elements_pos.setter
    def tail_elements_pos(self, value):
        value = np.array(value)

        self.__tail_elements_pos = value

    @property
    def color(self):
        return self.__color


class Boosts:
    # hint: here you can change the boost colors and symbols
    colors = {0: (15, 255, 63),
              1: (63, 255, 255),
              2: (255, 63, 255),
              3: (63, 31, 255)}
    characters = {0: '+', 1: '-', 2: '?', 3: '&'}

    def __init__(self, _field: Field):
        self.__field = _field
        self.__field.boosts = self
        self.__boosts = np.empty(shape=(0, 3), dtype=int)
        self.__boost_types_number = max(len(Boosts.characters), len(Boosts.colors))

    def create_boost(self, amount=1, pos=None, boost_type=None):
        for _ in range(amount):
            if boost_type is None:
                _boost_type = int(np.random.choice(self.__boost_types_number, 1, p=[.70, .15, .1, .05]))
            else:
                _boost_type = boost_type

            if not pos:
                if list(random_free_pos := self.__field.find_random_free_pos()) != [-1, -1]:
                    _boost_pos = random_free_pos
                else:
                    break
            else:
                _boost_pos = np.array(pos)

            self.__boosts = np.append(self.__boosts, np.array([[*_boost_pos, _boost_type]]), 0)

    def destroy_boost_at_pos(self, pos):
        for boost_type in range(self.boost_types_number):
            if not (index := find(self.boosts, np.append(pos, boost_type))) == []:
                self.__boosts = np.delete(self.boosts, index, 0)
                return boost_type

    def reset(self):
        self.__boosts = np.empty(shape=(0, 3), dtype=int)

    @property
    def boosts(self):
        return self.__boosts

    @property
    def boost_types_number(self):
        return self.__boost_types_number


class Walls:
    # hint: here you can change the walls color and symbol
    color = (255, 63, 15)
    character = '#'

    def __init__(self, _field: Field):
        self.__field = _field
        self.__field.walls = self
        self.__walls_pos = np.empty(shape=(0, 2), dtype=int)

    def create_wall(self, amount=1, pos=None):
        if amount < 0:
            self.delete_random_wall(abs(amount))

        for _ in range(amount):
            if not pos:
                _wall_pos = self.__field.find_random_free_pos()
            else:
                _wall_pos = np.array(pos)

            self.__walls_pos = np.append(self.__walls_pos, np.array([_wall_pos]), 0)

    def delete_random_wall(self, amount=1):
        if amount < 0:
            self.create_wall(abs(amount))

        for _ in range(amount):
            if len(self.__walls_pos) > 0:
                self.__walls_pos = np.delete(self.__walls_pos, np.random.randint(self.__walls_pos.shape[0]), 0)

    def reset(self):
        self.__walls_pos = np.empty(shape=(0, 2), dtype=int)

    @property
    def walls_pos(self):
        return self.__walls_pos


def main(use_console=True):
    global time, pause

    # the screen variable for a future
    screen = pg.display.set_mode((1, 1))

    # hint: here you can change the field size (10, 10) and turn on the lethality of the field boundaries
    field = Field((19, 19))

    # 2+ player mode may have some bugs
    '''
    hint:
        here you can change the head position, its moves per second, its controls, name, 
        color and turn on contacting with other snakes (all parameters after position are optional):
            ...(field, (0, 0), 7, (pg.K_i, pg.K_k, pg.K_j, pg.K_l), 'God', (255, 255, 0), True).
    
        You can also add a new snake:
            Head(field, (11, 10), 1, (pg.K_w, pg.K_s, pg.K_a, pg.K_d), 'Dog', (0, 0, 255), False).
    '''
    Head(field, (9, 9))

    boosts = Boosts(field)
    Walls(field)

    # hint: here you can change the amount of the boosts, they position and boost type (5, (6, 9), 0)
    boosts.create_boost(3)

    while True:
        for event in pg.event.get():
            [exit() for _ in ' ' if event.type == pg.QUIT]

            if event.type == pg.KEYDOWN:
                for head in field.snake_heads:
                    if not pause:
                        head.change_movement_direction(event.key)

                if event.key == pg.K_p or event.key == pg.K_SPACE:
                    pause = not pause

                if event.key == pg.K_r:
                    field.reset_all()
                    boosts.create_boost(3)

                if event.key == pg.K_ESCAPE:
                    exit()

        if not pause:
            [head.move() for head in field.snake_heads]
            field.update()

        pg.display.set_caption(f'FPS: {clock.get_fps()}')

        if use_console and any([obj.is_alive for obj in field.snake_heads]):
            system('cls')

            if pause:
                sys.stdout.write(colored(51, 96, 255, 'PAUSE'))

            for head in field.snake_heads:
                if pause:
                    sys.stdout.write('\t')
                sys.stdout.writelines(f'{colored(200, 255, 0, head.name)}:\t'
                                      f'Score: {colored(0, 127, 255, head.score)} | '
                                      f'Tail length: {colored(127, 255, 63, len(head.tail.tail_elements_pos))}\n')

            # hint: here you can turn off the pretty print and turn on the debug print (False, True)
            field.print()

        if not pause:
            time += 1
        clock.tick(20)


if __name__ == '__main__':
    main()
