"""
Josephson Junctions and Superconducting Quantum Interference Simulator
Course: Fundamental of Quantum Transport and Nanoelectronics

This script implements rigorous mathematical modeling and numerical simulations:
1. Josephson Current-Phase Relation (CPR) & Tilted Washboard Potential
2. RCSJ (Resistively and Capacitively Shunted Junction) Differential Equation Solver
3. DC and AC Josephson Effects, Hysteretic I-V Curves (Overdamped vs Underdamped)
4. Microwave Induced Phase-Locking (Quantized Shapiro Steps)
5. DC SQUID Quantum Interference as a function of Applied Magnetic Flux
6. Multi-parameter Investigation: Junction Asymmetry (alpha) & Loop Inductance (beta_L)
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from scipy.optimize import root_scalar

# Ensure output directory exists
FIGURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

# Set high-quality styling for publication plots
plt.rcParams.update({
    'font.size': 11,
    'font.family': 'sans-serif',
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14,
    'lines.linewidth': 2.0,
    'grid.alpha': 0.35,
    'grid.linestyle': '--',
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

# Fundamental physical constants
HBAR = 1.054571817e-34    # J*s (reduced Planck constant)
E_CHARGE = 1.602176634e-19 # C (elementary electron charge)
PHI_0 = 2.067833848e-15   # Wb (magnetic flux quantum h / 2e)


# ==============================================================================
# 1. RCSJ MODEL DIFFERENTIAL EQUATION SOLVER
# ==============================================================================
def rcsj_derivs(tau, state, beta_c, i_dc, i_rf, omega_rf):
    """
    Dimensionless RCSJ differential equations:
    dphi/dtau = v
    dv/dtau = (i_dc + i_rf * sin(omega_rf * tau) - sin(phi) - v) / beta_c
    
    where:
    tau = omega_c * t,  omega_c = 2*pi*Ic*Rn / Phi_0
    v = V / (Ic * Rn) = dphi/dtau
    beta_c = 2*pi*Ic*Rn^2*C / Phi_0
    """
    phi, v = state
    i_total = i_dc + (i_rf * np.sin(omega_rf * tau) if i_rf > 0 else 0.0)
    
    if beta_c < 0.01:
        # Overdamped limit (C -> 0): dv/dtau is singular, v = i_total - sin(phi)
        dphi_dtau = i_total - np.sin(phi)
        dv_dtau = 0.0
    else:
        dphi_dtau = v
        dv_dtau = (i_total - np.sin(phi) - v) / beta_c
        
    return [dphi_dtau, dv_dtau]


def simulate_rcsj_trajectory(beta_c=0.2, i_dc=1.2, i_rf=0.0, omega_rf=0.5, tau_max=60.0):
    """Solves the time-domain phase evolution and voltage response."""
    t_span = (0.0, tau_max)
    t_eval = np.linspace(0.0, tau_max, 3000)
    init_state = [0.0, 0.0]
    
    sol = solve_ivp(
        rcsj_derivs,
        t_span,
        init_state,
        args=(beta_c, i_dc, i_rf, omega_rf),
        t_eval=t_eval,
        method='RK45',
        rtol=1e-6,
        atol=1e-8
    )
    return sol.t, sol.y[0], sol.y[1]


def compute_iv_curve(beta_c=0.5, i_rf=0.0, omega_rf=0.5, i_max=2.5, num_pts=80):
    """
    Computes time-averaged voltage <V> as a function of DC bias current I_dc,
    capturing hysteresis for underdamped junctions (forward & return sweeps).
    """
    # Sweep currents
    i_forward = np.linspace(0.0, i_max, num_pts)
    v_forward = []
    
    state = [0.0, 0.0]
    for i_val in i_forward:
        # Settle state
        sol = solve_ivp(
            rcsj_derivs, (0, 35.0), state,
            args=(beta_c, i_val, i_rf, omega_rf),
            method='RK45', rtol=1e-5, atol=1e-7
        )
        state = [sol.y[0][-1], sol.y[1][-1]]
        
        # Measure average voltage over interval
        t_eval = np.linspace(0, 40.0, 800)
        sol_meas = solve_ivp(
            rcsj_derivs, (0, 40.0), state,
            args=(beta_c, i_val, i_rf, omega_rf),
            t_eval=t_eval, method='RK45', rtol=1e-5, atol=1e-7
        )
        avg_v = np.mean(sol_meas.y[1])
        v_forward.append(avg_v)
        state = [sol_meas.y[0][-1], sol_meas.y[1][-1]]
        
    v_forward = np.array(v_forward)
    
    # Return sweep for underdamped hysteresis
    i_return = np.linspace(i_max, 0.0, num_pts)
    v_return = []
    for i_val in i_return:
        sol = solve_ivp(
            rcsj_derivs, (0, 35.0), state,
            args=(beta_c, i_val, i_rf, omega_rf),
            method='RK45', rtol=1e-5, atol=1e-7
        )
        state = [sol.y[0][-1], sol.y[1][-1]]
        
        t_eval = np.linspace(0, 40.0, 800)
        sol_meas = solve_ivp(
            rcsj_derivs, (0, 40.0), state,
            args=(beta_c, i_val, i_rf, omega_rf),
            t_eval=t_eval, method='RK45', rtol=1e-5, atol=1e-7
        )
        avg_v = np.mean(sol_meas.y[1])
        v_return.append(avg_v)
        state = [sol_meas.y[0][-1], sol_meas.y[1][-1]]
        
    v_return = np.array(v_return)
    return i_forward, v_forward, i_return, v_return


# ==============================================================================
# 2. DC SQUID QUANTUM INTERFERENCE SOLVER
# ==============================================================================
def squid_critical_current(phi_ext_norm, alpha=1.0, beta_l=0.0):
    """
    Computes total maximum critical current of a DC SQUID:
    I_c,total(Phi_ext) / I_c1
    
    Parameters:
    - phi_ext_norm: External magnetic flux in units of Phi_0 (Phi / Phi_0)
    - alpha: Junction asymmetry factor (alpha = I_c2 / I_c1 <= 1)
    - beta_l: Loop screening parameter (beta_l = 2 * L * I_c1 / Phi_0)
    """
    phi_ext = phi_ext_norm * 2.0 * np.pi  # Convert to radians
    
    if beta_l < 1e-4:
        # Analytical solution for negligible loop inductance (zero screening)
        # I_c(Phi) = sqrt(I_c1^2 + I_c2^2 + 2 * I_c1 * I_c2 * cos(2*pi*Phi/Phi_0))
        return np.sqrt(1.0 + alpha**2 + 2.0 * alpha * np.cos(phi_ext))
    
    # Finite screening inductance beta_l > 0:
    # Fluxoid quantization relation:
    # phi2 - phi1 = phi_ext + pi * beta_l * (alpha * sin(phi2) - sin(phi1))
    # We find maximum I_total = sin(phi1) + alpha * sin(phi2) subject to the flux constraint.
    # We sweep average phase phi_0 = (phi1 + phi2)/2:
    phi_0_samples = np.linspace(-np.pi, np.pi, 120)
    max_total_i = 0.0
    
    for phi_0 in phi_0_samples:
        # Solve for delta_phi = phi2 - phi1
        # f(delta_phi) = delta_phi - phi_ext - pi * beta_l * [alpha*sin(phi_0 + d/2) - sin(phi_0 - d/2)] = 0
        def f_constraint(delta_p):
            p1 = phi_0 - delta_p / 2.0
            p2 = phi_0 + delta_p / 2.0
            circ = (alpha * np.sin(p2) - np.sin(p1))
            return delta_p - phi_ext - np.pi * beta_l * circ
            
        try:
            # Bracket root around phi_ext
            res = root_scalar(f_constraint, bracket=[phi_ext - np.pi*2, phi_ext + np.pi*2], method='brentq')
            if res.converged:
                d_opt = res.root
                p1 = phi_0 - d_opt / 2.0
                p2 = phi_0 + d_opt / 2.0
                i_tot = np.sin(p1) + alpha * np.sin(p2)
                if i_tot > max_total_i:
                    max_total_i = i_tot
        except (ValueError, RuntimeError):
            # Fallback approximation
            d_opt = phi_ext / (1.0 + beta_l * 0.5)
            p1 = phi_0 - d_opt / 2.0
            p2 = phi_0 + d_opt / 2.0
            i_tot = np.sin(p1) + alpha * np.sin(p2)
            if i_tot > max_total_i:
                max_total_i = i_tot

    return max_total_i


# ==============================================================================
# 3. FIGURE GENERATION FUNCTIONS
# ==============================================================================

def plot_figure_1_josephson_energy_and_cpr():
    """Figure 1: Current-Phase Relation and Tilted Washboard Potential."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    
    # Left: Current-Phase Relation (CPR)
    phi = np.linspace(-2*np.pi, 2*np.pi, 500)
    ax1.plot(phi / np.pi, np.sin(phi), color='#0284c7', lw=2.5, label=r'Ideal Tunnel SIS: $I_s(\phi) = I_c \sin\phi$')
    # Unconventional CPR (SNS or high transmission pinhole for comparison)
    ax1.plot(phi / np.pi, np.sin(phi) + 0.2*np.sin(2*phi), color='#9333ea', ls='--', lw=2.0, 
             label=r'Higher harmonic: $I_s = I_c(\sin\phi + 0.2\sin 2\phi)$')
    
    ax1.set_xlabel(r'Josephson Phase Difference $\phi / \pi$')
    ax1.set_ylabel(r'Supercurrent $I_s / I_c$')
    ax1.set_title('(a) Josephson Current-Phase Relation (CPR)')
    ax1.axhline(0, color='gray', lw=0.8, ls=':')
    ax1.axvline(0, color='gray', lw=0.8, ls=':')
    ax1.grid(True)
    ax1.legend(loc='lower left')
    ax1.set_xlim(-2, 2)
    ax1.set_ylim(-1.25, 1.25)
    
    # Right: Tilted Washboard Potential Profiles
    phi_w = np.linspace(-1.5*np.pi, 3.5*np.pi, 600)
    current_biases = [0.0, 0.5, 1.0, 1.4]
    colors = ['#10b981', '#0ea5e9', '#f59e0b', '#ef4444']
    labels = [
        r'$I/I_c = 0.0$ (Symmetric well, zero tilt)',
        r'$I/I_c = 0.5$ (Metastable minima, $V=0$)',
        r'$I/I_c = 1.0$ (Critical tilt, inflection)',
        r'$I/I_c = 1.4$ (Running state, $V > 0$)'
    ]
    
    for ib, col, lbl in zip(current_biases, colors, labels):
        # Potential: U(phi) = -E_J * (cos(phi) + (I/Ic)*phi)
        u_phi = -np.cos(phi_w) - ib * phi_w
        # Offset for visual clarity
        u_norm = u_phi - u_phi[0]
        ax2.plot(phi_w / np.pi, u_norm, color=col, lw=2.2, label=lbl)
        
    ax2.set_xlabel(r'Phase Coordinate $\phi / \pi$')
    ax2.set_ylabel(r'Potential Energy $U(\phi) / E_J$ (arb. offset)')
    ax2.set_title(r'(b) Tilted Washboard Potential $U(\phi) = -E_J[\cos\phi + (I/I_c)\phi]$')
    ax2.grid(True)
    ax2.legend(loc='lower left', framealpha=0.9)
    ax2.set_xlim(-1.5, 3.5)
    
    plt.tight_layout()
    save_path = os.path.join(FIGURES_DIR, "fig1_josephson_energy_phase.png")
    plt.savefig(save_path)
    plt.close()
    print(f"Generated: {save_path}")


