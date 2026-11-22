import base64
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from modules.infrastructure import LAYOUT, compose
from modules.navigation import CELL_M, FACILITIES, build_routes, render_terrain
from modules.rover_sim import FAC_META, build_html
VEDAS_API_KEY = st.secrets["VEDAS_API_KEY"]

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================
st.set_page_config(page_title="LUNARSET | Mission Control", page_icon="🌕", layout="wide")

BASE_DIR = Path(__file__).parent
MAP_PATH = BASE_DIR / "assets" / "lunarset_lunar_map_marked.png.jpeg"
SPRITE_DIR = BASE_DIR / "assets" / "sprites"
SPRITES = ["habitat", "greenhouse", "solar", "communication"]

# =========================================================
# 2. THEME
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Inter', sans-serif; }
.stApp {
    background: radial-gradient(1200px 600px at 80% -10%, #14264a 0%, rgba(8,13,25,0) 60%), #080D19;
    color: #F2F4F8;
}
section[data-testid="stSidebar"] { background: linear-gradient(180deg,#0f1a30,#0a1324); border-right: 1px solid #22314d; }
h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: #F4B855 !important; letter-spacing: .04em; }
p, label, li { color: #DCE2EE; }
.block-container { padding-top: 1.6rem; max-width: 1500px; }
div.stButton > button, div.stDownloadButton > button {
    background: linear-gradient(135deg,#F4B855,#D99A32); color:#101827; border-radius:10px; border:none;
    font-weight:700; letter-spacing:.04em; padding:.55rem 1.1rem;
}
div.stButton > button:hover, div.stDownloadButton > button:hover { filter:brightness(1.1); transform:translateY(-1px); }
.hero { text-align:center; padding:10px 0 18px; }
.hero .logo { font-family:'Orbitron',sans-serif; font-weight:900; font-size:3.1rem; letter-spacing:.35em; padding-left:.35em;
    background:linear-gradient(90deg,#F4B855,#ffe3a6,#F4B855); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.hero .tag { color:#9FB0CC; letter-spacing:.18em; font-size:.8rem; text-transform:uppercase; }
.pill { display:inline-block; padding:3px 12px; border:1px solid #34445D; border-radius:999px; font-size:.72rem; color:#AAB7CC; margin:0 4px; background:#0d1830; }
.pill b { color:#F4B855; }
.metric-card { background:linear-gradient(160deg,#16294a,#101b30); padding:18px; border-radius:14px; border:1px solid #2d4064; height:100%; }
.metric-card h3 { margin:0 0 4px 0; font-size:1.6rem; }
.metric-card b { color:#fff; }
.metric-card p { color:#aab7cc; font-size:.9rem; margin:.4rem 0 0; }
.fac-card { background:#101b30; border:1px solid #2d4064; border-radius:14px; padding:10px; text-align:center; }
.fac-card img { width:100%; height:150px; object-fit:contain; background:radial-gradient(circle,#1b2c4d,#0b1426); border-radius:10px; }
.fac-card b { color:#F4B855; display:block; margin-top:8px; font-size:.85rem; letter-spacing:.06em; }
.fac-card span { color:#9FB0CC; font-size:.75rem; }
.stepper { display:flex; gap:8px; margin:6px 0 14px; }
.step { flex:1; padding:8px 12px; border-radius:10px; border:1px solid #2d4064; background:#0d1830; font-size:.78rem; color:#8fa0bb; letter-spacing:.06em; }
.step.on { border-color:#F4B855; color:#F4B855; background:#241d0f; }
.step.done { color:#56e39f; border-color:#1f6b4a; }
div[data-testid="stExpander"] { border:1px solid #2d4064; border-radius:12px; background:#0f1a2f; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 3. HELPERS
# =========================================================
def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()

@st.cache_data(show_spinner=False)
def load_sprites_b64():
    return {k: b64(SPRITE_DIR / f"{k}.png") for k in SPRITES if (SPRITE_DIR / f"{k}.png").exists()}

@st.cache_data(show_spinner=False)
def load_nav():
    nav, rough = build_routes()
    terrain = base64.b64encode(render_terrain(rough, nav["craters"])).decode()
    return nav, terrain

@st.cache_data(show_spinner=False)
def demo_terrain_png():
    nav, rough = build_routes()
    jpg = render_terrain(rough, nav["craters"], scale=24)
    return cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)

def stepper(active: int):
    names = ["01 · PRE-LANDING", "02 · LANDING", "03 · POST-LANDING"]
    html = "".join(
        f"<div class='step {'on' if i == active else 'done' if i < active else ''}'>{n}</div>"
        for i, n in enumerate(names))
    st.markdown(f"<div class='stepper'>{html}</div>", unsafe_allow_html=True)

# =========================================================
# 4. SIDEBAR
# =========================================================
st.sidebar.markdown("# 🌕 LUNARSET")
st.sidebar.caption("LUNAR MISSION CONTROL")
st.sidebar.divider()
phase = st.sidebar.radio("MISSION PHASE", ["Mission Overview", "01 | Pre-Landing", "02 | Landing", "03 | Post-Landing"])
st.sidebar.divider()
st.sidebar.markdown("### MISSION PARAMETERS")
st.sidebar.write("**Target body:** 🌕 Moon")
st.sidebar.write("**Target region:** Lunar South Pole")
st.sidebar.write("**Mission status:** Research Prototype")
st.sidebar.write("**Data basis:** Illustrative / conceptual")

# =========================================================
# 5. HEADER
# =========================================================
st.markdown("""
<div class='hero'>
  <div class='logo'>LUNARSET</div>
  <div class='tag'>From Lunar Data to an Intelligent Lunar Base</div>
  <div style='margin-top:10px'><span class='pill'>REGION <b>SOUTH POLE</b></span><span class='pill'>MODE <b>DEMONSTRATION</b></span><span class='pill'>DATA <b>CONCEPTUAL</b></span></div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 6. PRE-LANDING IMAGE PROCESSING (unchanged logic)
# =========================================================
def generate_candidate_image(uploaded_video, requested_points):
    temp_path = None
    cap = None
    try:
        suffix = Path(uploaded_video.name).suffix or ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(uploaded_video.getvalue())
            temp_path = f.name
        cap = cv2.VideoCapture(temp_path)
        if not cap.isOpened():
            raise ValueError("Could not open video. Try MP4 format.")
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            raise ValueError("No readable video frames found.")
        frame_number = total_frames // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            success, frame = cap.read()
        if not success:
            raise ValueError("Could not extract video frame.")
        height, width = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners = cv2.goodFeaturesToTrack(gray, maxCorners=requested_points, qualityLevel=0.015,
                                          minDistance=max(20, int(min(width, height) * 0.12)), blockSize=7)
        points = []
        if corners is not None:
            points = [(int(round(p[0][0])), int(round(p[0][1]))) for p in corners]
        fallback = [(int(width * 0.30), int(height * 0.45)), (int(width * 0.55), int(height * 0.55)),
                    (int(width * 0.75), int(height * 0.38)), (int(width * 0.40), int(height * 0.70)),
                    (int(width * 0.80), int(height * 0.65))]
        while len(points) < requested_points:
            points.append(fallback[len(points)])
        points = points[:requested_points]
        colors = [(70, 170, 255), (70, 235, 255), (100, 255, 130), (220, 140, 255), (255, 190, 90)]
        annotated = frame.copy()
        for i, (x, y) in enumerate(points):
            color = colors[i % len(colors)]
            cv2.circle(annotated, (x, y), 13, color, -1)
            cv2.circle(annotated, (x, y), 23, color, 2)
            cv2.putText(annotated, f"landing location {i + 1}", (min(x + 18, max(5, width - 190)), max(28, y - 18)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2, cv2.LINE_AA)
        cv2.rectangle(annotated, (0, 0), (width, 42), (8, 13, 25), -1)
        cv2.putText(annotated, f"LUNARSET | FRAME {frame_number} | VISUAL CANDIDATES", (12, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.58, (245, 190, 85), 2, cv2.LINE_AA)
        success, encoded = cv2.imencode(".png", annotated)
        if not success:
            raise ValueError("PNG generation failed.")
        return encoded.tobytes(), frame_number, total_frames, points
    finally:
        if cap is not None:
            cap.release()
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

# =========================================================
# 7. MISSION OVERVIEW
# =========================================================
if phase == "Mission Overview":
    st.title("Lunar Mission Overview")
    st.write("LUNARSET is an integrated lunar mission-planning prototype focused on the lunar south pole. "
             "It walks a mission from orbital reconnaissance, through base deployment, to rover operations.")

    c1, c2, c3 = st.columns(3)
    cards = [("01", "Pre-Landing", "Terrain intelligence and candidate landing-site assessment"),
             ("02", "Landing", "Infrastructure models placed on your lunar terrain photograph"),
             ("03", "Post-Landing", "Click the rover and watch it navigate A*-planned routes between facilities")]
    for col, (n, t, d) in zip((c1, c2, c3), cards):
        col.markdown(f"<div class='metric-card'><h3>{n}</h3><b>{t}</b><p>{d}</p></div>", unsafe_allow_html=True)

    st.divider()
    st.subheader("Base Infrastructure Assets")
    sp = load_sprites_b64()
    items = [("habitat", "LUNAR HABITAT", "Crew living modules, airlock, tunnels"),
             ("greenhouse", "AGRICULTURAL LAB", "Pressurised hydroponic greenhouse"),
             ("solar", "SOLAR POWER STATION", "Arrays, batteries, distribution unit"),
             ("communication", "COMMUNICATION STATION", "High-gain dish, mast, relay")]
    cols = st.columns(4)
    for col, (k, t, d) in zip(cols, items):
        if k in sp:
            col.markdown(f"<div class='fac-card'><img src='data:image/png;base64,{sp[k]}'><b>{t}</b><span>{d}</span></div>",
                         unsafe_allow_html=True)
    st.caption("Conceptual engineering assets generated with Meshy AI — not validated flight hardware.")

    st.divider()
    st.subheader("Lunar South Pole Reference Map")
    if MAP_PATH.exists():
        st.image(str(MAP_PATH), width="stretch")
    else:
        st.info("Place lunarset_lunar_map_marked.png.jpeg inside the assets folder.")

# =========================================================
# 8. PRE-LANDING
# =========================================================
elif phase == "01 | Pre-Landing":
    stepper(0)
    st.title("01 | Pre-Landing")
    st.subheader("Orbital Reconnaissance & Site Selection")
    st.write("Upload a lunar observation video. LUNARSET extracts a representative frame and marks visually distinctive points.")

    left, right = st.columns([1, 1])
    with left:
        uploaded_video = st.file_uploader("Upload lunar observation video", type=["mp4", "mov", "avi"], key="prelanding_video")
        count = st.slider("Number of visual candidate markers", 1, 5, 3)
        if uploaded_video is not None:
            st.video(uploaded_video)
            if st.button("GENERATE ANNOTATED LUNAR IMAGE"):
                with st.spinner("Extracting frame and detecting image features..."):
                    try:
                        image_bytes, frame_no, total, points = generate_candidate_image(uploaded_video, count)
                        st.session_state.update(lunarset_image=image_bytes, lunarset_frame=frame_no,
                                                lunarset_total=total, lunarset_points=points)
                    except Exception as e:
                        st.error(f"Image processing failed: {e}")
    with right:
        if "lunarset_image" in st.session_state:
            st.image(st.session_state["lunarset_image"], caption="Extracted frame with visual candidate markers", width="stretch")
            st.success(f"Image extracted from frame {st.session_state['lunarset_frame']} of {st.session_state['lunarset_total']}.")
            for i, (x, y) in enumerate(st.session_state["lunarset_points"], 1):
                st.write(f"Candidate {i}: X = {x}, Y = {y} pixels")
            st.download_button("DOWNLOAD ANNOTATED IMAGE", data=st.session_state["lunarset_image"],
                               file_name="LUNARSET_Landing_Candidates.png", mime="image/png")
            st.warning("These markers are visual image features, not verified safe landing sites or geographic coordinates.")
        else:
            st.info("The annotated frame will appear here after processing.")

    st.divider()
    st.subheader("Lunar Surface Reference Map")
    if MAP_PATH.exists():
        st.image(str(MAP_PATH), width="stretch")
    st.caption("Verify map source, projection and coordinate system before scientific analysis.")

    st.subheader("Candidate Site Assessment")
    for site in ["Candidate Alpha", "Candidate Beta", "Candidate Gamma"]:
        with st.expander(site):
            st.write("Candidate for further terrain, slope, elevation and hazard assessment.")

# =========================================================
# 9. LANDING: INFRASTRUCTURE MODELS PLACED ON THE UPLOADED PHOTO
# =========================================================
elif phase == "02 | Landing":
    stepper(1)
    st.title("02 | Landing")
    st.subheader("Landing Assessment & Base Deployment")
    st.write("Upload a lunar surface photograph. LUNARSET places the habitat, agricultural lab, solar station and "
             "communication station models on it, together with the landing and resource-investigation zones.")

    if not all((SPRITE_DIR / f"{k}.png").exists() for k in SPRITES):
        st.error("Infrastructure sprites not found in assets/sprites/. Copy the assets folder next to app.py.")
        st.stop()

    up_col, opt_col = st.columns([3, 2])
    with up_col:
        terrain_file = st.file_uploader("Upload lunar terrain image", type=["png", "jpg", "jpeg"], key="landing_data")
        use_demo = st.checkbox("No photo handy? Use built-in demonstration terrain", value=False)
    with opt_col:
        shown = st.multiselect("Facilities to place", list(LAYOUT), default=list(LAYOUT))
        scale = st.slider("Model size", 0.6, 1.5, 1.0, 0.05)
        o1, o2, o3 = st.columns(3)
        snap = o1.toggle("Smooth-ground snap", True, help="Nudges models toward visually smoother image patches (texture proxy only).")
        labels = o2.toggle("Labels", True)
        links = o3.toggle("Links", True)

    terrain = None
    if terrain_file is not None:
        terrain = cv2.imdecode(np.frombuffer(terrain_file.getvalue(), np.uint8), cv2.IMREAD_COLOR)
        if terrain is None:
            st.error("Unable to read uploaded image.")
    elif use_demo:
        terrain = demo_terrain_png()

    if terrain is not None:
        h0, w0 = terrain.shape[:2]
        if w0 > 1800:                                   # keep compositing fast
            terrain = cv2.resize(terrain, (1800, int(h0 * 1800 / w0)), interpolation=cv2.INTER_AREA)
        result, pos = compose(terrain, show=shown, scale=scale, snap=snap, labels=labels, links=links)

        t1, t2 = st.tabs(["🏗  Proposed Base", "📷  Original Photograph"])
        with t1:
            st.image(cv2.cvtColor(result, cv2.COLOR_BGR2RGB), caption="Infrastructure models placed on your terrain photograph", width="stretch")
            ok, enc = cv2.imencode(".png", result)
            if ok:
                st.download_button("DOWNLOAD BASE PLACEMENT IMAGE", data=enc.tobytes(),
                                   file_name="LUNARSET_Base_Infrastructure.png", mime="image/png")
        with t2:
            st.image(cv2.cvtColor(terrain, cv2.COLOR_BGR2RGB), caption="Original lunar surface image", width="stretch")

        st.subheader("Infrastructure Components")
        ccols = st.columns(4)
        sp = load_sprites_b64()
        for i, n in enumerate(n for n in shown if LAYOUT[n]["sprite"]):
            ccols[i % 4].markdown(
                f"<div class='fac-card'><img src='data:image/png;base64,{sp[LAYOUT[n]['sprite']]}'><b>{n}</b></div>",
                unsafe_allow_html=True)
        extra = [n for n in shown if not LAYOUT[n]["sprite"]]
        if extra:
            st.write("Zones:", " · ".join(extra))
        st.warning("Facility positions are conceptual and image-relative. They are not optimised using measured lunar "
                   "elevation, slope, illumination or hazard data. 3D renders are conceptual, not flight hardware.")
        st.info("➡ Continue to **03 | Post-Landing** to send the rover between these facilities.")
    else:
        st.info("Upload a lunar surface photograph (or tick the demo option) to display the proposed infrastructure placement.")

# =========================================================
# 10. POST-LANDING: ROVER NAVIGATION SIMULATION
# =========================================================
elif phase == "03 | Post-Landing":
    stepper(2)
    st.title("03 | Post-Landing")
    st.subheader("Surface Operations & Rover Navigation")
    st.write("**Click the rover** to start the tour — it drives along an A*-planned path that avoids craters. "
             "On arrival you get a notification and can pick the next facility. You can also click any facility, "
             "inspect its route, and press **START ROVER**.")

    sprites = load_sprites_b64()
    if len(sprites) < len(SPRITES):
        st.error("Infrastructure sprites not found in assets/sprites/.")
        st.stop()
    nav, terrain_b64 = load_nav()
    components.html(build_html(nav, FACILITIES, terrain_b64, sprites, CELL_M), height=800, scrolling=False)

    st.divider()
    st.subheader("Planned Route Catalogue")
    order = list(FACILITIES)
    rows = []
    for key, r in nav["routes"].items():
        a, b = key.split("|")
        if order.index(a) < order.index(b):
            rows.append({"From": a, "To": b, "Path distance (m)": r["dist"], "Straight line (m)": r["straight"],
                         "Bearing": f"{r['bearing']}° {r['dir']}", "Legs": len(r["waypoints"]), "Terrain risk": r["risk"]})
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.warning("Illustrative base grid (1 cell = 10 m) with generated craters. Routes use A* over a synthetic "
               "slope/roughness/crater-proximity cost layer — not real lunar DEM, coordinates or rover dynamics.")

# =========================================================
# 11. FOOTER
# =========================================================
st.divider()
st.markdown("<p style='text-align:center;color:#9AA8BC;'>LUNARSET | Lunar South Pole Mission Planning Prototype"
            "<br>Illustrative simulations are identified as such.</p>", unsafe_allow_html=True)
