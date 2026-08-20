"""
THE LAST SURVIVORS - Part 1
Created by Mr Abubakar Saudagar
Plain Studios
"""

import random
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout

FPS = 40

# ---------------- CHARACTER DATA ----------------
CHARACTERS = {
    "abubakar": {
        "name": "Abubakar",
        "desc": "Selfish genius. Natural leader. Deadly in a fight.",
        "speed": 6,
        "attack": 3,
        "health": 5,
        "color": (0.8, 0.15, 0.15, 1),
    },
    "saim": {
        "name": "Saim",
        "desc": "Best driver alive. Reads any map. Kind of an idiot.",
        "speed": 5,
        "attack": 1,
        "health": 3,
        "color": (0.15, 0.4, 0.8, 1),
    },
}


# ---------------- SPLASH SCREENS ----------------
class CreatorScreen(Screen):
    def on_enter(self):
        Clock.schedule_once(lambda dt: self.manager.__setattr__("current", "studio"), 2.2)


class StudioScreen(Screen):
    def on_enter(self):
        Clock.schedule_once(lambda dt: self.manager.__setattr__("current", "title"), 2.2)


class TitleScreen(Screen):
    pass


# ---------------- CHARACTER SELECT ----------------
class SelectScreen(Screen):
    def choose(self, char_key):
        app = App.get_running_app()
        app.player_char = char_key
        app.companion_char = "saim" if char_key == "abubakar" else "abubakar"
        self.manager.current = "game"


# ---------------- GAME WIDGET ----------------
class GameArea(Widget):
    def __init__(self, player_key, companion_key, on_win, on_lose, **kwargs):
        super().__init__(**kwargs)
        self.player_key = player_key
        self.companion_key = companion_key
        self.pdata = CHARACTERS[player_key]
        self.cdata = CHARACTERS[companion_key]
        self.on_win = on_win
        self.on_lose = on_lose

        self.player_health = self.pdata["health"]
        self.stage = 1  # 1,2,3 then lab
        self.stage_progress = 0
        self.stage_target = 400  # distance to clear a stage

        self.player_x = 60
        self.player_y = 200
        self.comp_x = 20
        self.comp_y = 200

        self.zombies = []
        self.obstacles = []
        self.keys_held = set()

        self._keyboard = Window.request_keyboard(self._kb_closed, self)
        self._keyboard.bind(on_key_down=self._on_key_down, on_key_up=self._on_key_up)

        self.spawn_timer = 0
        Clock.schedule_interval(self.update, 1.0 / FPS)

    def _kb_closed(self):
        self._keyboard.unbind(on_key_down=self._on_key_down, on_key_up=self._on_key_up)
        self._keyboard = None

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        self.keys_held.add(keycode[1])

    def _on_key_up(self, keyboard, keycode):
        self.keys_held.discard(keycode[1])

    def spawn_zombie(self):
        y = random.randint(40, int(self.height) - 40) if self.height else 200
        self.zombies.append({"x": self.width + 40, "y": y, "speed": random.uniform(2, 4)})

    def spawn_obstacle(self):
        y = random.randint(40, int(self.height) - 80) if self.height else 200
        self.obstacles.append({"x": self.width + 60, "y": y, "w": 40, "h": 60})

    def update(self, dt):
        if not self.width:
            return

        # movement
        move_x = 0
        move_y = 0
        if "up" in self.keys_held or "w" in self.keys_held:
            move_y = 1
        if "down" in self.keys_held or "s" in self.keys_held:
            move_y = -1
        if "left" in self.keys_held or "a" in self.keys_held:
            move_x = -1
        if "right" in self.keys_held or "d" in self.keys_held:
            move_x = 1

        speed = self.pdata["speed"]
        self.player_y += move_y * speed
        self.player_x += move_x * speed * 0.4  # limited horizontal drift
        self.player_y = max(20, min(self.height - 20, self.player_y))
        self.player_x = max(10, min(120, self.player_x))

        # companion follows loosely, occasionally auto-acts (dumb if Saim / smart if Abubakar)
        self.comp_y += (self.player_y - self.comp_y) * 0.06
        self.comp_x = max(10, self.player_x - 40)

        # world scroll = progress
        self.stage_progress += speed * 0.5

        # spawn stuff
        self.spawn_timer += 1
        if self.spawn_timer > 45:
            self.spawn_timer = 0
            if random.random() < 0.7:
                self.spawn_zombie()
            else:
                self.spawn_obstacle()

        # move zombies & obstacles toward player, check collisions
        for z in self.zombies:
            z["x"] -= z["speed"]
        for o in self.obstacles:
            o["x"] -= 3

        px, py = self.player_x, self.player_y
        for z in list(self.zombies):
            if z["x"] < px + 25 and z["x"] > px - 25 and abs(z["y"] - py) < 25:
                # companion (Abubakar) can auto-fight zombies if he's the companion
                if self.companion_key == "abubakar" and random.random() < 0.5:
                    self.zombies.remove(z)
                    continue
                self.player_health -= 1
                self.zombies.remove(z)
                if self.player_health <= 0:
                    self.on_lose()
                    return

        for o in list(self.obstacles):
            if o["x"] < px + 20 and o["x"] > px - 20 and abs(o["y"] - py) < 30:
                # Saim companion helps navigate around obstacles automatically
                if self.companion_key == "saim":
                    self.player_x = max(10, self.player_x - 15)
                else:
                    self.player_health -= 1
                    if self.player_health <= 0:
                        self.on_lose()
                        return
                self.obstacles.remove(o)

        self.zombies = [z for z in self.zombies if z["x"] > -40]
        self.obstacles = [o for o in self.obstacles if o["x"] > -60]

        # stage progression
        if self.stage_progress >= self.stage_target:
            self.stage_progress = 0
            self.stage += 1
            self.zombies.clear()
            self.obstacles.clear()
            if self.stage > 3:
                self.on_win()
                return

        self.draw()

    def draw(self):
        self.canvas.clear()
        with self.canvas:
            # background
            Color(0.03, 0.08, 0.04, 1)
            Rectangle(pos=(0, 0), size=(self.width, self.height))

            # ground line
            Color(0.1, 0.2, 0.1, 1)
            Rectangle(pos=(0, 0), size=(self.width, 15))

            # obstacles
            Color(0.4, 0.25, 0.1, 1)
            for o in self.obstacles:
                Rectangle(pos=(o["x"], o["y"]), size=(o["w"], o["h"]))

            # zombies
            Color(0.2, 0.6, 0.2, 1)
            for z in self.zombies:
                Ellipse(pos=(z["x"] - 15, z["y"] - 15), size=(30, 30))

            # companion
            r, g, b, a = self.cdata["color"]
            Color(r, g, b, 0.6)
            Ellipse(pos=(self.comp_x - 14, self.comp_y - 14), size=(28, 28))

            # player
            r, g, b, a = self.pdata["color"]
            Color(r, g, b, a)
            Ellipse(pos=(self.player_x - 16, self.player_y - 16), size=(32, 32))


