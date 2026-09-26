#!/usr/bin/env python3
"""
Parametric reconstruction of the Halo Electronics HFJ11-x2450E-LxxRL
1x1 tab-down 10/100BASE-TX FastJack integrated RJ45 magjack.

WHY THIS EXISTS
---------------
Halo does not publish a STEP/VRML model, and the KiCad footprint
  Connector_RJ:RJ45_HALO_HFJ11-x2450E-LxxRL_Horizontal
points at
  ${KICAD10_3DMODEL_DIR}/Connector_RJ.3dshapes/RJ45_HALO_HFJ11-x2450E-LxxRL_Horizontal.step
which does not exist: upstream kicad-packages3D ships only three files in
Connector_RJ.3dshapes (Amphenol RJHSE538X, Molex 9346520x, Pulse JK0654219NL).
So this model is reconstructed from the manufacturer drawing.

SOURCE OF DIMENSIONS
  https://www.haloelectronics.com/pdf/fastjack-100baset.pdf
  page 1 part table  -> HFJ11-2450E-LxxRL is "Footprint C"
  page 2 "Mechanical" -> body envelope (dimensions are outlines, so the drawing
                        geometry was scale-calibrated to read the height)

  0.625   [15.88] mm  body width     == KiCad F.Fab X extent (-3.495..12.385)
  0.850max[21.59] mm  body depth     == KiCad F.Fab Y extent (-4.340..17.250)
  0.656   [16.66] mm  overall width including shield lugs
  0.429   [10.90] mm  mating face -> recommended PCB edge
                        (== 17.250 - 6.350, and 6.350 is exactly the Y of the
                         footprint's np_thru_hole locating-peg row)
  ~13.3 mm            body height above PCB, from the front view of the
                        drawing; cross-checked against a real 10/100 magjack
                        (Amphenol RJHSE538X body = 13.46 mm)

Pin and hole data is taken directly from the KiCad footprint pads.

COORDINATE FRAME (KiCad 3D-model convention)
  model_x = footprint_x
  model_y = -footprint_y        (KiCad inverts footprint Y for 3D models)
  model_z = height above the top PCB surface
The footprint origin (0,0) is the J1 datum used in Ethernet.kicad_pcb.
"""

import cadquery as cq
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.TopAbs import TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
import OCP.TopoDS
import OCP.BRepAlgoAPI
import OCP.TopTools

OUT_STEP = "halo_hfj11_x2450e_lxxrl.step"
OUT_WRL = "halo_hfj11_x2450e_lxxrl.wrl"

# ----------------------------------------------------------------- envelope
BODY_X0, BODY_X1 = -3.495, 12.385        # 15.880 wide  (0.625 [15.88])
BODY_Y0, BODY_Y1 = -17.250, 4.340        # 21.590 deep  (0.850max [21.59])
BODY_Z0, BODY_Z1 = 0.000, 13.300          # 13.300 tall
BODY_CX = (BODY_X0 + BODY_X1) / 2.0       # 4.445

SHIELD_X0, SHIELD_X1 = -3.885, 12.775    # 16.660 overall (0.656 [16.66])

PCB_EDGE_Y = BODY_Y0 + 10.900             # -6.350, recommended PCB edge

# RJ45 port opening, proportioned from a real 10/100 magjack
# (Amphenol RJHSE538X: opening 11.61 W x 10.36 H inside a 13.46 tall body)
PORT_W, PORT_H = 11.600, 10.360
PORT_Z0 = 2.550
PORT_Z1 = PORT_Z0 + PORT_H               # 12.910
PORT_X0 = BODY_CX - PORT_W / 2.0          # -1.355
PORT_X1 = BODY_CX + PORT_W / 2.0          # 10.245
PORT_BACK_Y = -1.000                     # cavity floor

PIN_D, LEDPIN_D, SHPOST_D, PEG_D = 0.89, 1.02, 1.60, 3.25
PIN_Z0, PEG_Z0 = -3.100, -2.000

# footprint pad (x, y) -> model (x, -y)
SIGNAL_PADS = [(0.000, 0.000), (1.270, -2.540), (2.540, 0.000), (3.810, -2.540),
               (5.080, 0.000), (6.350, -2.540), (7.620, 0.000), (8.890, -2.540)]
LED_PADS = [(-2.185, 10.410), (0.355, 10.410), (8.535, 10.410), (11.075, 10.410)]
SHIELD_PADS = [(-3.300, 3.300), (12.190, 3.300)]
PEG_PADS = [(-1.270, 6.350), (10.160, 6.350)]

PORT_DEPTH = (PORT_BACK_Y - BODY_Y0) + 0.2


def _box(x0, y0, z0, x1, y1, z1):
    return (cq.Workplane("XY")
            .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .translate((x0, y0, z0)))


def _cyl(d, z0, z1, xc, yc):
    return (cq.Workplane("XY", origin=(xc, yc, z0))
            .circle(d / 2.0)
            .extrude(z1 - z0))


