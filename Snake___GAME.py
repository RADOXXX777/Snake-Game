"""
SNAKE GAME - Python (turtle, no installation needed)

Run it from IDLE (F5) or:  python snake_game_v2.py

Controls:
    Arrow keys / WASD  - move
    P                  - pause / resume
    R                  - restart
    Close the window   - quit

Features:
    - Title header with snake emblems
    - Side panel with BEST SCORE, score, length and level
    - Game speeds up as you level up (every 50 points)
    - High score saved between runs
"""

import json
import math
import os
import random
import tkinter
import turtle

# ---------- Settings ----------
CELL = 20
COLS, ROWS = 30, 26
BOX_W, BOX_H = COLS * CELL, ROWS * CELL

WIN_W, WIN_H = 880, 660
BOX_LEFT, BOX_TOP = -420, 240
PANEL_LEFT, PANEL_W = 200, 220
PANEL_CX = PANEL_LEFT + PANEL_W // 2

START_DELAY = 130      # ms between moves (lower = faster)
MIN_DELAY = 55
FOOD_POINTS = 10
POINTS_PER_LEVEL = 50

HIGHSCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "snake_highscore.json")

# Colors
BG = "#0f1117"
BOX_BG = "#141821"
GRID = "#1b2030"
BORDER = "#50dc78"
CARD_BG = "#1a1f2b"
CARD_BORDER = "#2c3345"
GREEN = "#50dc78"
GOLD = "#ffcd50"
RED = "#f05050"
WHITE = "#e6e6eb"
GRAY = "#8a90a2"

UP, DOWN, LEFT, RIGHT = (0, -1), (0, 1), (-1, 0), (1, 0)


# ---------- Helpers ----------
def load_highscore():
    try:
        with open(HIGHSCORE_FILE, "r") as f:
            return int(json.load(f).get("highscore", 0))
    except (OSError, ValueError):
        return 0


def save_highscore(value):
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            json.dump({"highscore": value}, f)
    except OSError:
        pass


def lerp_color(c1, c2, t):
    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)
    return "#%02x%02x%02x" % (r, g, b)


def to_screen(cx, cy):
    """Convert grid cell to screen coordinates (center of the cell)."""
    return (BOX_LEFT + CELL / 2 + cx * CELL,
            BOX_TOP - CELL / 2 - cy * CELL)


def draw_rect(t, left, top, w, h, fill=None, outline=None, width=2):
    t.penup()
    t.goto(left, top)
    t.setheading(0)
    t.pensize(width)
    t.pencolor(outline or fill or "white")
    if fill:
        t.fillcolor(fill)
        t.begin_fill()
    t.pendown()
    for d in (w, h, w, h):
        t.forward(d)
        t.right(90)
    t.penup()
    if fill:
        t.end_fill()


def write(t, x, y, text, color, size, style="bold", align="center"):
    t.goto(x, y)
    t.color(color)
    t.write(text, align=align, font=("Consolas", size, style))


# ---------- Screen ----------
screen = turtle.Screen()
screen.title("Snake Game - Python")
screen.bgcolor(BG)
screen.setup(WIN_W, WIN_H)
screen.tracer(0)

deco = turtle.Turtle()      # static decoration
deco.hideturtle()
deco.penup()
deco.speed(0)

panel = turtle.Turtle()     # dynamic panel values
panel.hideturtle()
panel.penup()

food_t = turtle.Turtle()
food_t.shape("circle")
food_t.shapesize(0.8, 0.8)
food_t.color(RED)
food_t.penup()

snake_pen = turtle.Turtle()
snake_pen.shape("square")
snake_pen.penup()

msg = turtle.Turtle()       # overlay messages (created last = drawn on top)
msg.hideturtle()
msg.penup()
msg.speed(0)


