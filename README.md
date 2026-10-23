# IMA44 / AKD2G Servo Commissioning and Drive-Train Characterization

Bringing a Tolomatic IMA44 electric linear actuator and a Kollmorgen AKD2G
servo drive from boxes to commanded motion, then measuring what the drive train
can actually do.

The actuator compresses a bellows on the MAMBA rapid cycling bubble chamber at
Fermilab. Every number here exists because some downstream calculation needed it
and nobody had measured it.

---

## Hardware

| Part | Model |
|---|---|
| Actuator | Tolomatic IMA444RN04SK6MV43DX12A4N — 4 mm lead roller screw, 460 V winding, no brake |
| Drive | Kollmorgen AKD2G-SPE-7V06S-A1F3-0000 — 480 V 3-phase, 6 A, single axis, STO, EtherCAT |
| Cable | Kollmorgen hybrid H6-21-015-B1-VL-012000 — power and feedback in one |
| Regen | 33 Ω / 1.5 kW (BAR-1500-33) |

Commissioning procedure, including the exact motor parameters and the order the
WorkBench screens have to be done in, is in
[docs/akd2g-setup.md](docs/akd2g-setup.md).

---

## What the drive train can do

Derived from the motor data confirmed on the drive, 2026-10-23.

```
force per amp   =  2*pi * eta * Kt / lead
                =  2*pi * 0.90 * 1.693717 / 0.004
                =  2394 N/A        (538 lbf/A)

reflected mass  =  J * (2*pi / lead)^2
                =  9.60209e-4 * (2*pi / 0.004)^2
                =  2369 kg
```

| | Value |
|---|---|
| Continuous current | 5 Arms → 12.0 kN |
| Peak current | 15 Arms → **35.9 kN** |
| Maximum speed | 3500 rpm → 233 mm/s (9.19 in/s) |
| Reflected inertia | 2369 kg |
| Coil thermal time constant | 565 s (9.4 min) |

### Two findings worth acting on

**The motor can overload the screw.** Peak current is 15 Arms, which produces
35.9 kN against the IMA44's 17.4 kN rated thrust — **206% of rating**. The drive
current limit has to be set at or below 7.27 A. That is not a precaution, it is
the only thing standing between a mistyped field and a destroyed ball screw.

**Acceleration, not velocity, is the binding constraint.** The 4 mm lead squares
the rotor's contribution to reflected inertia, so the motor sees 2369 kg before
any load is attached. Accelerating that mass is most of the peak current in any
fast move:

| Stroke | 500 ms | 300 ms | 150 ms | 100 ms |
|---|---|---|---|---|
| 10 mm | 0.18 A | 0.49 A | 1.98 A | 4.45 A |
| 20 mm | 0.36 A | 0.99 A | 3.96 A | **8.91 A** |
| 40 mm | 0.71 A | 1.98 A | **7.92 A** | **17.8 A** |

Bold exceeds the 5 A continuous rating from inertia alone, with zero external
load. Inertia current scales as stroke / time², so halving a move time
quadruples the current it costs.

Working through this is in [analysis/drive-train.md](analysis/drive-train.md).

---

## Measuring the load

The actuator drives a metal bellows whose spring rate nobody had measured. The
procedure in [procedures/bellows-stroke-test.md](procedures/bellows-stroke-test.md)
gets it, along with two other numbers, in an afternoon.

The method matters more than the numbers. **Command torque, not position.**

In position mode the drive delivers whatever current it takes to reach the
commanded point, up to its limit. Against an unknown spring, the first thing that
tells you the load is stiffer than you guessed is the current limit — by which
point you are already at full force.

In torque mode you command a current, which is a force, and the actuator travels
until the load pushes back just as hard. **The force can never exceed what you
asked for.** Walk the current up a step at a time and read off how far it went.

Running each step in both directions costs nothing extra and gives friction for
free, because friction reverses sign with direction while the spring does not:

```
x_true    = (x_extend + x_retract) / 2        friction cancels
F_friction = k * (x_retract - x_extend) / 2   half the gap
```

[`analysis/ladder_reduce.py`](analysis/ladder_reduce.py) takes the raw
(current, position) pairs and returns the spring rate, the friction, the lost
motion, which limit binds the stroke, and the safe hold time at each current.

---

## Two things about this machine that will hurt you

**There is no brake and the screw backdrives.** A compressed bellows is a loaded
spring. If the drive faults, loses power, or is disabled while compressed, that
energy comes back out through the actuator. At 7.2 kN and 40 mm that is 144 J
releasing at roughly 350 mm/s with the motor spinning to 5200 rpm. Always ramp to
zero current before disabling.

**No thermal sensor is configured.** Torque mode will hold current indefinitely
and nothing is watching the motor temperature. The coil thermal constant gives a
usable rule:

```
safe hold time  =  -tau * ln(1 - (I_continuous / I)^2)        tau = 565 s
```

| Current | Force | Safe hold |
|---|---|---|
| 6 A | 14.4 kN | 11.2 min |
| 7.66 A | 18.3 kN | 5.2 min |
| 10 A | 23.9 kN | 2.7 min |
| 15 A | 35.9 kN | 1.1 min |

A first-order model that ignores the housing and ambient, so treat it as
guidance rather than protection. It is still far better than nothing, and it
says the three-second dwells used in the stroke test are nowhere near trouble.

---

## What is still assumed

Screw efficiency η = 0.90 is not from a datasheet. It propagates directly into
every force on this page — a real η of 0.85 moves every number by 5.6%.

The 17.4 kN thrust rating and the 4 mm lead both come from the model code and
should be confirmed against Tolomatic's datasheet for this exact unit. The
screw's critical speed versus stroke is unknown and may bind below 3500 rpm on a
long stroke.

The drive-train resonance used in the motion planning (18–28 Hz) comes from an
assumed stiffness. The stroke test measures the real one.

---

## Layout

```
docs/         Commissioning procedure and drive configuration
analysis/     Drive-train characterization and the data reduction script
procedures/   Bench test procedures with expected results
```
