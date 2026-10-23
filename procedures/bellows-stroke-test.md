# Bellows stroke test

Measures the bellows spring rate, the drive-train friction, and the lost motion
between the motor encoder and the rod — in one afternoon, with no gas and no
cryogenics.

All three are numbers the motion planning needs and none of them can be looked
up.

---

## The method, and why it is torque mode

**In position mode the drive delivers whatever current it takes** to reach the
commanded point, up to its limit. Against a spring whose rate you do not know,
the first thing that tells you it is stiffer than expected is the current limit,
and by then you are already at full force.

**In torque mode you command a current, which is a force**, and the actuator
travels until the bellows pushes back just as hard. The force can never exceed
what you asked for. You walk the current up a step at a time and read off how
far it went. The curve you build is the measurement.

AKD2G Service Motion has a Torque mode with Current 1 / Current 2 fields and a
Start/Stop button, so the tool already exists. It needs Command Source set to
Mode 0 (Service).

Run each step in **both directions**. Friction reverses sign with direction while
the spring does not, so:

```
x_true     = (x_extend + x_retract) / 2        friction cancels in the mean
F_friction = k * (x_retract - x_extend) / 2    half the gap, times the rate
```

One extra measurement per step, and friction comes out for free.

---

## Before enabling the drive

**Read the IMA44 stroke off the label.** It is a model option and it is the hard
ceiling on everything below.

**Confirm Kt and lead in WorkBench.** Every force on this page is wrong if either
is wrong. Expect Kt near 1.69 N·m/Arms and lead 4 mm/rev.

**Set the drive current limit to 3.0 A** in WorkBench's Limits screen. This sits
underneath the torque command so a mis-typed field cannot produce more than
7.2 kN. The motor's 15 A peak would produce 35.9 kN against a 17.4 kN rated
screw, so this is load-bearing, not belt-and-braces.

**Vent the chamber.** You want the bellows spring alone, with no gas pressure
term. That is what makes the measured slope a clean spring rate instead of a
mixture of two things.

**Mount a dial indicator on the rod or the bellows end plate.** The AKD2G reads
the motor encoder — it knows how far the motor turned, not how far the rod went.
The gap between the two is backlash plus drive-train flex, and the drive cannot
see it.

**Set up the WorkBench Scope** to record position feedback, current feedback and
velocity. That is where the current measurement comes from, not a clamp meter.

---

## Finding home

Zero force is zero current. Command 0 A and let the bellows push the actuator
back until nothing is pushing on anything.

Except it is a band, not a point — the rod stops where the spring force drops
below breakaway friction. So approach from both sides:

1. Compress about 5 mm at 0.5 A, then command 0 A. Record where it settles as `x_a`.
2. Drive a few mm the other way, command 0 A. Record `x_b`.
3. `home = (x_a + x_b) / 2`, and `friction = k * (x_b - x_a) / 2`

Repeat three times. The midpoints should agree within the indicator's
resolution; the gap between them is the friction band.

Set the drive zero there and **write down the raw encoder count**. You will
re-home after every disassembly and after every cooldown — thermal contraction
moves this point far more than the working stroke does.

> **Zero force on the bellows is not zero force on the actuator.** Once a vacuum
> jacket is evacuated, atmosphere pushes on the outer bellows with A_eff × 1 atm
> continuously. There are two homes, vented and under vacuum. Measure both and
> record the offset.

---

## The ladder

Service Motion in **Torque / Pulse** mode. Pulse alternates between the commanded
value and zero on a timer, which bounds how long the motor holds current without
anyone having to remember. Three seconds on is enough to settle and read.

| Step | Current | Force |
|---|---|---|
| 1 | 0.25 A | 599 N |
| 2 | 0.50 A | 1197 N |
| 3 | 0.75 A | 1796 N |
| 4 | 1.00 A | 2394 N |
| 5 | 1.50 A | 3592 N |
| 6 | 2.00 A | 4789 N |
| 7 | 2.50 A | 5986 N |
| 8 | 3.00 A | 7183 N |

At each step record: drive position extending, drive position retracting, and the
dial indicator.

**Compute ΔF/Δx after every step before commanding the next.** That running slope
is both the measurement and the live safety check.

### Stop immediately if

| Symptom | What it means |
|---|---|
| ΔF/Δx jumps suddenly | The bellows is approaching solid height. A spring rate that climbs steeply is the only warning you get. Call that step the limit. |
| Position does not change between steps | Something is bottomed out or seized. More current will damage whatever is in the way. |
| Indicator and drive position diverge further | Backlash taking up on the first step is normal. A growing gap later means something is deflecting that should not be. |
| Motor housing hot to the touch | No thermal sensor is configured, so nothing will fault. Check between every step above 1.5 A. |
| Any new noise | Ticking, grinding, a change in pitch. Stop first, diagnose second. |

---

## Reduction

[`../analysis/ladder_reduce.py`](../analysis/ladder_reduce.py) takes the table and
returns:

```
k            bellows spring rate              [N/mm]
F_friction   screw + seal breakaway force     [N]
lost motion  encoder versus indicator          [mm]
x_max        usable stroke, and which limit binds
V_filler     chamber volume to displace for a pressure target
```

It fits a line through the friction-cancelled midpoints rather than dividing each
row, because a small error in the zero reference distorts small steps far more
than large ones. The fit puts that error in the intercept where it belongs.

---

## What the result is for

`x_max = F_limit / k` — **the usable stroke is probably a force limit, not a
travel limit.** The actuator runs out of thrust against a stiff bellows long
before it runs out of rod. Which of the three ceilings binds first (actuator
thrust, bellows solid height, or mechanical stroke) is exactly what this test
tells you, and it is the input the chamber sizing has been waiting on.

The spring rate also feeds back into the motion planning. Drive-train resonance
goes as √(k_series / m_eff), and with 2369 kg of reflected inertia, where that
resonance lands decides the shortest move time that does not ring.
