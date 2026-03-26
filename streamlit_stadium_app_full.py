import os
import math
from io import BytesIO

import folium
import geopandas as gpd
import pandas as pd
import requests
import streamlit as st
from folium.features import CustomIcon
from folium.plugins import MarkerCluster
from shapely.geometry import Point
from streamlit_folium import st_folium

# -------------------------
# PAGE CONFIG
# -------------------------

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    .main > div {
        padding-top: 0rem;
        max-width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# FILE PATHS
# -------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "full_stadium_dataset.csv")

# -------------------------
# HELPERS
# -------------------------

def haversine(lat1, lon1, lat2, lon2):
    r = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def geocode(city):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city, "format": "json", "limit": 1}
    headers = {"User-Agent": "stadium-app"}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        return float(data[0]["lat"]), float(data[0]["lon"]), data[0]["display_name"]
    except Exception:
        return None


def safe_int_text(x):
    return f"{int(x):,}" if pd.notnull(x) else "N/A"


def safe_dollar_text(x):
    return f"${int(x):,}" if pd.notnull(x) else "N/A"


# -------------------------
# LOAD STADIUM DATA
# -------------------------

if not os.path.exists(CSV_PATH):
    st.error(
        f"Could not find full_stadium_dataset.csv in the same folder as this app.\n\nExpected path:\n{CSV_PATH}"
    )
    st.stop()

stadiums = pd.read_csv(CSV_PATH)

required_cols = {"stadium", "team", "league", "city", "state", "lat", "lon"}
missing_cols = required_cols - set(stadiums.columns)
if missing_cols:
    st.error(f"full_stadium_dataset.csv is missing required columns: {sorted(missing_cols)}")
    st.stop()

# -------------------------
# LOGO FUNCTION
# -------------------------

def get_logo(team, league):
    league_map = {
        "NFL": "nfl",
        "NBA": "nba",
        "MLB": "mlb",
        "NHL": "nhl",
    }

    team_map = {
        # NFL
        "Falcons": "atl",
        "Panthers": "car",
        "Bears": "chi",
        "Packers": "gb",
        "Cowboys": "dal",
        "Giants": "nyg",
        "Jets": "nyj",
        "Patriots": "ne",
        "Bills": "buf",
        "Dolphins": "mia",
        "Steelers": "pit",
        "Browns": "cle",
        "Bengals": "cin",
        "Ravens": "bal",
        "Titans": "ten",
        "Texans": "hou",
        "Colts": "ind",
        "Jaguars": "jax",
        "Chiefs": "kc",
        "Broncos": "den",
        "Raiders": "lv",
        "Chargers": "lac",
        "Rams": "lar",
        "Seahawks": "sea",
        "49ers": "sf",
        "Cardinals": "ari",
        "Saints": "no",
        "Buccaneers": "tb",
        "Commanders": "wsh",
        "Vikings": "min",
        "Lions": "det",
        "Eagles": "phi",

        # NBA
        "Lakers": "lal",
        "Clippers": "lac",
        "Warriors": "gsw",
        "Kings": "sac",
        "Suns": "phx",
        "Trail Blazers": "por",
        "Jazz": "utah",
        "Nuggets": "den",
        "Spurs": "sa",
        "Mavericks": "dal",
        "Rockets": "hou",
        "Grizzlies": "mem",
        "Pelicans": "no",
        "Thunder": "okc",
        "Timberwolves": "min",
        "Bulls": "chi",
        "Cavaliers": "cle",
        "Pistons": "det",
        "Pacers": "ind",
        "Bucks": "mil",
        "Knicks": "ny",
        "Nets": "bkn",
        "76ers": "phi",
        "Celtics": "bos",
        "Raptors": "tor",
        "Heat": "mia",
        "Magic": "orl",
        "Hawks": "atl",
        "Hornets": "cha",
        "Wizards": "wsh",

        # MLB
        "Yankees": "nyy",
        "Mets": "nym",
        "Red Sox": "bos",
        "Blue Jays": "tor",
        "Orioles": "bal",
        "Rays": "tb",
        "White Sox": "chw",
        "Guardians": "cle",
        "Tigers": "det",
        "Royals": "kc",
        "Twins": "min",
        "Astros": "hou",
        "Angels": "laa",
        "Athletics": "oak",
        "Mariners": "sea",
        "Rangers": "tex",
        "Braves": "atl",
        "Marlins": "mia",
        "Nationals": "wsh",
        "Phillies": "phi",
        "Cubs": "chc",
        "Brewers": "mil",
        "Cardinals": "stl",
        "Pirates": "pit",
        "Dodgers": "lad",
        "Padres": "sd",
        "Giants": "sf",
        "Diamondbacks": "ari",
        "Rockies": "col",

        # NHL
        "Maple Leafs": "tor",
        "Canadiens": "mtl",
        "Bruins": "bos",
        "Sabres": "buf",
        "Red Wings": "det",
        "Senators": "ott",
        "Lightning": "tb",
        "Panthers": "fla",
        "Hurricanes": "car",
        "Capitals": "wsh",
        "Penguins": "pit",
        "Flyers": "phi",
        "Rangers": "nyr",
        "Islanders": "nyi",
        "Devils": "nj",
        "Blue Jackets": "cbj",
        "Blackhawks": "chi",
        "Blues": "stl",
        "Stars": "dal",
        "Predators": "nsh",
        "Jets": "wpg",
        "Wild": "min",
        "Avalanche": "col",
        "Golden Knights": "vgk",
        "Kraken": "sea",
        "Kings": "la",
        "Ducks": "ana",
        "Sharks": "sj",
        "Flames": "cgy",
        "Oilers": "edm",
        "Canucks": "van",
        "Utah Hockey Club": "utah",
    }

    code = team_map.get(team)
    league_code = league_map.get(league)

    if code and league_code:
        return f"https://a.espncdn.com/i/teamlogos/{league_code}/500/{code}.png"
    return None


