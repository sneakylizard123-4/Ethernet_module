# W5500 Ethernet Module

RJ45-to-SPI Ethernet breakout built around the W5500

This board turns a 4-wire SPI bus into a working 10/100 Ethernet port.
A WIZnet W5500 TCP/IP controller talks to a RJ45 jack over SPI, so the microcontroller never has to touch a packet.
The Ethernet PHY and the isolation transformer live inside the connector, so there is no line driver, and no magnetics to lay out.

The design follows WIZnet's reference design.

![Assembled 3D render](images/pcb/assembled-3d.png)

## Custom Features

- Four layers, with a solid GND plane on and a solid +3.3V plane.
- Split analog/digital supply through a ferrite bead
- Two on-board status LEDs driven from the W5500's SPDLED and DUPLED outputs, plus the connector's own front-panel pair fed by LINKLED and ACTLED.
- A populated 0 ohm four-element array (RN1) in the differential pairs.
- It is there for damping, not configuration, and it gives a place to add damping resistors later without respinning the board.
- Two 3.25 mm NPTH locating pegs land on the connector, so the jack self-aligns to the board outline during assembly.

## How It Works

| Block | Part | Role |
|---|---|---|
| Host interface | J2 (1x08 header) | 3.3V supply in, SPI, chip select, interrupt, reset |
| Ethernet controller | U1 (W5500, LQFP-48) | TCP/IP offload, MAC, 10/100 PHY |
| Ethernet magnetics | J1 (HFJ11-2450E-L11RL) | 1:1 transformer + common-mode choke + 2 front-panel LEDs |
| TX termination | R4, R6 (49.9 ohm) | Source-terminates each leg of the transmit pair |
| RX isolation | C15, C17 (6.8 nF), R5, R7 (49.9 ohm) | AC-couples the receive pair and matches it to the receive center tap |
| Center-tap bias | R8 (10 ohm), C16 (22 nF), C14 (10 nF) | Sets the common-mode DC bias on the receive pair |
| Pair damping | RN1 (0 ohm x4) | Damping/placeholder elements in all four pair legs |
| Clock | X1 (25 MHz), C9, C12 (18 pF) | W5500 X+ / X- oscillator |
| Analog decoupling | C2, C3 (10 uF), C7 (4.7 uF), C13 (0.1 uF), C5 (10 nF) | Bulk, TOCAP, AVDD HF, and internal 1.2V LDO output |
| Reference resistor | R1 (12.4k, 1%) | W5500 EXRES1, sets internal reference |
| Status | D1, D2 + R2, R3 (1k); R9, R10 (330) | SPDLED/DUPLED on the board, ACTLED/LINKLED at the jack |

### Power Tree

The board has no regulator. It expects a clean 3.3 V on pin 2 of J2 and that is the whole supply.

```
J2.2  +3.3V  (supply input from host)
 |
 +-- FB1  ferrite bead 120R @ 100MHz
 |     |
 |     +-- +3.3VA
 |           +-- U1 AVDD  pins 4 8 11 15 17 21   (W5500 analog supply)
 |           +-- R4 R6 R8  (TX termination bias, center-tap bias)
 |           +-- C3 10uF  (analog bulk)
 |
 +-- +3.3V
       +-- U1 VDD  pin 28                        (W5500 digital supply)
       +-- C2 10uF  (digital bulk)
       +-- J1 pins 9 11  (jack LED common anodes)
       +-- R2 R3 1k   (on-board status LEDs)

GND: J2.1, U1 AGND pins 3 9 14 16 19 48, U1 GND pin 29,
     J1 shield posts, all capacitor returns
```

- No PoE on this board
- No level shifting, 3.3v mcu only
- No onboard regulator

## PCB Design

- 50.0 x 21.4 mm, 4 layers, 1.6 mm FR-4.
- length matched traces

![Top copper](images/pcb/01-top-copper.png)

![Internal planes](images/pcb/04-internal-planes.png)

## Firmware

W5500 doesn't need firmware

## Usage

Wire the host to the 8-pin header and the module appears on the network.

| Pin | Function | Direction (host view) | Notes |
|---|---|---|---|
| 1 | GND | - | Board ground, tied to the jack shield |
| 2 | +3.3V | in | Supply input. This board does not regulate. |
| 3 | SCS | out | Chip select, active low |
| 4 | SCLK | out | SPI clock |
| 5 | MISO | in | W5500 -> host |
| 6 | MOSI | out | Host -> W5500 |
| 7 | INT | in | Interrupt, active low |
| 8 | RST | out | Reset, active low |

