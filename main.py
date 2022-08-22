from PIL import Image
from Packages.HueShifter import shift_image_hue
from Packages.StrConventers import *
import pygame as pg
import numpy as np
import pathlib as pl

pg.init()
clock = pg.time.Clock()

error_texture = pg.image.load(pl.Path(__file__).parent.joinpath('Texture Packs').joinpath('Default').joinpath('error'
                                                                                                              '.png'))
texture_pack_name = 'Default'


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


def update_error_texture():
    global error_texture

    error_texture = get_texture('error.png')


def pil_img2pg_img(img: Image):
    return pg.image.fromstring(img.tobytes(), img.size, img.mode)


def get_texture(texture, shift_hue2=None):
    data_pack_path = pl.Path(__file__).parent.joinpath('Texture Packs').joinpath(texture_pack_name)

    if not data_pack_path.exists():
        return error_texture

    texture_path = data_pack_path.joinpath(texture)

    if not texture_path.exists():
        return error_texture

    if shift_hue2 is None:
        return pg.image.load(texture_path)

    else:
        if not isinstance(shift_hue2, int) and not isinstance(shift_hue2, float):
            shift_hue2 = 0

        return pil_img2pg_img(shift_image_hue(str(texture_path), shift_hue2))


class Screen:
    empty_space_texture = get_texture('empty_tile')

    def __init__(self, shape: tuple[int, int], screen_boundaries_is_deadly=False, size_multiplier=50, font_name=None):
        self.__snakes = []
        self.__portals = []
        self.__boosts = None
        self.__walls = None

        self.__field_dtype = np.dtype([('object', object), ('type', int)])
        self.__field = np.zeros(shape, dtype=self.__field_dtype)

        self.__screen_boundaries_is_deadly = bool(screen_boundaries_is_deadly)

        self.__size_multiplier = size_multiplier
        self.__screen = pg.display.set_mode(tuple(np.array(self.field.shape) * self.__size_multiplier))

        if font_name is None or not pl.Path(__file__).parent.joinpath(f'Fonts/{font_name}').exists():
            font_name = 'fff-forward.regular.ttf'
        self.__font = pg.font.Font(pl.Path(__file__).parent.joinpath(f'Fonts/{font_name}'),
                                   min(self.screen.get_size()) // 50)

    def __str__(self) -> str:
        return f'{self.__field}'

    def __repr__(self) -> str:
        return f'Screen({self.__field.shape})'

    def write_to_the_field(self, _pos, _obj=0, _type=0):
        if self.is_out_of_field(_pos) == (0, 0):
            self.field[_pos[0], _pos[1]]['object'] = _obj
            self.field[_pos[0], _pos[1]]['type'] = _type

    def update(self):
        self.__field[:] = np.zeros(self.__field.shape, dtype=self.__field_dtype)

        if self.boosts is not None:
            for boost in self.boosts.boosts:
                self.write_to_the_field(boost[0:2], self.boosts, boost[2])

        for snake in self.__snakes:
            for element_pos in snake.tail_elements_pos:
                self.write_to_the_field(element_pos, snake, 1)

        for snake in self.__snakes:
            self.write_to_the_field(snake.head_pos, snake, 0)

        for portals in self.__portals:
            for portal in portals.portals_pos:
                self.write_to_the_field(portal, portals, 0)

        if self.walls is not None:
            for wall in self.walls.walls_pos:
                self.write_to_the_field(wall, self.walls, 0)

    def add_snake(self, snake):
        if isinstance(snake, Snake):
            self.__snakes.append(snake)
        else:
            raise TypeError('snake must be an instance of Snake')

    def add_portals(self, portals):
        if isinstance(portals, Portals):
            self.__portals.append(portals)
        else:
            raise TypeError('portals must be an instance of Portals')

    def check_for_objects_at_the_position(self, pos, current_snake=None) -> dict:
        pos = self.normalized_pos(pos)
        is_here_head = is_here_tail = False
        for snake in self.__snakes:
            if isinstance(self.field[pos[0], pos[1]]['object'], Snake):
                if self.field[pos[0], pos[1]]['type'] == 0:
                    if current_snake is None or current_snake.contact_with_other_snakes and snake is not current_snake:
                        is_here_head = True

                elif self.field[pos[0], pos[1]]['type'] == 1:
                    if current_snake is None or current_snake.contact_with_other_snakes:
                        tail_elements_pos = snake.tail_elements_pos
                        if snake.is_alive:
                            tail_elements_pos = tail_elements_pos[1:]
                        is_here_tail = is_here_tail or in_array(tail_elements_pos, pos)
                    else:
                        tail_elements_pos = current_snake.tail_elements_pos[1:]
                        is_here_tail = is_here_tail or in_array(tail_elements_pos, pos)

        is_here_boost = isinstance(self.field[pos[0], pos[1]]['object'], Boosts)

        is_here_wall = isinstance(self.field[pos[0], pos[1]]['object'], Walls)

        is_here_portal = isinstance(self.field[pos[0], pos[1]]['object'], Portals)

        return dict(head=is_here_head, tail=is_here_tail, boost=is_here_boost, wall=is_here_wall, portal=is_here_portal)

    def free_positions(self):
        free_positions = np.stack(np.meshgrid(range(self.field.shape[0]), range(self.field.shape[1])),
                                  -1).reshape(-1, 2)
        indices_for_delete = []

        for index, pos in enumerate(free_positions):
            if any(self.check_for_objects_at_the_position(pos).values()):
                indices_for_delete.append(index)

        free_positions = np.delete(free_positions, indices_for_delete, 0)
        return free_positions

    def field_is_filled(self):
        if self.free_positions().size > 0:
            return False
        return True

    def find_random_free_pos(self):
        if self.field_is_filled():
            return np.array([-1, -1], dtype=int)

        free_poses = self.free_positions()
        return free_poses[np.random.randint(0, free_poses.shape[0])]

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

    def reset_all(self):
        for snake in self.snakes:
            snake.reset()

        self.boosts.reset()
        self.walls.reset()

        for portals in self.portals:
            portals.reset()

    def normalized_pos(self, pos) -> np.array:
        pos = np.array(pos)

        if any(directions := self.is_out_of_field(pos)):
            for i in range(2):
                _ = {1: 0, -1: self.field.shape[i] - 1}
                pos[i] = _.get(directions[i], pos[i])

        return pos

    def update_screen(self, pause=False):
        self.update()

        mult = self.__size_multiplier
        self.__screen.fill((0, 0, 0))

        for index, _index in self.field_indexes():
            value = self.__field[index, _index]
            pos = (_index * mult, index * mult)
            self.draw_empty_tile(pos)
            if value[0] != 0:
                value[0].draw(value[1], pos, mult)
        self.print_player_stats(pause)
        pg.display.flip()

    def print_player_stats(self, pause=False):
        alpha = 127
        if pause:
            alpha = 255
            text = 'PAUSE'
            text_surface = self.__font.render(text, False, (0, 0, 255))
            self.screen.blit(text_surface,
                             (self.screen.get_width() - self.__font.size(text)[0],
                              self.screen.get_height() - self.__font.size(text)[1]))

        for index, snake in enumerate(self.snakes):
            text = f'{snake.name}:    Score: {snake.score} | Tail length: {len(snake.tail_elements_pos)}'
            text_surface = self.__font.render(text, False, (255, 255, 255))
            text_surface.set_alpha(alpha)
            self.screen.blit(text_surface, (0, index * (self.__font.get_height() + 10) + 5))

    def field_indexes(self):
        for index in range(self.__field.shape[0]):
            for _index in range(self.__field.shape[1]):
                yield index, _index

    def draw_empty_tile(self, pos):
        texture = pg.transform.scale(Screen.empty_space_texture, (self.__size_multiplier, self.__size_multiplier))
        self.screen.blit(texture, pos)

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
    def snakes(self):
        return self.__snakes

    @property
    def walls(self):
        return self.__walls

    @walls.setter
    def walls(self, value):
        if isinstance(value, Walls):
            self.__walls = value

    @property
    def portals(self):
        return self.__portals

    @property
    def screen_boundaries_is_deadly(self):
        return self.__screen_boundaries_is_deadly

    @screen_boundaries_is_deadly.setter
    def screen_boundaries_is_deadly(self, value):
        self.__screen_boundaries_is_deadly = bool(value)

    @property
    def size_multiplier(self):
        return self.__size_multiplier

    @property
    def screen(self):
        return self.__screen


class Snake:
    __snakes_number: int = 0

    @staticmethod
    def should_move_n_times(pt, t, f, mps):
        return mps*(t-pt)/f

    def __init__(self, _screen: Screen, pos=(0, 0), moves_per_second=4,
                 controls: str = None, name=None, hue=None, contact_with_other_snakes=False):

        if name is None:
            name = f'Snake{Snake.__snakes_number}'
        else:
            name = str(name)
        self.__name = name

        if hue is None:
            hue = np.random.randint(181)

        self.__hue = hue
        self.__head_static_texture = get_texture('snake_head_static.png', self.hue)
        self.__head_movement_texture = get_texture('snake_head_movement.png', self.hue)
        self.__skull = get_texture('dead_head.png', self.hue)
        self.__tail_texture = get_texture('tail.png', self.hue)

        Snake.__snakes_number += 1

        self.__moves_per_second = moves_per_second
        self.__screen = _screen
        self.__screen.add_snake(self)

        self.__head_pos: np.array = np.array(pos)
        self.__previous_pos = np.array([-1, -1])
        self.__start_pos = self.__head_pos
        self.__tail_elements_pos: np.array = np.array([[-1, -1]])
        self.__movement: np.array = np.zeros(2, dtype=np.int8)
        self.__last_movement_time: int = 0

        self.__contact_with_other_snakes = contact_with_other_snakes

        self.__is_alive = True
        self.__score = 0

        if controls is None:
            controls = (pg.K_w, pg.K_s, pg.K_a, pg.K_d)
        elif controls == 'ARROWS':
            controls = (pg.K_UP, pg.K_DOWN, pg.K_LEFT, pg.K_RIGHT)
        else:
            controls = (ord(element.lower()) for element in controls)

        self.__controls = list(controls)

    def next_pos(self) -> np.array:
        return self.screen.normalized_pos(self.head_pos + self.movement)

    def move(self, time):
        fps = min(max(clock.get_fps(), 1), 10_000)

        for _ in range(
                int(np.floor(Snake.should_move_n_times(self.__last_movement_time, time, fps, self.moves_per_second)))):
            if not self.check_for_obstacle(self.next_pos()) and self.is_alive and any(self.movement != 0):
                self.head_pos = (self.head_pos + self.movement)

                if isinstance(portals := self.screen.field[self.head_pos[0], self.head_pos[1]]['object'], Portals):
                    portals.teleport_snake(self, self.head_pos)
            elif self.check_for_obstacle(self.next_pos()):
                self.__is_alive = False

            if not self.is_alive:
                self.delete_last_element(minlen=0)

            self.__last_movement_time = time

    def change_movement_direction(self, key):
        directions = {x: y for x, y in zip(self.__controls, [[-1, 0], [1, 0], [0, -1], [0, 1]])}

        if key in directions:
            next_pos = self.screen.normalized_pos(self.head_pos + directions[key])

            if any(next_pos != self.previous_pos):
                self.movement = directions[key]

    def check_for_obstacle(self, pos: Sequence) -> bool:
        pos = np.array(pos)
        pos_is_obstacle = [self.screen.check_for_objects_at_the_position(pos, self)['head'],
                           self.screen.check_for_objects_at_the_position(pos, self)['tail'],
                           self.screen.check_for_objects_at_the_position(pos, self)['wall']]
        return ((any(pos + 1 > self.screen.field.shape) or any(pos < 0))
                and self.screen.screen_boundaries_is_deadly) or any(pos_is_obstacle)

    def add_new_element(self, amount=1):
        if amount < 0:
            self.delete_last_element(abs(amount))
            return

        for _ in range(amount):
            self.__tail_elements_pos = np.append([[-1, -1]], self.__tail_elements_pos, 0)

    def delete_last_element(self, amount=1, minlen=1):
        if amount < 0:
            self.add_new_element(abs(amount))
            return

        for _ in range(amount):
            if len(self.tail_elements_pos) > minlen:
                self.__tail_elements_pos = np.delete(self.tail_elements_pos, 0, 0)

    def eat(self):
        if self.screen.check_for_objects_at_the_position(self.head_pos)['boost']:

            boost_type = self.boosts.destroy_boost_at_pos(self.head_pos)

            self.boosts.give_boost(self, boost_type)

            self.boosts.create_boost(1)

            if boost_type in range(3):
                chance = (((self.screen.field.size - self.screen.walls.walls_pos.shape[0])
                           / self.screen.field.size)
                          ** (len(self.screen.snakes) + 1))
                if np.random.choice([0, 1], 1, p=[1 - chance, chance]):
                    self.walls.create_wall(1)

    def reset(self):
        self.__is_alive = True
        self.__score = 0

        self.__head_pos = self.start_pos
        self.__previous_pos = np.array([-1, -1])
        self.__movement = np.zeros(2, dtype=np.int8)

        self.__tail_elements_pos = np.array([[-1, -1]])

    def draw(self, _type, pos, size):
        screen = self.screen.screen
        match _type:
            case 0:
                if any(self.movement != (0, 0)) and self.is_alive:
                    rotating_angle = 0
                    match tuple(self.movement):
                        case (0, 1):
                            rotating_angle = -90
                        case (0, -1):
                            rotating_angle = 90
                        case (1, 0):
                            rotating_angle = 180

                    texture = pg.transform.rotate(self.__head_movement_texture, rotating_angle)

                elif all(self.movement == (0, 0)):
                    texture = self.__head_static_texture

                else:
                    texture = self.__skull

            case 1:
                texture = self.__tail_texture
            case _:
                texture = error_texture

        screen.blit(pg.transform.scale(texture, (size, size)), pos)

    @property
    def head_pos(self):
        return self.__head_pos

    @head_pos.setter
    def head_pos(self, value):
        value = np.array(value)

        if not self.check_for_obstacle(value):
            self.__previous_pos = self.head_pos
            self.__head_pos = self.screen.normalized_pos(value)

            if any(self.head_pos != self.previous_pos):
                for index in range(len(self.__tail_elements_pos)):
                    if index == len(self.__tail_elements_pos) - 1:
                        self.__tail_elements_pos[index] = self.previous_pos
                    else:
                        self.__tail_elements_pos[index] = self.__tail_elements_pos[index + 1]

        else:
            self.__is_alive = False

        self.eat()

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
    def screen(self):
        return self.__screen

    @property
    def previous_pos(self):
        return self.__previous_pos

    @property
    def boosts(self):
        return self.__screen.boosts

    @property
    def walls(self):
        return self.screen.walls

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

    @score.setter
    def score(self, value):
        self.__score = int(value)

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
    def hue(self):
        return self.__hue

    @hue.setter
    def hue(self, value):
        self.__hue = int(value)

        self.__head_static_texture = get_texture('snake_head_static.png', self.hue)
        self.__head_movement_texture = get_texture('snake_head_movement.png', self.hue)
        self.__skull = get_texture('dead_head.png', self.hue)
        self.__tail_texture = get_texture('tail.png', self.hue)

    @property
    def tail_elements_pos(self):
        return self.__tail_elements_pos

    @tail_elements_pos.setter
    def tail_elements_pos(self, value):
        value = np.array(value)

        self.__tail_elements_pos = value


class Boosts:
    probabilities = np.array([70, 15, 10, 5])

    @staticmethod
    def calculate_probabilities(sequence: Sequence):
        sequence = [abs(element) for element in sequence]

        _sum = sum(sequence)
        if _sum <= 0:
            return None
        return np.array([x / _sum for x in sequence])

    def __init__(self, _screen: Screen):
        self.__screen = _screen
        self.__screen.boosts = self
        self.__boosts = np.empty(shape=(0, 3), dtype=int)

        self.__textures: np.array = [get_texture(texture) for
                                     texture in ['plus_boost.png', 'minus_boost.png',
                                                 'random_boost.png', 'wall_destroyer_boost.png']]

        self.__boost_types_number = len(self.__textures)

    def create_boost(self, amount=1, pos=None, boost_type=None):
        for _ in range(amount):
            if boost_type is None:
                if (probabilities := self.calculate_probabilities(self.probabilities)) is not None:
                    _boost_type = int(np.random.choice(np.arange(self.__boost_types_number), 1, p=probabilities))
                else:
                    break

            else:
                _boost_type = boost_type
                if _boost_type:
                    break

            if not pos:
                if list(random_free_pos := self.__screen.find_random_free_pos()) != [-1, -1]:
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

    @staticmethod
    def give_boost(snake: Snake, boost_type: int):
        match boost_type:
            case 0:
                snake.add_new_element()
                snake.score += 1

            case 1:
                snake.delete_last_element()

            case 2:
                efficiency = np.random.randint(-1, 1)
                elements_number = np.random.randint(-2, 2)
                snake.add_new_element(elements_number)
                snake.score += elements_number + efficiency

            case 3:
                wall_amount_to_be_destroyed = snake.walls.walls_pos.size // 4
                snake.walls.delete_random_wall(wall_amount_to_be_destroyed)

                snake.score -= wall_amount_to_be_destroyed // 2

    def reset(self):
        self.__boosts = np.empty(shape=(0, 3), dtype=int)

    def draw(self, _type, pos, size):
        if _type in range(len(self.__textures)):
            texture = self.__textures[_type]
        else:
            texture = error_texture

        texture = pg.transform.scale(texture, (size, size))
        self.__screen.screen.blit(texture, pos)

    @property
    def boosts(self):
        return self.__boosts

    @property
    def boost_types_number(self):
        return self.__boost_types_number


class Walls:
    def __init__(self, _screen: Screen, spawning_is_enabled=True):
        self.__screen = _screen
        self.__screen.walls = self
        self.__walls_pos = np.empty(shape=(0, 2), dtype=int)
        self.__spawning_is_enabled = spawning_is_enabled

        self.__texture = get_texture('wall.png')

    def create_wall(self, amount=1, pos=None):
        if amount < 0:
            self.delete_random_wall(abs(amount))

        if self.__spawning_is_enabled:
            for _ in range(amount):
                if not pos:
                    _wall_pos = self.__screen.find_random_free_pos()
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

    def draw(self, _type, pos, size):
        if _type == 0:
            texture = self.__texture
        else:
            texture = error_texture

        texture = pg.transform.scale(texture, (size, size))
        self.__screen.screen.blit(texture, pos)

    @property
    def walls_pos(self):
        return self.__walls_pos


class Portals:
    def __init__(self, _screen: Screen, hue=None, spawning_is_enabled=True):
        self.__screen = _screen
        self.__screen.add_portals(self)
        self.__portals_pos = np.empty(shape=(0, 2), dtype=int)

        self.__spawning_is_enabled = spawning_is_enabled

        if hue is None:
            hue = np.random.randint(181)

        self.__hue = hue
        self.__texture = get_texture('portal.png', hue)

    def create_portal(self, amount=1, pos=None):
        if amount < 0:
            for _ in range(abs(amount)):
                self.delete_portal_at_pos()

        if self.__spawning_is_enabled:
            for _ in range(amount):
                if not pos:
                    self.__screen.update()
                    portal_pos = self.__screen.find_random_free_pos()
                else:
                    portal_pos = np.array(pos)

                self.__portals_pos = np.append(self.__portals_pos, np.array([portal_pos]), 0)

    def delete_portal_at_pos(self, pos=None):
        if pos is None:
            self.__portals_pos = np.delete(self.portals_pos, np.random.randint(len(self.portals_pos)), 0)
            return

        pos = np.array(pos)
        if not isinstance(index := find(self.portals_pos, pos), list):
            self.__portals_pos = np.delete(self.portals_pos, index, 0)

    def teleport_snake(self, snake: Snake, portal_pos):
        if (_len := len(self.portals_pos)) < 2:
            if _len == 1:
                self.delete_portal_at_pos(portal_pos)
                self.create_portal()
            return

        self.delete_portal_at_pos(portal_pos)
        teleport_to = self.portals_pos[np.random.randint(_len - 1)]
        self.delete_portal_at_pos(teleport_to)
        snake.head_pos = teleport_to
        self.create_portal(2)

    def draw(self, _type, pos, size):
        if _type == 0:
            texture = self.__texture
        else:
            texture = error_texture

        texture = pg.transform.scale(texture, (size, size))
        self.__screen.screen.blit(texture, pos)

    def reset(self):
        self.__portals_pos = np.empty(shape=(0, 2), dtype=int)

    @property
    def portals_pos(self):
        return self.__portals_pos

    @property
    def hue(self):
        return self.__hue

    @hue.setter
    def hue(self, value):
        self.__hue = int(value)
        self.__texture = get_texture('portal.png', self.hue)


def main():
    global texture_pack_name

    import configparser

    update_error_texture()

    config = configparser.ConfigParser()
    config.read(pl.Path(__file__).parent.joinpath('config.ini'))
    config.read_dict({'Game': {'': ''},
                      'Screen': {'': ''},
                      'Snake': {'': ''},
                      'FirstSnake': {'': ''},
                      'SecondSnake': {'': ''},
                      'ThirdSnake': {'': ''},
                      'FourthSnake': {'': ''},
                      'Boosts': {'': ''},
                      'Walls': {'': ''},
                      'Portals': {'': ''}})

    time = 0
    pause = False

    game_config = config['Game']

    fps = str2float(game_config.get('fps'), 30)

    pause_key = ord(game_config.get('pause_key', 'p'))
    restart_key = ord(game_config.get('restart_key', 'r'))

    texture_pack_name = game_config.get('texture_pack_name', 'Default')

    if not pl.Path(__file__).parent.joinpath('Texture Packs').joinpath(texture_pack_name).exists():
        texture_pack_name = 'Default'

    update_error_texture()

    Screen.empty_space_texture = get_texture('empty_tile.png')

    screen_config = config['Screen']

    screen_shape = str2tuple(screen_config.get('shape'), int, (31, 31))
    screen = Screen(screen_shape,
                    str2bool(screen_config.get('screen_boundaries_is_deadly')),
                    str2int(screen_config.get('size_multiplier'),
                            int(961 / (screen_shape[0] * screen_shape[1]) ** 0.5)),
                    screen_config.get('font_name'))

    snakes_config = config['Snake']

    # 2+ player mode may have some bugs
    snakes_count = min(max(str2int(snakes_config.get('snakes_count'), 1), 1), 4)
    first_snake_config = config['FirstSnake']
    second_snake_config = config['SecondSnake']
    third_snake_config = config['ThirdSnake']
    fourth_snake_config = config['FourthSnake']

    portals_config = config['Portals']
    portals_amount = max(str2int(portals_config.get('portals_amount'), 2), 2)
    portals_hue = [str2int(portals_config.get(f'portals{i}_hue'), None) for i in range(4)]
    portals_spawning_is_enabled = str2bool(portals_config.get('spawning_is_enabled'))

    right_down_corner = np.array(screen.field.shape) - 1
    corner_pos = np.array([[[0, 0], [0, right_down_corner[1]]],
                           [[right_down_corner[0], 0], [right_down_corner[0], right_down_corner[1]]]])

    all_snakes_configs = [first_snake_config, second_snake_config, third_snake_config, fourth_snake_config]
    default_snakes_controls = ['wsad', 'ARROWS', 'tgfh', 'ikjl']
    snakes_pos = np.array([corner_pos[y, x] for y, x in zip([1, 0, 1, 0], [0, 1, 1, 0])])
    snakes_params: np.array = np.array([
        [screen for _ in range(4)],
        [str2tuple(all_snakes_configs[i].get('start_position'), int, snakes_pos[i]) for i in range(4)],
        [str2float(all_snakes_configs[i].get('moves_per_second'), 5) for i in range(4)],
        [all_snakes_configs[i].get('controls', default_snakes_controls[i]) for i in range(4)],
        [all_snakes_configs[i].get('name', f'Snake{i+1}') for i in range(4)],
        [str2float(all_snakes_configs[i].get('hue'), None) for i in range(4)],
        [str2bool(all_snakes_configs[i].get('contact_with_other_snakes'), False) for i in range(4)]
    ])

    for n in range(snakes_count):
        Snake(*(snakes_params[i, n] for i in range(7)))

    for n in range(snakes_count):
        Portals(screen, portals_hue[n], portals_spawning_is_enabled).create_portal(portals_amount)

    boosts_config = config['Boosts']

    Boosts.probabilities = str2tuple(boosts_config.get('probabilities'), int, (75, 15, 10, 5))
    boosts = Boosts(screen)

    walls_config = config['Walls']

    Walls(screen, str2bool(walls_config.get('spawning_is_enabled')))

    start_amount_of_boosts = max(screen.field.shape[0] * screen.field.shape[1] // 108, snakes_count)

    if boosts_config.get('start_amount') != 'None':
        start_amount_of_boosts = str2int(boosts_config.get('start_amount'),
                                         screen.field.shape[0] * screen.field.shape[1] // 108)

    boosts.create_boost(start_amount_of_boosts)

    while True:
        for event in pg.event.get():
            [exit() for _ in ' ' if event.type == pg.QUIT]

            if event.type == pg.KEYDOWN:
                for snake in screen.snakes:
                    if not pause:
                        snake.change_movement_direction(event.key)

                if event.key == pause_key or event.key == pg.K_SPACE:
                    pause = not pause

                if event.key == restart_key:
                    pause = False
                    screen.reset_all()
                    boosts.create_boost(start_amount_of_boosts)
                    for portals in screen.portals:
                        portals.create_portal(portals_amount)

                if event.key == pg.K_ESCAPE:
                    exit()

        if not pause:
            [snake.move(time) for snake in screen.snakes]

        pg.display.set_caption(f'Snake game [FPS: {clock.get_fps()}]')

        screen.update_screen(pause)

        if not pause:
            time += 1
        clock.tick(fps)


if __name__ == '__main__':
    main()
