import pickle
from ctypes import windll
import os

from functions import get_screen, get_windows_hwnd
from l2bot import MainLineageWindow, ValuesMonitor, LineageWindow, SerialSender

import tkinter as tk
from tkinter.font import Font
from tkinter import *
from tkinter import ttk
from PIL import ImageTk, Image

import time

user32 = windll.user32
user32.SetProcessDPIAware()


class L2BotApp:
    cycle_update = False

    def __init__(self, master):
        self.master = master
        self.frame = tk.Frame(self.master)

        self.show_main_window()

    def show_main_window(self):
        self.frame.title = 'Bot'
        self.master.geometry('200x340+2200+600')
        self.master.resizable(False, False)

        window_name_btn = Button(self.frame, text='Подключить окна', height=1)
        window_name_btn.place(relx=0.05, y=10, relwidth=0.9)
        window_name_btn.bind('<ButtonRelease-1>', lambda event: self.setup_l2_window())

        auto_calibration_btn = Button(self.frame, text='Настройки окон', height=1)
        auto_calibration_btn.place(relx=0.05, y=55, relwidth=0.9)
        auto_calibration_btn.bind('<ButtonRelease-1>', lambda event: self.window_setup_l2_supports())

        auto_calibration_btn = Button(self.frame, text='Автокалибровка', height=1)
        auto_calibration_btn.place(relx=0.05, y=85, relwidth=0.9)
        auto_calibration_btn.bind('<ButtonRelease-1>', lambda event: self.calibration_window_init('auto'))

        set_hp_button = Button(self.frame, text='Указать ХП', height=1)
        set_hp_button.place(relx=0.05, y=115, relwidth=0.9)
        set_hp_button.bind('<ButtonRelease-1>', lambda event: self.calibration_window_init('manual_hp'))

        set_mp_button = Button(self.frame, text='Указать МП', height=1)
        set_mp_button.place(relx=0.05, y=145, relwidth=0.9)
        set_mp_button.bind('<ButtonRelease-1>', lambda event: self.calibration_window_init('manual_mp'))

        set_target_hp_button = Button(self.frame, text='Указать ХП цели', height=1)
        set_target_hp_button.place(relx=0.05, y=175, relwidth=0.9)
        set_target_hp_button.bind('<ButtonRelease-1>', lambda event: self.calibration_window_init('manual_target_hp'))

        screen_btn = Button(self.frame, text='Сделать скриншот', height=1)
        screen_btn.place(relx=0.05, y=205, relwidth=0.9)
        screen_btn.bind('<ButtonRelease-1>', lambda ev: self.l2_window.save_screen())

        self.updater_button = Button(self.frame, text='Включить', height=1)
        self.updater_button.place(relx=0.05, y=235, relwidth=0.9)
        self.updater_button.bind('<ButtonRelease-1>', self.change_cycle_update)

        self.hp_label = Label(text='HP: None')
        self.hp_label.place(relx=0.05, y=270, relwidth=0.9)

        self.mp_label = Label(text='MP: None')
        self.mp_label.place(relx=0.05, y=290, relwidth=0.9)

        self.target_hp_label = Label(text='T_HP: None')
        self.target_hp_label.place(relx=0.05, y=310, relwidth=0.9)

        self.frame.place(x=0, y=0, relwidth=1, relheight=1)

    def change_cycle_update(self, event):
        self.cycle_update = not self.cycle_update
        if self.cycle_update:
            self.updater_button['text'] = 'Выключить'
            self.monitor = ValuesMonitor(self)
            self.monitor.start()
            self.serial_sender = SerialSender('COM3')
            self.serial_sender.start()
        else:
            self.monitor.stop()
            self.serial_sender.stop()
            self.updater_button['text'] = 'Включить'
            self.hp_label['text'] = 'HP: None'
            self.mp_label['text'] = 'MP: None'
            self.target_hp_label['text'] = 'T_HP: None'

    def update_values(self):
        if self.cycle_update:
            self.hp_label['text'] = 'HP: %d' % self.l2_window.hp
            self.mp_label['text'] = 'MP: %d' % self.l2_window.mp
            self.target_hp_label['text'] = 'T_HP: %d' % self.l2_window.target_hp
            self.master.after(500, self.update_values)

    def calibration_window_init(self, method):
        self.calibration_window = Toplevel(self.master)
        self.app = CalibrationWindow(self, method)

    def setup_l2_window(self):
        windows_settings = WindowInfo()
        self.l2_window = MainLineageWindow(windows_settings, self.serial_sender)

    def window_setup_l2_supports(self):
        self.supports_window = Toplevel(self.master)
        self.app = SetupWindowsSettings(self)