`LINKLED` and `ACTLED` and are intentionally dim because they are fed through 1 kohm.

![Schematic: RJ45 sheet](images/schematic/02-rj45.png)

## BOM (Bill of Materials)

Full BOM: [BOM.csv](BOM.csv)

| Item | Cost |
|---|---|
| J1 RJ45 magjack (HFJ11-2450E-L11RL, DigiKey) | $5.23 |
| U1 W5500 LQFP-48 (LCSC) | $2.85 |
| X1 25 MHz crystal (LCSC) | $0.10 |
| All remaining parts: 17 capacitors, 2 LEDs, the ferrite bead, 10 resistors, RN1, X1 and the J2 header (LCSC) | $0.32 |
| **Total parts, 1 board** | **$8.49** |
| **Total parts, 5 boards** | **$42.45** |
| PCB, 5x 4-layer FR-4 50 x 21.4 mm (estimate) | ~$10.00 |
| **Grand total, 5 boards** | **~$52.45** |

## Production

- All production files are in `kicad/production/`
- PCB: 50.0 x 21.4 mm, 4-layer, 1.6 mm FR-4, lead-free HASL finish, green soldermask. Gerbers are in `kicad/production/Ethernet.zip`
- Assembly: 33 SMD parts on the top side plus J1 and J2 through-hole. Everything is on one side, so this is a single-pass reflow followed by hand-soldering the connector and the header.

## Repository Structure

```
Ethernet/
|-- BOM.csv                     supplier links and totals
|-- JOURNAL.md                  build log
|-- README.md
|-- .gitignore
|-- images/
|   |-- pcb/
|   |   |-- assembled-3d.png   STEP-derived 3D render
|   |   |-- 01-top-copper.png
|   |   |-- 02-top-silkscreen.png
|   |   |-- 03-bottom.png
|   |   `-- 04-internal-planes.png
|   `-- schematic/
|       |-- 00-top-level.png / .svg
|       |-- 01-power.png       / .svg
|       |-- 02-rj45.png        / .svg
|       |-- 03-connector.png   / .svg
|       `-- 04-w5500.png       / .svg
`-- kicad/
    |-- Ethernet.kicad_pro
    |-- Ethernet.kicad_sch     root sheet
    |-- power.kicad_sch        FB1 rail split
    |-- rj45.kicad_sch         J1 and the magnetics network
    |-- connector.kicad_sch    J2
    |-- w5500.kicad_sch         U1, X1, RN1, LEDs
    |-- Ethernet.kicad_pcb
    |-- 3dparts/
    |   |-- halo_hfj11_x2450e_lxxrl.step   reconstructed RJ45 model
    |   |-- halo_hfj11_x2450e_lxxrl.wrl    VRML fallback
    |   `-- build_halo_hfj11_model.py      parametric source for the model
    `-- production/
        |-- Ethernet.step      STEP AP214 of the populated board
        |-- Ethernet.zip       Gerber + Excellon + drill map, zipped
        |-- netlist.ipc        IPC-D-356 netlist
        |-- positions.csv      pick-and-place
        |-- designators.csv
        |-- bom.csv
        |-- ipc2581/
        |   `-- Ethernet.xml   IPC-2581 export
        `-- gerbers/           Gerber + Excellon + drill map
```

## Known Issues

- The connector sits 6.1 mm further inboard than Halo recommends.
- No mounting holes
- No silkscreen
- The on-board LEDs are dim

## Credits & Inspiration

- WIZnet W5500 "RJ45 with Magnetics" reference design. This board is an implementation of it, not an original Ethernet front end. The W5500 datasheet and hardware design guide set the termination and center-tap values.
- HALO Electronics for the `HFJ11-2450E-L11RL` FastJack, and for publishing a mechanical drawing detailed enough to build a 3D model from.
- JLCPCB for the parts library this was designed against, and for a 4-layer stackup at this price.

## License

Released under [CERN-OHL-S-2.0](https://cern.ch/c/ohl-s/2.0) for the hardware

The W5500 and the FastJack are parts from other people. This repository covers the board design and the reconstructed 3D model only.
