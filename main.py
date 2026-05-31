"""
BMW E30 1990 - شاشة داشبورد سيارة احترافية
تطبيق أندرويد بوضع قيادة مقفل
المبرمج: نظام BMW E30 Dashboard v2.0
"""

import os
import threading
import time
import webbrowser
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.lang import Builder
from kivy.properties import (BooleanProperty, NumericProperty,
                              StringProperty, ListProperty)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager, FadeTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.utils import get_color_from_hex
from kivy.metrics import dp

# ============================================================
# الألوان الرئيسية - BMW E30 الكلاسيكية
# ============================================================
BMW_BLACK = get_color_from_hex("#0A0A0F")
BMW_DARK = get_color_from_hex("#111118")
BMW_PANEL = get_color_from_hex("#1A1A24")
BMW_BLUE = get_color_from_hex("#1E90FF")
BMW_BLUE_GLOW = get_color_from_hex("#4DB8FF")
BMW_RED = get_color_from_hex("#FF3333")
BMW_ORANGE = get_color_from_hex("#FF8800")
BMW_GREEN = get_color_from_hex("#00FF88")
BMW_WHITE = get_color_from_hex("#E8E8F0")
BMW_GRAY = get_color_from_hex("#888899")
BMW_GOLD = get_color_from_hex("#D4AF37")

# الرمز السري الافتراضي
DEFAULT_PIN = "1990"


# ============================================================
# KV Language - تصميم الواجهة
# ============================================================
KV = """
#:import get_color_from_hex kivy.utils.get_color_from_hex

<GlowButton@Button>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    color: get_color_from_hex('#E8E8F0')
    font_size: '14sp'
    bold: True
    canvas.before:
        Color:
            rgba: get_color_from_hex('#1A1A24')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]
        Color:
            rgba: get_color_from_hex('#1E90FF') if self.state == 'normal' else get_color_from_hex('#4DB8FF')
        Line:
            rounded_rectangle: [self.x, self.y, self.width, self.height, dp(8)]
            width: 1.5

<DashLabel@Label>:
    color: get_color_from_hex('#E8E8F0')
    font_size: '12sp'

<SectionPanel@BoxLayout>:
    canvas.before:
        Color:
            rgba: get_color_from_hex('#1A1A24')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(10)]
        Color:
            rgba: get_color_from_hex('#1E90FF')
        Line:
            rounded_rectangle: [self.x+0.5, self.y+0.5, self.width-1, self.height-1, dp(10)]
            width: 0.8

<MainDashboard>:
    canvas.before:
        Color:
            rgba: get_color_from_hex('#0A0A0F')
        Rectangle:
            pos: self.pos
            size: self.size

<PinScreen>:
    canvas.before:
        Color:
            rgba: get_color_from_hex('#0A0A0F')
        Rectangle:
            pos: self.pos
            size: self.size

<AppScreen>:
    canvas.before:
        Color:
            rgba: get_color_from_hex('#0A0A0F')
        Rectangle:
            pos: self.pos
            size: self.size
"""

Builder.load_string(KV)


# ============================================================
# مؤشر دائري (عداد السرعة / RPM)
# ============================================================
class CircularGauge(Widget):
    value = NumericProperty(0)
    max_value = NumericProperty(100)
    min_value = NumericProperty(0)
    label_text = StringProperty("")
    unit_text = StringProperty("")
    color_main = ListProperty([0.12, 0.56, 1, 1])
    color_bg = ListProperty([0.1, 0.1, 0.14, 1])
    show_value = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            value=self._redraw, size=self._redraw,
            pos=self._redraw, max_value=self._redraw
        )

    def _redraw(self, *args):
        self.canvas.clear()
        cx = self.center_x
        cy = self.center_y
        r = min(self.width, self.height) * 0.42

        with self.canvas:
            # الخلفية
            Color(*self.color_bg)
            Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))

            # الحلقة الخارجية
            Color(0.2, 0.2, 0.3, 1)
            Line(circle=(cx, cy, r), width=dp(6))

            # القوس الملون
            pct = (self.value - self.min_value) / max(
                self.max_value - self.min_value, 1
            )
            angle = pct * 270
            Color(*self.color_main)
            Line(
                circle=(cx, cy, r, 135, 135 + angle),
                width=dp(5),
                cap="round"
            )

            # النقاط على الحلقة
            import math
            for i in range(9):
                a = math.radians(135 + i * 33.75)
                rx = cx + (r - dp(3)) * math.cos(a)
                ry = cy + (r - dp(3)) * math.sin(a)
                Color(0.5, 0.5, 0.6, 1)
                Ellipse(pos=(rx - dp(2), ry - dp(2)), size=(dp(4), dp(4)))

            # النقطة الإبرة
            needle_angle = math.radians(135 + pct * 270)
            nx = cx + (r - dp(8)) * math.cos(needle_angle)
            ny = cy + (r - dp(8)) * math.sin(needle_angle)
            Color(1, 0.2, 0.2, 1)
            Line(points=[cx, cy, nx, ny], width=dp(2.5), cap="round")

            # المركز
            Color(0.15, 0.15, 0.2, 1)
            Ellipse(pos=(cx - dp(8), cy - dp(8)), size=(dp(16), dp(16)))
            Color(*self.color_main)
            Line(circle=(cx, cy, dp(8)), width=dp(1.5))

        if self.show_value:
            if hasattr(self, '_val_label'):
                self.remove_widget(self._val_label)
                self.remove_widget(self._unit_label)
                self.remove_widget(self._name_label)

            self._val_label = Label(
                text=str(int(self.value)),
                font_size=f"{int(r * 0.35)}sp",
                color=BMW_WHITE,
                bold=True,
                pos=(cx - r, cy - r * 0.25),
                size=(r * 2, r * 0.4)
            )
            self._unit_label = Label(
                text=self.unit_text,
                font_size=f"{int(r * 0.16)}sp",
                color=BMW_GRAY,
                pos=(cx - r, cy - r * 0.55),
                size=(r * 2, r * 0.3)
            )
            self._name_label = Label(
                text=self.label_text,
                font_size=f"{int(r * 0.18)}sp",
                color=BMW_BLUE_GLOW,
                bold=True,
                pos=(cx - r, cy - r * 1.1),
                size=(r * 2, r * 0.3)
            )
            self.add_widget(self._val_label)
            self.add_widget(self._unit_label)
            self.add_widget(self._name_label)