class SetupWindowsSettings:
    def __init__(self, root):
        self.root = root
        self.master = root.supports_window
        self.master.geometry(f'600x340+{root.master.winfo_x()}+{root.master.winfo_y()}')
        self.master.resizable(False, False)

        self.window_info = WindowInfo()

        self.ui_init()

    def ui_init(self):
        tab_parent = ttk.Notebook(self.master)

        self.listboxes = []
        self.names = []
        self.actives = []

        font = Font(family="Lucida Console", size=10)

        for i in range(9):
            tab = ttk.Frame(tab_parent)

            tab_parent.add(tab, text=f'Окно {i + 1}')
            frame = ttk.Frame(tab)
            ttk.Label(frame, text='Название окна').pack(side=LEFT)
            sv = StringVar()
            sv.set(self.window_info[i]['name'])
            self.names.append(sv)
            ttk.Entry(frame, textvariable=sv).pack(side=LEFT, padx=3)
            cvar = BooleanVar()
            cvar.set(self.window_info[i]['active'])
            self.actives.append(cvar)
            ttk.Checkbutton(frame, text='Активное', variable=cvar, onvalue=1, offvalue=0).pack(side=LEFT)
            frame.pack(anchor=NW, fill=X, pady=3)
            ttk.Button(frame, text='Сохранить', command=lambda a=i: self.save(a)).pack(side=LEFT, padx=3)
            ttk.Button(frame, text='Добавить триггер', command=lambda a=i: self.add_trigger(a)).pack(side=LEFT, padx=3)
            ttk.Button(frame, text='Удалить триггер', command=lambda a=i: self.delete_trigger(a)).pack(side=LEFT,
                                                                                                       padx=3)
            frame = ttk.Frame(tab)
            ttk.Label(frame, text='Название', width=40).grid(row=0, column=0)
            ttk.Label(frame, text='Процент', width=12).grid(row=0, column=1)
            ttk.Label(frame, text='Время использования', width=24).grid(row=0, column=2)
            ttk.Label(frame, text='Откат', width=10).grid(row=0, column=3)
            ttk.Label(frame, text='Кнопка', width=8).grid(row=0, column=5)
            frame.pack(fill=X)
            self.listboxes.append(Listbox(tab, font=font))
            self.listboxes[i].pack(expand=1, fill=BOTH)
            self.update_listbox(i)

        tab_parent.pack(expand=1, fill='both')

        btn_frame = ttk.Frame(self.master)
        btn_frame.pack(side=BOTTOM)

    def save(self, window_i):
        self.window_info[window_i]['active'] = self.actives[window_i].get()
        self.window_info[window_i]['name'] = self.names[window_i].get()
        self.window_info.save()

    def add_trigger(self, window_i):
        self.trigger_window = Toplevel(self.master)
        self.app = TriggerWindow(self, window_i)

    def delete_trigger(self, window_i):
        cs = self.listboxes[window_i].curselection()
        self.window_info.delete_by_i(window_i, cs[0])
        self.window_info.save()
        self.update_listbox(window_i)

    def update_listbox(self, window_i):
        lb = self.listboxes[window_i]
        lb.delete(0, END)

        for trigger_name in WindowInfo.ordering:
            for trigger in self.window_info[window_i]['triggers'][trigger_name]:
                percent = str(trigger.get('lt_percent', ''))
                if percent != '':
                    percent += '%'
                use_time = str(trigger.get('use_time', ''))
                if use_time != '':
                    use_time += 'c'
                cooldown = str(trigger.get('cooldown', ''))
                if cooldown != '':
                    cooldown += 'c'
                btn = str(trigger.get('btn', ''))
                if btn != '':
                    btn = 'F' + btn

                lb.insert(END, self.lb_formatter(TriggerWindow.convert(trigger_name, reverse=True), percent, use_time,
                                                 cooldown, btn))

    def lb_formatter(self, *args):

        col_lengths = [32, 13, 14, 8]
        s = ''
        for i, arg in enumerate(args):
            s += str(arg)
            nl = sum(col_lengths[:i + 1])
            s += ' ' * (nl - len(s))
        return s