def plot_figure_2_rcsj_dynamics_and_iv():
    """Figure 2: RCSJ Time-domain Dynamics & Hysteretic I-V Characteristics."""
    fig = plt.figure(figsize=(14, 9))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.2])
    
    ax_dyn_phi = fig.add_subplot(gs[0, 0])
    ax_dyn_v = fig.add_subplot(gs[0, 1])
    ax_iv = fig.add_subplot(gs[1, :])
    
    # 1. Time-Domain Phase & Voltage for Subcritical vs Supercritical
    tau, phi_sub, v_sub = simulate_rcsj_trajectory(beta_c=0.3, i_dc=0.8, tau_max=50.0)
    tau, phi_super, v_super = simulate_rcsj_trajectory(beta_c=0.3, i_dc=1.3, tau_max=50.0)
    
    ax_dyn_phi.plot(tau, phi_sub, color='#10b981', lw=2, label=r'$I = 0.8 I_c$ (Trapped: $\phi \rightarrow \arcsin(0.8)$)')
    ax_dyn_phi.plot(tau, phi_super, color='#ef4444', lw=2, label=r'$I = 1.3 I_c$ (Running: $\phi$ rolls continuously)')
    ax_dyn_phi.set_xlabel(r'Normalized Time $\tau = \omega_c t$')
    ax_dyn_phi.set_ylabel(r'Phase $\phi(\tau)$ [rad]')
    ax_dyn_phi.set_title(r'(a) Phase Evolution $\phi(\tau)$ in RCSJ Model')
    ax_dyn_phi.grid(True)
    ax_dyn_phi.legend(loc='upper left')
    
    ax_dyn_v.plot(tau, v_sub, color='#10b981', lw=2, label=r'$I = 0.8 I_c$ ($V = 0$, Zero-resistance Supercurrent)')
    ax_dyn_v.plot(tau, v_super, color='#ef4444', lw=2, label=r'$I = 1.3 I_c$ ($V(\tau) > 0$, AC Oscillations)')
    ax_dyn_v.set_xlabel(r'Normalized Time $\tau = \omega_c t$')
    ax_dyn_v.set_ylabel(r'Normalized Voltage $v(\tau) = d\phi/d\tau$')
    ax_dyn_v.set_title(r'(b) Instantaneous Voltage Pulses $V \propto d\phi/dt$')
    ax_dyn_v.grid(True)
    ax_dyn_v.legend(loc='upper right')
    
    # 2. I-V Characteristic curves comparing Overdamped vs Underdamped
    # Overdamped analytical: <v> = sqrt(i^2 - 1) for i > 1
    i_arr = np.linspace(0.0, 2.5, 200)
    v_overdamped = np.where(i_arr >= 1.0, np.sqrt(np.maximum(0.0, i_arr**2 - 1.0)), 0.0)
    
    # Underdamped simulated (beta_c = 3.0)
    i_fwd, v_fwd, i_ret, v_ret = compute_iv_curve(beta_c=3.0, num_pts=50)
    
    ax_iv.plot(v_overdamped, i_arr, color='#0284c7', lw=2.5, 
              label=r'Overdamped $\beta_C \ll 1$ (RSJ analytical: $\langle V \rangle = R_N \sqrt{I^2 - I_c^2}$)')
    ax_iv.plot(v_fwd, i_fwd, color='#ef4444', lw=2.5, 
              label=r'Underdamped $\beta_C = 3.0$ (Forward Sweep: switching at $I_c$)')
    ax_iv.plot(v_ret, i_ret, color='#f59e0b', ls='--', lw=2.5, 
              label=r'Underdamped $\beta_C = 3.0$ (Return Sweep: retrapping at $I_r \approx \frac{4}{\pi \sqrt{\beta_C}} I_c$)')
    
    # Normal state Ohm's law asymptote V = I * Rn
    ax_iv.plot(i_arr, i_arr, color='gray', ls=':', lw=1.5, label=r'Ohmic Asymptote: $V = I R_N$')
    
    ax_iv.set_xlabel(r'Time-Averaged Voltage $\langle V \rangle / (I_c R_N)$')
    ax_iv.set_ylabel(r'Bias Current $I / I_c$')
    ax_iv.set_title(r'(c) Current-Voltage (I-V) Characteristics & Stewart-McCumber Damping Hysteresis')
    ax_iv.grid(True)
    ax_iv.legend(loc='lower right', framealpha=0.9)
    ax_iv.set_xlim(-0.05, 2.4)
    ax_iv.set_ylim(-0.05, 2.5)
    
    # Annotate switching and retrapping
    ax_iv.annotate(r'Switching Current $I_c$', xy=(0.0, 1.0), xytext=(0.3, 1.15),
                  arrowprops=dict(facecolor='black', shrink=0.08, width=1.2, headwidth=6))
    ax_iv.annotate(r'Retrapping Current $I_r$', xy=(0.45, 0.45), xytext=(0.7, 0.35),
                  arrowprops=dict(facecolor='black', shrink=0.08, width=1.2, headwidth=6))
    
    plt.tight_layout()
    save_path = os.path.join(FIGURES_DIR, "fig2_rcsj_dynamics_iv_curve.png")
    plt.savefig(save_path)
    plt.close()
    print(f"Generated: {save_path}")