# -------------------------
# REDFIN DATA
# -------------------------

@st.cache_data(show_spinner=False)
def get_redfin():
    url = "https://redfin-public-data.s3.amazonaws.com/redfin_market_tracker/city_market_tracker.tsv"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        df = pd.read_csv(pd.io.common.StringIO(r.text), sep="\t")
        df.columns = [str(c).strip() for c in df.columns]

        region_col = "region" if "region" in df.columns else None
        price_col = "median_sale_price" if "median_sale_price" in df.columns else None

        if region_col is None or price_col is None:
            raise ValueError("Redfin columns not found")

        df["key"] = df[region_col].astype(str).str.lower().str.strip()
        return df[["key", price_col]].rename(columns={price_col: "median_sale_price"})

    except Exception:
        return pd.DataFrame(
            {
                "key": ["chicago", "charlotte", "new york", "los angeles", "atlanta"],
                "median_sale_price": [350000, 400000, 750000, 900000, 400000],
            }
        )


# -------------------------
# STATE FIPS
# -------------------------

STATE_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09",
    "DE": "10", "DC": "11", "FL": "12", "GA": "13", "HI": "15", "ID": "16", "IL": "17",
    "IN": "18", "IA": "19", "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24",
    "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29", "MT": "30", "NE": "31",
    "NV": "32", "NH": "33", "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38",
    "OH": "39", "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46",
    "TN": "47", "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53", "WV": "54",
    "WI": "55", "WY": "56",
}

# -------------------------
# CENSUS POPULATION
# -------------------------

