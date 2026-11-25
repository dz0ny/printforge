"""Airflow of a fan-cooled enclosure, reduced to a side section. Needs numpy.

A model describes its enclosure with an airflow() hook that returns a dict, all lengths in mm:

    {"width": 293,                       # Inside width, across the section.
     "box": (u0, v0, u1, v1),            # The inside of the enclosure in the section, u to the back and v up.
     "axes": ("depth", "height"),
     "room": 25,                         # Room temperature in °C.
     "openings": [{"name", "side", "span": (a, b), "area": mm2, "k": 2.6}],
     "fans": [{"name", "side", "span": (a, b), "flow": m3/h, "pressure": Pa, "out": True}],
     "blocks": [{"name", "box": (u0, v0, u1, v1), "fill": 0..1, "watts": 0, "color": "#rrggbb",
                 "through": {"flow": m3/h, "inlet": side, "outlet": side}}]}

A side is "front" (low u), "back", "bottom" (low v) or "top". The fill of a block is the share of the width it takes.

The solve has three steps, each a model and none a measurement:
1. A balance: the openings are orifices in parallel on one chamber, and each fan follows a straight line from its
   free flow to its highest pressure. This gives the flow through every opening.
2. A flow field in the section for those flows, without inertia: it shows the paths, not jets or eddies.
3. The air temperature carried along that field, with a fixed amount of mixing between neighbours.
"""
import math

RHO, CP = 1.2, 1005.0     # Air: density in kg/m3 and heat capacity in J/(kg K).
K_SHARP = 2.6             # Loss of a sharp-edged opening on its own velocity, a discharge coefficient of 0.62.
MIXING = 2e-4             # Mixing between neighbouring cells in m2/s, ten times the diffusivity of still air.
SIDES = ("front", "back", "bottom", "top")


def balance(openings, fans):
    """Chamber pressure against the room in Pa, and the flow into the chamber through each opening and fan in m3/s."""
    def flows(p):
        passive = [-math.copysign(o["area"] * 1e-6 * math.sqrt(2 * abs(p) / (RHO * o.get("k", K_SHARP))), p) for o in openings]
        forced = []
        for f in fans:
            free, top = f["flow"] / 3600, max(f["pressure"], 1e-9)
            rise = -p if f.get("out", True) else p      # The pressure the fan has to work against.
            q = free * min(1.5, max(0.0, 1 - rise / top))
            forced.append(-q if f.get("out", True) else q)
        return passive, forced

    lo, hi = -1e4, 1e4
    for _ in range(80):
        mid = (lo + hi) / 2
        passive, forced = flows(mid)
        if sum(passive) + sum(forced) > 0:
            lo = mid
        else:
            hi = mid
    p = (lo + hi) / 2
    return (p, *flows(p))