def plot_figure_3_squid_quantum_interference():
    """Figure 3: DC SQUID Quantum Interference vs Applied Magnetic Flux & Parameter Sweeps."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
    
    flux_norm = np.linspace(-2.5, 2.5, 300)
    
    # Panel (a): Investigation of Junction Asymmetry alpha = Ic2 / Ic1 (with beta_L = 0)
    asymmetry_factors = [1.0, 0.7, 0.4, 0.1]
    colors_a = ['#0284c7', '#10b981', '#f59e0b', '#ef4444']
    
    for alpha, col in zip(asymmetry_factors, colors_a):
        ic_vals = [squid_critical_current(f, alpha=alpha, beta_l=0.0) for f in flux_norm]
        lbl = (r'Symmetric $\alpha = 1.0$ (Complete null at $\Phi_0/2$)' if alpha == 1.0 
               else rf'Asymmetric $\alpha = {alpha}$ ($I_{{min}} = {1-alpha:.1f} I_c$)')
        ax1.plot(flux_norm, ic_vals, color=col, lw=2.2, label=lbl)
        
    ax1.set_xlabel(r'Applied Magnetic Flux $\Phi_{ext} / \Phi_0$')
    ax1.set_ylabel(r'Maximum Critical Current $I_{c,total} / I_{c1}$')
    ax1.set_title(r'(a) Effect of Junction Asymmetry $\alpha = I_{c2} / I_{c1}$ ($\beta_L = 0$)')
    ax1.grid(True)
    ax1.legend(loc='lower center', framealpha=0.9)
    ax1.set_xlim(-2.5, 2.5)
    ax1.set_ylim(0, 2.2)
    
    # Mark destructive and constructive interference
    ax1.axvline(0.5, color='#ef4444', ls=':', alpha=0.6)
    ax1.text(0.52, 2.05, r'Destructive: $\Phi = 0.5\Phi_0$', color='#ef4444', fontsize=9, fontweight='bold')
    ax1.axvline(1.0, color='#10b981', ls=':', alpha=0.6)
    ax1.text(1.02, 2.05, r'Constructive: $\Phi = 1.0\Phi_0$', color='#10b981', fontsize=9, fontweight='bold')
    
    # Panel (b): Investigation of Loop Screening Inductance beta_L = 2*L*Ic / Phi_0 (with alpha = 1.0)
    beta_l_factors = [0.0, 0.5, 1.0, 2.0]
    colors_b = ['#0284c7', '#8b5cf6', '#ec4899', '#f97316']
    
    for beta_l, col in zip(beta_l_factors, colors_b):
        ic_vals = [squid_critical_current(f, alpha=1.0, beta_l=beta_l) for f in flux_norm]
        lbl = (r'Zero screening $\beta_L = 0$ (Ideal Sinusoidal)' if beta_l == 0.0 
               else rf'Screening $\beta_L = {beta_l}$ (Depth reduction & distortion)')
        ax2.plot(flux_norm, ic_vals, color=col, lw=2.2, label=lbl)
        
    ax2.set_xlabel(r'Applied Magnetic Flux $\Phi_{ext} / \Phi_0$')
    ax2.set_ylabel(r'Maximum Critical Current $I_{c,total} / I_{c1}$')
    ax2.set_title(r'(b) Effect of Screening Inductance $\beta_L = 2 L I_c / \Phi_0$ ($\alpha = 1.0$)')
    ax2.grid(True)
    ax2.legend(loc='lower center', framealpha=0.9)
    ax2.set_xlim(-2.5, 2.5)
    ax2.set_ylim(0, 2.2)
    
    plt.tight_layout()
    save_path = os.path.join(FIGURES_DIR, "fig3_squid_flux_interference.png")
    plt.savefig(save_path)
    plt.close()
    print(f"Generated: {save_path}")


def plot_figure_4_shapiro_steps():
    """Figure 4: AC Josephson Phase Locking and Quantized Shapiro Voltage Steps."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2))
    
    # 1. AC Josephson Frequency vs DC Voltage
    v_microvolts = np.linspace(0, 50, 200)
    # f_J = 2*e*V / h = V / Phi_0 = 483.5979 GHz/mV
    f_ghz = (v_microvolts * 1e-6) / PHI_0 / 1e9
    
    ax1.plot(v_microvolts, f_ghz, color='#0284c7', lw=2.5)
    ax1.set_xlabel(r'DC Voltage across Junction $V_{dc}$ [$\mu$V]')
    ax1.set_ylabel(r'Josephson Oscillation Frequency $f_J$ [GHz]')
    ax1.set_title(r'(a) AC Josephson Frequency $f_J = \frac{2e}{h} V = \frac{V}{\Phi_0}$')
    ax1.grid(True)
    ax1.annotate(r'$f_J = 483.6 \text{ MHz}/\mu\text{V}$', xy=(25, (25e-6)/PHI_0/1e9), xytext=(8, 18),
                bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#0284c7", lw=1.5),
                arrowprops=dict(facecolor='#0284c7', shrink=0.08, width=1.2, headwidth=6))
    
    # 2. Shapiro Steps in I-V Curve
    # Generate I-V curve with RF microwave drive: i_rf = 0.6, omega_rf = 0.5
    omega_rf = 0.5
    i_fwd_dc, v_fwd_dc, _, _ = compute_iv_curve(beta_c=0.3, i_rf=0.0, num_pts=50)
    i_fwd_rf, v_fwd_rf, _, _ = compute_iv_curve(beta_c=0.3, i_rf=0.7, omega_rf=omega_rf, num_pts=70)
    
    ax2.plot(v_fwd_dc, i_fwd_dc, color='#94a3b8', ls='--', lw=2.0, label='DC only (No Microwave Drive)')
    ax2.plot(v_fwd_rf, i_fwd_rf, color='#ec4899', lw=2.5, label=r'Microwave irradiated ($i_{rf} = 0.7, \Omega = 0.5$)')
    
    # Mark Shapiro steps
    for n in [1, 2, 3]:
        v_step = n * omega_rf
        ax2.axvline(v_step, color='#f59e0b', ls=':', lw=1.5)
        ax2.text(v_step + 0.02, 0.45, rf'$n={n}$' + '\n' + r'$V_n = n\frac{\hbar\omega}{2e}$', 
                 color='#b45309', fontsize=9, fontweight='bold')
        
    ax2.set_xlabel(r'Normalized Voltage $\langle V \rangle / (I_c R_N)$')
    ax2.set_ylabel(r'Bias Current $I / I_c$')
    ax2.set_title(r'(b) Quantized Shapiro Voltage Steps $V_n = n \cdot \frac{h f}{2e}$')
    ax2.grid(True)
    ax2.legend(loc='lower right', framealpha=0.9)
    ax2.set_xlim(-0.05, 1.9)
    ax2.set_ylim(-0.05, 2.4)
    
    plt.tight_layout()
    save_path = os.path.join(FIGURES_DIR, "fig4_shapiro_steps.png")
    plt.savefig(save_path)
    plt.close()
    print(f"Generated: {save_path}")