def build():
    # ---- main body
    body = _box(BODY_X0, BODY_Y0, BODY_Z0, BODY_X1, BODY_Y1, BODY_Z1)

    # ---- RJ45 port cavity, open at the mating face
    body = body.cut(_box(PORT_X0, BODY_Y0 - 0.5, PORT_Z0,
                         PORT_X1, PORT_BACK_Y, PORT_Z1))
    # cavity roof step, so the opening narrows toward the front
    body = body.cut(_box(PORT_X0 - 0.4, BODY_Y0 - 0.5, PORT_Z1 - 0.9,
                         PORT_X1 + 0.4, BODY_Y0 + 2.2, PORT_Z1 + 0.5))
    # lower lip that a tab-down jack keeps under the port
    body = body.cut(_box(PORT_X0 - 1.2, BODY_Y0 - 0.5, PORT_Z0 - 1.2,
                         PORT_X1 + 1.2, BODY_Y0 + 1.4, PORT_Z0))

    # ---- lower front recess (connector belly clear of the PCB)
    body = body.cut(_box(BODY_X0 + 0.9, BODY_Y0, BODY_Z0,
                         BODY_X1 - 0.9, BODY_Y0 + 1.0, 1.6))

    parts = [body]

    # ---- two LED apertures on the top face at the LED pin row
    led_y = -LED_PADS[0][1]
    for x0, x1 in ((LED_PADS[0][0], LED_PADS[1][0]),
                   (LED_PADS[2][0], LED_PADS[3][0])):
        parts.append(_box(x0 + 0.45, led_y - 1.30, BODY_Z1 - 0.9,
                          x1 - 0.45, led_y + 1.30, BODY_Z1))

    # ---- shield / ground through-hole posts. Clipped to the body sides:
    # the tail drops flush with the housing wall, the side lugs set the
    # 16.660 overall width (0.656 [16.66]).
    for xc, yc in SHIELD_PADS:
        tail = _cyl(SHPOST_D, PIN_Z0, BODY_Z0 + 6.0, xc, -yc)
        parts.append(tail.intersect(
            _box(BODY_X0, -yc - 2.0, PIN_Z0 - 1.0,
                 BODY_X1, -yc + 2.0, BODY_Z0 + 7.0)))

    # ---- side shield lugs -> 16.660 overall
    for xl, xh in ((SHIELD_X0, BODY_X0), (BODY_X1, SHIELD_X1)):
        parts.append(_box(xl, -7.0, 0.0, xh, 2.0, 3.2))

    # ---- locating pegs -> drop into the footprint np_thru_hole pair
    for xc, yc in PEG_PADS:
        parts.append(_cyl(PEG_D, PEG_Z0, BODY_Z0, xc, -yc))

    # ---- signal and LED pins
    for xc, yc in SIGNAL_PADS:
        parts.append(_cyl(PIN_D, PIN_Z0, 1.0, xc, -yc))
    for xc, yc in LED_PADS:
        parts.append(_cyl(LEDPIN_D, PIN_Z0, 1.0, xc, -yc))

    # ---- 8 gold contact springs reaching into the port cavity
    for xc, _yc in SIGNAL_PADS:
        parts.append(_box(xc - 0.30, PORT_BACK_Y - 1.30, 8.10,
                          xc + 0.30, PORT_BACK_Y + 0.30, 12.30))

    shapes = [p.val() if isinstance(p, cq.Workplane) else p for p in parts]
    solids = []
    for sh in shapes:
        solids.extend(sh.Solids())
    # Fuse to a single solid: kicad-packages3D asks for "a solid single object
    # (a union of parts) for size and loading optimization".
    base = solids[0]
    tools = OCP.TopTools.TopTools_ListOfShape()
    for sh in solids[1:]:
        tools.Append(sh.wrapped)
    args = OCP.TopTools.TopTools_ListOfShape()
    args.Append(base.wrapped)
    op = OCP.BRepAlgoAPI.BRepAlgoAPI_Fuse()
    op.SetArguments(args)
    op.SetTools(tools)
    op.SetRunParallel(True)
    op.SetFuzzyValue(1e-7)
    op.Build()
    if not op.IsDone():
        raise RuntimeError("boolean fuse failed")
    op.SimplifyResult()
    fused = cq.Shape.cast(op.Shape())
    return cq.Workplane("XY").newObject([fused])


def report(shape, label):
    if isinstance(shape, cq.Workplane):
        shape = shape.val()
    bb = Bnd_Box()
    BRepBndLib.Add_s(shape.wrapped, bb, False)
    xm, ym, zm, xM, yM, zM = bb.Get()
    n = 0
    exp = TopExp_Explorer(shape.wrapped, TopAbs_SOLID)
    while exp.More():
        n += 1
        exp.Next()
    gp = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape.wrapped, gp)
    print("[%s] solids=%d volume=%.1f mm^3" % (label, n, gp.Mass()))
    print("        X[%8.3f,%8.3f] W=%7.3f   (want 16.660)"
          % (xm, xM, xM - xm))
    print("        Y[%8.3f,%8.3f] D=%7.3f   (want 21.590)" % (ym, yM, yM - ym))
    print("        Z[%8.3f,%8.3f] H=%7.3f" % (zm, zM, zM - zm))
    print("        mating face Y=%.3f   recommended PCB edge Y=%.3f"
          % (ym, PCB_EDGE_Y))
    print("        overhang past PCB edge = %.3f mm" % (ym - PCB_EDGE_Y))
    return xm, ym, zm, xM, yM, zM


if __name__ == "__main__":
    model = build()
    report(model, "as built")
    cq.exporters.export(model, OUT_STEP)
    # verify by re-importing what was actually written
    back = cq.importers.importStep(OUT_STEP)
    print()
    report(back, "re-imported from %s" % OUT_STEP)
    cq.exporters.export(model, OUT_WRL, exportType="VRML")
    print("\nwrote %s" % OUT_STEP)
    print("wrote %s" % OUT_WRL)
