"""Terrain generation + A* rover routing (illustrative lunar base grid)."""
import heapq, math
import numpy as np
import cv2

GRID_W, GRID_H = 64, 42          # cells
CELL_M = 10                      # 1 cell = 10 m (illustrative)

# Facility positions (grid cells). Layout follows the idealization reference
# image: habitat top-left, solar top-right, comms left, greenhouse bottom-right,
# landing zone bottom-centre-left, resource zone far right.
FACILITIES = {
    "Landing Zone":          dict(pos=(14, 35), key="landing",       sprite=None),
    "Lunar Habitat":         dict(pos=(17, 12), key="habitat",       sprite="habitat"),
    "Agricultural Lab":      dict(pos=(49, 30), key="greenhouse",    sprite="greenhouse"),
    "Solar Power Station":   dict(pos=(48, 9),  key="solar",         sprite="solar"),
    "Communication Station": dict(pos=(6, 24),  key="communication", sprite="communication"),
    "Resource Zone":         dict(pos=(58, 19), key="resource",      sprite=None),
}

def make_terrain(seed=7):
    rng = np.random.default_rng(seed)
    W, H = GRID_W, GRID_H
    craters = []
    keep_clear = [f["pos"] for f in FACILITIES.values()]
    tries = 0
    while len(craters) < 15 and tries < 800:
        tries += 1
        cx, cy = rng.uniform(3, W - 3), rng.uniform(3, H - 3)
        r = rng.uniform(1.6, 3.6)
        if any(math.hypot(cx - x, cy - y) < r + 6.5 for x, y in keep_clear):
            continue
        if any(math.hypot(cx - c[0], cy - c[1]) < r + c[2] + 1 for c in craters):
            continue
        craters.append((float(cx), float(cy), float(r)))
    yy, xx = np.mgrid[0:H, 0:W]
    rough = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 2.5)
    rough = (rough - rough.min()) / (rough.max() - rough.min())          # 0..1
    blocked = np.zeros((H, W), bool)
    near = np.zeros((H, W), np.float32)
    for cx, cy, r in craters:
        d = np.hypot(xx - cx, yy - cy)
        blocked |= d <= r + 0.6
        near = np.maximum(near, np.clip(1 - (d - r) / 3.0, 0, 1))        # rim proximity
    return craters, rough, blocked, near

def _astar(start, goal, cost, blocked):
    H, W = blocked.shape
    sx, sy = start; gx, gy = goal
    openq = [(0, 0, (sx, sy))]
    g = {(sx, sy): 0.0}; came = {}
    nbrs = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
    while openq:
        _, gc, cur = heapq.heappop(openq)
        if cur == (gx, gy):
            p = [cur]
            while cur in came:
                cur = came[cur]; p.append(cur)
            return p[::-1]
        if gc > g.get(cur, 1e9): continue
        for dx, dy in nbrs:
            nx, ny = cur[0] + dx, cur[1] + dy
            if not (0 <= nx < W and 0 <= ny < H) or blocked[ny, nx]: continue
            if dx and dy and (blocked[cur[1], nx] or blocked[ny, cur[0]]): continue
            step = math.hypot(dx, dy) * (1 + cost[ny, nx])
            ng = g[cur] + step
            if ng < g.get((nx, ny), 1e9):
                g[(nx, ny)] = ng; came[(nx, ny)] = cur
                h = math.hypot(gx - nx, gy - ny)
                heapq.heappush(openq, (ng + h, ng, (nx, ny)))
    return None

def _rdp(pts, eps):
    if len(pts) < 3: return pts
    a, b = np.array(pts[0]), np.array(pts[-1])
    ab = b - a; n = np.hypot(*ab) or 1e-9
    d = [abs(ab[0]*(p[1]-a[1]) - ab[1]*(p[0]-a[0])) / n for p in pts[1:-1]]
    i = int(np.argmax(d))
    if d[i] > eps:
        return _rdp(pts[:i+2], eps)[:-1] + _rdp(pts[i+1:], eps)
    return [pts[0], pts[-1]]

