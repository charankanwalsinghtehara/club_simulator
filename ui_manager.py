"""Reusable HUD, keyboard/mouse menus, dialogue, and notifications."""

from ursina import Button, Entity, Text, application, camera, color, destroy, mouse


class UIManager:
    def __init__(self):
        self.prompt = Text(parent=camera.ui, text="", position=(-0.62, -0.43),
                           origin=(0, 0), scale=0.9, color=color.white)
        self.wallet_label = Text(parent=camera.ui, text="", position=(-0.86, 0.46),
                                 origin=(-0.5, 0.5), scale=0.8, color=color.rgb32(255, 215, 132))
        self.controls = Text(parent=camera.ui, text="WASD move  |  Shift sprint  |  E interact  |  H history  |  M audio",
                             position=(0.86, 0.46), origin=(0.5, 0.5),
                             scale=0.58, color=color.rgb32(220, 215, 232))
        self.toast = Text(parent=camera.ui, text="", position=(0, -0.34),
                          origin=(0, 0), scale=0.9, color=color.white)
        self.toast_timer = 0.0
        self.menu_root = None
        self.menu_buttons = []
        self.menu_callbacks = []
        self.selected_option = 0
        self._was_mouse_locked = False
        self.sound_callback = None

    @property
    def menu_open(self):
        return self.menu_root is not None

    def set_prompt(self, text):
        if self.prompt.text != text:
            self.prompt.text = text

    def set_wallet(self, balance):
        self.wallet_label.text = f"Wallet: INR {balance:,}"

    def notify(self, message, duration=3.0):
        self.toast.text = message
        self.toast_timer = duration

    def show_dialogue(self, speaker, message):
        self.open_menu(
            speaker,
            [(message, lambda: None), ("Close", lambda: None)],
            footer="Press Enter or click Close"
        )

    def open_menu(self, title, options, footer="Select an option"):
        self.close_menu()
        if application.window_type == "onscreen":
            self._was_mouse_locked = mouse.locked
            mouse.locked = False
            mouse.visible = True
        self.menu_root = Entity(parent=camera.ui)
        Entity(parent=self.menu_root, model="quad", position=(0, 0, 0.1),
               scale=(0.72, 0.76), color=color.rgba32(12, 10, 23, 245))
        Text(parent=self.menu_root, text=title, position=(0, 0.29, -0.1),
             origin=(0, 0), scale=1.35, color=color.rgb32(255, 91, 190))
        self.menu_buttons = []
        self.menu_callbacks = []
        self.selected_option = 0
        row_count = max(1, len(options))
        spacing = min(0.135, 0.48 / row_count)
        start_y = (row_count - 1) * spacing / 2 + 0.025
        for index, (label, callback) in enumerate(options):
            button = Button(
                parent=self.menu_root,
                text=label,
                position=(0, start_y - index * spacing, -0.1),
                scale=(0.57, min(0.092, spacing * 0.78)),
                color=color.rgb32(40, 32, 60),
                highlight_color=color.rgb32(84, 48, 108),
                text_color=color.white,
                text_size=0.55,
                on_click=self._make_callback(callback)
            )
            self.menu_buttons.append(button)
            self.menu_callbacks.append(callback)
        Text(parent=self.menu_root, text=footer, position=(0, -0.31, -0.1),
             origin=(0, 0), scale=0.65, color=color.rgb32(190, 185, 204))
        self._update_selection()

    def _make_callback(self, callback):
        def invoke_callback():
            self._run_callback(callback)
        return invoke_callback

    def _run_callback(self, callback):
        if self.sound_callback:
            self.sound_callback()
        self.close_menu()
        callback()

    def _update_selection(self):
        for index, button in enumerate(self.menu_buttons):
            button.color = color.rgb32(82, 45, 105) if index == self.selected_option else color.rgb32(40, 32, 60)

    def choose(self, index):
        if not self.menu_open or not 0 <= index < len(self.menu_callbacks):
            return
        self._run_callback(self.menu_callbacks[index])

    def handle_key(self, key):
        if not self.menu_open:
            return False
        if key == "escape":
            self.close_menu()
            return True
        if key in ("enter", "numpad enter"):
            self.choose(self.selected_option)
            return True
        if key in ("up arrow", "w"):
            self.selected_option = (self.selected_option - 1) % len(self.menu_callbacks)
            self._update_selection()
            return True
        if key in ("down arrow", "s"):
            self.selected_option = (self.selected_option + 1) % len(self.menu_callbacks)
            self._update_selection()
            return True
        if len(key) == 1 and key.isdigit() and key != "0":
            self.choose(int(key) - 1)
            return True
        return True

    def close_menu(self):
        if self.menu_root is None:
            return
        destroy(self.menu_root)
        self.menu_root = None
        self.menu_buttons = []
        self.menu_callbacks = []
        if application.window_type == "onscreen":
            mouse.locked = self._was_mouse_locked
            mouse.visible = not self._was_mouse_locked

    def update(self, dt):
        if self.toast_timer > 0:
            self.toast_timer = max(0, self.toast_timer - dt)
            if self.toast_timer == 0:
                self.toast.text = ""