# ============================================================
# شاشة إدخال PIN
# ============================================================
class PinScreen(Screen):
    entered_pin = StringProperty("")
    correct_pin = StringProperty(DEFAULT_PIN)
    attempt_count = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        layout = FloatLayout()

        # الخلفية الشبكية
        bg = Widget(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        with bg.canvas:
            Color(0.06, 0.06, 0.1, 1)
            Rectangle(pos=(0, 0), size=Window.size)
        layout.add_widget(bg)

        # لوحة المركز
        panel = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            size=(dp(300), dp(480)),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            spacing=dp(12),
            padding=dp(24)
        )

        # شعار BMW
        logo_lbl = Label(
            text="⟨ BMW ⟩",
            font_size="28sp",
            color=BMW_GOLD,
            bold=True,
            size_hint=(1, None),
            height=dp(45)
        )
        panel.add_widget(logo_lbl)

        sub_lbl = Label(
            text="E30 · 1990 · DASHBOARD",
            font_size="11sp",
            color=BMW_GRAY,
            size_hint=(1, None),
            height=dp(22)
        )
        panel.add_widget(sub_lbl)

        sep = Widget(size_hint=(1, None), height=dp(8))
        panel.add_widget(sep)

        lock_lbl = Label(
            text="🔒  وضع القيادة المحمي",
            font_size="13sp",
            color=BMW_BLUE,
            bold=True,
            size_hint=(1, None),
            height=dp(30)
        )
        panel.add_widget(lock_lbl)

        # عرض الأرقام المدخلة
        self.pin_display = Label(
            text="● ● ● ●",
            font_size="24sp",
            color=BMW_WHITE,
            size_hint=(1, None),
            height=dp(48)
        )
        panel.add_widget(self.pin_display)

        self.status_label = Label(
            text="أدخل الرمز للمتابعة",
            font_size="12sp",
            color=BMW_GRAY,
            size_hint=(1, None),
            height=dp(25)
        )
        panel.add_widget(self.status_label)

        # لوحة الأرقام
        keypad = GridLayout(
            cols=3, spacing=dp(10),
            size_hint=(1, None), height=dp(240)
        )
        keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "⌫", "0", "✓"]
        for k in keys:
            btn = Button(
                text=k,
                font_size="20sp",
                bold=True,
                background_color=(0, 0, 0, 0),
                background_normal="",
                color=BMW_WHITE if k not in ["⌫", "✓"] else (
                    BMW_RED if k == "⌫" else BMW_GREEN
                ),
                size_hint=(1, 1)
            )
            with btn.canvas.before:
                Color(0.12, 0.12, 0.18, 1)
                RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(8)])
                Color(0.3, 0.3, 0.45, 0.5)
                Line(
                    rounded_rectangle=[btn.x, btn.y, btn.width, btn.height, dp(8)],
                    width=1
                )

            def _update_rect(btn=btn, *args):
                for instr in btn.canvas.before.children:
                    if isinstance(instr, RoundedRectangle):
                        instr.pos = btn.pos
                        instr.size = btn.size
                    elif isinstance(instr, Line):
                        instr.rounded_rectangle = [
                            btn.x, btn.y, btn.width, btn.height, dp(8)
                        ]
            btn.bind(pos=_update_rect, size=_update_rect)

            key_val = k
            btn.bind(on_press=lambda b, v=key_val: self._key_pressed(v))
            keypad.add_widget(btn)

        panel.add_widget(keypad)

        hint_lbl = Label(
            text="الرمز الافتراضي: 1990",
            font_size="10sp",
            color=get_color_from_hex("#555566"),
            size_hint=(1, None),
            height=dp(20)
        )
        panel.add_widget(hint_lbl)

        # إطار اللوحة
        with panel.canvas.before:
            Color(0.1, 0.1, 0.16, 1)
            RoundedRectangle(pos=panel.pos, size=panel.size, radius=[dp(16)])
            Color(0.12, 0.35, 0.8, 0.6)
            Line(
                rounded_rectangle=[panel.x, panel.y, panel.width, panel.height, dp(16)],
                width=1.5
            )

        def update_panel(*args):
            for instr in panel.canvas.before.children:
                if isinstance(instr, RoundedRectangle):
                    instr.pos = panel.pos
                    instr.size = panel.size
                elif isinstance(instr, Line):
                    instr.rounded_rectangle = [
                        panel.x, panel.y, panel.width, panel.height, dp(16)
                    ]
        panel.bind(pos=update_panel, size=update_panel)

        layout.add_widget(panel)
        self.add_widget(layout)

    def _key_pressed(self, key):
        if key == "⌫":
            self.entered_pin = self.entered_pin[:-1]
        elif key == "✓":
            self._check_pin()
        elif len(self.entered_pin) < 6:
            self.entered_pin += key

        # تحديث عرض النقاط
        dots = "  ".join(["●"] * len(self.entered_pin) + ["○"] * (4 - min(len(self.entered_pin), 4)))
        self.pin_display.text = dots

    def _check_pin(self):
        if self.entered_pin == self.correct_pin:
            self.status_label.text = "✓ رمز صحيح - مرحباً!"
            self.status_label.color = BMW_GREEN
            Clock.schedule_once(self._go_to_dashboard, 0.6)
        else:
            self.attempt_count += 1
            self.status_label.text = f"✗ رمز خاطئ ({self.attempt_count} محاولة)"
            self.status_label.color = BMW_RED
            self.entered_pin = ""
            self.pin_display.text = "○  ○  ○  ○"
            anim = Animation(x=self.pin_display.x + dp(10), duration=0.05) + \
                   Animation(x=self.pin_display.x - dp(10), duration=0.05) + \
                   Animation(x=self.pin_display.x, duration=0.05)
            anim.start(self.pin_display)

    def _go_to_dashboard(self, dt):
        self.manager.current = "dashboard"
        self.entered_pin = ""
        self.pin_display.text = "○  ○  ○  ○"