def bearing(p, q):
    """Compass bearing (deg, 0=N, clockwise). Grid x = east, y = south."""
    dx, dy = q[0] - p[0], -(q[1] - p[1])
    return (math.degrees(math.atan2(dx, dy)) + 360) % 360

def compass(b):
    names = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return names[int((b + 11.25) // 22.5) % 16]

def build_routes():
    craters, rough, blocked, near = make_terrain()
    cost = 1.2 * rough + 2.5 * near                       # terrain-risk cost layer
    names = list(FACILITIES)
    routes = {}
    for a in names:
        for b in names:
            if a == b: continue
            sa, sb = FACILITIES[a]["pos"], FACILITIES[b]["pos"]
            path = _astar(sa, sb, cost, blocked)
            arr = np.array(path, float)
            k = 5                                          # smooth, keep endpoints
            pad = np.vstack([np.repeat(arr[:1], k, 0), arr, np.repeat(arr[-1:], k, 0)])
            sm = np.vstack([pad[i:i+2*k+1].mean(0) for i in range(len(arr))])
            sm[0], sm[-1] = arr[0], arr[-1]
            wp = _rdp([tuple(map(float, p)) for p in arr], 1.6)
            seg = []
            for i in range(len(wp) - 1):
                d = math.dist(wp[i], wp[i+1]) * CELL_M; br = bearing(wp[i], wp[i+1])
                seg.append(dict(frm=[round(wp[i][0]),round(wp[i][1])], to=[round(wp[i+1][0]),round(wp[i+1][1])],
                                dist=round(d), bearing=round(br), dir=compass(br)))
            total = float(sum(math.dist(sm[i], sm[i+1]) for i in range(len(sm)-1)) * CELL_M)
            risk = float(np.mean([cost[int(round(y)), int(round(x))] for x, y in arr]))
            level = "LOW" if risk < 0.9 else "MODERATE" if risk < 1.5 else "ELEVATED"
            ob = bearing(sa, sb)
            routes[f"{a}|{b}"] = dict(path=[[round(float(x),2), round(float(y),2)] for x, y in sm[::2].tolist()] + [list(map(float, sm[-1]))],
                                      dist=round(total), straight=round(math.dist(sa, sb) * CELL_M),
                                      bearing=round(ob), dir=compass(ob), risk=level, riskScore=round(risk, 2),
                                      waypoints=seg)
    return dict(craters=[[round(a,2),round(b,2),round(c,2)] for a,b,c in craters], routes=routes), rough

def render_terrain(rough, craters, scale=16, seed=3):
    """Top-down regolith texture with shaded craters (illustrative, not real data)."""
    rng = np.random.default_rng(seed)
    W, H = GRID_W * scale, GRID_H * scale
    base = cv2.resize(rough, (W, H), interpolation=cv2.INTER_CUBIC)
    noise = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 1.2)
    fine = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 6)
    grain = rng.random((H, W)).astype(np.float32)
    img = 70 + 34 * base + 34 * (fine - .5) + 22 * (noise - .5) + 20 * (grain - .5)
    rocks = (rng.random((H, W)) > 0.9985).astype(np.float32)
    img += 60 * cv2.GaussianBlur(rocks, (0, 0), 1.6) * 6
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    for cx, cy, r in craters:
        px, py, pr = (cx + .5) * scale, (cy + .5) * scale, r * scale
        d = np.hypot(xx - px, yy - py)
        bowl = d < pr
        shade = np.zeros_like(img)
        shade[bowl] = -16 + 30 * ((xx[bowl] - px) / pr + (yy[bowl] - py) / pr) / 2   # lit from lower-right
        rim = np.exp(-((d - pr) ** 2) / (2 * (pr * 0.10) ** 2))
        img += shade + 30 * rim * (1 - ((xx - px) / (d + 1e-3) * -.7 + (yy - py) / (d + 1e-3) * -.7) * .4)
    img = np.clip(img, 0, 255).astype(np.uint8)
    rgb = cv2.merge([np.clip(img*0.92,0,255).astype(np.uint8), np.clip(img*0.97,0,255).astype(np.uint8), np.clip(img*1.06,0,255).astype(np.uint8)])
    rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
    return buf.tobytes()
