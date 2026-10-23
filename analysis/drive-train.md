# Drive-train characterization

Everything here follows from four numbers confirmed on the drive's motor
configuration screen, plus one assumption.

| Symbol | Value | Source |
|---|---|---|
| Kt | 1.693717 N·m/Arms | Motor spec block, confirmed 2026-10-23 |
| J | 9.60209 kg·cm² = 9.60209×10⁻⁴ kg·m² | Motor spec block |
| lead | 4 mm/rev | Actuator model code — **unconfirmed against datasheet** |
| η | 0.90 | **Assumed.** Not a datasheet value |

The `Arms` on the torque constant matters. Servo torque constants are quoted
either per RMS amp or per peak amp and the two differ by √2, which is a 41% error
in force if you take the wrong one.

---

## Force per amp

A screw converts torque to thrust through its lead:

```
F = 2*pi * eta * Kt * i / lead
  = 2*pi * 0.90 * 1.693717 / 0.004
  = 2394 N per amp        (538 lbf/A)
```

| Reference point | Current | Force |
|---|---|---|
| Motor continuous | 5.00 A | 11.97 kN |
| IMA44 rated thrust | 7.27 A | 17.40 kN |
| Motor peak | 15.00 A | 35.91 kN |

**The motor can produce 206% of the screw's rated thrust.** Set the drive current
limit at or below 7.27 A before commanding anything.

η = 0.90 is the weak link. A real efficiency of 0.85 moves every force here by
5.6%, and it is not a number you can look up for a specific screw and preload.
The stroke test measures the combination (η · Kt / lead) directly by comparing
commanded current to measured force, which is the honest way to get it.

---

## Reflected inertia

The rotor has to be accelerated along with the load, and the screw multiplies its
apparent mass:

```
m_eff = J * (2*pi / lead)^2
      = 9.60209e-4 * (2*pi / 0.004)^2
      = 9.60209e-4 * 2.4674e6
      = 2369 kg
```

The lead appears **squared** because kinetic energy goes as velocity squared, and
a smaller lead means the motor spins faster for the same linear speed. A 4 mm
lead is a high-force, low-speed configuration, and 2369 kg is the price of the
2394 N/A.

This is the dominant term in any fast move. Before the bellows pushes back at
all, accelerating the rotor costs:

```
a = 4.5 * x / t^2          trapezoid, equal thirds
F = m_eff * a
i = F / 2394
```

| Stroke | 500 ms | 300 ms | 200 ms | 150 ms | 100 ms |
|---|---|---|---|---|---|
| 5 mm | 0.09 A | 0.25 A | 0.56 A | 0.99 A | 2.23 A |
| 10 mm | 0.18 A | 0.49 A | 1.11 A | 1.98 A | 4.45 A |
| 20 mm | 0.36 A | 0.99 A | 2.23 A | 3.96 A | 8.91 A |
| 40 mm | 0.71 A | 1.98 A | 4.45 A | 7.92 A | 17.81 A |

Inertia current scales as x/t², so halving a move time quadruples it. There is a
lot of room at 300–500 ms and almost none below 100 ms.

---

## Speed

```
v_max = 3500 rpm * 4 mm/rev / 60 = 233.3 mm/s = 9.19 in/s
```

Is that a real rating or a voltage wall? Back-EMF at full speed:

```
Ke = 108.2580 Vrms/kRPM  ->  378.9 Vrms at 3500 rpm
electrical frequency = 3500/60 * 8 poles / 2 = 233.3 Hz
X_ll = 2*pi * 233.3 * 11.5e-3 = 16.86 ohm
terminal V at 5 Arms = sqrt((378.9 + 5*2.32)^2 + (5*16.86)^2) = 399.5 Vrms
```

Against a 460 Vrms maximum, that leaves about 61 V of headroom. **3500 rpm is a
rating, not a voltage limit** — the drive does not run out first. (Rough phasor
check using line-to-line values throughout; good enough to answer the question,
not a substitute for a proper machine model.)

Minimum move times this imposes, from v_peak = 1.5 x / t:

| Stroke | t minimum |
|---|---|
| 8 mm | 51 ms |
| 15 mm | 96 ms |
| 25 mm | 161 ms |

Speed is not the binding constraint at any stroke this application needs.
Acceleration current and drive-train ringing both bind first.

### A check worth doing on any servo motor

```
Ke / Kt = 108.258 / 1.693717 = 63.9
```

For a healthy motor with Ke in Vrms/kRPM and Kt in N·m/Arms, this ratio should
land near 60. A result near 127 means the constants are in peak units rather
than RMS, which mis-scales current and produces overload faults that look like
mechanical problems.

For the record, the theoretical relation Ke = Kt/√3 predicts 0.978 V·s/rad
against the datasheet's 1.0338 — a 5.4% discrepancy. The ideal relation ignores
saturation and harmonics. Use the datasheet number.

---

## Thermal

The motor configuration lists a coil thermal constant of 1.768388 mHz, which read
as 1/τ gives **τ = 565 s = 9.4 minutes**.

With no thermal sensor configured, a first-order model gives how long the coil
can sit above its continuous rating before reaching the temperature it would
settle at continuously:

```
t = -tau * ln(1 - (I_continuous / I)^2)
```

| Current | Force | Safe hold |
|---|---|---|
| 6 A | 14.4 kN | 11.2 min |
| 7 A | 16.8 kN | 6.7 min |
| 7.66 A | 18.3 kN | 5.2 min |
| 10 A | 23.9 kN | 2.7 min |
| 15 A | 35.9 kN | 1.1 min |

Ignores the housing, the ambient, and the mounting. Guidance, not protection.
The units reading on that mHz field is worth confirming with Kollmorgen.

---

## Stored energy

No brake, and the screw backdrives. A compressed spring load will drive the
actuator backwards if the drive is disabled or faults:

```
E = 0.5 * F * x
v_release = sqrt(2 * E / m_eff)
```

| Force held | Compression | Energy | Release speed | Motor |
|---|---|---|---|---|
| 1.2 kN | 10 mm | 6.0 J | 71 mm/s | 1070 rpm |
| 2.4 kN | 20 mm | 23.9 J | 142 mm/s | 2130 rpm |
| 4.8 kN | 30 mm | 71.8 J | 246 mm/s | 3690 rpm |
| 7.2 kN | 40 mm | 143.7 J | 348 mm/s | 5220 rpm |

The large reflected inertia is doing something useful here — it limits the
release speed. 2369 kg absorbs the energy that a lighter drive train would turn
into velocity. It is still 144 J looking for somewhere to go, and somewhere around 30 mm of
compression the release drives the motor past its 3500 rpm rating. Where exactly
depends on the spring rate, which is what the stroke test measures.

Ramp to zero current before disabling. Every time.
