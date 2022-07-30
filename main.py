from PIL import Image
from Packages.HueShifter import shift_image_hue
from Packages.StrConventers import *
import pygame as pg
import numpy as np
import pathlib as pl

pg.init()
clock = pg.time.Clock()

error_texture = pg.image.load('Texture Packs/Default/error.png')
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


def pil_img2pg_img(img: Image):
    return pg.image.fromstring(img.tobytes(), img.size, img.mode)


class Screen:
    empty_space_texture = pg.image.load(f'Texture Packs/Default/empty_tile.png')

    def __init__(self, shape: tuple[int, int], screen_boundaries_is_deadly=False, size_multiplier=50):
        self.__snakes = []
        self.__boosts = None
        self.__walls = None

        self.__field_dtype = np.dtype([('object', object), ('type', int)])
        self.__field = np.zeros(shape, dtype=self.__field_dtype)

        self.__screen_boundaries_is_deadly = bool(screen_boundaries_is_deadly)

        self.__size_multiplier = size_multiplier
        self.__screen = pg.display.set_mode(tuple(np.array(self.field.shape) * self.__size_multiplier))

        self.__font = pg.font.Font('./Fonts/fff-forward.regular.ttf', min(self.screen.get_size()) // 50)

    def __str__(self) -> str:
        return f'{self.__field}'

    def __repr__(self) -> str:
        return f'Screen({self.__field.shape})'

    def update(self):
        self.__field[:] = np.zeros(self.__field.shape, dtype=self.__field_dtype)

        if self.boosts is not None:
            for boost in self.boosts.boosts:
                if all(boost[:-1] != np.array([-1, -1])):
                    self.field[boost[0], boost[1]]['object'] = self.boosts
                    self.field[boost[0], boost[1]]['type'] = boost[2]

        for snake in self.__snakes:
            for element_pos in snake.tail_elements_pos:
                if all(element_pos != np.array([-1, -1])):
                    self.field[element_pos[0], element_pos[1]]['object'] = snake
                    self.field[element_pos[0], element_pos[1]]['type'] = 1

        for snake in self.__snakes:
            self.field[snake.head_pos[0], snake.head_pos[1]]['object'] = snake
            self.field[snake.head_pos[0], snake.head_pos[1]]['type'] = 0

        if self.walls is not None:
            for wall in self.walls.walls_pos:
                if all(wall != np.array([-1, -1])):
                    self.field[wall[0], wall[1]]['object'] = self.walls
                    self.field[wall[0], wall[1]]['type'] = 0

    def add_snake(self, snake):
        if isinstance(snake, Snake):
            self.__snakes.append(snake)
        else:
            raise TypeError('snake must be an instance of Snake')

    def check_for_objects_at_the_position(self, pos, current_snake=None) -> dict:
        pos = np.array(pos)
        is_here_head = is_here_tail = False
        for snake in self.__snakes:
            if (current_snake is not None and current_snake.contact_with_other_snakes) and snake is not current_snake:
                is_here_head = all(snake.head_pos == pos) or is_here_head
            elif current_snake is None:
                is_here_head = all(snake.head_pos == pos) or is_here_head

            if current_snake is None or current_snake.contact_with_other_snakes:
                tail_elements_pos = snake.tail_elements_pos
                if snake.is_alive:
                    tail_elements_pos = tail_elements_pos[1:]
                is_here_tail = is_here_tail or in_array(tail_elements_pos, pos)
            else:
                tail_elements_pos = current_snake.tail_elements_pos[1:]
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

    def reset_all(self):
        for snake in self.snakes:
            snake.reset()

        self.boosts.reset()
        self.walls.reset()

    def normalized_pos(self, pos) -> np.array:
        pos = np.array(pos)

        if any(directions := self.is_out_of_field(pos)):
            for i in range(2):
                _ = {1: 0, -1: self.field.shape[i] - 1}
                pos[i] = _.get(directions[i], pos[i])

        return pos

    def update_screen(self, pause=False):
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
    def get_texture_paths(texture_num: Literal[0, 1, 2, 3], _texture_pack_name: str = None):
        if _texture_pack_name is None:
            _texture_pack_name = texture_pack_name

        data_pack_path = pl.Path(__file__).parent.joinpath('Texture Packs').joinpath(_texture_pack_name)

        texture_paths_tuple = (data_pack_path.joinpath('snake_head_static.png'),
                               data_pack_path.joinpath('snake_head_movement.png'),
                               data_pack_path.joinpath('dead_head.png'),
                               data_pack_path.joinpath('tail.png'))

        return texture_paths_tuple[texture_num]

    def __init__(self, _screen: Screen, pos=(0, 0), moves_per_second=4,
                 controls: str = None, name=None, hue=None, contact_with_other_snakes=False):

        if name is None:
            name = f'Snake{Snake.__snakes_number}'
        else:
            name = str(name)
        self.__name = name

        if hue is None:
            hue = np.random.randint(180)

        self.__hue = hue
        self.__head_static_texture = pil_img2pg_img(shift_image_hue(Snake.get_texture_paths(0), self.hue))
        self.__head_movement_texture = pil_img2pg_img(shift_image_hue(Snake.get_texture_paths(1), self.hue))
        self.__skull = pil_img2pg_img(shift_image_hue(Snake.get_texture_paths(2), self.hue))
        self.__tail_texture = pil_img2pg_img(shift_image_hue(Snake.get_texture_paths(3), self.hue))

        Snake.__snakes_number += 1

        self.__moves_per_second = moves_per_second
        self.__screen = _screen
        self.__screen.add_snake(self)

        self.__head_pos: np.array = np.array(pos)
        self.__previous_pos = np.array([-1, -1])
        self.__start_pos = self.__head_pos
        self.__tail_elements_pos: np.array = np.array([[-1, -1]])
        self.__movement: np.array = np.zeros(2, dtype=np.int8)

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

        if fps > 0 == time % (fps // min(self.moves_per_second, int(fps))):
            if not self.check_for_obstacle(self.next_pos()) and self.is_alive and any(self.movement != 0):
                self.head_pos = (self.head_pos + self.movement)
            elif self.check_for_obstacle(self.next_pos()):
                self.__is_alive = False

            if not self.is_alive:
                self.delete_last_element()

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

    def delete_last_element(self, amount=1):
        if amount < 0:
            self.add_new_element(abs(amount))
            return

        for _ in range(amount):
            if len(self.tail_elements_pos) > 1:
                self.__tail_elements_pos = np.delete(self.tail_elements_pos, 0, 0)

    def eat(self):
        if self.screen.check_for_objects_at_the_position(self.head_pos)['boost']:

            boost_type = self.boosts.destroy_boost_at_pos(self.head_pos)
            match boost_type:
                case 0:
                    self.add_new_element()
                    self.__score += 1

                case 1:
                    self.delete_last_element()

                case 2:
                    efficiency = np.random.randint(-1, 1)
                    elements_number = np.random.randint(-2, 2)
                    self.add_new_element(elements_number)
                    self.__score += elements_number + efficiency

                case 3:
                    wall_amount_to_be_destroyed = self.walls.walls_pos.size // 4
                    self.walls.delete_random_wall(wall_amount_to_be_destroyed)

                    self.__score -= wall_amount_to_be_destroyed // 2

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
                    screen.blit(pg.transform.scale(texture, (size, size)), pos)

                elif all(self.movement == (0, 0)):
                    screen.blit(pg.transform.scale(self.__head_static_texture, (size, size)), pos)

                else:
                    screen.blit(pg.transform.scale(self.__skull, (size, size)), pos)

            case 1:
                screen.blit(pg.transform.scale(self.__tail_texture, (size, size)), pos)
            case _:
                screen.blit(pg.transform.scale(error_texture, (size, size)), pos)

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

        self.__head_static_texture = pil_img2pg_img(shift_image_hue(Snake.get_texture_paths(0), self.hue))
        self.__head_movement_texture = pil_img2pg_img(shift_image_hue(Snake.get_texture_paths(1), self.hue))
        self.__tail_texture = pil_img2pg_img(shift_image_hue(Snake.get_texture_paths(2), self.hue))

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

        self.__textures = (pg.image.load(f'Texture Packs/{texture_pack_name}/plus.png'),
                           pg.image.load(f'Texture Packs/{texture_pack_name}/minus.png'),
                           pg.image.load(f'Texture Packs/{texture_pack_name}/question_mark.png'),
                           pg.image.load(f'Texture Packs/{texture_pack_name}/blue_cross.png'))

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

        self.__texture = pg.image.load(f'Texture Packs/{texture_pack_name}/wall.png')

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


def main():
    global texture_pack_name

    import configparser

    config = configparser.ConfigParser()
    config.read('config.ini')
    config.read_dict({'Game': {'': ''},
                      'Screen': {'': ''},
                      'Snake': {'': ''},
                      'FirstSnake': {'': ''},
                      'SecondSnake': {'': ''},
                      'Boosts': {'': ''},
                      'Walls': {'': ''}})

    time = 0
    pause = False

    game_config = config['Game']

    fps = str2int(game_config.get('fps'), 30)

    pause_key = ord(game_config.get('pause_key', 'p'))
    restart_key = ord(game_config.get('restart_key', 'r'))

    texture_pack_name = game_config.get('texture_pack_name', 'Default')

    if not pl.Path(__file__).parent.joinpath('Texture Packs').joinpath(texture_pack_name).exists():
        texture_pack_name = 'Default'

    Screen.empty_space_texture = pg.image.load(f'Texture Packs/{texture_pack_name}/empty_tile.png')

    screen_config = config['Screen']

    screen_shape = str2tuple(screen_config.get('shape'), int, (31, 31))
    screen = Screen(screen_shape,
                    str2bool(screen_config.get('screen_boundaries_is_deadly')),
                    str2int(screen_config.get('size_multiplier'), int(961/(screen_shape[0]*screen_shape[1])**0.5)))

    snakes_config = config['Snake']

    # 2-player mode may have some bugs
    two_player_mode = str2bool(snakes_config.get('two_player_mode'))
    first_snake_config = config['FirstSnake']
    second_snake_config = config['SecondSnake']

    if two_player_mode:
        start_positions = (str2tuple(first_snake_config.get('start_position'), int, (0, 0)),
                           str2tuple(second_snake_config.get('start_position'), int,
                                     tuple(np.array(screen.field.shape) - 1)))

        Snake(screen, start_positions[0], str2int(first_snake_config.get('moves_per_second'), 4),
              first_snake_config.get('controls', 'wsad'), first_snake_config.get('name'),
              str2int(first_snake_config.get('hue'), None),
              str2bool(first_snake_config.get('contact_with_other_snakes')))
        Snake(screen, start_positions[1], str2int(second_snake_config.get('moves_per_second'), 4),
              second_snake_config.get('controls', 'ARROWS'), second_snake_config.get('name'),
              str2int(second_snake_config.get('hue'), None),
              str2bool(second_snake_config.get('contact_with_other_snakes')))
    else:
        Snake(screen, (screen.field.shape[0] // 2, screen.field.shape[1] // 2),
              str2int(first_snake_config.get('moves_per_second'), 4), first_snake_config.get('controls', 'wsad'),
              first_snake_config.get('name'),
              str2int(first_snake_config.get('hue'), None),
              str2bool(first_snake_config.get('contact_with_other_snakes')))

    boosts_config = config['Boosts']

    Boosts.probabilities = str2tuple(boosts_config.get('probabilities'), int, (75, 15, 10, 5))
    boosts = Boosts(screen)

    walls_config = config['Walls']

    Walls(screen, str2bool(walls_config.get('spawning_is_enabled')))

    start_amount_of_boosts = max(screen.field.shape[0] * screen.field.shape[1] // 108, 1 + int(two_player_mode))

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

                if event.key == pg.K_ESCAPE:
                    exit()

        if not pause:
            [snake.move(time) for snake in screen.snakes]

            screen.update()

        pg.display.set_caption(f'Snake game [FPS: {clock.get_fps()}]')

        screen.update_screen(pause)

        if not pause:
            time += 1
        clock.tick(fps)


if __name__ == '__main__':
    main()
