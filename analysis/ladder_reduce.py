#!/usr/bin/env python3
"""
MAMBA bellows ladder reduction.

Paste today's torque-ladder numbers into LADDER below, run the file, read
the answers. Pure standard library -- no numpy needed. Plot is optional.

    python3 ladder_reduce.py

What it gives you:
    k            bellows spring rate            [N/mm]
    F_friction   screw + seal breakaway force   [N]
    x_max        usable stroke at a force limit [mm]
    V_filler     chamber filler volume needed to hit a pressure target

The physics, in one line: the actuator pushes, the bellows pushes back, and
friction sits between them with a sign that flips with direction.  Averaging
the extend and retract positions at the same current cancels friction and
leaves the pure spring curve; half the gap between them IS the friction.
"""

import math

# ----------------------------------------------------------------------
# DRIVE TRAIN -- confirm all three in WorkBench / on the actuator label.
# Every force below scales directly with these.
# ----------------------------------------------------------------------
KT    = 1.693717     # N*m/Arms  CONFIRMED on the motor spec block 2026-10-23
JROT  = 9.60209e-4   # kg*m^2     CONFIRMED (9.60209 kg*cm^2 on the block)
LEAD  = 0.004        # m/rev   screw lead        STILL UNCONFIRMED - Tolomatic model code
ETA   = 0.90         # -       screw efficiency  STILL ASSUMED, not a datasheet value

N_MAX   = 3500.0     # rpm     CONFIRMED motor max speed
I_PEAK  = 15.0       # Arms    CONFIRMED motor peak current
KE      = 108.2580   # Vrms/kRPM  CONFIRMED (use this, not Kt/sqrt(3) -- 5.4% apart)
TAU_COIL = 1/1.768388e-3   # s  coil thermal time constant, read as 1/f from the
                           #    "1.768388 mHz" field.  565 s = 9.4 min.  [Inferred]

FORCE_PER_AMP = 2 * math.pi * ETA * KT / LEAD      # N/A
M_EFF         = JROT * (2 * math.pi / LEAD) ** 2   # kg, reflected to linear

# ----------------------------------------------------------------------
# BELLOWS -- from your circumference measurement, 2026-10-16
# ----------------------------------------------------------------------
IN       = 0.0254
CIRC_IN  = 15.0                      # measured around the outer convolutions
BORE_IN  = 4.0                       # ID from the KJL part description
OD_IN    = CIRC_IN / math.pi
DMEAN_IN = (OD_IN + BORE_IN) / 2
A_EFF    = math.pi / 4 * (DMEAN_IN * IN) ** 2      # m^2
# A_eff = pi/4 * D_mean^2 is the standard estimate.  The true definition is
# dV/dx -- confirm by water displacement before anything final.

# ----------------------------------------------------------------------
# LIMITS
# ----------------------------------------------------------------------
F_ACTUATOR = 17.4e3   # N   IMA44 rated thrust
I_CONT     = 5.0      # A   motor continuous rating
BELLOWS_OAL_IN  = 6.0
BELLOWS_LIVE_IN = 4.0   # GUESS -- measure the convoluted section, flange to flange
COMPRESS_FRAC   = 0.15  # KJL: unbraided hose "compresses up to 15%" (static spec)

# ----------------------------------------------------------------------
# TODAY'S DATA  -- (current_A, x_extend_mm, x_retract_mm, indicator_mm or None)
#
#   x_extend  : position after commanding this current from a relaxed start
#   x_retract : position after returning to this current from a MORE
#               compressed state  (so friction pushes the other way)
#   indicator : dial indicator on the rod, same reference, or None
#
# Both positions as the DRIVE reports them, same sign convention,
# zero at the zero-force home point.
# ----------------------------------------------------------------------
LADDER = [
    # (A,    x_ext,  x_ret,  indicator)
    (0.25,   None,   None,   None),
    (0.50,   None,   None,   None),
    (0.75,   None,   None,   None),
    (1.00,   None,   None,   None),
    (1.50,   None,   None,   None),
    (2.00,   None,   None,   None),
    (2.50,   None,   None,   None),
    (3.00,   None,   None,   None),
]

# Chamber, for the pressure/filler section
V0_L      = 1.699    # L   4 in x 8.25 in, header and camera port NOT included
P_BASE    = 4.0      # atm
P_TARGET  = 5.0      # atm
GAMMA     = 1.4      # air


