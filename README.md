# Snake game

Everyone knows [this](https://en.wikipedia.org/wiki/Snake_(video_game_genre)) game. I just decided to write it myself.

## Controls

Use arrows to change direction of the snake movement, key `P` or `Space` to pause and `R` to reset. Use `Esc` to exit.
To control the first snake use `WASD` keys, to control the second one use arrows,
to the third one use `tfgh`, to the fourth one use `ijkl` (can be adjusted in `config.ini`).

## New

- [Portals](./README.md#Portals)
- 3-player and 4-player mode
- game font can be changed by adding a new font to the `Font` folder and changing `font_name` field in `config.ini`

## Game objects

### Snake

​<img alt="Static snake head" height="16" src="./Texture Packs/Default/snake_head_static.png" title="Head" width="16"/> 
is a default texture of static snake head.\
​<img alt="Moving snake head" height="16" src="./Texture Packs/Default/snake_head_movement.png" title="Head" width="16"/> 
is a default texture of moving snake head.\
​<img alt="Dead snake head" height="16" src="./Texture Packs/Default/dead_head.png" title="Head" width="16"/> 
is a default texture of dead snake head.\
​<img alt="Snake tail" height="16" src="./Texture Packs/Default/tail.png" title="Tail" width="16"/> 
is a default texture of snake tail.

Hue of all the textures can be changed.

### Boosts

The <img alt="The plus boost" height="16" src="./Texture Packs/Default/plus_boost.png" title="Plus" width="16"/>
boost increases the length of the snake's tail and score by one.\
Chance: `70%`

The <img alt="The minus boost" height="16" src="./Texture Packs/Default/minus_boost.png" title="Minus" width="16"/>
boost decreases the length of the snake's tail by one.\
Chance: `15%`

The <img alt="The random boost" height="16" src="./Texture Packs/Default/random_boost.png" title="Random" width="16"/>
boost increases the length of the snake's tail by a number from -2 to 2, the score increases by the same number 
adding a number from -1 to 1.\
Chance: `10%`

The <img alt="The wall destroyer boost" height="16" src="./Texture Packs/Default/wall_destroyer_boost.png" title="Walls destroyer" width="16"/>
boost destroys the quarter of all the walls and decreases the score by half of all destroyed walls.\
Chance: `5%`

### Walls

Walls <img alt="Wall" height="16" src="./Texture Packs/Default/wall.png" title="Wall" width="16"/> are obstacles for
snakes. If a snake crashes into the wall, it dies.

### Portals

Portals <img alt="Just a portal" height="16" src="./Texture Packs/Default/portal.png" title="Portal" width="16"/>
can teleport a snake to random portal with the same color. Used portals are moved.\
Hue of portals texture can be changed.

Amount of different portals equal to amount of players (snakes).

## Code

To run the game you neet to have [python](https://www.python.org/downloads/), and install all the required packages.
To do it, open terminal in the project folder and enter `pip install -r requirements.txt`.
Then run `main.py` file.\

*(`main.py` is the main file that runs the game, but it uses the console. If you don't need the console, run `main.pyw` 
instead.)

If you want to change the game and its rules, you can just adjust different values in `config.ini`.

### Texture Packs

To create a texture pack, go to `Texture Packs`, create a folder and put there images with the same names as in `Default`.
Then open `config.ini`, and write the name of created folder in `Game` section in `texture_pack_name` instead of `Default`.

### Debug

`prof.py` writes information about execution time of functions and methods to `stats.prof`.
To view this information, open terminal in `Debug` folder and enter `snakeviz .\stats.prof` 
(or `python.exe -m snakeviz .\stats.prof`).

## Discussions

If you have ideas or questions write them on the [discussions](https://github.com/Nazar0360/Snake/discussions).

## Issues

If you find a bug or other issue write about it on the [issues](https://github.com/Nazar0360/Snake/issues).