class TriggerWindow:
    TRIGGERS = {'Мое ХП меньше ...%': 'hp_lt',
                'Мое МП меньше ...%': 'mp_lt',
                'ХП партийца меньше ...%': 'hp_party_lt',
                'МП партийца меньше ...%': 'mp_party_lt',
                'Бафф': 'buff',
                'Нет цели': 'no_target',
                'Моб убит': 'mob_dead'}

    def __init__(self, root, index):
        self.root = root
        self.index = index
        self.master = root.trigger_window
        self.master.geometry(f'280x210+{root.master.winfo_x() + 100}+{root.master.winfo_y() + 50}')
        self.master.resizable(False, False)

        ttk.Label(self.master, text='Выберите триггер').pack()
        self.trigger = StringVar()
        trigger_list = ttk.Combobox(self.master, width=30, textvariable=self.trigger)
        trigger_list['values'] = list(self.TRIGGERS.keys())
        trigger_list.pack()

        frame = ttk.Frame(self.master)
        self.percent = IntVar()
        ttk.Entry(frame, width=5, textvariable=self.percent).pack(side=LEFT)
        ttk.Label(frame, text='%').pack(side=LEFT)
        frame.pack(pady=10)
        frame = ttk.Frame(self.master)
        ttk.Label(frame, text='Кнопка первой панели').pack(side=LEFT)
        self.btn = IntVar()
        ttk.Entry(frame, width=5, textvariable=self.btn).pack(side=LEFT, padx=10)
        frame.pack(pady=5)
        frame = ttk.Frame(self.master)
        ttk.Label(frame, text='Время использования').pack(side=LEFT)
        self.use_time = IntVar()
        ttk.Entry(frame, width=5, textvariable=self.use_time).pack(side=LEFT, padx=10)
        frame.pack(pady=5)
        frame = ttk.Frame(self.master)
        ttk.Label(frame, text='Время отката').pack(side=LEFT)
        self.cooldown = IntVar()
        ttk.Entry(frame, width=5, textvariable=self.cooldown).pack(side=LEFT, padx=10)
        frame.pack(pady=5)
        ttk.Button(self.master, text='Добавить', command=self.add).pack(pady=5)

    def add(self):
        tr = self.convert(self.trigger.get())
        d = {}
        if tr == 'hp_lt' or tr == 'mp_lt' or tr == 'hp_party_lt' or tr == 'mp_party_lt':
            d = {'lt_percent': self.percent.get(), 'btn': self.btn.get(), 'use_time': self.use_time.get(),
                 'cooldown': self.cooldown.get()}
        elif tr == 'buff':
            d = {'btn': self.btn.get(), 'use_time': self.use_time.get(), 'cooldown': self.cooldown.get()}
        elif tr == 'mob_dead':
            d = {'btn': self.btn.get(), 'use_time': self.use_time.get()}
        elif tr == 'no_target':
            d = {'btn': self.btn.get(), 'use_time': self.use_time.get()}
        self.root.window_info[self.index]['triggers'][tr].append(d)
        self.root.window_info.save()
        self.root.update_listbox(self.index)
        self.master.destroy()

    @classmethod
    def convert(cls, value, reverse=False):
        if not reverse:
            return cls.TRIGGERS[value]
        for key, trigger in cls.TRIGGERS.items():
            if trigger == value:
                return key


