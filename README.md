🌕 LUNARSET

From Lunar Data to an Intelligent Lunar Base

LUNARSET is a lunar mission-planning prototype designed for the lunar south pole. Built with Python and Streamlit, it integrates ISRO's VEDAS API with terrain analysis, landing-location identification, infrastructure planning, and rover navigation.

Mission Workflow

LUNARSET covers three mission phases:

01. Pre-Landing

- Upload a lunar observation video.
- Extract a representative frame.
- Identify visually distinctive features and mark potential landing locations.

02. Landing

- Upload lunar terrain imagery or use the available demonstration terrain.
- Visualize conceptual lunar infrastructure, including crew habitat, greenhouse, research laboratory, solar power station, and communication station.
- Display landing and resource-investigation zones.

03. Post-Landing

- Plan rover routes between mission facilities.
- Use A* pathfinding to navigate around marked hazards.
- Visualize rover movement, route distance, progress, and estimated travel time.

ISRO Data Integration

- ISRO VEDAS API Centre: Used for integration of Earth observation and geospatial data services.
- API credentials are stored locally and should not be committed to the public repository.

Technology Stack

- Python
- Streamlit
- OpenCV
- Plotly
- NumPy
- ISRO VEDAS API

Run Locally

git clone https://github.com/nishitakhadilkar/Lunарset.git
cd Lunарset
pip install -r requirements.txt
streamlit run app.py

Open "http://localhost:8501" in your browser.

Project Structure

LUNARSET/
├── app.py
├── requirements.txt
├── modules/
│   ├── infrastructure.py
│   ├── navigation.py
│   └── rover_sim.py
├── assets/
│   ├── sprites/
│   ├── originals/
│   └── lunarset_lunar_map_marked.png.jpeg
└── .streamlit/
    └── secrets.toml

Scientific and Engineering Limitations

- Landing locations and terrain markers are preliminary visual indicators, not validated safe landing sites.
- Infrastructure layouts and rover routes are illustrative.
- Uploaded optical imagery alone does not provide elevation, temperature, or geographic coordinates.
- Resource-investigation zones do not confirm the presence of accessible water ice.
- Infrastructure models are conceptual visualizations, not validated flight hardware.
- Route and risk estimates are not mission safety guarantees.

Future Development

- Chandrayaan terrain and elevation data integration.
- DEM-based slope and surface-roughness analysis.
- Multi-criteria landing-site suitability assessment.
- Interactive 3D lunar terrain and infrastructure visualization.
- Exportable mission-planning reports.

Project Status

Research and development prototype.

Developed for lunar surface intelligence and mission-planning applications.