# ============================================================
# الداشبورد الرئيسي
# ============================================================
class MainDashboard(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.wifi_on = False
        self.bt_on = False
        self.speed_value = 0
        self.rpm_value = 0
        self._speed_anim = None
        Clock.schedule_once(self._build_ui, 0)

    def _build_ui(self, dt):
        root = FloatLayout()

        # ========== الجزء العلوي: الوقت والحالة ==========
        top_bar = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(42),
            pos_hint={"x": 0, "top": 1},
            padding=[dp(12), dp(6)],
            spacing=dp(10)
        )
        with top_bar.canvas.before:
            Color(0.06, 0.06, 0.1, 1)
            Rectangle(pos=top_bar.pos, size=top_bar.size)
        top_bar.bind(
            pos=lambda w, v: setattr(
                top_bar.canvas.before.children[-1], 'pos', v
            ),
            size=lambda w, v: setattr(
                top_bar.canvas.before.children[-1], 'size', v
            )
        )

        bmw_lbl = Label(
            text="⟨ BMW E30 1990 ⟩",
            font_size="14sp",
            bold=True,
            color=BMW_GOLD,
            size_hint=(None, 1),
            width=dp(160)
        )
        top_bar.add_widget(bmw_lbl)

        top_bar.add_widget(Widget())

        self.time_label = Label(
            text="00:00",
            font_size="16sp",
            bold=True,
            color=BMW_WHITE,
            size_hint=(None, 1),
            width=dp(80)
        )
        top_bar.add_widget(self.time_label)

        self.date_label = Label(
            text="",
            font_size="10sp",
            color=BMW_GRAY,
            size_hint=(None, 1),
            width=dp(120)
        )
        top_bar.add_widget(self.date_label)

        lock_btn = Button(
            text="🔒 قفل",
            font_size="12sp",
            bold=True,
            background_color=(0, 0, 0, 0),
            background_normal="",
            color=BMW_RED,
            size_hint=(None, 1),
            width=dp(80)
        )
        lock_btn.bind(on_press=self._lock_screen)
        top_bar.add_widget(lock_btn)

        root.add_widget(top_bar)

        # ========== العدادات الرئيسية ==========
        gauges_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(200),
            pos_hint={"x": 0, "top": 0.88},
            padding=dp(8),
            spacing=dp(8)
        )

        self.speed_gauge = CircularGauge(
            max_value=240,
            label_text="السرعة",
            unit_text="km/h",
            color_main=[0.12, 0.56, 1, 1],
            size_hint=(1, 1)
        )
        gauges_row.add_widget(self.speed_gauge)

        self.rpm_gauge = CircularGauge(
            max_value=8000,
            label_text="RPM",
            unit_text="×100",
            color_main=[1, 0.4, 0.1, 1],
            size_hint=(1, 1)
        )
        gauges_row.add_widget(self.rpm_gauge)

        self.temp_gauge = CircularGauge(
            max_value=120,
            value=88,
            label_text="الحرارة",
            unit_text="°C",
            color_main=[0, 1, 0.53, 1],
            size_hint=(1, 1)
        )
        gauges_row.add_widget(self.temp_gauge)

        self.fuel_gauge = CircularGauge(
            max_value=100,
            value=65,
            label_text="الوقود",
            unit_text="%",
            color_main=[0.84, 0.69, 0.22, 1],
            size_hint=(1, 1)
        )
        gauges_row.add_widget(self.fuel_gauge)

        root.add_widget(gauges_row)

        # ========== صف التحكم: WiFi / BT / صوت ==========
        ctrl_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(55),
            pos_hint={"x": 0, "top": 0.58},
            padding=[dp(8), dp(4)],
            spacing=dp(8)
        )

        self.wifi_btn = Button(
            text="📶 WiFi OFF",
            font_size="12sp",
            bold=True,
            background_color=(0, 0, 0, 0),
            background_normal="",
            color=BMW_GRAY,
            size_hint=(1, 1)
        )
        self._style_toggle_btn(self.wifi_btn, False)
        self.wifi_btn.bind(on_press=self._toggle_wifi)
        ctrl_row.add_widget(self.wifi_btn)

        self.bt_btn = Button(
            text="🔵 BT OFF",
            font_size="12sp",
            bold=True,
            background_color=(0, 0, 0, 0),
            background_normal="",
            color=BMW_GRAY,
            size_hint=(1, 1)
        )
        self._style_toggle_btn(self.bt_btn, False)
        self.bt_btn.bind(on_press=self._toggle_bt)
        ctrl_row.add_widget(self.bt_btn)

        vol_down = Button(
            text="🔈",
            font_size="18sp",
            background_color=(0, 0, 0, 0),
            background_normal="",
            color=BMW_WHITE,
            size_hint=(None, 1),
            width=dp(55)
        )
        vol_down.bind(on_press=lambda x: None)
        ctrl_row.add_widget(vol_down)

        self.vol_label = Label(
            text="🔊 50%",
            font_size="12sp",
            color=BMW_WHITE,
            size_hint=(None, 1),
            width=dp(60)
        )
        ctrl_row.add_widget(self.vol_label)

        vol_up = Button(
            text="🔊",
            font_size="18sp",
            background_color=(0, 0, 0, 0),
            background_normal="",
            color=BMW_WHITE,
            size_hint=(None, 1),
            width=dp(55)
        )
        vol_up.bind(on_press=lambda x: None)
        ctrl_row.add_widget(vol_up)

        root.add_widget(ctrl_row)

        # ========== شبكة التطبيقات ==========
        apps_grid = GridLayout(
            cols=4,
            size_hint=(1, None),
            height=dp(130),
            pos_hint={"x": 0, "top": 0.46},
            padding=dp(8),
            spacing=dp(8)
        )

        apps = [
            ("▶  يوتيوب", BMW_RED, self._open_youtube),
            ("🗺  خرائط", BMW_GREEN, self._open_maps),
            ("📍 تتبع", BMW_BLUE, self._open_tracking),
            ("📞  هاتف", BMW_BLUE_GLOW, self._open_phone),
            ("🎵  موسيقى", BMW_ORANGE, self._open_music),
            ("⚙  إعدادات", BMW_GRAY, self._open_settings),
            ("📷  كاميرا", BMW_GOLD, self._open_camera),
            ("🌐  متصفح", BMW_WHITE, self._open_browser),
        ]

        for name, color, callback in apps:
            btn = Button(
                text=name,
                font_size="11sp",
                bold=True,
                background_color=(0, 0, 0, 0),
                background_normal="",
                color=color,
                size_hint=(1, 1)
            )
            with btn.canvas.before:
                Color(0.1, 0.1, 0.15, 1)
                RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(8)])
                Color(*color[:3], 0.4)
                Line(
                    rounded_rectangle=[btn.x, btn.y, btn.width, btn.height, dp(8)],
                    width=1.2
                )

            def _fix(b=btn, c=color):
                for instr in b.canvas.before.children:
                    if isinstance(instr, RoundedRectangle):
                        instr.pos = b.pos
                        instr.size = b.size
                    elif isinstance(instr, Line):
                        instr.rounded_rectangle = [
                            b.x, b.y, b.width, b.height, dp(8)
                        ]

            btn.bind(pos=lambda w, v, b=btn, c=color: _fix(b, c),
                     size=lambda w, v, b=btn, c=color: _fix(b, c))
            btn.bind(on_press=lambda x, cb=callback: cb())
            apps_grid.add_widget(btn)

        root.add_widget(apps_grid)

        # ========== شريط الحالة السفلي ==========
        status_bar = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(36),
            pos_hint={"x": 0, "y": 0},
            padding=[dp(12), dp(4)],
            spacing=dp(16)
        )
        with status_bar.canvas.before:
            Color(0.06, 0.06, 0.1, 1)
            Rectangle(pos=(0, 0), size=(10000, dp(36)))

        self.gps_label = Label(
            text="📍 GPS: نشط",
            font_size="10sp",
            color=BMW_GREEN,
            size_hint=(None, 1),
            width=dp(100)
        )
        status_bar.add_widget(self.gps_label)

        self.speed_text = Label(
            text="0 km/h",
            font_size="12sp",
            bold=True,
            color=BMW_BLUE_GLOW,
            size_hint=(None, 1),
            width=dp(80)
        )
        status_bar.add_widget(self.speed_text)

        status_bar.add_widget(Widget())

        self.temp_text = Label(
            text="🌡 88°C",
            font_size="10sp",
            color=BMW_GREEN,
            size_hint=(None, 1),
            width=dp(70)
        )
        status_bar.add_widget(self.temp_text)

        bmw_status = Label(
            text="BMW E30 · وضع القيادة",
            font_size="10sp",
            color=BMW_GOLD,
            size_hint=(None, 1),
            width=dp(160)
        )
        status_bar.add_widget(bmw_status)

        root.add_widget(status_bar)

        self.add_widget(root)

        # ========== تحديثات دورية ==========
        Clock.schedule_interval(self._update_clock, 1)
        Clock.schedule_interval(self._simulate_speed, 0.1)

    def _style_toggle_btn(self, btn, is_on):
        btn.canvas.before.clear()
        with btn.canvas.before:
            if is_on:
                Color(0.1, 0.4, 0.1, 1)
            else:
                Color(0.1, 0.1, 0.15, 1)
            RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(8)])
            Color(*(BMW_GREEN if is_on else BMW_GRAY)[:3], 0.6)
            Line(
                rounded_rectangle=[btn.x, btn.y, btn.width, btn.height, dp(8)],
                width=1.2
            )

        def _fix(*args):
            for instr in btn.canvas.before.children:
                if isinstance(instr, RoundedRectangle):
                    instr.pos = btn.pos
                    instr.size = btn.size
                elif isinstance(instr, Line):
                    instr.rounded_rectangle = [
                        btn.x, btn.y, btn.width, btn.height, dp(8)
                    ]

        btn.bind(pos=_fix, size=_fix)

    def _update_clock(self, dt):
        now = datetime.now()
        self.time_label.text = now.strftime("%H:%M")
        self.date_label.text = now.strftime("%A - %d/%m/%Y")

    def _simulate_speed(self, dt):
        import random
        # محاكاة تغير السرعة بشكل واقعي
        delta = random.randint(-3, 4)
        new_speed = max(0, min(180, self.speed_value + delta))
        self.speed_value = new_speed
        self.speed_gauge.value = new_speed
        self.rpm_value = max(800, min(7500, int(new_speed * 38 + random.randint(-200, 200))))
        self.rpm_gauge.value = self.rpm_value
        self.speed_text.text = f"{int(new_speed)} km/h"

        # تغيير لون حسب السرعة
        if new_speed < 60:
            self.speed_gauge.color_main = [0.12, 0.56, 1, 1]
        elif new_speed < 120:
            self.speed_gauge.color_main = [1, 0.6, 0, 1]
        else:
            self.speed_gauge.color_main = [1, 0.2, 0.1, 1]

    def _toggle_wifi(self, *args):
        self.wifi_on = not self.wifi_on
        if self.wifi_on:
            self.wifi_btn.text = "📶 WiFi ON"
            self.wifi_btn.color = BMW_GREEN
        else:
            self.wifi_btn.text = "📶 WiFi OFF"
            self.wifi_btn.color = BMW_GRAY
        self._style_toggle_btn(self.wifi_btn, self.wifi_on)
        self._show_toast("WiFi " + ("مفعّل ✓" if self.wifi_on else "معطّل"))

    def _toggle_bt(self, *args):
        self.bt_on = not self.bt_on
        if self.bt_on:
            self.bt_btn.text = "🔵 BT ON"
            self.bt_btn.color = BMW_BLUE
        else:
            self.bt_btn.text = "🔵 BT OFF"
            self.bt_btn.color = BMW_GRAY
        self._style_toggle_btn(self.bt_btn, self.bt_on)
        self._show_toast("البلوتوث " + ("مفعّل ✓" if self.bt_on else "معطّل"))

    def _open_youtube(self):
        try:
            from android.intent import Intent
            i = Intent(Intent.ACTION_VIEW)
            i.setData("https://www.youtube.com")
            App.get_running_app().startActivity(i)
        except Exception:
            webbrowser.open("https://www.youtube.com")
        self._show_toast("فتح يوتيوب...")

    def _open_maps(self):
        try:
            from android.intent import Intent
            i = Intent(Intent.ACTION_VIEW)
            i.setData("geo:0,0?q=")
            App.get_running_app().startActivity(i)
        except Exception:
            webbrowser.open("https://maps.google.com")
        self._show_toast("فتح خرائط قوقل...")

    def _open_tracking(self):
        self.manager.current = "tracking"
        self._show_toast("وضع التتبع المباشر")

    def _open_phone(self):
        try:
            from android.intent import Intent
            i = Intent(Intent.ACTION_DIAL)
            App.get_running_app().startActivity(i)
        except Exception:
            self._show_toast("لا يمكن فتح الهاتف في المحاكي")

    def _open_music(self):
        try:
            from android.intent import Intent
            i = Intent(Intent.ACTION_VIEW)
            i.setType("audio/*")
            App.get_running_app().startActivity(i)
        except Exception:
            self._show_toast("فتح مشغل الموسيقى...")

    def _open_settings(self):
        self.manager.current = "settings"

    def _open_camera(self):
        try:
            from android.intent import Intent
            i = Intent("android.media.action.IMAGE_CAPTURE")
            App.get_running_app().startActivity(i)
        except Exception:
            self._show_toast("فتح الكاميرا...")

    def _open_browser(self):
        webbrowser.open("https://google.com")
        self._show_toast("فتح المتصفح...")

    def _lock_screen(self, *args):
        popup = Popup(
            title="تأكيد القفل",
            title_color=BMW_WHITE,
            separator_color=BMW_BLUE,
            size_hint=(None, None),
            size=(dp(280), dp(180)),
            background_color=BMW_PANEL[:3] + [0.95]
        )
        content = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(16))
        lbl = Label(
            text="هل تريد قفل الشاشة؟\nستحتاج الرمز للعودة.",
            font_size="13sp",
            color=BMW_WHITE,
            halign="center"
        )
        content.add_widget(lbl)
        btns = BoxLayout(spacing=dp(10), size_hint=(1, None), height=dp(44))
        yes = Button(
            text="نعم، اقفل",
            background_color=(0.7, 0.1, 0.1, 1),
            bold=True
        )
        no = Button(
            text="إلغاء",
            background_color=(0.1, 0.1, 0.2, 1),
            bold=True
        )
        yes.bind(on_press=lambda x: self._do_lock(popup))
        no.bind(on_press=popup.dismiss)
        btns.add_widget(yes)
        btns.add_widget(no)
        content.add_widget(btns)
        popup.content = content
        popup.open()

    def _do_lock(self, popup):
        popup.dismiss()
        self.manager.current = "pin"

    def _show_toast(self, msg):
        toast = Label(
            text=msg,
            font_size="12sp",
            color=BMW_WHITE,
            size_hint=(None, None),
            size=(dp(200), dp(36)),
            pos_hint={"center_x": 0.5, "y": 0.08}
        )
        with toast.canvas.before:
            Color(0.1, 0.3, 0.6, 0.9)
            RoundedRectangle(pos=toast.pos, size=toast.size, radius=[dp(18)])

        def fix(*a):
            for instr in toast.canvas.before.children:
                if isinstance(instr, RoundedRectangle):
                    instr.pos = toast.pos
                    instr.size = toast.size

        toast.bind(pos=fix, size=fix)
        self.add_widget(toast)

        def remove(*a):
            if toast.parent:
                self.remove_widget(toast)

        anim = Animation(opacity=1, duration=0.2) + \
               Animation(opacity=1, duration=1.5) + \
               Animation(opacity=0, duration=0.4)
        anim.bind(on_complete=remove)
        toast.opacity = 0
        anim.start(toast)


