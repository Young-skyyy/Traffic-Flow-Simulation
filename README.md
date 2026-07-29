# Vehicle Dynamics & CAN Bus Simulation Toolkit

A Python-based simulation toolkit for vehicle dynamics modeling, fuel consumption analysis, CAN bus simulation, and traffic flow analysis. Built for automotive testing and HiL validation workflows.

## Project Structure

```
.
├── vehicle_dynamics.py    # Core: vehicle physics, BSFC fuel model, WLTC cycle
├── can_demo.py            # CAN bus simulation, DBC generation, error injection
├── traffic_sim.py         # Traffic signal, multi-lane queue, accident simulation
├── traffic_flow.py        # Road capacity & traffic flow fundamentals
├── simulated_ecu.dbc      # Auto-generated DBC file (5 ECUs, Vector CANoe compatible)
├── can_log.asc            # ASC trace log with timestamps
├── bsfc_map.png           # BSFC heatmap visualization
├── requirements.txt       # Python dependencies
└── README.md
```

## Modules

| Module | File | Description |
|--------|------|-------------|
| Vehicle Dynamics | `vehicle_dynamics.py` | Acceleration, braking distance, BSFC-based fuel consumption, WLTC Class 3 transient cycle |
| CAN Bus Simulation | `can_demo.py` | 5-ECU message generation, DBC/ASC export, bus load analysis, error frame injection |
| Traffic Simulation | `traffic_sim.py` | Signal control, multi-lane queuing, accident impact on capacity |
| Traffic Flow | `traffic_flow.py` | Speed-density-flow relations, single-lane capacity calculation |

## Features

### Vehicle Dynamics & Fuel Model
- **Vehicle physical model**: powertrain parameters, aerodynamic drag, rolling resistance
- **BSFC interpolation**: bilinear interpolation on brake specific fuel consumption map for instantaneous fuel rate
- **WLTC Class 3 cycle**: full 1800-second transient simulation with DFCO (deceleration fuel cut-off), acceleration enrichment, and driver model
- **Phase-by-phase analysis**: Low / Medium / High / Extra-High speed phase breakdown
- **BSFC heatmap**: matplotlib visualization of engine efficiency contours

### CAN Bus Simulation
- **5 simulated ECUs**: EMS, BMS, ABS, TCU, BCM with realistic message timing
- **Auto-generated DBC file**: signal definitions, value tables, multiplexed messages
- **ASC log export**: timestamped trace log, directly importable into Vector CANoe
- **Bus load monitoring**: real-time load percentage (typically < 35% at 500 kbps)
- **Error frame injection**: configurable error rate for robustness testing
- **DTC fault scanning**: diagnostic trouble code enumeration

### Traffic Flow
- Single/dual-lane queue analysis under signal control
- Accident scenario: lane closure impact on bottleneck capacity
- Protected left-turn phase simulation

## Quick Start

### Prerequisites
- Python 3.8+
- Dependencies listed in `requirements.txt`

### Installation

```bash
git clone https://github.com/Young-skyyy/Traffic-Flow-Simulation.git
cd Traffic-Flow-Simulation
pip install -r requirements.txt
```

### Run Simulations

```bash
# Vehicle dynamics: acceleration, braking, fuel consumption, WLTC cycle
python vehicle_dynamics.py

# CAN bus simulation: ECU messages, DBC generation, ASC log
python can_demo.py

# Traffic signal & queue analysis
python traffic_sim.py

# Traffic flow fundamentals
python traffic_flow.py
```

### Sample Outputs

Running `vehicle_dynamics.py` generates:
- Acceleration curve (0-100 km/h)
- Braking distance vs. initial speed
- Fuel consumption (L/100km) for different vehicle types
- BSFC heatmap (`bsfc_map.png`)
- WLTC cycle speed profile and phase fuel statistics

Running `can_demo.py` generates:
- `simulated_ecu.dbc` — DBC database for 5 ECUs with full signal definitions
- `can_log.asc` — ASC trace log with timestamps, ready for Vector CANoe import
- Terminal output of bus load %, error frame count, and DTC summary

## Screenshots

### BSFC Engine Efficiency Map
![BSFC Map](bsfc_map.png)

*Bilinear interpolation on brake specific fuel consumption contours. Lower BSFC (darker regions) indicates higher engine thermal efficiency.*

## Key Techniques

- **Bilinear interpolation** on empirical BSFC maps for engine efficiency lookup
- **Transient fuel correction**: DFCO (fuel cut during deceleration), acceleration enrichment factor
- **CAN frame encoding**: 11-bit arbitration, Intel/Motorola byte ordering, signal packing within 8-byte payloads
- **Vehicle physics**: Newton's second law with aerodynamic drag ($F_d = \\frac{1}{2} \\rho C_d A v^2$) and rolling resistance

## License

This project is for educational and portfolio demonstration purposes.
