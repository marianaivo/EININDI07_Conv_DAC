# https://www.thinksrs.com/downloads/programs/therm%20calc/ntccalibrator/ntccalculator.html

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NTC Thermistor Calibrator (fix2)
- Calcula coeficientes Steinhart–Hart (A, B, C) e Beta/R25
- Plota Dados / S–H / β
- Calculadora R→T e T→R (aceita vírgula decimal e milhares)
- ENTER confirma nos campos da calculadora
"""

import math
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

K25 = 273.15 + 25.0

# -------- Utilidades numéricas --------
def norm_float(s: str) -> float:
    """
    Converte strings como '1.234,56', '1,234.56', '1234,5' ou '1234.5' em float.
    """
    s = s.strip()
    if not s:
        raise ValueError("Número vazio.")
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    return float(s)

def c_to_k(t_c): return t_c + 273.15
def k_to_c(t_k): return t_k - 273.15

# -------- Modelo Steinhart–Hart --------
def compute_steinhart_hart(R, T_c):
    """
    Resolve A, B, C em 1/T = A + B ln(R) + C (ln R)^3 com 3 pares R–T.
    """
    if len(R) != 3 or len(T_c) != 3:
        raise ValueError("Forneça exatamente três pares R–T para S–H.")
    T_k = np.array([c_to_k(t) for t in T_c], dtype=float)
    y = 1.0 / T_k
    x = np.log(np.array(R, dtype=float))
    X = np.column_stack([np.ones(3), x, x**3])
    try:
        coeffs = np.linalg.solve(X, y)
    except np.linalg.LinAlgError:
        coeffs, *_ = np.linalg.lstsq(X, y, rcond=None)
    return coeffs.tolist()  # A, B, C

def sh_R_from_T(A, B, C, T_c):
    """ Resolve R para uma T(°C) via Newton. """
    T_k = c_to_k(T_c); y = 1.0 / T_k
    R = 10000.0
    for _ in range(60):
        if R <= 0: R = 1.0
        lnR = math.log(R)
        f = A + B*lnR + C*(lnR**3) - y
        df = (B + 3*C*(lnR**2)) / R
        step = f/df if df != 0 else f*1e-6
        R_new = R - step
        if abs(R_new - R) < 1e-9: break
        R = R_new
    return max(R, 1e-9)

def sh_T_from_R(A, B, C, R):
    """ T(°C) a partir de R usando S–H. """
    lnR = math.log(R)
    invT = A + B*lnR + C*(lnR**3)
    if invT <= 0:
        raise ValueError("Resultado inválido do S–H (1/T ≤ 0). Verifique os pontos.")
    return k_to_c(1.0 / invT)

# -------- Modelo Beta --------
def compute_beta_R25(R, T_c):
    """
    Calcula beta a partir dos 2 primeiros pontos e R25 pela média sobre os pontos.
    """
    if len(R) < 2 or len(T_c) < 2:
        raise ValueError("Mínimo de dois pontos para o modelo β.")
    R1, R2 = float(R[0]), float(R[1])
    T1k, T2k = c_to_k(float(T_c[0])), c_to_k(float(T_c[1]))
    beta = math.log(R1/R2) / (1.0/T1k - 1.0/T2k)
    R25s = []
    for Ri, Ti_c in zip(R, T_c):
        Tik = c_to_k(float(Ti_c))
        R25_i = Ri * math.exp(-beta * (1.0/Tik - 1.0/K25))
        R25s.append(R25_i)
    R25 = float(np.mean(R25s))
    return beta, R25

def beta_R_from_T(beta, R25, T_c):
    Tik = c_to_k(T_c)
    return R25 * math.exp(beta*(1.0/Tik - 1.0/K25))

def beta_T_from_R(beta, R25, R):
    invT = 1.0/K25 + (1.0/beta)*math.log(R/R25)
    if invT <= 0:
        raise ValueError("Resultado inválido do modelo β (1/T ≤ 0).")
    return k_to_c(1.0/invT)

# -------- App --------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NTC Thermistor Calibrator")
        self.geometry("1050x700")
        self.minsize(980, 640)

        # Coeficientes
        self._coeffs = {"A": None, "B": None, "C": None, "beta": None, "R25": None}

        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.create_widgets()

    def create_widgets(self):
        root = ttk.Frame(self, padding=10); root.pack(fill="both", expand=True)
        left = ttk.Frame(root); left.pack(side="left", fill="y")

        # Entradas R–T
        inputs = ttk.LabelFrame(left, text="R–T Pairs (Ω, °C)")
        inputs.pack(fill="x", padx=5, pady=5)

        defaults_R = [25000, 10000, 4000]
        defaults_T = [5, 25, 45]
        self.r_vars = [tk.StringVar(value=str(defaults_R[i])) for i in range(3)]
        self.t_vars = [tk.StringVar(value=str(defaults_T[i])) for i in range(3)]

        for i in range(3):
            row = ttk.Frame(inputs); row.pack(fill="x", padx=5, pady=2)
            ttk.Label(row, text=f"R{i+1} (Ω):", width=12).pack(side="left")
            ttk.Entry(row, textvariable=self.r_vars[i], width=14, justify="right").pack(side="left")
            ttk.Label(row, text=f"T{i+1} (°C):", width=12).pack(side="left", padx=(12,0))
            ttk.Entry(row, textvariable=self.t_vars[i], width=14, justify="right").pack(side="left")

        btns = ttk.Frame(inputs); btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="Compute", command=self.on_compute).pack(side="left")
        ttk.Button(btns, text="Reset", command=self.on_reset).pack(side="left", padx=6)

        # Coeficientes
        coeffs = ttk.LabelFrame(left, text="Calculated Coefficients")
        coeffs.pack(fill="x", padx=5, pady=5)

        self.a_var = tk.StringVar(value="-")
        self.b_var = tk.StringVar(value="-")
        self.c_var = tk.StringVar(value="-")
        self.beta_var = tk.StringVar(value="-")
        self.r25_var = tk.StringVar(value="-")

        def mk_row(parent, label, var, suffix=""):
            row = ttk.Frame(parent); row.pack(fill="x", padx=5, pady=2)
            ttk.Label(row, text=label, width=18).pack(side="left")
            ttk.Entry(row, textvariable=var, width=22, state="readonly", justify="right").pack(side="left")
            ttk.Label(row, text=suffix).pack(side="left")

        mk_row(coeffs, "A (S–H)", self.a_var, "1/K")
        mk_row(coeffs, "B (S–H)", self.b_var, "1/K")
        mk_row(coeffs, "C (S–H)", self.c_var, "1/K")
        ttk.Separator(coeffs, orient="horizontal").pack(fill="x", pady=4)
        mk_row(coeffs, "β (Beta model)", self.beta_var, "K")
        mk_row(coeffs, "R(25°C)", self.r25_var, "Ω")

        savebar = ttk.Frame(coeffs); savebar.pack(fill="x", pady=6)
        ttk.Button(savebar, text="Save coefficients…", command=self.save_coeffs).pack(side="left")

        # Calculadora
        calc = ttk.LabelFrame(left, text="Model Calculator"); calc.pack(fill="x", padx=5, pady=5)
        self.model_choice = tk.StringVar(value="SH")
        ttk.Radiobutton(calc, text="Use S–H model", variable=self.model_choice, value="SH").pack(anchor="w", padx=5)
        ttk.Radiobutton(calc, text="Use β model", variable=self.model_choice, value="B").pack(anchor="w", padx=5)

        # R -> T
        rt = ttk.Frame(calc); rt.pack(fill="x", padx=5, pady=6)
        ttk.Label(rt, text="R(Ω) → T(°C): ").pack(side="left")
        self.calc_R_var = tk.StringVar(value="10000")
        e_calcR = ttk.Entry(rt, textvariable=self.calc_R_var, width=14, justify="right"); e_calcR.pack(side="left")
        ttk.Button(rt, text="=", command=self.calc_T_from_R).pack(side="left", padx=4)
        self.calc_T_out = ttk.Label(rt, text="— °C", width=16); self.calc_T_out.pack(side="left")
        e_calcR.bind("<Return>", lambda e: self.calc_T_from_R())

        # T -> R
        tr = ttk.Frame(calc); tr.pack(fill="x", padx=5, pady=6)
        ttk.Label(tr, text="T(°C) → R(Ω): ").pack(side="left")
        self.calc_T_var = tk.StringVar(value="25")
        e_calcT = ttk.Entry(tr, textvariable=self.calc_T_var, width=14, justify="right"); e_calcT.pack(side="left")
        ttk.Button(tr, text="=", command=self.calc_R_from_T).pack(side="left", padx=4)
        self.calc_R_out = ttk.Label(tr, text="— Ω", width=16); self.calc_R_out.pack(side="left")
        e_calcT.bind("<Return>", lambda e: self.calc_R_from_T())

        # Opções de plot
        opts = ttk.LabelFrame(left, text="Plot Options"); opts.pack(fill="x", padx=5, pady=5)
        self.show_data = tk.BooleanVar(value=True)
        self.show_sh = tk.BooleanVar(value=True)
        self.show_beta = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="Data points", variable=self.show_data, command=self.redraw_plot).pack(anchor="w", padx=5)
        ttk.Checkbutton(opts, text="S–H model", variable=self.show_sh, command=self.redraw_plot).pack(anchor="w", padx=5)
        ttk.Checkbutton(opts, text="β model", variable=self.show_beta, command=self.redraw_plot).pack(anchor="w", padx=5)

        scale_row = ttk.Frame(opts); scale_row.pack(fill="x", padx=5, pady=2)
        ttk.Label(scale_row, text="Temp range (°C):").pack(side="left")
        self.tmin_var = tk.StringVar(value="0"); self.tmax_var = tk.StringVar(value="60")
        ttk.Entry(scale_row, textvariable=self.tmin_var, width=6, justify="right").pack(side="left", padx=(4,2))
        ttk.Label(scale_row, text="to").pack(side="left")
        ttk.Entry(scale_row, textvariable=self.tmax_var, width=6, justify="right").pack(side="left", padx=(2,6))
        ttk.Button(scale_row, text="Update", command=self.redraw_plot).pack(side="left")

        # Área do gráfico
        right = ttk.Frame(root); right.pack(side="left", fill="both", expand=True)
        fig = Figure(figsize=(6,5), dpi=100)
        self.ax = fig.add_subplot(111)
        self.ax.set_title("R vs. Temperature")
        self.ax.set_xlabel("Temperature (°C)")
        self.ax.set_ylabel("Resistance (Ω)")
        self.ax.grid(True)
        self.canvas = FigureCanvasTkAgg(fig, master=right)
        self.canvas.draw(); self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.redraw_plot()

    # -------- Ações --------
    def parse_inputs(self):
        R = [norm_float(v.get()) for v in self.r_vars]
        T = [norm_float(v.get()) for v in self.t_vars]
        if any(r <= 0 for r in R): 
            raise ValueError("Resistências devem ser > 0.")
        return R, T

    def on_compute(self):
        try:
            R, T = self.parse_inputs()
            A, B, C = compute_steinhart_hart(R, T)
            beta, R25 = compute_beta_R25(R, T)
            self._coeffs = {"A": A, "B": B, "C": C, "beta": beta, "R25": R25}
            self.a_var.set(f"{A:.9f}"); self.b_var.set(f"{B:.9f}"); self.c_var.set(f"{C:.9f}")
            self.beta_var.set(f"{beta:.2f}"); self.r25_var.set(f"{R25:.2f}")
            self.redraw_plot()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_reset(self):
        for i, val in enumerate([25000, 10000, 4000]): self.r_vars[i].set(str(val))
        for i, val in enumerate([5, 25, 45]): self.t_vars[i].set(str(val))
        self.a_var.set("-"); self.b_var.set("-"); self.c_var.set("-")
        self.beta_var.set("-"); self.r25_var.set("-")
        self._coeffs = {"A": None, "B": None, "C": None, "beta": None, "R25": None}
        self.redraw_plot()

    def ensure_coeffs(self):
        if any(self._coeffs[k] is None for k in ("A","B","C","beta","R25")):
            R, T = self.parse_inputs()
            A, B, C = compute_steinhart_hart(R, T)
            beta, R25 = compute_beta_R25(R, T)
            self._coeffs = {"A": A, "B": B, "C": C, "beta": beta, "R25": R25}
            self.a_var.set(f"{A:.9f}"); self.b_var.set(f"{B:.9f}"); self.c_var.set(f"{C:.9f}")
            self.beta_var.set(f"{beta:.2f}"); self.r25_var.set(f"{R25:.2f}")

    def calc_T_from_R(self):
        try:
            self.ensure_coeffs()
            R = norm_float(self.calc_R_var.get())
            if R <= 0: raise ValueError("R deve ser > 0.")
            if self.model_choice.get() == "SH":
                T = sh_T_from_R(self._coeffs["A"], self._coeffs["B"], self._coeffs["C"], R)
            else:
                T = beta_T_from_R(self._coeffs["beta"], self._coeffs["R25"], R)
            self.calc_T_out.config(text=f"{T:.3f} °C")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def calc_R_from_T(self):
        try:
            self.ensure_coeffs()
            T = norm_float(self.calc_T_var.get())
            if self.model_choice.get() == "SH":
                R = sh_R_from_T(self._coeffs["A"], self._coeffs["B"], self._coeffs["C"], T)
            else:
                R = beta_R_from_T(self._coeffs["beta"], self._coeffs["R25"], T)
            self.calc_R_out.config(text=f"{R:.2f} Ω")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def redraw_plot(self):
        if not hasattr(self, "ax"): return
        self.ax.cla()
        self.ax.set_title("R vs. Temperature")
        self.ax.set_xlabel("Temperature (°C)")
        self.ax.set_ylabel("Resistance (Ω)")
        self.ax.grid(True)

        try:
            tmin = norm_float(self.tmin_var.get()); tmax = norm_float(self.tmax_var.get())
        except Exception:
            tmin, tmax = 0.0, 60.0
        if tmax <= tmin: tmax = tmin + 1.0
        Ts = np.linspace(tmin, tmax, 200)

        # Dados
        try:
            R, T = self.parse_inputs()
            if getattr(self, "show_data", None) and self.show_data.get():
                self.ax.scatter(T, R, label="Data", marker="o", s=40)
        except Exception:
            pass

        # S–H
        try:
            if all(self._coeffs[k] is not None for k in ("A","B","C")) and self.show_sh.get():
                A,B,C = self._coeffs["A"], self._coeffs["B"], self._coeffs["C"]
                Rsh = [sh_R_from_T(A,B,C,t) for t in Ts]
                self.ax.plot(Ts, Rsh, label="S–H model")
        except Exception:
            pass

        # β
        try:
            if all(self._coeffs[k] is not None for k in ("beta","R25")) and self.show_beta.get():
                beta, R25 = self._coeffs["beta"], self._coeffs["R25"]
                Rb = [beta_R_from_T(beta, R25, t) for t in Ts]
                self.ax.plot(Ts, Rb, label="β model")
        except Exception:
            pass

        self.ax.legend(loc="best")
        self.canvas.draw_idle()

    def save_coeffs(self):
        try:
            self.ensure_coeffs()
            payload = {
                "SteinhartHart": {"A": self._coeffs["A"], "B": self._coeffs["B"], "C": self._coeffs["C"]},
                "BetaModel": {"beta": self._coeffs["beta"], "R25": self._coeffs["R25"]},
                "notes": "Units: A,B,C in 1/K; beta in K; R25 in ohms."
            }
            path = filedialog.asksaveasfilename(
                title="Save coefficients",
                defaultextension=".json",
                filetypes=[("JSON","*.json"), ("All files","*.*")],
                initialfile="ntc_coeffs.json"
            )
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)
                messagebox.showinfo("Saved", f"Saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = App()
    app.mainloop()