class WindowInfo:
    ordering = ['hp_lt', 'mp_lt', 'hp_party_lt', 'mp_party_lt', 'mob_dead', 'buff', 'no_target']

    def __init__(self):
        self.values = [{'active': 0, 'name': '',
                        'triggers': {'hp_lt': [], 'mp_lt': [], 'hp_party_lt': [], 'mp_party_lt': [], 'mob_dead': [],
                                     'no_target': [], 'buff': []}}
                       for x in range(9)]
        self.load()

    def save(self):
        if not os.path.exists('save'):
            os.makedirs('save')
        with open('save/window_bind.l2b', 'wb') as f:
            pickle.dump(self.values, f)

    def load(self):
        if os.path.exists('save/window_bind.l2b'):
            with open('save/window_bind.l2b', 'rb') as f:
                try:
                    self.values = pickle.load(f)
                except:
                    pass

    def delete_by_i(self, window_i, del_i):
        window_tr = self[window_i]['triggers']

        i = 0
        while del_i > len(self.sum_tr_list(window_i, i)) - 1:
            i += 1
        i -= 1
        if i == 0:
            window_tr[self.ordering[i]].pop(del_i)
        elif i > 0:
            window_tr[self.ordering[i]].pop(del_i - len(self.sum_tr_list(window_i, i - 1)))

    def sum_tr_list(self, window_i, count):
        window_tr = self[window_i]['triggers']
        l = []
        for i in range(min(count, len(self.ordering))):
            l += window_tr[self.ordering[i]]
        return l

    def __getitem__(self, item):
        return self.values[item]

    def __str__(self):
        return str(self.values)