# ============================================================
# شاشة التتبع المباشر
# ============================================================
class TrackingScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lat = 24.7136
        self.lon = 46.6753
        self.speed_log = []
        self._build_ui()
        Clock.schedule_interval(self._update_tracking, 2)

    def _build_ui(self):
        layout = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))

        # Header
        header = BoxLayout(
            size_hint=(1, None), height=dp(40),
            spacing=dp(10)
        )
        back_btn = Button(
            text="← رجوع",
            size_hint=(None, 1), width=dp(90),
            background_color=(0.1, 0.3, 0.6, 1),
            bold=True
        )
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        header.add_widget(back_btn)

        title = Label(
            text="📍 التتبع المباشر - لحظة بلحظة",
            font_size="14sp", bold=True, color=BMW_GOLD
        )
        header.add_widget(title)
        layout.add_widget(header)

        # خريطة مبسطة
        map_panel = BoxLayout(
            orientation="vertical",
            size_hint=(1, 0.5),
            padding=dp(4)
        )
        with map_panel.canvas.before:
            Color(0.05, 0.1, 0.05, 1)
            RoundedRectangle(pos=map_panel.pos, size=map_panel.size, radius=[dp(10)])
            Color(0.1, 0.6, 0.1, 0.3)
            Line(
                rounded_rectangle=[*map_panel.pos, *map_panel.size, dp(10)],
                width=1.5
            )
        map_panel.bind(
            pos=lambda w, v: self._fix_panel(map_panel),
            size=lambda w, v: self._fix_panel(map_panel)
        )

        # Google Maps في WebView
        gmap_btn = Button(
            text="🗺 فتح خرائط قوقل مع الموقع الحالي",
            font_size="13sp",
            bold=True,
            background_color=(0.1, 0.5, 0.2, 1),
            color=BMW_WHITE,
            size_hint=(1, None),
            height=dp(52)
        )
        gmap_btn.bind(on_press=lambda x: self._open_gmap())
        map_panel.add_widget(gmap_btn)

        self.coords_label = Label(
            text=f"📌 إحداثيات: {self.lat:.4f}°N, {self.lon:.4f}°E",
            font_size="11sp",
            color=BMW_GREEN
        )
        map_panel.add_widget(self.coords_label)

        self.accuracy_label = Label(
            text="دقة GPS: ±5 متر",
            font_size="10sp",
            color=BMW_GRAY
        )
        map_panel.add_widget(self.accuracy_label)

        layout.add_widget(map_panel)

        # إحصائيات
        stats_grid = GridLayout(
            cols=2, size_hint=(1, None), height=dp(120),
            spacing=dp(8)
        )
        stats = [
            ("السرعة الحالية", "0 km/h", "speed_stat"),
            ("أقصى سرعة", "0 km/h", "max_speed_stat"),
            ("المسافة", "0.0 كم", "distance_stat"),
            ("الوقت", "00:00:00", "time_stat"),
        ]
        for title, val, attr in stats:
            box = BoxLayout(orientation="vertical")
            with box.canvas.before:
                Color(0.1, 0.1, 0.16, 1)
                RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(8)])
            box.bind(
                pos=lambda w, v, b=box: self._fix_small(b),
                size=lambda w, v, b=box: self._fix_small(b)
            )
            lbl_t = Label(text=title, font_size="10sp", color=BMW_GRAY)
            lbl_v = Label(text=val, font_size="14sp", bold=True, color=BMW_BLUE_GLOW)
            setattr(self, attr, lbl_v)
            box.add_widget(lbl_t)
            box.add_widget(lbl_v)
            stats_grid.add_widget(box)

        layout.add_widget(stats_grid)

        # سجل المسار
        log_label = Label(
            text="سجل المسار:",
            font_size="11sp",
            color=BMW_GOLD,
            size_hint=(1, None),
            height=dp(24),
            halign="right"
        )
        layout.add_widget(log_label)

        scroll = ScrollView(size_hint=(1, 1))
        self.log_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(4)
        )
        self.log_container.bind(
            minimum_height=self.log_container.setter('height')
        )
        scroll.add_widget(self.log_container)
        layout.add_widget(scroll)

        self.add_widget(layout)
        self.start_time = time.time()
        self.total_distance = 0
        self.max_speed = 0

    def _fix_panel(self, panel):
        for instr in panel.canvas.before.children:
            if isinstance(instr, RoundedRectangle):
                instr.pos = panel.pos
                instr.size = panel.size
            elif isinstance(instr, Line):
                instr.rounded_rectangle = [*panel.pos, *panel.size, dp(10)]

    def _fix_small(self, box):
        for instr in box.canvas.before.children:
            if isinstance(instr, RoundedRectangle):
                instr.pos = box.pos
                instr.size = box.size

    def _open_gmap(self):
        url = f"https://maps.google.com/maps?q={self.lat},{self.lon}&z=15"
        try:
            webbrowser.open(url)
        except Exception:
            pass

    def _update_tracking(self, dt):
        import random
        import math
        # محاكاة تحرك GPS
        self.lat += random.uniform(-0.0001, 0.0001)
        self.lon += random.uniform(-0.0001, 0.0001)

        speed = random.randint(40, 120)
        if speed > self.max_speed:
            self.max_speed = speed
        self.total_distance += speed * 2 / 3600  # كم

        elapsed = int(time.time() - self.start_time)
        h = elapsed // 3600
        m = (elapsed % 3600) // 60
        s = elapsed % 60

        self.coords_label.text = f"📌 {self.lat:.5f}°N, {self.lon:.5f}°E"
        self.speed_stat.text = f"{speed} km/h"
        self.max_speed_stat.text = f"{self.max_speed} km/h"
        self.distance_stat.text = f"{self.total_distance:.2f} كم"
        self.time_stat.text = f"{h:02d}:{m:02d}:{s:02d}"

        # إضافة سجل
        log_entry = Label(
            text=f"⏱ {h:02d}:{m:02d}:{s:02d}  📍 {self.lat:.4f}, {self.lon:.4f}  🚗 {speed} km/h",
            font_size="9sp",
            color=BMW_GRAY,
            size_hint=(1, None),
            height=dp(20),
            halign="right",
            text_size=(Window.width - dp(24), None)
        )
        self.log_container.add_widget(log_entry)
        if len(self.log_container.children) > 20:
            self.log_container.remove_widget(self.log_container.children[-1])