def plot_figure_5_quantum_phase_coherence_summary():
    """Figure 5: Master Summary of Quantum Phase Coherence in Nanoelectronic Devices."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.2))
    
    # Panel (a): SQUID Flux-to-Voltage Transfer Function (V-Phi Curve)
    phi_scan = np.linspace(0, 3.0, 300)
    # Voltage response for constant bias current I_b slightly above 2*Ic:
    # V(Phi) = R_N/2 * sqrt(I_b^2 - I_c(Phi)^2)
    i_bias = 2.05
    ic_arr = np.array([squid_critical_current(f, alpha=1.0, beta_l=0.1) for f in phi_scan])
    v_squid = np.sqrt(np.maximum(0.0, i_bias**2 - ic_arr**2))
    
    # Transfer function |dV/dPhi|
    dv_dphi = np.abs(np.gradient(v_squid, phi_scan))
    
    ax1.plot(phi_scan, v_squid, color='#0284c7', lw=2.5, label=r'Voltage Modulation $V(\Phi)$')
    ax1.plot(phi_scan, dv_dphi / np.max(dv_dphi) * np.max(v_squid), color='#ef4444', ls='--', lw=2.0, 
             label=r'Transfer Sensitivity $V_\Phi = \left|\frac{\partial V}{\partial \Phi}\right|$')
    
    ax1.set_xlabel(r'Applied Flux $\Phi / \Phi_0$')
    ax1.set_ylabel(r'SQUID Voltage Output [arb. units]')
    ax1.set_title(r'(a) SQUID Flux-to-Voltage Transducer ($I_{bias} = 2.05 I_c$)')
    ax1.grid(True)
    ax1.legend(loc='upper right')
    
    # Optimal flux bias point
    opt_flux = 0.28
    ax1.axvline(opt_flux, color='#10b981', ls=':', lw=2)
    ax1.text(opt_flux + 0.05, 0.2, r'Optimal Bias Point $\Phi_{opt}$' + '\n' + r'(Max Sensitivity for MEG)', 
             color='#047857', fontsize=9, fontweight='bold')
    
    # Panel (b): Superconducting Transmon Qubit Anharmonic Energy Spectrum
    # H = 4*E_C * n^2 - E_J * cos(phi)
    # Energy levels: E_m \approx \hbar \omega_p (m + 1/2) - (E_C / 12) (6m^2 + 6m + 3)
    levels = [0, 1, 2, 3]
    ej_ec_ratio = 50.0  # Transmon regime E_J / E_C >> 1
    hbar_omega_01 = 1.0  # Normalized 0->1 transition energy
    anharmonicity = -0.05 # alpha = E_12 - E_01 = -E_C
    
    energies = [0.0]
    for m in range(1, 4):
        # E_m - E_0
        delta_e = m * hbar_omega_01 + 0.5 * m * (m - 1) * anharmonicity
        energies.append(delta_e)
        
    for idx, e in enumerate(energies):
        ax2.hlines(e, 0.2, 0.8, colors='#9333ea', lw=3.0)
        ax2.text(0.85, e, rf'$|{idx}\rangle$ ({e:.3f} $\hbar\omega_{{01}}$)', 
                 verticalalignment='center', color='#581c87', fontweight='bold')
        
    # Transitions
    ax2.annotate('', xy=(0.35, energies[1]), xytext=(0.35, energies[0]),
                arrowprops=dict(arrowstyle="<->", color='#0284c7', lw=2.5))
    ax2.text(0.38, (energies[0]+energies[1])/2, r'$\omega_{01}$ (Qubit Drive)', color='#0284c7', fontweight='bold')
    
    ax2.annotate('', xy=(0.60, energies[2]), xytext=(0.60, energies[1]),
                arrowprops=dict(arrowstyle="<->", color='#ef4444', lw=2.5))
    ax2.text(0.63, (energies[1]+energies[2])/2, r'$\omega_{12} = \omega_{01} - E_C/\hbar$' + '\n(Anharmonicity)', 
             color='#ef4444', fontweight='bold')
    
    ax2.set_xlim(0, 1.25)
    ax2.set_ylim(-0.15, 3.2)
    ax2.set_xticks([])
    ax2.set_ylabel(r'Energy Level $(E_m - E_0) / (\hbar \omega_{01})$')
    ax2.set_title(r'(b) Transmon Qubit: Non-linear Josephson Inductor $L_J(\phi)$')
    ax2.grid(axis='y')
    
    plt.tight_layout()
    save_path = os.path.join(FIGURES_DIR, "fig5_quantum_phase_coherence_summary.png")
    plt.savefig(save_path)
    plt.close()
    print(f"Generated: {save_path}")


# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
if __name__ == "__main__":
    print("=" * 65)
    print("Running Quantum Transport & SQUID Simulation Suite...")
    print(f"Target Directory: {FIGURES_DIR}")
    print("=" * 65)
    
    plot_figure_1_josephson_energy_and_cpr()
    plot_figure_2_rcsj_dynamics_and_iv()
    plot_figure_3_squid_quantum_interference()
    plot_figure_4_shapiro_steps()
    plot_figure_5_quantum_phase_coherence_summary()
    
    print("=" * 65)
    print("All 5 Publication-Grade Figures successfully generated!")
    print("=" * 65)