@st.cache_data(show_spinner=False)
def load_census_state(state_abbr):
    """
    Loads tract geometry + ACS population for one US state.
    Returns GeoDataFrame in EPSG:3857 or None.
    """
    fips = STATE_FIPS.get(str(state_abbr).upper())
    if not fips:
        return None

    try:
        tract_url = f"https://www2.census.gov/geo/tiger/TIGER2023/TRACT/tl_2023_{fips}_tract.zip"
        tracts = gpd.read_file(tract_url)

        api_url = f"https://api.census.gov/data/2022/acs/acs5?get=B01003_001E&for=tract:*&in=state:{fips}"
        resp = requests.get(api_url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        pop = pd.DataFrame(data[1:], columns=data[0])
        pop = pop.rename(
            columns={
                "B01003_001E": "population",
                "state": "state",
                "county": "county",
                "tract": "tract",
            }
        )
        pop["GEOID"] = pop["state"] + pop["county"] + pop["tract"]
        pop["population"] = pd.to_numeric(pop["population"], errors="coerce")

        tracts["GEOID"] = tracts["GEOID"].astype(str)
        merged = tracts.merge(pop[["GEOID", "population"]], on="GEOID", how="left")
        merged = merged.to_crs(epsg=3857)
        return merged

    except Exception:
        return None


def get_population(lat, lon, tracts_gdf, radius_miles=10):
    if tracts_gdf is None:
        return None

    try:
        point = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(epsg=3857)
        buffer = point.buffer(radius_miles * 1609.34)
        total = tracts_gdf.loc[tracts_gdf.intersects(buffer.iloc[0]), "population"].fillna(0).sum()
        return int(total)
    except Exception:
        return None


# -------------------------
# DEVELOPMENT / COMMERCIAL PROXY
# -------------------------

def get_commercial_density_proxy(population_value, price_value):
    """
    Dependency-safe proxy for near-stadium commercial intensity / development pressure.
    This is not a true transaction count. It gives a stable comparative signal.
    """
    if pd.isnull(population_value) or population_value <= 0:
        return None

    if pd.isnull(price_value) or price_value <= 0:
        return int(population_value / 1000)

    value = (population_value / 1000) * (500000 / price_value)
    return round(value, 1)


# -------------------------
# APP UI
# -------------------------

st.title("Sports Venues and CRE Activity Dashboard")

if "run_search" not in st.session_state:
    st.session_state.run_search = False

city = st.text_input("City", "Chicago")
radius = st.slider("Search Radius (miles)", 10, 200, 50)

if st.button("Show stadiums"):
    st.session_state.run_search = True

if not st.session_state.run_search:
    st.info("Enter a city and click Show stadiums.")
    st.stop()

geo = geocode(city)
if geo is None:
    st.error("Could not geocode that city.")
    st.stop()

search_lat, search_lon, display_name = geo

redfin = get_redfin()

df = stadiums.copy()
df["city"] = df["city"].astype(str).str.strip()
df["state"] = df["state"].astype(str).str.strip()
df["team"] = df["team"].astype(str).str.strip()
df["league"] = df["league"].astype(str).str.strip()

df["distance"] = df.apply(
    lambda r: haversine(search_lat, search_lon, float(r["lat"]), float(r["lon"])),
    axis=1,
)

df = df.loc[df["distance"] <= radius].copy()

if df.empty:
    st.warning("No stadiums found within that radius. Try increasing the radius.")
    m = folium.Map(location=[search_lat, search_lon], zoom_start=8)
    folium.Marker([search_lat, search_lon], tooltip=display_name).add_to(m)
    st_folium(m, height=900, width=None)
    st.stop()

# Merge Redfin city pricing
df["key"] = df["city"].str.lower().str.strip()
df = df.merge(redfin, on="key", how="left")
df["median_sale_price"] = pd.to_numeric(df["median_sale_price"], errors="coerce")

# Distance-adjusted nearby housing proxy
df["price_adj"] = df["median_sale_price"] * (1 - (df["distance"] / 200))
df.loc[df["price_adj"] < 0, "price_adj"] = 0

# Population by state, cached one state at a time
df["population"] = None

us_states_needed = sorted([s for s in df["state"].dropna().unique() if s in STATE_FIPS])

for st_abbr in us_states_needed:
    tracts = load_census_state(st_abbr)
    mask = df["state"] == st_abbr
    df.loc[mask, "population"] = df.loc[mask].apply(
        lambda r: get_population(float(r["lat"]), float(r["lon"]), tracts, radius_miles=10),
        axis=1,
    )

df["population"] = pd.to_numeric(df["population"], errors="coerce")

# Dependency-safe commercial / development proxy
df["commercial_density"] = df.apply(
    lambda r: get_commercial_density_proxy(r["population"], r["price_adj"]),
    axis=1,
)

# Simple ranking score
df["investment_score"] = (
    df["population"].fillna(0) / (df["price_adj"].replace(0, pd.NA))
).astype("Float64") * (df["commercial_density"].fillna(0) + 1)

# KPI row
k1, k2, k3, k4 = st.columns(4)
k1.metric("Nearby stadiums", f"{len(df):,}")
k2.metric("Avg adjusted price", safe_dollar_text(df["price_adj"].dropna().mean() if df["price_adj"].notna().any() else None))
k3.metric("Avg 10-mi population", safe_int_text(df["population"].dropna().mean() if df["population"].notna().any() else None))
k4.metric("Avg commercial proxy", f"{df['commercial_density'].dropna().mean():.1f}" if df["commercial_density"].notna().any() else "N/A")

# Map
m = folium.Map(location=[search_lat, search_lon], zoom_start=8, tiles="CartoDB positron")
cluster = MarkerCluster().add_to(m)

folium.Marker(
    [search_lat, search_lon],
    tooltip=display_name,
    popup=display_name,
).add_to(m)

for _, r in df.iterrows():
    logo = get_logo(r["team"], r["league"])

    try:
        icon = CustomIcon(logo, icon_size=(35, 35)) if logo else None
    except Exception:
        icon = None

    pop_text = safe_int_text(r.get("population"))
    price_text = safe_dollar_text(r.get("price_adj"))
    density_val = r.get("commercial_density")
    density_text = f"{density_val}" if pd.notnull(density_val) else "N/A"
    raw_price_text = safe_dollar_text(r.get("median_sale_price"))
    score_val = r.get("investment_score")
    score_text = f"{float(score_val):.2f}" if pd.notnull(score_val) else "N/A"

    popup = f"""
    <b>{r['stadium']}</b><br>
    {r['team']} ({r['league']})<br>
    {r['city']}, {r['state']}<br>
    Distance: {r['distance']:.1f} mi<br>
    City Sale Price: {raw_price_text}<br>
    Adjusted Price Proxy: {price_text}<br>
    Population (10 mi): {pop_text}<br>
    Commercial / Development Proxy: {density_text}<br>
    Investment Score: {score_text}
    """

    folium.Marker(
        [float(r["lat"]), float(r["lon"])],
        tooltip=r["stadium"],
        popup=popup,
        icon=icon,
    ).add_to(cluster)

st.subheader(f"Map for {display_name}")
st_folium(m, height=900, width=None)

# Table
display_df = df[
    [
        "stadium",
        "team",
        "league",
        "city",
        "state",
        "distance",
        "median_sale_price",
        "price_adj",
        "population",
        "commercial_density",
        "investment_score",
    ]
].copy()

display_df = display_df.sort_values(["distance", "league", "team"]).reset_index(drop=True)
display_df["distance"] = display_df["distance"].round(1)
display_df["median_sale_price"] = display_df["median_sale_price"].round(0)
display_df["price_adj"] = display_df["price_adj"].round(0)
display_df["investment_score"] = display_df["investment_score"].round(2)

st.subheader("Nearby Stadium Data")
st.dataframe(display_df, use_container_width=True)