def solve(spec, cell=3.0, mixing=MIXING):
    """Solve the enclosure of an airflow() dict. Returns numbers for the page, the fields row by row from the bottom."""
    import numpy as np

    width = spec["width"] / 1000
    u0, v0, u1, v1 = (float(x) for x in spec["box"])
    nu, nv = max(8, round((u1 - u0) / cell)), max(8, round((v1 - v0) / cell))
    hu, hv = (u1 - u0) / nu / 1000, (v1 - v0) / nv / 1000
    openings, fans, blocks = list(spec.get("openings", [])), list(spec.get("fans", [])), list(spec.get("blocks", []))
    for item in openings + fans:
        assert item["side"] in SIDES, f"{item['name']}: the side must be one of {SIDES}"
    p, passive, forced = balance(openings, fans)
    ports = [dict(o, kind="opening", q=q) for o, q in zip(openings, passive)]
    ports += [dict(f, kind="fan", q=q) for f, q in zip(fans, forced)]

    def cover(lo, hi, origin, step, n):
        """The share of each of n cells along one axis that lies between lo and hi."""
        edges = origin + step * np.arange(n + 1)
        return np.clip((np.minimum(edges[1:], hi) - np.maximum(edges[:-1], lo)) / step, 0, 1)

    # Open share of the width in every cell. Index [j, i]: j up, i to the back.
    blocked = np.zeros((nv, nu))
    for b in blocks:
        bu0, bv0, bu1, bv1 = b["box"]
        b["_cu"], b["_cv"] = cover(bu0, bu1, u0, hu * 1000, nu), cover(bv0, bv1, v0, hv * 1000, nv)
        blocked += b.get("fill", 1.0) * np.outer(b["_cv"], b["_cu"])
    eps = np.clip(1 - blocked, 0, 1)
    eps[eps < 0.05] = 0        # A slit of a few percent of the width carries no air worth following.
    fluid = eps > 0

    def ring(b, side=None):
        """The one-cell layer of air around a block, or on one of its sides, as the open share of each cell."""
        iu, iv = np.nonzero(b["_cu"] > 0.5)[0], np.nonzero(b["_cv"] > 0.5)[0]
        mask = np.zeros((nv, nu), bool)
        if not len(iu) or not len(iv):
            return mask
        i0, i1, j0, j1 = iu[0], iu[-1], iv[0], iv[-1]
        if side in (None, "front") and i0 > 0:
            mask[j0:j1 + 1, i0 - 1] = True
        if side in (None, "back") and i1 < nu - 1:
            mask[j0:j1 + 1, i1 + 1] = True
        if side in (None, "bottom") and j0 > 0:
            mask[j0 - 1, i0:i1 + 1] = True
        if side in (None, "top") and j1 < nv - 1:
            mask[j1 + 1, i0:i1 + 1] = True
        return mask * eps

    def edge(port):
        """Weights of the boundary cells of an opening, summing to one."""
        a, b = port["span"]
        mask = np.zeros((nv, nu))
        if port["side"] in ("front", "back"):
            mask[:, 0 if port["side"] == "front" else nu - 1] = cover(a, b, v0, hv * 1000, nv)
        else:
            mask[0 if port["side"] == "bottom" else nv - 1, :] = cover(a, b, u0, hu * 1000, nu)
        mask *= eps
        assert mask.sum() > 0, f"{port['name']}: the opening lies on a wall that is closed there"
        return mask / mask.sum()

    # Sources of volume in m3/s: the openings and fans, and the devices that move their own air.
    source = np.zeros((nv, nu))
    for port in ports:
        port["_w"] = edge(port)
        source += port["q"] * port["_w"]
    for b in blocks:
        through = b.get("through")
        if through:
            q = through["flow"] / 3600
            sink, out = ring(b, through["inlet"]), ring(b, through["outlet"])
            assert sink.sum() and out.sum(), f"{b['name']}: no air on its inlet or outlet side"
            b["_in"], b["_out"], b["_q"] = sink / sink.sum(), out / out.sum(), q
            source += q * (b["_out"] - b["_in"])

    # Flow without inertia: the flow through a face is its open share times the difference of a potential.
    gu = np.minimum(eps[:, :-1], eps[:, 1:]) * width * hv / hu      # Faces between i and i + 1.
    gv = np.minimum(eps[:-1, :], eps[1:, :]) * width * hu / hv      # Faces between j and j + 1.

    def apply(phi):
        out = np.zeros_like(phi)
        du, dv = gu * (phi[:, :-1] - phi[:, 1:]), gv * (phi[:-1, :] - phi[1:, :])
        out[:, :-1] += du
        out[:, 1:] -= du
        out[:-1, :] += dv
        out[1:, :] -= dv
        return out

    diag = np.zeros((nv, nu))
    diag[:, :-1] += gu
    diag[:, 1:] += gu
    diag[:-1, :] += gv
    diag[1:, :] += gv
    live = diag > 0
    assert abs(source[~live].sum()) < 1e-12, "an opening has no way into the enclosure"
    inv = np.where(live, 1 / np.where(live, diag, 1), 0)
    rhs = np.where(live, source, 0)
    rhs[live] -= rhs[live].mean()              # The flows in and out balance, up to rounding.
    phi, r = np.zeros((nv, nu)), rhs.copy()
    z = inv * r
    d, rz, target = z.copy(), float((r * z).sum()), 1e-11 * float(np.abs(rhs).max() or 1)
    for _ in range(20000):
        if float(np.abs(r).max()) < target:
            break
        ad = apply(d)
        alpha = rz / float((d * ad).sum())
        phi += alpha * d
        r -= alpha * ad
        z = inv * r
        rz, old = float((r * z).sum()), rz
        d = z + rz / old * d
    fu, fv = gu * (phi[:, :-1] - phi[:, 1:]), gv * (phi[:-1, :] - phi[1:, :])   # m3/s to the back and up.

    # Temperature above the room. Each cell takes the air that flows in, mixes a little with its neighbours and
    # adds the heat released in it. A device that moves its own air puts its heat into its outlet.
    heat = np.zeros((nv, nu))
    for b in blocks:
        if b.get("watts") and not b.get("through"):
            cells = np.maximum(ring(b), (np.outer(b["_cv"], b["_cu"]) > 0.5) * eps)
            assert cells.sum(), f"{b['name']}: no air around it to take its heat"
            heat += b["watts"] / (RHO * CP) * cells / cells.sum()
    mu, mv = mixing * gu, mixing * gv
    in_w, in_e = np.zeros((nv, nu)), np.zeros((nv, nu))     # Flow into a cell from the cell in front and behind.
    in_s, in_n = np.zeros((nv, nu)), np.zeros((nv, nu))     # And from below and above.
    in_w[:, 1:], in_e[:, :-1] = np.maximum(fu, 0) + mu, np.maximum(-fu, 0) + mu
    in_s[1:, :], in_n[:-1, :] = np.maximum(fv, 0) + mv, np.maximum(-fv, 0) + mv
    room_in = sum(max(port["q"], 0) * port["_w"] for port in ports) if ports else 0
    total = in_w + in_e + in_s + in_n + room_in
    for b in blocks:
        if b.get("through"):
            total = total + b["_q"] * b["_out"]
    safe = np.where(total > 0, total, 1)
    theta = np.zeros((nv, nu))
    for step in range(60000):
        gain = heat.copy()
        gain[:, 1:] += in_w[:, 1:] * theta[:, :-1]
        gain[:, :-1] += in_e[:, :-1] * theta[:, 1:]
        gain[1:, :] += in_s[1:, :] * theta[:-1, :]
        gain[:-1, :] += in_n[:-1, :] * theta[1:, :]
        for b in blocks:
            if b.get("through"):
                b["_tin"] = float((theta * b["_in"]).sum())
                b["_tout"] = b["_tin"] + b.get("watts", 0) / (RHO * CP * b["_q"])
                gain += b["_q"] * b["_out"] * b["_tout"]
        new = np.where(total > 0, gain / safe, 0)
        change = float(np.abs(new - theta).max())
        theta = new
        if step % 50 == 0 and change < 1e-5:
            break

    # Speed of the air in the open part of each cell, at the cell centers.
    cu, cv = np.zeros((nv, nu)), np.zeros((nv, nu))
    cu[:, :-1] += fu / 2
    cu[:, 1:] += fu / 2
    cv[:-1, :] += fv / 2
    cv[1:, :] += fv / 2
    for port in ports:                                      # The boundary faces carry the opening's own flow.
        sign = {"front": 1, "back": -1, "bottom": 1, "top": -1}[port["side"]]
        (cu if port["side"] in ("front", "back") else cv)[...] += sign * port["q"] * port["_w"] / 2
    open_area = np.where(fluid, eps, 1) * width
    vel_u, vel_v = cu / (open_area * hv), cv / (open_area * hu)

    watts = sum(b.get("watts", 0) for b in blocks)
    flow_in = sum(max(port["q"], 0) for port in ports)
    flow_out = -sum(min(port["q"], 0) for port in ports)
    carried = sum(-port["q"] * float((theta * port["_w"]).sum()) for port in ports if port["q"] < 0) * RHO * CP
    free = sum(f["flow"] for f in fans) / 3600
    volume = float(eps.sum()) * hu * hv * width
    room = float(spec.get("room", 25))

    def port_row(port):
        t = float((theta * port["_w"]).sum()) if port["q"] < 0 else 0.0
        return {"name": port["name"], "kind": port["kind"], "side": port["side"], "span": list(port["span"]),
                "m3h": round(port["q"] * 3600, 2), "share": round(abs(port["q"]) / max(flow_in, 1e-12), 4),
                "speed": round(abs(port["q"]) / (port["area"] * 1e-6), 2) if port.get("area") else None,
                "area": port.get("area"), "rise": round(t, 2)}

    def block_row(b):
        around = ring(b) > 0
        row = {"name": b["name"], "box": [float(x) for x in b["box"]], "fill": b.get("fill", 1.0),
               "watts": b.get("watts", 0), "color": b.get("color"), "label": bool(b.get("watts") or b.get("label")),
               "around": round(float(theta[around].mean()), 2) if around.any() else None}
        if b.get("through"):
            row.update(through=dict(b["through"]), intake=round(b["_tin"], 2), exhaust=round(b["_tout"], 2))
        return row

    return {
        "axes": list(spec.get("axes", ("depth", "height"))), "box": [u0, v0, u1, v1], "width": spec["width"],
        "nu": nu, "nv": nv, "room": room,
        "pressure": round(p, 3), "flow_m3h": round(flow_in * 3600, 2), "free_m3h": round(free * 3600, 2),
        "watts": watts, "rise": round(watts / (RHO * CP * flow_in), 2) if flow_in > 0 else None,
        "changes_per_min": round(flow_in / volume * 60, 1) if volume > 0 else None,
        "checks": {"in_m3h": round(flow_in * 3600, 3), "out_m3h": round(flow_out * 3600, 3),
                   "heat_out_w": round(carried, 2), "heat_in_w": round(watts, 2)},
        "ports": [port_row(port) for port in ports],
        "blocks": [block_row(b) for b in blocks],
        "max_rise": round(float(theta[fluid].max()), 2) if fluid.any() else 0,
        "max_speed": round(float(np.hypot(vel_u, vel_v)[fluid].max()), 3) if fluid.any() else 0,
        # The top of the speed scale: a few cells in narrow slits are much faster than the rest.
        "scale_speed": round(float(np.percentile(np.hypot(vel_u, vel_v)[fluid], 99)), 3) if fluid.any() else 0,
        "eps": [round(float(x), 3) for x in eps.ravel()],
        "vu": [round(float(x), 4) for x in vel_u.ravel()],
        "vv": [round(float(x), 4) for x in vel_v.ravel()],
        "theta": [round(float(x), 3) for x in theta.ravel()],
        "notes": list(spec.get("notes", [])),
    }
