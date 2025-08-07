import customtkinter as ctk
from math import radians, sin, cos, atan2, degrees, sqrt

# Initialize theme
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

# Correct Beaufort scale calculation
def beaufort_scale(speed_kn):
    limits = [1, 4, 7, 11, 17, 22, 28, 34, 41, 48, 56, 64]
    names = [
        "Calmo", "Vento leve", "Brisa fraca", "Brisa leve",
        "Brisa moderada", "Brisa fresca", "Vento fresco", "Vento forte",
        "Tempestuoso", "Tempestade", "Tempestade forte", "Furacão"
    ]
    for i, lim in enumerate(limits):
        if speed_kn < lim:
            return i, names[i]
    return 12, names[-1]

class TrueWindApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("True Wind")
        self.geometry("480x720")
        self.minsize(360, 600)
        self._last = None

        ctk.CTkLabel(self, text="True Wind", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(20,5))
        ctk.CTkLabel(self, text="Criado por Christiano Leszkiewicz", font=ctk.CTkFont(size=12)).pack(pady=(0,15))

        container = ctk.CTkFrame(self, corner_radius=12, fg_color="#f7f9fc")
        container.pack(fill="x", padx=20, pady=10)
        for i in range(4): container.grid_columnconfigure(i, weight=1)
        labels = ["Velocidade do barco (kn)", "Aproamento (°)", "Velocidade do vento (kn)", "Direção do vento (°)"]
        self.entries = []
        for idx, txt in enumerate(labels):
            ctk.CTkLabel(container, text=txt, anchor="w").grid(row=idx, column=0, sticky="w", padx=10, pady=(12,0))
            ent = ctk.CTkEntry(container, placeholder_text="0.0", width=140, corner_radius=8)
            ent.grid(row=idx, column=1, columnspan=3, sticky="ew", padx=(0,10), pady=(12,0))
            self.entries.append(ent)

        mode_frame = ctk.CTkFrame(container, corner_radius=8, fg_color="#e1e5ea")
        mode_frame.grid(row=4, column=0, columnspan=4, pady=15, padx=10, sticky="ew")
        self.wind_mode = ctk.StringVar(value="north")
        ctk.CTkRadioButton(mode_frame, text="North ref", variable=self.wind_mode, value="north").pack(side="left", expand=True, padx=10, pady=8)
        ctk.CTkRadioButton(mode_frame, text="Heading ref", variable=self.wind_mode, value="heading").pack(side="left", expand=True, padx=10, pady=8)

        self.view_mode = ctk.StringVar(value="NorthUP")
        opt_menu = ctk.CTkOptionMenu(container, values=["NorthUP","HeadUP"], variable=self.view_mode, width=200)
        opt_menu.grid(row=5, column=0, columnspan=4, pady=(0,20), padx=10, sticky="ew")

        ctk.CTkButton(container, text="Calcular True Wind", command=self.calculate, corner_radius=10).grid(
            row=6, column=0, columnspan=4, pady=(0,20), padx=10, sticky="ew")

        self.result = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=18), fg_color="#ffffff", corner_radius=8)
        self.result.pack(fill="x", padx=20, pady=(0,15))

        self.canvas = ctk.CTkCanvas(self, bg="#f7f9fc", highlightthickness=0)
        self.canvas.pack(expand=True, fill="both", padx=20, pady=(0,20))
        self.canvas.bind('<Configure>', lambda e: self._redraw())
        # Footer
        self.footer = ctk.CTkLabel(self, text="Criado por Christiano Leszkiewicz", font=ctk.CTkFont(size=12), text_color="#BB1414")
        self.footer.pack(pady=(0,10))

    def calculate(self):
        try:
            Vs, heading, Vw, wind_meas = map(lambda e: float(e.get().replace(',','.')), self.entries)
            wind_to = (wind_meas + 180) % 360
            if self.wind_mode.get() == "heading":
                wind_to = (wind_to + heading) % 360
            hdg, wto = radians(heading), radians(wind_to)
            Vt_x = Vw * sin(wto) - Vs * sin(hdg)
            Vt_y = Vw * cos(wto) - Vs * cos(hdg)
            speed = sqrt(Vt_x**2 + Vt_y**2)
            direction = (degrees(atan2(Vt_x, Vt_y)) + 360) % 360 if speed > 1e-6 else 0.0
            bft, beaufort = beaufort_scale(speed)
            self.result.configure(text=f"{speed:.2f} kn · {direction:.1f}° · Bft {bft} ({beaufort})")
            self._last = (heading, Vt_x, Vt_y, direction)
            self._redraw()
        except ValueError:
            self.result.configure(text="Invalid input")

    def _redraw(self):
        if not self._last: return
        self._draw(*self._last)

    def _draw(self, heading, Vt_x, Vt_y, direction):
        c, w, h = self.canvas, self.canvas.winfo_width(), self.canvas.winfo_height()
        cx, cy, R = w/2, h/2, min(w,h)/2 - 40
        if self.view_mode.get()=="HeadUP": tick_rot, boat_rot = radians(-heading), 0
        else: tick_rot, boat_rot = 0, radians(heading)
        def rot(x,y,ang): return (x*cos(ang)-y*sin(ang), x*sin(ang)+y*cos(ang))
        c.delete("all")
        c.create_oval(cx-R, cy-R, cx+R, cy+R, outline="#333", width=2)
        for deg in range(0,360,30):
            r = radians(deg)
            p1 = rot(R*sin(r), -R*cos(r), tick_rot)
            p2 = rot((R-25)*sin(r), -(R-25)*cos(r), tick_rot)
            c.create_line(cx+p1[0], cy+p1[1], cx+p2[0], cy+p2[1], fill="#333")
            t = rot((R+15)*sin(r), -(R+15)*cos(r), tick_rot)
            c.create_text(cx+t[0], cy+t[1], text=str(deg), font=("Arial", 9))
        pts = [(0, -R*0.3), (R*0.15, R*0.3), (-R*0.15, R*0.3)]
        poly = [rot(x,y,boat_rot) for x,y in pts]
        c.create_polygon(*[(cx+px, cy+py) for px,py in poly], fill="#555", outline="#333", width=2)
        vec_len = sqrt(Vt_x**2 + Vt_y**2)
        scale = min(1, (R/6)/vec_len) if vec_len else 0
        vx, vy = rot(Vt_x, -Vt_y, tick_rot) if self.view_mode.get()=="HeadUP" else (Vt_x, -Vt_y)
        ex, ey = cx + vx*6*scale, cy + vy*6*scale
        c.create_line(cx, cy, ex, ey, arrow="last", width=3, fill="#f55")

if __name__=='__main__':
    TrueWindApp().mainloop()