def draw_snake_icon(x, y, facing):
    """Original snake emblem: a wavy green snake. facing = 1 (right) or -1 (left)."""
    n = 9
    for i in range(n):
        t = i / (n - 1)
        px = x + facing * i * 13
        py = y + 7 * math.sin(i * 0.85)
        col = lerp_color((30, 110, 60), (80, 220, 120), t)
        deco.goto(px, py)
        deco.dot(9 + 9 * t, col)

    # Head details: eyes and tongue
    px = x + facing * (n - 1) * 13
    py = y + 7 * math.sin((n - 1) * 0.85)
    for dy in (5, -5):
        deco.goto(px + facing * 3, py + dy)
        deco.dot(6, "white")
        deco.goto(px + facing * 4, py + dy)
        deco.dot(3, "black")

    deco.pencolor(RED)
    deco.pensize(2)
    deco.goto(px + facing * 9, py)
    deco.pendown()
    deco.goto(px + facing * 16, py)
    deco.goto(px + facing * 21, py + 4)
    deco.goto(px + facing * 16, py)
    deco.goto(px + facing * 21, py - 4)
    deco.penup()


def draw_background():
    # Header
    write(deco, 2, 274, "SNAKE GAME", "#1e6e3c", 30)      # shadow
    write(deco, 0, 276, "SNAKE GAME", GREEN, 30)
    draw_snake_icon(-290, 296, 1)
    draw_snake_icon(290, 296, -1)
    deco.goto(BOX_LEFT, 258)
    deco.pencolor(CARD_BORDER)
    deco.pensize(2)
    deco.pendown()
    deco.goto(-BOX_LEFT, 258)
    deco.penup()

    # Game box
    draw_rect(deco, BOX_LEFT, BOX_TOP, BOX_W, BOX_H, fill=BOX_BG, outline=BORDER, width=4)

    # Grid lines
    deco.pensize(1)
    deco.pencolor(GRID)
    for c in range(1, COLS):
        x = BOX_LEFT + c * CELL
        deco.goto(x, BOX_TOP - 2)
        deco.pendown()
        deco.goto(x, BOX_TOP - BOX_H + 2)
        deco.penup()
    for r in range(1, ROWS):
        y = BOX_TOP - r * CELL
        deco.goto(BOX_LEFT + 2, y)
        deco.pendown()
        deco.goto(BOX_LEFT + BOX_W - 2, y)
        deco.penup()

    # Side panel: stat cards
    card_h = 80
    tops = [240, 150, 60, -30]
    labels = ["BEST SCORE", "SCORE", "LENGTH", "LEVEL"]
    for top, label in zip(tops, labels):
        border = GOLD if label == "BEST SCORE" else CARD_BORDER
        draw_rect(deco, PANEL_LEFT, top, PANEL_W, card_h, fill=CARD_BG, outline=border, width=2)
        write(deco, PANEL_CX, top - 26, label, GRAY, 11)

    # Controls card
    draw_rect(deco, PANEL_LEFT, -120, PANEL_W, 160, fill=CARD_BG, outline=CARD_BORDER, width=2)
    write(deco, PANEL_CX, -152, "CONTROLS", GRAY, 11)
    for i, line in enumerate(["Arrows / WASD : move",
                              "P : pause",
                              "R : restart",
                              "Eat red food to grow"]):
        write(deco, PANEL_CX, -182 - i * 26, line, WHITE, 11, style="normal")

    # Footer
    write(deco, 0, -318, "Made with Python", GRAY, 11, style="normal")


def show_message(title, lines, color):
    msg.clear()
    cx = BOX_LEFT + BOX_W / 2
    cy = BOX_TOP - BOX_H / 2
    h = 80 + 28 * len(lines)
    w = 380
    top = cy + h / 2
    draw_rect(msg, cx - w / 2, top, w, h, fill="#0b0d12", outline=color, width=3)
    write(msg, cx, top - 60, title, color, 28)
    for i, line in enumerate(lines):
        write(msg, cx, top - 95 - i * 26, line, WHITE, 12, style="normal")