class CalibrationWindow:
    def __init__(self, main_window, method):
        self.master = main_window.calibration_window
        self.frame = tk.Frame(self.master)
        self.frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.main_window = main_window
        self.l2_window = main_window.l2_window
        self.l2_window.update_screen()
        self.pos = self.l2_window.pos
        self.size = self.l2_window.size
        self.master.geometry('%dx%d+%d+%d' % (self.size[0], self.size[1], self.pos[0], self.pos[1] - 1))
        self.master.resizable(False, False)
        self.master.overrideredirect(True)
        self.set_background()
        self.method = method

        if method == 'auto':
            self.auto_calibration()
        elif method == 'manual_hp' or method == 'manual_mp' or method == 'manual_target_hp':
            self.draw_line()

    def set_background(self):
        image = ImageTk.PhotoImage(self.l2_window.screen)
        bg_label = tk.Label(self.frame, image=image)
        bg_label.image = image

        if hasattr(self, 'canvas'):
            self.canvas.destroy()
        self.canvas = tk.Canvas(self.frame, width=self.size[0], height=self.size[1])
        self.canvas.create_image(0, 0, image=image, anchor=tk.NW)
        self.canvas.pack()

    def auto_calibration(self):
        def show_end_buttons():
            if hasattr(self, 'btn_ok'):
                self.btn_ok.destroy()
            if hasattr(self, 'btn_repeat'):
                self.btn_repeat.destroy()
            if hasattr(self, 'btn_cancel'):
                self.btn_cancel.destroy()

            def Ok(event):
                self.master.destroy()
                self.main_window.master.focus_force()

            def cancel(event):
                self.l2_window.hp_line = None
                self.l2_window.mp_line = None
                self.l2_window.target_hp_line = None
                self.master.destroy()
                self.main_window.master.focus_force()

            self.btn_ok = Button(self.frame, text='Ok', width=20, height=2)
            self.btn_ok.place(relx=0.5, x=-150, rely=0.5)
            self.btn_ok.bind('<ButtonRelease-1>', Ok)

            self.btn_cancel = Button(self.frame, text='Отмена', width=20, height=2)
            self.btn_cancel.place(relx=0.5, x=2, rely=0.5)
            self.btn_cancel.bind('<ButtonRelease-1>', cancel)

        self.l2_window.calibration()
        self.draw_lines()
        self.master.focus_force()
        show_end_buttons()

    def draw_line(self):
        self.l2_window.update_screen()
        self.set_background()
        line = [0, 0, 0, 0]
        self.motion_bind = None
        self.canvas_line = None
        self.master.focus_force()

        def new_line(event):
            if self.canvas_line:
                self.canvas.delete(self.canvas_line)
            line[0] = line[2] = event.x
            line[1] = line[3] = event.y
            self.motion_bind = self.master.bind('<Motion>', update_line)

        def update_line(event):
            if event.x > line[0]:
                line[2] = event.x
            if self.canvas_line:
                self.canvas.delete(self.canvas_line)
            self.canvas_line = self.canvas.create_line(line, width=2, fill='white')

        def close_line(event):
            update_line(event)
            if self.motion_bind:
                self.master.unbind('<Motion>', self.motion_bind)
            if self.new_line_bind:
                self.master.unbind('<Button-1>', self.new_line_bind)
            if self.close_line_bind:
                self.master.unbind('<ButtonRelease-1>', self.close_line_bind)
            show_end_buttons()

        def show_end_buttons():

            def Ok(event):
                if self.method == 'manual_hp':
                    self.l2_window.hp_line = line
                elif self.method == 'manual_mp':
                    self.l2_window.mp_line = line
                elif self.method == 'manual_target_hp':
                    self.l2_window.target_hp_line = line
                self.master.destroy()
                self.main_window.master.focus_force()

            def cancel(event):
                self.master.destroy()
                self.main_window.master.focus_force()

            def repeat(event):
                if hasattr(self, 'btn_ok'):
                    self.btn_ok.destroy()
                if hasattr(self, 'btn_repeat'):
                    self.btn_repeat.destroy()
                if hasattr(self, 'btn_cancel'):
                    self.btn_cancel.destroy()
                if self.canvas_line:
                    self.canvas.delete(self.canvas_line)
                self.draw_line()

            self.btn_ok = Button(self.frame, text='Ok')
            self.btn_ok.place(x=line[2] - 120, y=line[3] + 10)
            self.btn_ok.bind('<ButtonRelease-1>', Ok)

            self.btn_repeat = Button(self.frame, text='Повторить')
            self.btn_repeat.place(x=line[2] - 92, y=line[3] + 10)
            self.btn_repeat.bind('<ButtonRelease-1>', repeat)

            self.btn_cancel = Button(self.frame, text='Отмена')
            self.btn_cancel.place(x=line[2] - 20, y=line[3] + 10)
            self.btn_cancel.bind('<ButtonRelease-1>', cancel)

        self.new_line_bind = self.master.bind('<Button-1>', new_line)
        self.close_line_bind = self.master.bind('<ButtonRelease-1>', close_line)

    def draw_lines(self):
        self.set_background()
        if self.l2_window.hp_line:
            self.hp_line = self.canvas.create_line(self.l2_window.hp_line, width=2, fill='white')
        if self.l2_window.mp_line:
            self.mp_line = self.canvas.create_line(self.l2_window.mp_line, width=2, fill='white')
        if self.l2_window.target_hp_line:
            self.target_hp_line = self.canvas.create_line(self.l2_window.target_hp_line, width=2, fill='white')
        try:
            self.party_hp_lines = []
            self.party_mp_lines = []
            for i, php_line in enumerate(self.l2_window.party_hp_lines):
                self.party_hp_lines.append(self.canvas.create_line(php_line, width=2, fill='white'))
                self.party_mp_lines.append(
                    self.canvas.create_line(self.l2_window.party_mp_lines, width=2, fill='white'))
        except:
            pass


if __name__ == '__main__':
    root = tk.Tk()
    app = L2BotApp(root)
    root.mainloop()
