# Fuel-Optimised reactor circuit update

## Goal

Keep the supplied four-reactor blueprint as an immutable source copy and create a separate candidate with per-reactor fuel insertion and spent-cell removal control.

## Selected circuit behavior

- The fuel inserter for each reactor is enabled by that reactor's decider only when `uranium-fuel-cell = 0` and `signal-T < 550`.
- The spent-cell removal inserter for each reactor is enabled directly by that reactor's burner-fuel signal when `depleted-uranium-fuel-cell > 0`.
- Each reactor, decider, feed inserter, and removal inserter remain on a separate circuit network.
- Preserve all entity positions and the original source file. Change only circuit behavior and circuit wires.

## Why this design

The source blueprint has four wired removal-side inserters and four unwired feed-side inserters. All eight require `signal-thermometer-blue = 1`, so the feed-side inserters cannot receive their enabling signal. The four deciders currently output that signal on `uranium-fuel-cell = 0 AND signal-T = 550`; this does not represent the presence of a spent cell, and the exact-temperature comparison is too narrow for a temperature threshold.

Using the existing deciders for feeding and the reactor's burner-fuel signal for spent-cell removal fixes those mismatches without adding entities or changing layout.

## Files

- `designs/nuclear_fuel_optimised_source.txt`: byte-for-byte copy of the uploaded blueprint.
- `designs/nuclear_fuel_optimised_circuit_v1.txt`: circuit-updated candidate.
- `reports/nuclear_fuel_optimised_circuit_v1.json`: source/candidate hashes and entity-level circuit change summary.

## Review limits

- Circuit signal interpretation and inserter pickup/drop behavior must still be confirmed in Factorio. The project validator does not simulate circuit networks or burner inventories.
- No placement, fluid, or power changes are in scope.
- Treat game behavior as `UNKNOWN` until tested in-game.