# ---------------- GAME SCREEN ----------------
class GameScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        self.root_layout = self.ids.game_root
        self.root_layout.clear_widgets()

        self.hud = Label(
            text=self.hud_text(app, 1),
            size_hint=(1, None), height=40,
            pos_hint={"top": 1},
        )
        self.game_area = GameArea(
            app.player_char, app.companion_char,
            on_win=self.win, on_lose=self.lose,
        )
        self.root_layout.add_widget(self.game_area)
        self.root_layout.add_widget(self.hud)
        Clock.schedule_interval(self.refresh_hud, 0.3)

    def hud_text(self, app, health):
        return f"{CHARACTERS[app.player_char]['name']}  |  HP: {health}  |  Stage: {self.game_area.stage if hasattr(self, 'game_area') else 1}/3"

    def refresh_hud(self, dt):
        if hasattr(self, "game_area"):
            self.hud.text = (
                f"{CHARACTERS[App.get_running_app().player_char]['name']}  |  "
                f"HP: {self.game_area.player_health}  |  Stage: {min(self.game_area.stage,3)}/3"
            )
            if self.game_area.stage > 3:
                return False

    def win(self):
        self.manager.current = "win"

    def lose(self):
        self.manager.current = "lose"


# ---------------- END SCREENS ----------------
class WinScreen(Screen):
    def on_enter(self):
        Clock.schedule_once(lambda dt: self.manager.__setattr__("current", "studio_end"), 3)


class StudioEndScreen(Screen):
    def on_enter(self):
        Clock.schedule_once(lambda dt: self.manager.__setattr__("current", "creator_end"), 2.2)