# ============================================================
# شاشة الإعدادات
# ============================================================
class SettingsScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        layout = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(10)
        )

        header = BoxLayout(size_hint=(1, None), height=dp(44), spacing=dp(10))
        back_btn = Button(
            text="← رجوع",
            size_hint=(None, 1), width=dp(90),
            background_color=(0.1, 0.3, 0.6, 1),
            bold=True
        )
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'dashboard'))
        header.add_widget(back_btn)
        header.add_widget(Label(
            text="⚙  الإعدادات",
            font_size="15sp", bold=True, color=BMW_GOLD
        ))
        layout.add_widget(header)

        # تغيير PIN
        pin_panel = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(150),
            spacing=dp(8),
            padding=dp(12)
        )
        with pin_panel.canvas.before:
            Color(0.1, 0.1, 0.16, 1)
            RoundedRectangle(pos=pin_panel.pos, size=pin_panel.size, radius=[dp(10)])
            Color(0.3, 0.3, 0.6, 0.5)
            Line(
                rounded_rectangle=[*pin_panel.pos, *pin_panel.size, dp(10)],
                width=1
            )

        pin_panel.add_widget(Label(
            text="🔑 تغيير الرمز السري",
            font_size="13sp", bold=True, color=BMW_GOLD,
            size_hint=(1, None), height=dp(28)
        ))

        self.new_pin_input = TextInput(
            hint_text="الرمز الجديد (أرقام فقط)",
            font_size="14sp",
            multiline=False,
            password=True,
            input_filter="int",
            background_color=(0.08, 0.08, 0.14, 1),
            foreground_color=BMW_WHITE,
            cursor_color=BMW_BLUE,
            size_hint=(1, None),
            height=dp(40)
        )
        pin_panel.add_widget(self.new_pin_input)

        save_pin = Button(
            text="💾 حفظ الرمز الجديد",
            background_color=(0.1, 0.4, 0.1, 1),
            bold=True,
            size_hint=(1, None),
            height=dp(40)
        )
        save_pin.bind(on_press=self._save_pin)
        pin_panel.add_widget(save_pin)
        layout.add_widget(pin_panel)

        # معلومات الجهاز
        info_panel = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(100),
            spacing=dp(6),
            padding=dp(12)
        )
        with info_panel.canvas.before:
            Color(0.1, 0.1, 0.16, 1)
            RoundedRectangle(pos=info_panel.pos, size=info_panel.size, radius=[dp(10)])

        for info in [
            "📱 الجهاز: Samsung Galaxy Core 4",
            "🚗 نموذج: BMW E30 · 1990",
            "💻 الإصدار: Dashboard v2.0",
            "👨‍💻 Python · Kivy Framework"
        ]:
            info_panel.add_widget(Label(
                text=info, font_size="11sp",
                color=BMW_GRAY,
                size_hint=(1, None), height=dp(20),
                halign="right",
                text_size=(Window.width - dp(40), None)
            ))
        layout.add_widget(info_panel)

        layout.add_widget(Widget())
        self.add_widget(layout)

    def _save_pin(self, *args):
        new_pin = self.new_pin_input.text.strip()
        if len(new_pin) >= 4:
            # تحديث PIN في شاشة البداية
            app = App.get_running_app()
            pin_screen = app.sm.get_screen("pin")
            pin_screen.correct_pin = new_pin
            self.new_pin_input.text = ""
            self._show_ok(f"✓ تم تغيير الرمز إلى: {'*' * len(new_pin)}")
        else:
            self._show_ok("✗ الرمز يجب أن يكون 4 أرقام على الأقل")

    def _show_ok(self, msg):
        popup = Popup(
            title="إشعار",
            title_color=BMW_WHITE,
            content=Label(text=msg, color=BMW_GREEN if msg.startswith("✓") else BMW_RED),
            size_hint=(None, None),
            size=(dp(260), dp(120)),
            background_color=BMW_PANEL[:3] + [0.95]
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)