# ======================================================================
def linfit(xs, ys):
    """Least squares y = m*x + b.  Returns (m, b, r2)."""
    n = len(xs)
    if n < 2:
        raise ValueError("need at least 2 points")
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0:
        raise ValueError("all x identical -- nothing moved?")
    m = sxy / sxx
    b = my - m * mx
    ss_res = sum((y - (m * x + b)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return m, b, r2


def adiabatic_peak(p_base, dV, V0, gamma):
    """Peak pressure after compressing V0 by dV, adiabatically."""
    if dV >= V0:
        raise ValueError("swept volume exceeds chamber volume")
    return p_base * (V0 / (V0 - dV)) ** gamma


def main():
    print("=" * 68)
    print("DRIVE TRAIN")
    print("=" * 68)
    print(f"  force per amp   {FORCE_PER_AMP:8.0f} N/A   ({FORCE_PER_AMP/4.448:.0f} lbf/A)")
    print(f"  reflected mass  {M_EFF:8.0f} kg")
    print(f"  A_eff           {A_EFF*1e4:8.2f} cm^2  ({A_EFF/IN**2:.2f} in^2)")
    print(f"  swept volume    {A_EFF*1e-3*1e6:8.3f} cm^3 per mm of stroke")

    v_max = N_MAX * LEAD / 60.0
    print(f"\n  MOTOR CEILINGS")
    print(f"  max speed       {N_MAX:8.0f} rpm -> {v_max*1000:.1f} mm/s "
          f"({v_max/IN:.2f} in/s)")
    print(f"  peak current    {I_PEAK:8.1f} A   -> {I_PEAK*FORCE_PER_AMP/1000:.1f} kN "
          f"= {I_PEAK*FORCE_PER_AMP/F_ACTUATOR*100:.0f}% of the actuator's rated thrust")
    print(f"  !! set the drive current limit at or below "
          f"{F_ACTUATOR/FORCE_PER_AMP:.2f} A or the motor can overload the screw")
    print(f"\n  safe hold time above the {I_CONT:.0f} A continuous rating "
          f"(no thermal sensor fitted):")
    print(f"    t = -tau * ln(1 - (I_cont/I)^2),  tau = {TAU_COIL:.0f} s")
    for i_a in (6.0, 7.0, 7.66, 10.0, I_PEAK):
        t = -TAU_COIL * math.log(1 - (I_CONT / i_a) ** 2)
        print(f"    {i_a:5.2f} A ({i_a*FORCE_PER_AMP/1000:4.1f} kN)  ->  "
              f"{t:5.0f} s  ({t/60:.1f} min)")

    rows = [r for r in LADDER if r[1] is not None and r[2] is not None]
    if not rows:
        print("\n  No data yet -- fill in LADDER and run again.")
        print(f"  Reference: {F_ACTUATOR/FORCE_PER_AMP:.2f} A reaches the "
              f"{F_ACTUATOR/1000:.1f} kN actuator rating.")
        return

    print("\n" + "=" * 68)
    print("LADDER")
    print("=" * 68)
    print(f"  {'I (A)':>6} {'F (N)':>8} {'x_ext':>8} {'x_ret':>8} "
          f"{'x_true':>8} {'gap':>7} {'k_inc':>8}")

    forces, x_true, fric = [], [], []
    prev = None
    for (i_a, xe, xr, ind) in rows:
        F  = i_a * FORCE_PER_AMP
        xt = (xe + xr) / 2.0          # friction cancels in the mean
        gap = xr - xe                 # = 2 * F_friction / k
        k_inc = ""
        if prev is not None and xt != prev[1]:
            k_inc = f"{(F - prev[0]) / (xt - prev[1]):8.1f}"
        forces.append(F); x_true.append(xt)
        prev = (F, xt)
        print(f"  {i_a:>6.2f} {F:>8.0f} {xe:>8.3f} {xr:>8.3f} "
              f"{xt:>8.3f} {gap:>7.3f} {k_inc:>8}")

    k, b, r2 = linfit(x_true, forces)     # N per mm, since x is in mm
    print(f"\n  SPRING RATE   k = {k:.1f} N/mm   ({k*25.4/4.448:.0f} lbf/in)"
          f"   intercept {b:.0f} N   R^2 = {r2:.4f}")
    if r2 < 0.98:
        print("  !! R^2 is low. Either the bellows is nonlinear (going solid?)"
              "\n     or a reading is off. Look at the k_inc column.")
    if abs(b) > 0.1 * max(forces):
        print(f"  !! Large intercept ({b:.0f} N). Either home is not the true"
              "\n     zero-force point, or there is a preload you have not accounted for.")

    for (i_a, xe, xr, ind) in rows:
        fric.append(k * (xr - xe) / 2.0)
    f_avg = sum(fric) / len(fric)
    print(f"  FRICTION      F_fric = {f_avg:.0f} N  "
          f"({f_avg/FORCE_PER_AMP:.3f} A, {f_avg/4.448:.0f} lbf)")
    print(f"                spread {min(fric):.0f} to {max(fric):.0f} N")

    inds = [(xe, xr, ind) for (_, xe, xr, ind) in rows if ind is not None]
    if inds:
        gaps = [abs((xe + xr) / 2 - ind) for (xe, xr, ind) in inds]
        print(f"  LOST MOTION   drive vs indicator: {min(gaps):.3f} to "
              f"{max(gaps):.3f} mm  (backlash + driveline flex)")
    else:
        print("  LOST MOTION   no indicator data -- the drive cannot see this itself")

    print("\n" + "=" * 68)
    print("WHAT THE STROKE IS LIMITED BY")
    print("=" * 68)
    x_force = F_ACTUATOR / k
    x_motor = I_CONT * FORCE_PER_AMP / k
    x_bell  = COMPRESS_FRAC * BELLOWS_LIVE_IN * IN * 1000
    limits = [("actuator thrust 17.4 kN", x_force),
              ("motor continuous 5 A",    x_motor),
              (f"bellows 15% of {BELLOWS_LIVE_IN:.1f} in live", x_bell)]
    for name, val in sorted(limits, key=lambda t: t[1]):
        print(f"  {val:7.1f} mm   {name}")
    x_use, which = min(limits, key=lambda t: t[1])[1], min(limits, key=lambda t: t[1])[0]
    print(f"\n  BINDING LIMIT: {which}  ->  {x_use:.1f} mm")
    print("  (and 15% is a STATIC misalignment spec, not a cyclic fatigue rating)")

    print("\n" + "=" * 68)
    print(f"PRESSURE, {P_BASE:.0f} atm base, adiabatic")
    print("=" * 68)
    V0 = V0_L / 1000.0
    print(f"  {'stroke':>8} {'dV cm^3':>9} {'P_peak':>9} {'dP psi':>8} {'hold A':>8}")
    for frac in (0.25, 0.5, 0.75, 1.0):
        x = x_use * frac
        dV = A_EFF * x / 1000.0
        try:
            p2 = adiabatic_peak(P_BASE, dV, V0, GAMMA)
        except ValueError:
            continue
        # held current = bellows spring + pressure differential on the bellows
        F_hold = k * x + A_EFF * (p2 - 1.0) * 101325.0
        print(f"  {x:>7.1f} mm {dV*1e6:>9.1f} {p2:>8.3f} a "
              f"{(p2-P_BASE)*14.6959:>8.2f} {F_hold/FORCE_PER_AMP:>8.2f}"
              f"{'  !! over 5 A' if F_hold/FORCE_PER_AMP > I_CONT else ''}")

    need = 1 - (P_BASE / P_TARGET) ** (1 / GAMMA)
    print(f"\n  {P_BASE:.0f} -> {P_TARGET:.0f} atm needs dV/V0 = {need*100:.2f}% "
          f"= {need*V0*1e6:.0f} cm^3 at the current {V0_L:.2f} L")
    print(f"  which is {need*V0/A_EFF*1000:.1f} mm of stroke "
          f"-- {'WITHIN' if need*V0/A_EFF*1000 <= x_use else 'BEYOND'} the "
          f"{x_use:.1f} mm limit above")

    print("\n  FILLER NEEDED to reach the target at a safe stroke:")
    print(f"  {'stroke':>8} {'V0 needed':>11} {'filler':>10}")
    for x in (5, 8, 10, 15):
        if x > x_use * 1.25:
            continue
        dV = A_EFF * x / 1000.0
        v_need = dV / need
        print(f"  {x:>7.1f} mm {v_need*1e3:>9.2f} L {(V0 - v_need)*1e6:>8.0f} cm^3"
              f"{'   (impossible, needs a bigger chamber)' if v_need > V0 else ''}")

    print("\n" + "=" * 68)
    print("SANITY CHECKS")
    print("=" * 68)
    print(f"  k from fit vs k from endpoints: {k:.1f} vs "
          f"{(forces[-1]-forces[0])/(x_true[-1]-x_true[0]):.1f} N/mm")
    e_max = 0.5 * k * 1000 * (x_use / 1000) ** 2
    v_rel = math.sqrt(2 * e_max / M_EFF)
    print(f"  stored energy at {x_use:.1f} mm: {e_max:.0f} J"
          f"  -> releases at {v_rel*1000:.0f} mm/s if the drive trips (no brake)")
    print(f"  units check: k [N/mm] * x [mm] = F [N]; "
          f"A_eff [m^2] * x [m] = V [m^3].  OK")
    v_max = N_MAX * LEAD / 60.0
    print(f"  fastest move at {x_use:.1f} mm, limited by {N_MAX:.0f} rpm: "
          f"t_min = {1.5*(x_use/1000)/v_max*1000:.0f} ms "
          f"(trapezoid, v_pk = 1.5 x/t)")

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n  (matplotlib not installed -- skipping plot)")
        return
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot([r[1] for r in rows], forces, "o--", label="extend (friction opposes)")
    ax.plot([r[2] for r in rows], forces, "s--", label="retract (friction assists)")
    ax.plot(x_true, forces, "k^-", label="mean = true spring curve")
    xs = [0, max(x_true)]
    ax.plot(xs, [k * x + b for x in xs], "r:", label=f"fit: k = {k:.1f} N/mm")
    ax.set_xlabel("position [mm]"); ax.set_ylabel("force [N]")
    ax.set_title("MAMBA bellows force vs position")
    ax.legend(); ax.grid(alpha=0.3); fig.tight_layout()
    fig.savefig("ladder.png", dpi=150)
    print("\n  plot written to ladder.png")


if __name__ == "__main__":
    main()