# ---------- Game ----------
class Game:
    def __init__(self):
        self.best = load_highscore()
        self.reset()

    def reset(self):
        cx, cy = COLS // 2, ROWS // 2
        self.snake = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = RIGHT
        self.pending = RIGHT
        self.score = 0
        self.level = 1
        self.delay = START_DELAY
        self.started = False
        self.paused = False
        self.over = False
        self.new_best = False
        self.food = self.random_food()
        show_message("READY?", ["Press an arrow key or WASD to start"], GREEN)
        self.refresh_panel()

    def random_food(self):
        taken = set(self.snake)
        free = [(x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in taken]
        return random.choice(free) if free else None

    def turn(self, direction):
        if self.over or self.paused:
            return
        if direction == (-self.direction[0], -self.direction[1]):
            return  # can't reverse into yourself
        self.pending = direction
        if not self.started:
            self.started = True
            msg.clear()

    def toggle_pause(self):
        if self.over or not self.started:
            return
        self.paused = not self.paused
        if self.paused:
            show_message("PAUSED", ["Press P to resume"], GOLD)
        else:
            msg.clear()

    def step(self):
        self.direction = self.pending
        dx, dy = self.direction
        hx, hy = self.snake[0]
        nx, ny = hx + dx, hy + dy

        eating = (nx, ny) == self.food
        body = self.snake if eating else self.snake[:-1]

        if not (0 <= nx < COLS and 0 <= ny < ROWS) or (nx, ny) in body:
            self.end()
            return

        self.snake.insert(0, (nx, ny))
        if eating:
            self.score += FOOD_POINTS
            self.level = self.score // POINTS_PER_LEVEL + 1
            self.delay = max(MIN_DELAY, START_DELAY - (self.level - 1) * 8)
            if self.score > self.best:
                self.best = self.score
                self.new_best = True
                save_highscore(self.best)
            self.food = self.random_food()
            self.refresh_panel()
            if self.food is None:
                self.end(won=True)
        else:
            self.snake.pop()

    def end(self, won=False):
        self.over = True
        if self.score > self.best:
            self.best = self.score
            save_highscore(self.best)
        self.refresh_panel()
        title = "YOU WIN!" if won else "GAME OVER"
        color = GOLD if won else RED
        line1 = f"Score: {self.score}"
        if self.new_best:
            line1 += "   NEW BEST!"
        show_message(title, [line1, "Press R to restart"], color)

    def refresh_panel(self):
        panel.clear()
        tops = [240, 150, 60, -30]
        values = [(self.best, GOLD), (self.score, WHITE),
                  (len(self.snake), GREEN), (self.level, WHITE)]
        for top, (value, color) in zip(tops, values):
            write(panel, PANEL_CX, top - 68, str(value), color, 28)

    def draw(self):
        snake_pen.clearstamps()
        n = len(self.snake)
        for i in range(n - 1, -1, -1):  # tail first, head drawn last (on top)
            x, y = to_screen(*self.snake[i])
            snake_pen.goto(x, y)
            if i == 0:
                snake_pen.color("#8dffae")
                snake_pen.shapesize(0.95, 0.95)
            else:
                t = i / max(n - 1, 1)
                snake_pen.color(lerp_color((60, 205, 120), (30, 120, 70), t))
                snake_pen.shapesize(0.85, 0.85)
            snake_pen.stamp()
        snake_pen.goto(3000, 3000)

        if self.food:
            food_t.goto(*to_screen(*self.food))
        else:
            food_t.goto(3000, 3000)


# ---------- Setup ----------
draw_background()
game = Game()


def tick():
    try:
        if game.started and not game.paused and not game.over:
            game.step()
        game.draw()
        screen.update()
        screen.ontimer(tick, game.delay)
    except (turtle.Terminator, tkinter.TclError):
        pass  # window was closed


screen.listen()
for keys, direction in ((("Up", "w", "W"), UP), (("Down", "s", "S"), DOWN),
                        (("Left", "a", "A"), LEFT), (("Right", "d", "D"), RIGHT)):
    for key in keys:
        screen.onkeypress(lambda d=direction: game.turn(d), key)
for key in ("p", "P"):
    screen.onkeypress(game.toggle_pause, key)
for key in ("r", "R"):
    screen.onkeypress(game.reset, key)

tick()
screen.mainloop()