# ============================================================
# التطبيق الرئيسي
# ============================================================
class BMWE30App(App):
    title = "BMW E30 · Dashboard"

    def build(self):
        Window.clearcolor = BMW_BLACK

        # منع الرجوع في الأندرويد
        Window.bind(on_keyboard=self._handle_keyboard)

        self.sm = ScreenManager(transition=FadeTransition(duration=0.3))

        pin = PinScreen(name="pin")
        dashboard = MainDashboard(name="dashboard")
        tracking = TrackingScreen(name="tracking")
        settings = SettingsScreen(name="settings")

        self.sm.add_widget(pin)
        self.sm.add_widget(dashboard)
        self.sm.add_widget(tracking)
        self.sm.add_widget(settings)

        self.sm.current = "pin"
        return self.sm

    def _handle_keyboard(self, window, key, *args):
        # منع زر الرجوع (keycode 27 = ESC / زر الرجوع في أندرويد)
        if key == 27:
            if self.sm.current == "pin":
                return True  # منع الخروج تماماً
            elif self.sm.current in ["tracking", "settings"]:
                self.sm.current = "dashboard"
                return True
            elif self.sm.current == "dashboard":
                # عرض شاشة القفل بدلاً من الخروج
                self.sm.current = "pin"
                return True
        return False

    def on_pause(self):
        return True  # السماح بالتوقف المؤقت

    def on_resume(self):
        pass  # استئناف من التوقف


if __name__ == "__main__":
    BMWE30App().run()