class CreatorEndScreen(Screen):
    pass


class LoseScreen(Screen):
    def restart(self):
        self.manager.current = "select"


# ---------------- KV LAYOUT ----------------
KV = """
ScreenManager:
    CreatorScreen:
    StudioScreen:
    TitleScreen:
    SelectScreen:
    GameScreen:
    WinScreen:
    StudioEndScreen:
    CreatorEndScreen:
    LoseScreen:

<CreatorScreen>:
    name: "creator"
    canvas.before:
        Color:
            rgba: 0,0,0,1
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: "Created by\\nMr Abubakar Saudagar"
        font_size: "26sp"
        halign: "center"
        color: 0.6,1,0.6,1

<StudioScreen>:
    name: "studio"
    canvas.before:
        Color:
            rgba: 0,0,0,1
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: "PLAIN STUDIOS\\nPRESENTS"
        font_size: "24sp"
        halign: "center"
        color: 0.55,0.85,0.6,1

<TitleScreen>:
    name: "title"
    canvas.before:
        Color:
            rgba: 0.02,0.05,0.02,1
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: "vertical"
        padding: 30
        spacing: 20
        Label:
            text: "THE LAST\\nSURVIVORS"
            font_size: "38sp"
            halign: "center"
            color: 0.85,1,0.8,1
        Button:
            text: "START"
            size_hint: (1, 0.2)
            background_color: 0.3,0.6,0.3,1
            on_release: app.root.current = "select"

<SelectScreen>:
    name: "select"
    canvas.before:
        Color:
            rgba: 0.02,0.05,0.02,1
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: "vertical"
        padding: 20
        spacing: 15
        Label:
            text: "CHOOSE YOUR SURVIVOR"
            font_size: "20sp"
            size_hint: (1, 0.15)
            color: 0.8,1,0.8,1
        BoxLayout:
            spacing: 15
            BoxLayout:
                orientation: "vertical"
                spacing: 8
                Label:
                    text: "ABUBAKAR"
                    font_size: "18sp"
                    color: 0.9,0.3,0.3,1
                Label:
                    text: "Selfish genius.\\nDeadly fighter.\\nNo weakness."
                    font_size: "13sp"
                Button:
                    text: "PLAY AS ABUBAKAR"
                    on_release: root.choose("abubakar")
            BoxLayout:
                orientation: "vertical"
                spacing: 8
                Label:
                    text: "SAIM"
                    font_size: "18sp"
                    color: 0.3,0.5,0.9,1
                Label:
                    text: "Great driver.\\nReads any map.\\nKind of dumb."
                    font_size: "13sp"
                Button:
                    text: "PLAY AS SAIM"
                    on_release: root.choose("saim")

<GameScreen>:
    name: "game"
    FloatLayout:
        id: game_root

<WinScreen>:
    name: "win"
    canvas.before:
        Color:
            rgba: 0,0,0,1
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: "TO BE CONTINUED..."
        font_size: "28sp"
        color: 0.8,1,0.8,1

<StudioEndScreen>:
    name: "studio_end"
    canvas.before:
        Color:
            rgba: 0,0,0,1
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: "PLAIN STUDIOS\\nPRESENTS"
        font_size: "24sp"
        halign: "center"
        color: 0.55,0.85,0.6,1

<CreatorEndScreen>:
    name: "creator_end"
    canvas.before:
        Color:
            rgba: 0,0,0,1
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: "Created by\\nMr Abubakar Saudagar"
        font_size: "26sp"
        halign: "center"
        color: 0.6,1,0.6,1

<LoseScreen>:
    name: "lose"
    canvas.before:
        Color:
            rgba: 0.1,0,0,1
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: "vertical"
        padding: 40
        spacing: 20
        Label:
            text: "YOU DIDN'T SURVIVE"
            font_size: "24sp"
            color: 1,0.5,0.5,1
        Button:
            text: "TRY AGAIN"
            size_hint: (1, 0.2)
            on_release: root.restart()
"""


class LastSurvivorsApp(App):
    player_char = "abubakar"
    companion_char = "saim"

    def build(self):
        self.title = "The Last Survivors"
        return __import__("kivy.lang", fromlist=["Builder"]).Builder.load_string(KV)


if __name__ == "__main__":
    LastSurvivorsApp().run()
