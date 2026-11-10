from __future__ import annotations

import base64
import html
import hashlib
import json
import math
import re
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "scouting.sqlite3"
ROLE_CRITERIA_PATH = ROOT / "data" / "role_criteria.json"

NAVY = "#1F3446"
NAVY_2 = "#2E4658"
GOLD = "#A8793F"
GOLD_2 = "#D7B98E"
BURGUNDY = "#9A6D3A"
MUTED = "#687783"
BORDER = "#DDD8CF"
PAGE_BG = "#F1EFEA"
SURFACE = "#FAF9F6"
SOFT_SURFACE = "#F5F1EA"


st.set_page_config(
    page_title="England Academy Scouting",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
<style>
:root {{ --navy:{NAVY}; --gold:{GOLD}; --muted:{MUTED}; --border:{BORDER}; --page-bg:{PAGE_BG}; --surface:{SURFACE}; --soft-surface:{SOFT_SURFACE}; }}
html, body, [class*="css"] {{ font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
.stApp {{ background:{PAGE_BG}; color:{NAVY}; }}
.block-container {{ max-width:1540px; padding-top:1.45rem; padding-bottom:4rem; }}
header[data-testid="stHeader"] {{ background:transparent; }}
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{ display:none !important; }}
section[data-testid="stSidebar"] {{ background:linear-gradient(180deg,{NAVY} 0%,{NAVY_2} 100%); border-right:4px solid {GOLD}; }}
section[data-testid="stSidebar"] * {{ color:white; }}
section[data-testid="stSidebar"] [data-baseweb="radio"] > div {{ gap:.15rem; }}
section[data-testid="stSidebar"] label[data-baseweb="radio"] {{ padding:.42rem .45rem; border-radius:10px; }}
section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) {{ background:rgba(255,255,255,.10); }}
section[data-testid="stSidebar"] div[role="radiogroup"] p {{ font-weight:800; }}
.tool-brand {{ padding:.25rem .1rem .9rem; }}
.tool-brand .ey {{ font-size:.72rem; letter-spacing:.16em; color:{GOLD_2}; font-weight:900; text-transform:uppercase; }}
.tool-brand .name {{ font-size:1.42rem; line-height:1.05; font-weight:950; color:white; margin-top:.28rem; }}
.tool-brand .sub {{ font-size:.76rem; color:#CBD5E1; margin-top:.4rem; }}
.st-key-app_top_nav {{ border-bottom:1px solid {BORDER}; padding:.35rem .2rem .2rem; margin-bottom:.85rem; background:rgba(250,249,246,.97); }}
.st-key-app_top_nav [data-testid="stHorizontalBlock"] {{ align-items:center; }}
.app-brand {{ display:flex;align-items:center;gap:10px;font-size:1rem;font-weight:950;color:{NAVY};white-space:nowrap; }}
.st-key-app_top_nav .stButton>button {{ border:0 !important;border-radius:0 !important;background:transparent !important;min-height:2.45rem;font-size:.8rem !important;padding:.2rem .3rem !important; }}
.st-key-app_top_nav .stButton>button:hover {{ color:{GOLD} !important; }}
.st-key-app_top_nav button[kind="primary"] {{ color:{NAVY} !important;border-bottom:3px solid {GOLD} !important; }}
.page-head {{ margin:.05rem 0 1.05rem; }}
.page-kicker {{ color:{GOLD}; font-size:.72rem; font-weight:950; letter-spacing:.14em; text-transform:uppercase; }}
.page-title {{ color:{NAVY}; font-size:2.15rem; line-height:1.06; font-weight:950; margin:.16rem 0 .2rem; letter-spacing:-.035em; }}
.page-sub {{ color:{MUTED}; font-size:.93rem; max-width:850px; }}
.gold-rule {{ width:54px; height:4px; border-radius:99px; background:{GOLD}; margin-top:.72rem; }}
.panel {{ background:{SURFACE}; border:1px solid {BORDER}; border-radius:20px; box-shadow:0 10px 30px rgba(31,52,70,.055); padding:18px; }}
.panel-tight {{ padding:14px; }}
.section-title {{ font-size:1.04rem; color:{NAVY}; font-weight:950; margin:0 0 .7rem; }}
.section-note {{ color:{MUTED}; font-size:.79rem; margin-top:-.42rem; margin-bottom:.8rem; }}
.metric-card {{ background:{SURFACE}; border:1px solid {BORDER}; border-radius:16px; padding:14px 15px; box-shadow:0 7px 20px rgba(31,52,70,.04); min-height:86px; }}
.metric-label {{ color:#718096; text-transform:uppercase; letter-spacing:.08em; font-size:.66rem; font-weight:900; }}
.metric-value {{ color:{NAVY}; font-weight:950; font-size:1.55rem; line-height:1.15; margin-top:.28rem; }}
.metric-note {{ color:{MUTED}; font-size:.72rem; margin-top:.2rem; }}
.club-hero {{ display:flex; align-items:center; gap:18px; min-height:122px; }}
.club-logo-box {{ width:96px; height:96px; border-radius:20px; background:{SURFACE}; border:1px solid {BORDER}; display:flex; align-items:center; justify-content:center; flex:0 0 auto; box-shadow:0 7px 20px rgba(31,52,70,.05); }}
.club-logo-box img {{ max-width:75px; max-height:75px; object-fit:contain; }}
.club-logo-fallback {{ width:100%; height:100%; display:flex; align-items:center; justify-content:center; color:{NAVY}; font-size:.9rem; font-weight:950; letter-spacing:.04em; background:linear-gradient(145deg,#F8F6F1,#E9E3D8); border-radius:inherit; }}
.club-name {{ font-size:2rem; line-height:1.05; font-weight:950; color:{NAVY}; letter-spacing:-.03em; }}
.meta-line {{ color:{MUTED}; font-size:.88rem; margin-top:.35rem; }}
.pill {{ display:inline-block; margin:.55rem .35rem 0 0; padding:.36rem .66rem; border-radius:999px; font-size:.7rem; font-weight:900; border:1px solid rgba(214,165,0,.3); background:rgba(214,165,0,.10); color:{NAVY}; }}
.pill.dark {{ background:{NAVY}; border-color:{NAVY}; color:white; }}
.pill.good {{ background:#ECFDF5; border-color:#A7F3D0; color:#065F46; }}
.club-card {{ height:156px; background:{SURFACE}; border:1px solid {BORDER}; border-radius:17px; padding:13px; box-shadow:0 7px 18px rgba(31,52,70,.045); display:flex; align-items:center; gap:12px; }}
.club-card-logo {{ width:62px; height:62px; flex:0 0 auto; border-radius:14px; background:{SOFT_SURFACE}; display:flex; align-items:center; justify-content:center; border:1px solid {BORDER}; }}
.club-card-logo img {{ max-width:49px; max-height:49px; object-fit:contain; }}
.club-card-name {{ font-weight:950; color:{NAVY}; font-size:.95rem; line-height:1.12; }}
.club-card-meta {{ color:{MUTED}; font-size:.73rem; margin-top:.28rem; line-height:1.3; }}
.player-card {{ background:{SURFACE}; border:1px solid {BORDER}; border-radius:18px; padding:13px; box-shadow:0 8px 23px rgba(31,52,70,.05); min-height:335px; }}
.photo-wrap {{ position:relative; width:100%; aspect-ratio:1/1.08; border-radius:14px; overflow:hidden; background:linear-gradient(145deg,#E9E3D8,#F8F6F1); display:flex; align-items:center; justify-content:center; border:1px solid {BORDER}; }}
.photo-wrap.small {{ width:115px; aspect-ratio:1/1.08; flex:0 0 auto; }}
.photo-wrap.hero {{ width:96px; aspect-ratio:1/1.10; flex:0 0 96px; }}
.photo-initial {{ color:#94A3B8; font-size:1.8rem; font-weight:950; letter-spacing:.02em; }}
.photo-wrap img {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; object-position:50% 12%; }}
.player-card-name {{ color:{NAVY}; font-size:1rem; font-weight:950; margin-top:.7rem; line-height:1.15; }}
.player-card-meta {{ color:{MUTED}; font-size:.75rem; margin-top:.25rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.mv {{ color:{NAVY}; font-size:.78rem; font-weight:900; margin-top:.46rem; }}
.profile-head {{ display:flex; gap:19px; align-items:flex-start; }}
.player-name {{ color:{NAVY}; font-size:clamp(1.25rem,2vw,1.7rem); font-weight:950; line-height:1.08; letter-spacing:-.025em; overflow-wrap:anywhere; word-break:normal; max-width:100%; }}
.player-club {{ color:#475569; font-size:.97rem; font-weight:850; margin-top:.32rem; }}
.player-meta {{ color:{MUTED}; font-size:.84rem; line-height:1.55; margin-top:.5rem; }}
.profile-sidebar {{ position:sticky; top:1rem; }}
.profile-photo {{ width:100%; max-width:210px; aspect-ratio:.86/1; margin:0 auto 1rem; border-radius:15px; }}
.profile-photo-wide {{ width:120px; height:138px; aspect-ratio:auto; flex:0 0 120px; border-radius:14px; }}
.profile-hero-row {{ display:flex; align-items:center; gap:22px; }}
.profile-chip-row {{ display:flex; flex-wrap:wrap; gap:7px; margin-top:.75rem; }}
.profile-chip {{ display:inline-flex; align-items:center; min-height:28px; border-radius:8px; padding:.28rem .62rem; background:{SOFT_SURFACE}; color:{NAVY}; font-size:.75rem; font-weight:750; }}
.profile-chip.position {{ color:{BURGUNDY}; background:rgba(127,29,29,.08); }}
.profile-player-name {{ color:{NAVY}; font-size:1.45rem; line-height:1.13; font-weight:900; letter-spacing:-.025em; overflow-wrap:anywhere; }}
.profile-academy {{ color:{MUTED}; font-size:.82rem; margin-top:.35rem; }}
.profile-position {{ display:inline-block; margin-top:.65rem; padding:.3rem .62rem; border-radius:7px; color:{BURGUNDY}; background:rgba(127,29,29,.08); font-size:.76rem; font-weight:850; }}
.role-identity-row {{ display:flex; flex-wrap:wrap; gap:7px; margin-top:.72rem; }}
.role-identity-chip {{ display:inline-flex; align-items:center; gap:6px; border:1px solid {BORDER}; border-radius:9px; padding:.38rem .58rem; background:{SOFT_SURFACE}; color:{NAVY}; font-size:.71rem; }}
.role-identity-chip b {{ font-weight:900; }}
.profile-facts {{ display:grid; grid-template-columns:1fr 1fr; gap:0 12px; margin-top:1rem; }}
.profile-fact {{ border-top:1px solid {BORDER}; padding:.62rem 0; min-width:0; }}
.profile-fact span {{ display:block; color:{MUTED}; font-size:.67rem; text-transform:uppercase; letter-spacing:.06em; }}
.profile-fact b {{ display:block; color:{NAVY}; font-size:.82rem; font-weight:800; overflow-wrap:anywhere; }}
.profile-section-head {{ color:{NAVY}; font-size:1rem; font-weight:900; margin:0 0 .65rem; }}
.profile-empty {{ border:1px dashed #C9C0B3; border-radius:13px; padding:1rem; color:{MUTED}; background:{SOFT_SURFACE}; font-size:.84rem; }}
.attr-row {{ display:grid; grid-template-columns:minmax(116px,1fr) 2.2fr 36px; gap:8px; align-items:center; margin:.47rem 0; }}
.attr-name {{ font-size:.74rem; color:#475569; font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.attr-track {{ height:7px; background:#E8E1D7; border-radius:999px; overflow:hidden; }}
.attr-fill {{ height:100%; background:linear-gradient(90deg,{NAVY},{BURGUNDY}); border-radius:999px; }}
.attr-score {{ color:{NAVY}; font-size:.72rem; font-weight:950; text-align:right; }}
.signal-card {{ border:1px solid {BORDER}; border-radius:15px; padding:12px 13px; background:linear-gradient(145deg,{SURFACE},{SOFT_SURFACE}); margin:.38rem 0; }}
.signal-head {{ display:flex; justify-content:space-between; align-items:center; gap:12px; }}
.signal-title {{ color:{NAVY}; font-size:.86rem; font-weight:900; }}
.signal-score {{ color:{NAVY}; font-size:1.05rem; font-weight:950; white-space:nowrap; }}
.signal-note {{ color:{MUTED}; font-size:.72rem; line-height:1.4; margin-top:.35rem; }}
.signal-track {{ height:8px; background:#E8E1D7; border-radius:999px; overflow:hidden; margin-top:.55rem; }}
.signal-fill {{ height:100%; border-radius:999px; background:linear-gradient(90deg,#C5A77F,{BURGUNDY}); }}
.insight-card {{ min-height:106px; border-radius:16px; padding:13px 14px; background:linear-gradient(145deg,{SOFT_SURFACE},{SURFACE}); border:1px solid {BORDER}; }}
.insight-label {{ color:{MUTED}; text-transform:uppercase; letter-spacing:.07em; font-size:.62rem; font-weight:900; }}
.insight-value {{ color:{NAVY}; font-size:1.05rem; line-height:1.2; font-weight:950; margin-top:.35rem; }}
.insight-note {{ color:{MUTED}; font-size:.7rem; line-height:1.35; margin-top:.28rem; }}
.attribute-card {{ border:1px solid {BORDER}; border-radius:14px; padding:10px 12px; background:{SURFACE}; margin:.35rem 0; }}
.attribute-card .attr-row {{ margin:.25rem 0 0; }}
.history-card {{ border-left:3px solid {GOLD}; padding:3px 0 3px 12px; margin:.3rem 0 .55rem; }}
.history-title {{ color:{NAVY}; font-weight:900; font-size:.9rem; }}
.history-meta {{ color:{MUTED}; font-size:.72rem; margin-top:.2rem; }}
.tag-soft {{ display:inline-block; border-radius:999px; background:{SOFT_SURFACE}; color:#596875; padding:.18rem .5rem; font-size:.66rem; font-weight:850; margin:.25rem .25rem 0 0; }}
.role-row {{ display:flex; justify-content:space-between; align-items:center; padding:.45rem 0; border-bottom:1px solid #E8E1D7; gap:10px; }}
.role-row:last-child {{ border-bottom:0; }}
.role-name {{ color:#475569; font-size:.78rem; font-weight:750; }}
.role-score {{ color:{NAVY}; font-size:.78rem; font-weight:950; }}
.empty-card {{ background:{SOFT_SURFACE}; border:1px dashed #C9C0B3; border-radius:16px; padding:1rem; color:{MUTED}; font-size:.82rem; }}
.compare-card {{ background:{SURFACE}; border:1px solid {BORDER}; border-radius:17px; padding:13px; box-shadow:0 7px 19px rgba(31,52,70,.045); }}
.compare-name {{ color:{NAVY}; font-weight:950; font-size:.97rem; margin-top:.55rem; }}
.compare-meta {{ color:{MUTED}; font-size:.72rem; margin-top:.18rem; }}
.stButton>button {{ border-radius:11px !important; border:1px solid {BORDER} !important; background:{SURFACE} !important; color:{NAVY} !important; font-weight:850 !important; min-height:2.35rem; box-shadow:none !important; }}
.stButton>button:hover {{ border-color:{GOLD} !important; color:{NAVY} !important; }}
button[kind="primary"] {{ background:{NAVY} !important; color:white !important; border-color:{NAVY} !important; }}
[data-baseweb="select"] > div, .stTextInput input {{ border-radius:11px !important; }}
[data-baseweb="select"] > div, .stTextInput input, [data-testid="stNumberInput"] input {{ background:{SURFACE} !important; border-color:{BORDER} !important; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ background:{SURFACE}; border-color:{BORDER} !important; }}
[data-baseweb="popover"] {{ color:{NAVY}; }}
section[data-testid="stSidebar"] [data-baseweb="select"] > div {{ background:{SURFACE} !important; }}
section[data-testid="stSidebar"] [data-baseweb="select"] *, section[data-testid="stSidebar"] input {{ color:#0F172A !important; -webkit-text-fill-color:#0F172A !important; }}
section[data-testid="stSidebar"] [data-baseweb="select"] [role="listbox"] *, [data-baseweb="popover"] [role="listbox"] * {{ color:#0F172A !important; -webkit-text-fill-color:#0F172A !important; }}
section[data-testid="stSidebar"] [data-baseweb="select"] svg {{ fill:#0F172A !important; }}
[data-testid="stDataFrame"] {{ border:1px solid {BORDER}; border-radius:14px; overflow:hidden; background:{SURFACE}; }}
[data-testid="stTabs"] button {{ font-weight:850; }}
@media(max-width:900px) {{ .page-title{{font-size:1.75rem}} .player-name{{font-size:1.35rem}} .photo-wrap.hero{{width:88px;flex-basis:88px}} }}
@media(max-width:900px) {{ .profile-sidebar{{position:static}} .profile-photo{{max-width:150px}} }}
@media(max-width:700px) {{ .profile-hero-row{{align-items:flex-start;gap:14px}} .profile-photo-wide{{width:88px;height:104px;flex-basis:88px}} .profile-player-name{{font-size:1.2rem}} }}
</style>
""",
    unsafe_allow_html=True,
)


def db() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def sql(query: str, params: tuple = ()) -> pd.DataFrame:
    with db() as con:
        return pd.read_sql_query(query, con, params=params)


def load_metadata() -> dict[str, str]:
    if not DB_PATH.is_file():
        return {}
    frame = sql("SELECT key, value FROM metadata")
    return dict(zip(frame["key"], frame["value"]))


def load_players() -> pd.DataFrame:
    return sql(
        """
        SELECT p.*,
               COALESCE((
                   SELECT a.local_path FROM player_photo_assets a
                   WHERE a.canonical_id=p.canonical_id AND a.status='cached'
               ), '') AS cached_photo_path,
               COALESCE((
                   SELECT s.image_url FROM player_photo_sources s
                   WHERE s.canonical_id=p.canonical_id AND TRIM(COALESCE(s.image_url,''))<>''
                   ORDER BY s.recorded_utc DESC LIMIT 1
               ), '') AS verified_photo_url,
               COALESCE((
                   SELECT GROUP_CONCAT(image_url, char(10)) FROM (
                       SELECT s.image_url FROM player_photo_sources s
                       WHERE s.canonical_id=p.canonical_id AND TRIM(COALESCE(s.image_url,''))<>''
                       ORDER BY s.recorded_utc DESC
                   )
               ), '') AS photo_candidate_urls,
               CASE WHEN COALESCE(p.has_attributes,0)=1 OR EXISTS (
                   SELECT 1 FROM scouting_workbook_radar_axes r
                   WHERE r.canonical_id=p.canonical_id AND r.score IS NOT NULL
               ) THEN 1 ELSE 0 END AS has_scouting_data
        FROM players p ORDER BY p.club, p.player_name
        """
    )


def load_clubs() -> pd.DataFrame:
    return sql(
        """
        SELECT
            c.*,
            COALESCE(NULLIF(TRIM(c.logo_url), ''), '') AS academy_logo_url,
            CASE WHEN COALESCE(TRIM(c.tm_club_id), '') <> '' THEN
                'https://tmssl.akamaized.net/images/wappen/head/' || TRIM(c.tm_club_id) || '.png'
                ELSE '' END AS academy_logo_fallback,
            COALESCE(MAX(CASE WHEN t.squad_level='U18' THEN t.player_count END), 0) AS u18_count,
            COALESCE(MAX(CASE WHEN t.squad_level='U21' THEN t.player_count END), 0) AS u21_count,
            COALESCE(MAX(CASE WHEN t.squad_level='U18' THEN t.roster_status END), 'Not sourced') AS u18_roster_status,
            COALESCE(MAX(CASE WHEN t.squad_level='U21' THEN t.roster_status END), 'Not sourced') AS u21_roster_status,
            COUNT(DISTINCT CASE WHEN t.roster_status='Sourced' THEN t.squad_level END) AS sourced_team_count,
            COUNT(DISTINCT m.canonical_id) AS player_count,
            COUNT(DISTINCT CASE WHEN COALESCE(p.has_attributes, 0)=1 OR EXISTS (
                SELECT 1 FROM scouting_workbook_radar_axes r
                WHERE r.canonical_id=p.canonical_id AND r.score IS NOT NULL
            ) THEN m.canonical_id END) AS attribute_profiles,
            COUNT(DISTINCT NULLIF(p.nationality, '')) AS nationalities
        FROM clubs c
        LEFT JOIN academy_teams t ON t.club=c.club
        LEFT JOIN academy_memberships m ON m.club=c.club
        LEFT JOIN players p ON p.canonical_id=m.canonical_id
        GROUP BY c.club
        ORDER BY c.academy_category, c.club
        """
    )


def load_team_players(club: str, squad_level: str) -> pd.DataFrame:
    return sql(
        """
        SELECT p.*, m.squad_level AS academy_squad,
               COALESCE((
                   SELECT a.local_path FROM player_photo_assets a
                   WHERE a.canonical_id=p.canonical_id AND a.status='cached'
               ), '') AS cached_photo_path,
               COALESCE((
                   SELECT s.image_url FROM player_photo_sources s
                   WHERE s.canonical_id=p.canonical_id AND TRIM(COALESCE(s.image_url,''))<>''
                   ORDER BY s.recorded_utc DESC LIMIT 1
               ), '') AS verified_photo_url,
               COALESCE((
                   SELECT GROUP_CONCAT(image_url, char(10)) FROM (
                       SELECT s.image_url FROM player_photo_sources s
                       WHERE s.canonical_id=p.canonical_id AND TRIM(COALESCE(s.image_url,''))<>''
                       ORDER BY s.recorded_utc DESC
                   )
               ), '') AS photo_candidate_urls,
               CASE WHEN COALESCE(p.has_attributes,0)=1 OR EXISTS (
                   SELECT 1 FROM scouting_workbook_radar_axes r
                   WHERE r.canonical_id=p.canonical_id AND r.score IS NOT NULL
               ) THEN 1 ELSE 0 END AS has_scouting_data
        FROM players p
        JOIN academy_memberships m ON m.canonical_id=p.canonical_id
        WHERE m.club=? AND m.squad_level=?
        ORDER BY p.player_name
        """,
        (club, squad_level),
    )


def load_attributes(canonical_id: str, profile_key: str | None = None) -> pd.DataFrame:
    profile_key = profile_key or best_attribute_profile_key(canonical_id)
    if not profile_key:
        return pd.DataFrame()
    if profile_key.startswith("handoff|"):
        return sql(
            """
            SELECT attr_group, attribute, score, source_website, fm_edition,
                   source_profile_name, source_url, link_confidence, identity_flag,
                   values_basis, scale_max, profile_key,
                   score * 100.0 / scale_max AS normalized_score
            FROM scouting_workbook_attributes
            WHERE canonical_id=? AND profile_key=?
            ORDER BY attr_group, attribute
            """,
            (canonical_id, profile_key),
        )
    source = profile_key.removeprefix("legacy|")
    frame = sql(
        """
        SELECT attr_group, attribute, score, source, ? AS source_website,
               NULL AS fm_edition, NULL AS source_profile_name,
               CASE WHEN instr(source, 'https://') > 0
                    THEN substr(source, instr(source, 'https://')) ELSE NULL END AS source_url,
               'LEGACY_DATABASE' AS link_confidence, 'NO' AS identity_flag,
               'Existing database source' AS values_basis,
               CASE WHEN (SELECT MAX(a2.score) FROM attributes a2
                          WHERE a2.canonical_id=attributes.canonical_id AND a2.source=attributes.source) < 100
                    THEN 99.0 ELSE 100.0 END AS scale_max,
               'legacy|' || source AS profile_key,
               score * 100.0 / CASE WHEN (SELECT MAX(a2.score) FROM attributes a2
                                          WHERE a2.canonical_id=attributes.canonical_id AND a2.source=attributes.source) < 100
                                    THEN 99.0 ELSE 100.0 END AS normalized_score
        FROM attributes
        WHERE canonical_id=? AND source=? AND attribute NOT LIKE 'Unlabeled slot %'
        ORDER BY attr_group, attribute
        """,
        (source.split("|")[0].strip(), canonical_id, source),
    )
    return frame


def load_attribute_profiles(canonical_id: str) -> pd.DataFrame:
    workbook = sql(
        """
        SELECT p.profile_key, p.source_website, p.fm_edition, p.source_profile_name,
               p.source_url, p.link_confidence, p.identity_flag, p.values_basis,
               p.scale_max, COUNT(a.attribute) AS attribute_count, 1 AS is_workbook
        FROM scouting_workbook_profiles p
        LEFT JOIN scouting_workbook_attributes a
          ON a.canonical_id=p.canonical_id AND a.profile_key=p.profile_key
        WHERE p.canonical_id=?
        GROUP BY p.profile_key, p.source_website, p.fm_edition, p.source_profile_name,
                 p.source_url, p.link_confidence, p.identity_flag, p.values_basis, p.scale_max
        HAVING COALESCE(p.source_url,'')<>'' OR COUNT(a.attribute)>0
        """,
        (canonical_id,),
    )
    legacy = sql(
        """
        SELECT 'legacy|' || source AS profile_key,
               trim(substr(source, 1, CASE WHEN instr(source, '|')>0 THEN instr(source,'|')-1 ELSE length(source) END)) AS source_website,
               NULL AS fm_edition, NULL AS source_profile_name,
               CASE WHEN instr(source, 'https://')>0 THEN substr(source,instr(source,'https://')) ELSE NULL END AS source_url,
               'LEGACY_DATABASE' AS link_confidence, 'NO' AS identity_flag,
               'Existing database source' AS values_basis,
               CASE WHEN MAX(score) < 100 THEN 99.0 ELSE 100.0 END AS scale_max,
               COUNT(DISTINCT attribute) AS attribute_count, 0 AS is_workbook
        FROM attributes
        WHERE canonical_id=? AND attribute NOT LIKE 'Unlabeled slot %'
        GROUP BY source
        """,
        (canonical_id,),
    )
    result = pd.concat([workbook, legacy], ignore_index=True)
    if result.empty:
        return result
    result["edition_rank"] = result.fm_edition.map(fm_edition_rank)
    result["link_rank"] = result.link_confidence.map(
        lambda value: {"LINKED_USER_PROFILE": 3, "MASTER_ONLY": 2, "LEGACY_DATABASE": 1, "PROVISIONAL_USER_LINK": 0}.get(str(value), 0)
    )
    result["attribute_count"] = pd.to_numeric(result.attribute_count, errors="coerce").fillna(0).astype(int)
    return result.sort_values(
        ["link_rank", "attribute_count", "edition_rank", "is_workbook"],
        ascending=[False, False, False, False],
        kind="stable",
    ).reset_index(drop=True)


def fm_edition_rank(value: object) -> float:
    text = safe(value, "")
    if not text:
        return -1.0
    if text == "243":
        return 24.3
    try:
        return float(text)
    except ValueError:
        match = re.search(r"\bFM\s*(\d{2,3}(?:\.\d+)?)\b", text, re.IGNORECASE)
        if not match:
            return -1.0
        edition = match.group(1)
        return 24.3 if edition == "243" else float(edition)


def best_attribute_profile_key(canonical_id: str) -> str | None:
    profiles = load_attribute_profiles(canonical_id)
    return str(profiles.iloc[0].profile_key) if not profiles.empty else None


def attribute_profile_label(row: pd.Series) -> str:
    source = safe(row.source_website, "Source")
    edition = safe(row.fm_edition, "edition not listed")
    count = int(row.attribute_count or 0)
    scale = f"/{int(row.scale_max)}" if pd.notna(row.scale_max) else ""
    identity = " · provisional user link" if safe(row.link_confidence) == "PROVISIONAL_USER_LINK" else ""
    summary_only = " · summary only" if count == 0 else ""
    return f"{source} {edition} · {count} attributes{scale}{identity}{summary_only}"


def load_source_attribute_log(canonical_id: str, profile_key: str | None) -> pd.DataFrame:
    if not profile_key or not profile_key.startswith("handoff|"):
        return pd.DataFrame()
    return sql(
        """
        SELECT source_category, attribute_order, attribute_name, raw_value, scale_max, availability,
               mapping_note, fm_edition, source_website, source_url, identity_flag,
               link_confidence
        FROM scouting_source_attribute_log
        WHERE canonical_id=? AND profile_key=?
        ORDER BY source_category, attribute_order, row_no
        """,
        (canonical_id, profile_key),
    )


def load_batch_profile_metrics(canonical_id: str, profile_key: str | None = None) -> pd.DataFrame:
    if profile_key and profile_key.startswith("handoff|"):
        current = sql(
            """
            SELECT metric_name, metric_value, fm_edition,
                   import_source AS metric_source, source_url, scale
            FROM scouting_workbook_profile_metrics
            WHERE canonical_id=? AND profile_key=?
            ORDER BY metric_name
            """,
            (canonical_id, profile_key),
        )
        if not current.empty:
            return current
    return sql(
        """
        SELECT metric_name, metric_value, fm_edition, metric_source, source_url,
               NULL AS scale
        FROM fm_profile_metrics
        WHERE canonical_id=? AND metric_source IN ('FM_BATCH_83_ALL_FILES', 'ENGLAND_YOUTH_ALL_ATTRIBUTES_AND_RADAR_HANDOFF')
        ORDER BY metric_name
        """,
        (canonical_id,),
    )


def load_roles(canonical_id: str) -> pd.DataFrame:
    return sql(
        """
        SELECT phase, role, MAX(score) AS score
        FROM roles
        WHERE canonical_id=?
        GROUP BY phase, role
        ORDER BY phase, score DESC
        """,
        (canonical_id,),
    )


def load_roster_sources(club: str, squad_level: str) -> pd.DataFrame:
    """Official roster evidence added after the initial Transfermarkt build."""
    try:
        return sql(
            """
            SELECT source_url, source_title, published_date, coverage
            FROM roster_sources
            WHERE club=? AND squad_level=?
            ORDER BY published_date DESC
            """,
            (club, squad_level),
        )
    except Exception:
        return pd.DataFrame(columns=["source_url", "source_title", "published_date", "coverage"])


def load_history(canonical_id: str, table: str) -> pd.DataFrame:
    allowed = {"performances", "transfers", "injuries", "market_values"}
    if table not in allowed:
        return pd.DataFrame()
    return sql(f"SELECT * FROM {table} WHERE canonical_id=?", (canonical_id,)).drop(
        columns=["canonical_id", "record_key"], errors="ignore"
    )


def safe(value: object, fallback: str = "—") -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return fallback
    text = str(value).strip()
    return fallback if text.lower() in {"", "nan", "none", "null"} else text


def number_int(value: object) -> int:
    parsed = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return int(parsed) if pd.notna(parsed) else 0


def esc(value: object) -> str:
    return html.escape(safe(value, ""))


def transfermarkt_profile_url(player: pd.Series) -> str:
    url = safe(player.get("profile_url"), "")
    parsed = urlparse(url)
    trusted_hosts = {"transfermarkt.com", "www.transfermarkt.com", "transfermarkt.co.uk", "www.transfermarkt.co.uk"}
    return url if parsed.scheme == "https" and parsed.hostname in trusted_hosts and "/profil/spieler/" in parsed.path else ""


@st.cache_data(show_spinner=False)
def local_photo_data(path: str, modified_ns: int) -> str:
    try:
        payload = Path(path).read_bytes()
        return "data:image/jpeg;base64," + base64.b64encode(payload).decode("ascii")
    except OSError:
        return ""


def initials(name: object) -> str:
    parts = [part for part in safe(name, "P").split() if part]
    return "".join(part[0] for part in parts[:2]).upper() or "P"


def photo_html(row: pd.Series, style_class: str = "") -> str:
    def usable_photo(value: object) -> str:
        candidate = safe(value, "")
        normalized = candidate.casefold()
        return "" if any(marker in normalized for marker in ("default.jpg", "fallback.png", "placeholder", "/wappen/", "/club/")) else candidate

    local_path = safe(row.get("cached_photo_path"), "")
    url = ""
    if local_path:
        photo_path = Path(local_path)
        if not photo_path.is_file():
            photo_path = ROOT / "data" / "player_photos" / photo_path.name
        if photo_path.is_file():
            url = local_photo_data(str(photo_path), photo_path.stat().st_mtime_ns)
    if not url:
        url = usable_photo(row.get("image_url"))
    candidates = [usable_photo(value) for value in safe(row.get("photo_candidate_urls"), "").splitlines()]
    verified = usable_photo(row.get("verified_photo_url"))
    if verified:
        candidates.insert(0, verified)
    fallbacks = list(dict.fromkeys(candidate for candidate in candidates if candidate and candidate != url))
    fallback_attr = f" data-fallbacks='{html.escape(json.dumps(fallbacks), quote=True)}'" if fallbacks else ""
    image = (
        f"<img src='{html.escape(url, quote=True)}'{fallback_attr} loading='lazy' "
        "onerror=\"const q=JSON.parse(this.dataset.fallbacks||'[]');const n=q.shift();this.dataset.fallbacks=JSON.stringify(q);if(n){this.src=n;}else{this.style.display='none';}\">"
        if url
        else ""
    )
    return (
        f"<div class='photo-wrap {style_class}'><div class='photo-initial'>"
        f"{initials(row.get('player_name'))}</div>{image}</div>"
    )


def logo_html(
    url: object,
    club: object,
    box: str = "club-logo-box",
    fallback_url: object = "",
) -> str:
    primary = safe(url, "")
    fallback = safe(fallback_url, "")
    image_url = primary or fallback
    fallback_badge = f"<div class='club-logo-fallback' style='display:{'none' if image_url else 'flex'}'>{esc(initials(club))}</div>"
    if not image_url:
        return f"<div class='{box}'>{fallback_badge}</div>"
    return (
        f"<div class='{box}'><img src='{html.escape(image_url, quote=True)}' "
        f"data-fallback='{html.escape(fallback if primary else '', quote=True)}' alt='{esc(club)} logo' "
        "loading='lazy' referrerpolicy='no-referrer' "
        "onerror=\"if(this.dataset.fallback){this.src=this.dataset.fallback;this.dataset.fallback='';}"
        "else{this.style.display='none';this.nextElementSibling.style.display='flex';}\">"
        f"{fallback_badge}</div>"
    )


def age_number(value: object) -> float | None:
    try:
        parsed = float(value)
        return parsed if 0 < parsed < 100 else None
    except (TypeError, ValueError):
        return None


def format_age(value: object) -> str:
    parsed = age_number(value)
    return f"{int(parsed)}" if parsed is not None else "Unknown"


def format_height(value: object) -> str:
    try:
        parsed = float(value)
        if not parsed:
            return "—"
        return f"{int(round(parsed * 100))} cm" if parsed < 3 else f"{int(round(parsed))} cm"
    except (TypeError, ValueError):
        return "—"


def format_market_value(value: object, numeric_value: object = None) -> str:
    text = safe(value, "")
    number = pd.to_numeric(pd.Series([numeric_value]), errors="coerce").iloc[0]
    # The source database was imported with a Windows codepage at one point,
    # which replaced the euro sign with U+FFFD.  The amount and unit survived.
    if "�" in text:
        text = text.replace("�", "€")
    if pd.notna(number) and not text:
        if number >= 1_000_000:
            amount = f"{number / 1_000_000:.2f}".rstrip("0").rstrip(".")
            return f"€{amount}m"
        if number >= 1_000:
            return f"€{number / 1_000:.0f}k"
        return f"€{number:,.0f}"
    return text or "No value recorded"


def squad_source_label(level: str, count: object, status: object) -> str:
    """Never present a zero as proof that an academy team does not exist."""
    if safe(status) == "Sourced":
        return f"{level}: {int(count)} rostered"
    if safe(status) == "Official registration":
        return f"{level}: {int(count)} officially registered"
    if safe(status) == "Official match evidence":
        return f"{level}: {int(count)} official match evidence (partial)"
    if safe(status) == "Official team confirmed":
        return f"{level}: official team confirmed; public roster unavailable"
    if safe(status) == "Outside U21 scope":
        return f"{level}: official U19 programme (outside U21 scope)"
    return f"{level}: official roster check required"


def page_head(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"<div class='page-head'><div class='page-kicker'>England Academy Scouting</div>"
        f"<div class='page-title'>{html.escape(title)}</div>"
        f"<div class='page-sub'>{html.escape(subtitle)}</div><div class='gold-rule'></div></div>",
        unsafe_allow_html=True,
    )


def metric(label: str, value: object, note: str = "") -> str:
    return (
        f"<div class='metric-card'><div class='metric-label'>{html.escape(str(label))}</div>"
        f"<div class='metric-value'>{html.escape(str(value))}</div>"
        f"<div class='metric-note'>{html.escape(str(note))}</div></div>"
    )


OUTFIELD_RADAR_ATTRIBUTES = {
    "Playmaking": ["Passing", "Vision", "Crossing", "Decisions", "Technique"],
    "Ball Control": ["Dribbling", "First Touch", "Technique", "Agility", "Balance"],
    "Shooting": ["Finishing", "Long Shots"],
    "Defending": ["Tackling", "Marking", "Positioning", "Anticipation", "Aggression", "Bravery"],
    "Physical": ["Strength", "Stamina", "Natural Fitness", "Injury Resistance", "Balance"],
    "Speed": ["Pace", "Acceleration"],
    "Aerial": ["Heading", "Jumping Reach", "Bravery"],
    "Mental": ["Aggression", "Anticipation", "Composure", "Concentration", "Consistency", "Decisions", "Determination", "Flair", "Important Matches", "Leadership", "Teamwork", "Work Rate"],
    "Set Pieces": ["Corners", "Free Kick Taking", "Long Throws", "Penalty Taking"],
    "Personality": ["Adaptability", "Ambition", "Compliance", "Fairness", "Loyalty", "Pressure", "Professionalism", "Sportsmanship", "Temperament", "Versatility"],
    "Off-ball Movement": ["Off The Ball", "Anticipation", "Positioning"],
}

GOALKEEPER_RADAR_ATTRIBUTES = {
    "Shot Stopping": ["Reflexes", "Handling", "One On Ones", "Punching"],
    "Area Command": ["Aerial Reach", "Command Of Area", "Communication", "Jumping Reach"],
    "Distribution": ["Kicking", "Throwing", "Passing", "First Touch"],
    "Sweeping": ["Rushing Out", "Anticipation", "Pace", "Acceleration", "Decisions"],
    "Mental": ["Composure", "Concentration", "Decisions", "Bravery", "Teamwork"],
    "Athleticism": ["Agility", "Balance", "Strength", "Stamina", "Jumping Reach"],
}

STYLE_LABELS = {
    "Playmaking": "playmaker / progression passing",
    "Ball Control": "ball carrier / close control",
    "Shooting": "shot threat",
    "Defending": "defensive contribution",
    "Physical": "physical involvement",
    "Speed": "direct running",
    "Aerial": "aerial presence",
    "Mental": "mental attributes",
    "Set Pieces": "set-piece delivery or execution",
    "Personality": "personality indicators",
    "Off-ball Movement": "movement without the ball",
    "Shot Stopping": "shot-stopping profile",
    "Area Command": "goal-area command",
    "Distribution": "goalkeeper distribution",
    "Sweeping": "sweeper actions",
    "Athleticism": "goalkeeper athleticism",
}


def load_role_criteria() -> list[dict[str, object]]:
    if not ROLE_CRITERIA_PATH.is_file():
        return []
    try:
        payload = json.loads(ROLE_CRITERIA_PATH.read_text(encoding="utf-8-sig"))
        return [item for item in payload if item.get("role_name") and item.get("key_attributes")]
    except (OSError, json.JSONDecodeError, TypeError):
        return []


ROLE_CRITERIA = load_role_criteria()


def role_position_codes(position: object) -> tuple[set[str], str]:
    """Return the listed position lanes and whether the source label is broad."""
    value = safe(position, "").casefold()
    if not value:
        return set(), "unknown"
    if "goalkeeper" in value or "keeper" in value or value.strip() == "gk":
        return {"GK"}, "specific"
    if "centre-forward" in value or "center-forward" in value:
        return {"ST"}, "specific"
    if "second striker" in value:
        return {"ST", "AM(C)"}, "specific"
    if "left winger" in value or "right winger" in value:
        return {"AM(L/R)"}, "specific"
    if "attacking midfield" in value:
        return {"AM(C)"}, "specific"
    if "central midfield" in value:
        return {"M(C)"}, "specific"
    if "defensive midfield" in value:
        return {"DM"}, "specific"
    if "left midfield" in value or "right midfield" in value:
        return {"M(L/R)"}, "specific"
    if "centre-back" in value or "center-back" in value:
        return {"D(C)"}, "specific"
    if "left-back" in value or "right-back" in value:
        return {"D(L/R)", "WB(L/R)"}, "specific"
    if value.strip() == "attack":
        return {"ST", "AM(L/R)"}, "broad"
    if value.strip() in {"midfield", "central midfield"}:
        return {"AM(C)", "M(C)", "M(L/R)", "DM"}, "broad"
    if value.strip() == "defender":
        return {"D(C)", "D(L/R)", "WB(L/R)"}, "broad"
    return set(), "unknown"


@st.cache_data(show_spinner=False)
def role_fit_estimates(canonical_id: str, profile_key: str | None = None) -> pd.DataFrame:
    """Estimate key-attribute match; missing attributes are omitted, never zeroed."""
    if not ROLE_CRITERIA:
        return pd.DataFrame()
    player = sql("SELECT position FROM players WHERE canonical_id=?", (canonical_id,))
    if player.empty:
        return pd.DataFrame()
    allowed_positions, position_basis = role_position_codes(player.iloc[0].position)
    if not allowed_positions:
        return pd.DataFrame()
    attrs = {str(name).strip().casefold(): value for name, value in attr_dict(canonical_id, profile_key).items()}
    rows: list[dict[str, object]] = []
    for item in ROLE_CRITERIA:
        role_positions = item.get("position", [])
        if isinstance(role_positions, str):
            role_positions = [role_positions]
        if not allowed_positions.intersection(str(code) for code in role_positions):
            continue
        required = [str(name) for name in item["key_attributes"]]
        observed = [attrs[name.casefold()] for name in required if name.casefold() in attrs]
        coverage = len(observed) / len(required) if required else 0.0
        # At least three quarters of a role's key attributes must be present.
        if len(observed) < 3 or coverage < 0.75:
            continue
        rows.append({
            "phase": str(item.get("phase", "")).replace("_", " ").title(),
            "role": str(item["role_name"]),
            "score": sum(observed) / len(observed),
            "known": len(observed),
            "required": len(required),
            "coverage": coverage,
            "key_attributes": ", ".join(required),
            "position_basis": position_basis,
        })
    return pd.DataFrame(rows).sort_values(["phase", "score"], ascending=[True, False]) if rows else pd.DataFrame()


def role_attribute_radar_figure(
    canonical_id: str, profile_key: str | None, role_row: pd.Series
) -> go.Figure | None:
    """Aggregate only recorded factors relevant to this role into readable dimensions."""
    attrs = {str(k).casefold(): float(v) for k, v in attr_dict(canonical_id, profile_key).items()}
    required = {name.strip().casefold() for name in str(role_row.key_attributes).split(",") if name.strip()}
    mapping = GOALKEEPER_RADAR_ATTRIBUTES if is_goalkeeper(canonical_id) else OUTFIELD_RADAR_ATTRIBUTES
    dimensions = []
    for axis, names in mapping.items():
        relevant = [name.casefold() for name in names if name.casefold() in required]
        observed = [attrs[name] for name in relevant if name in attrs]
        if observed:
            dimensions.append((axis, sum(observed) / len(observed), len(observed), len(relevant)))
    if not dimensions:
        return None
    labels = [x[0] for x in dimensions]
    values = [max(0.0, min(100.0, x[1])) for x in dimensions]
    hover = [f"<b>{esc(axis)}</b><br>{score:.0f} / 100<br>{known}/{total} contributing indicators available"
             for axis, score, known, total in dimensions]
    closed = len(labels) >= 3
    figure = go.Figure(go.Scatterpolar(
        r=values + [values[0]] if closed else values,
        theta=labels + [labels[0]] if closed else labels,
        mode="lines+markers" if closed else "markers", line=dict(color=BURGUNDY, width=3),
        marker=dict(size=9, color=GOLD_2, line=dict(color="white", width=2)),
        fill="toself" if closed else None, fillcolor="rgba(127,29,29,.12)" if closed else None,
        text=hover + [hover[0]] if closed else hover, hovertemplate="%{text}<extra></extra>", showlegend=False))
    figure.update_layout(height=390, margin=dict(l=35, r=35, t=14, b=22), paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(visible=True, range=[0,100], tickvals=[20,40,60,80,100],
                   gridcolor="#E3DBCF", linecolor="#CFC4B5", tickfont=dict(size=9, color="#687783")),
                   angularaxis=dict(gridcolor="#E8E1D7", linecolor="#D8CDBE", tickfont=dict(size=10, color=NAVY))))
    return figure


def role_phase_radar_figure(fits: pd.DataFrame, canonical_id: str, profile_key: str | None, phase: str) -> tuple[go.Figure | None, pd.Series | None]:
    """Select the leading supported role profile and plot its actual key attributes."""
    if fits.empty:
        return None, None
    rows = fits.loc[fits.phase == phase].sort_values("score", ascending=False)
    if rows.empty:
        return None, None
    role_row = rows.iloc[0]
    return role_attribute_radar_figure(canonical_id, profile_key, role_row), role_row


def render_role_fit(canonical_id: str, profile_key: str | None = None, detailed: bool = False) -> None:
    fits = role_fit_estimates(canonical_id, profile_key)
    st.markdown("<div class='profile-section-head'>Role profile</div>", unsafe_allow_html=True)
    st.caption("Role fit · key-factor match estimate · not a star rating")
    if fits.empty:
        st.markdown(
            "<div class='profile-empty'>There is not enough recorded role evidence to assign a reliable role yet. "
            "Missing values are left unknown.</div>",
            unsafe_allow_html=True,
        )
        return

    phases = (("In Possession", "With the ball"), ("Out Of Possession", "Without the ball"))
    cols = st.columns(2, gap="medium")
    for col, (phase, title) in zip(cols, phases):
        with col:
            st.markdown(f"**{title}**")
            figure, role_row = role_phase_radar_figure(fits, canonical_id, profile_key, phase)
            if figure is None:
                st.caption("Not enough supported role evidence for this phase.")
                continue
            st.caption(
                f"Leading profile: **{role_row.role}** · role fit {float(role_row.score):.0f}/100 · "
                f"{int(role_row.known)}/{int(role_row.required)} supporting indicators available"
            )
            phase_color = "#A8793F" if phase == "In Possession" else "#7C8992"
            figure.update_traces(line_color=phase_color, marker_color=phase_color,
                                 fillcolor="rgba(111,143,139,.12)" if phase == "In Possession" else "rgba(140,166,181,.12)")
            st.plotly_chart(
                figure, width="stretch", config={"displayModeBar": False},
                key=f"role_radar_{'detail' if detailed else 'overview'}_{phase}_{canonical_id}",
            )
    st.caption("Each dimension summarizes available indicators relevant to that role. Missing values are omitted; role fit is a profile comparison aid, not a performance grade.")


@st.cache_data(show_spinner="Finding players with this role profile…")
def cached_role_fit_index(canonical_ids: tuple[str, ...]) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for canonical_id in canonical_ids:
        fits = role_fit_estimates(canonical_id)
        if fits.empty:
            continue
        for _, row in fits.iterrows():
            records.append({"canonical_id": canonical_id, "phase": row.phase, "role": row.role})
    return pd.DataFrame(records, columns=["canonical_id", "phase", "role"])

OUTFIELD_AXIS_ORDER = list(OUTFIELD_RADAR_ATTRIBUTES)
GOALKEEPER_AXIS_ORDER = list(GOALKEEPER_RADAR_ATTRIBUTES)


def is_goalkeeper(canonical_id: str) -> bool:
    position = sql("SELECT position FROM players WHERE canonical_id=?", (canonical_id,))
    if position.empty:
        return False
    value = safe(position.iloc[0].position, "").casefold()
    return "goalkeeper" in value or "keeper" in value or value.strip() == "gk"


def load_workbook_radar(canonical_id: str, profile_key: str | None) -> pd.DataFrame:
    if not profile_key or not profile_key.startswith("handoff|"):
        return pd.DataFrame()
    return sql(
        """
        SELECT axis, score, method, coverage
        FROM scouting_workbook_radar_axes
        WHERE canonical_id=? AND profile_key=?
        ORDER BY axis
        """,
        (canonical_id, profile_key),
    )


def attr_dict(canonical_id: str, profile_key: str | None = None) -> dict[str, float]:
    attrs = load_attributes(canonical_id, profile_key)
    aliases = {
        "longshots": "Long Shots",
        "workrate": "Work Rate",
        "freekicks": "Free Kick Taking",
        "long throw": "Long Throws",
        "penalties": "Penalty Taking",
        "one vs one": "One On Ones",
    }
    preferred_groups = {
        "Acceleration": "Physical", "Adaptability": "Personality", "Aerial Reach": "Goalkeeping",
        "Aggression": "Mental", "Agility": "Ball Control", "Ambition": "Personality",
        "Anticipation": "Mental", "Balance": "Ball Control", "Bravery": "Aerial",
        "Command Of Area": "Goalkeeping", "Communication": "Goalkeeping", "Compliance": "Personality",
        "Composure": "Mental", "Concentration": "Mental", "Consistency": "Mental",
        "Corners": "Set Pieces", "Crossing": "Playmaking", "Decisions": "Mental",
        "Determination": "Mental", "Dribbling": "Ball Control", "Eccentricity": "Goalkeeping",
        "Fairness": "Personality", "Finishing": "Shooting", "First Touch": "Ball Control",
        "Flair": "Mental", "Free Kick Taking": "Set Pieces", "Handling": "Goalkeeping",
        "Heading": "Aerial", "Important Matches": "Mental", "Injury Resistance": "Physical",
        "Jumping Reach": "Aerial", "Kicking": "Goalkeeping", "Leadership": "Mental",
        "Long Shots": "Shooting", "Long Throws": "Set Pieces", "Loyalty": "Personality",
        "Marking": "Defending", "Natural Fitness": "Physical", "Off The Ball": "Ball Control",
        "One On Ones": "Goalkeeping", "Pace": "Physical", "Passing": "Playmaking",
        "Penalty Taking": "Set Pieces", "Positioning": "Defending", "Pressure": "Personality",
        "Professionalism": "Personality", "Punching": "Goalkeeping", "Reflexes": "Goalkeeping",
        "Rushing Out": "Goalkeeping", "Sportsmanship": "Personality", "Stamina": "Physical",
        "Strength": "Physical", "Tackling": "Defending", "Teamwork": "Mental",
        "Technique": "Ball Control", "Temperament": "Personality", "Throwing": "Goalkeeping",
        "Versatility": "Personality", "Vision": "Playmaking", "Work Rate": "Mental",
    }
    result: dict[str, float] = {}
    priorities: dict[str, int] = {}
    for _, row in attrs.iterrows():
        raw_name = str(row.attribute)
        name = aliases.get(raw_name.casefold(), raw_name)
        priority = int(row.attr_group == preferred_groups.get(name))
        if name not in result or priority > priorities[name]:
            value = row.get("normalized_score", row.score)
            result[name] = float(value)
            priorities[name] = priority
    return result


def mean(attrs: dict[str, float], names: list[str]) -> float | None:
    values = [attrs[name] for name in names if name in attrs]
    return sum(values) / len(values) if values else None


def availability_score(canonical_id: str) -> float:
    injuries = load_history(canonical_id, "injuries")
    if injuries.empty:
        return 100.0
    days = 0
    missed = 0.0
    for _, row in injuries.iterrows():
        missed += float(pd.to_numeric(pd.Series([row.get("games_missed")]), errors="coerce").fillna(0).iloc[0])
        found = re.search(r"(\d+)", str(row.get("days_out") or ""))
        if found:
            days += int(found.group(1))
    return max(25.0, 100.0 - min(45.0, missed * 2.4) - min(30.0, days / 12.0))


def canonical_radar_axis(axis: object) -> str:
    label = safe(axis, "")
    return {"Set Piece": "Set Pieces"}.get(label, label)


def radar_scores(canonical_id: str, profile_key: str | None = None) -> dict[str, float] | None:
    profile_key = profile_key or best_attribute_profile_key(canonical_id)
    attrs = attr_dict(canonical_id, profile_key)
    if is_goalkeeper(canonical_id):
        mapping = GOALKEEPER_RADAR_ATTRIBUTES
    else:
        mapping = OUTFIELD_RADAR_ATTRIBUTES
    scores: dict[str, float] = {}
    if not is_goalkeeper(canonical_id):
        stored = load_workbook_radar(canonical_id, profile_key)
        if not stored.empty:
            scores.update(
                {
                    canonical_radar_axis(row.axis): float(row.score)
                    for _, row in stored.iterrows()
                    if pd.notna(row.score) and str(row.axis) != "Goalkeeping"
                }
            )
    for axis, names in mapping.items():
        if axis in scores:
            continue
        value = mean(attrs, names)
        if value is not None:
            scores[axis] = float(value)
    if is_goalkeeper(canonical_id) and not scores:
        stored = load_workbook_radar(canonical_id, profile_key)
        row = stored[stored.axis == "Goalkeeping"] if not stored.empty else stored
        if not row.empty and pd.notna(row.iloc[0].score):
            scores["Goalkeeping summary"] = float(row.iloc[0].score)
    return scores or None


def radar_axis_details(canonical_id: str, profile_key: str | None = None) -> dict[str, tuple[str, str]]:
    profile_key = profile_key or best_attribute_profile_key(canonical_id)
    details: dict[str, tuple[str, str]] = {}
    stored = load_workbook_radar(canonical_id, profile_key)
    if not is_goalkeeper(canonical_id) and not stored.empty:
        for _, row in stored.iterrows():
            if pd.notna(row.score) and str(row.axis) != "Goalkeeping":
                details[canonical_radar_axis(row.axis)] = (safe(row.method, "Source profile"), safe(row.coverage, ""))
    attrs = attr_dict(canonical_id, profile_key)
    mapping = GOALKEEPER_RADAR_ATTRIBUTES if is_goalkeeper(canonical_id) else OUTFIELD_RADAR_ATTRIBUTES
    for axis, names in mapping.items():
        if axis in details:
            continue
        available = sum(name in attrs for name in names)
        if available:
            details[axis] = ("Mean of available named attributes", f"{available}/{len(names)}")
    return details


def style_indications(canonical_id: str, profile_key: str | None = None) -> list[tuple[str, float, str]]:
    scores = radar_scores(canonical_id, profile_key) or {}
    details = radar_axis_details(canonical_id, profile_key)
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:3]
    return [
        (STYLE_LABELS.get(axis, axis), value, details.get(axis, ("Source group score", ""))[1])
        for axis, value in ordered
    ]


def radar_insights(canonical_id: str, profile_key: str | None = None) -> dict[str, object]:
    scores = radar_scores(canonical_id, profile_key) or {}
    details = radar_axis_details(canonical_id, profile_key)
    if not scores:
        return {"scores": {}, "details": details, "top": None, "contrast": None}
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    high_axis, high_score = ranked[0]
    low_axis, low_score = ranked[-1]
    spread = high_score - low_score if len(ranked) > 1 else None
    return {
        "scores": scores,
        "details": details,
        "top": (high_axis, high_score),
        "contrast": (high_axis, low_axis, spread) if spread is not None else None,
    }


def strength_reading(value: float) -> str:
    if value >= 80:
        return "High on the 0–100 scale"
    if value >= 60:
        return "Above the scale midpoint"
    if value >= 40:
        return "Around the scale midpoint"
    return "Below the scale midpoint"


def axis_attribute_names(canonical_id: str, axis: str) -> list[str]:
    mapping = GOALKEEPER_RADAR_ATTRIBUTES if is_goalkeeper(canonical_id) else OUTFIELD_RADAR_ATTRIBUTES
    return mapping.get(axis, [])


def radar_figure(canonical_id: str, profile_key: str | None = None) -> go.Figure | None:
    scores = radar_scores(canonical_id, profile_key)
    if not scores:
        return None
    order = GOALKEEPER_AXIS_ORDER if is_goalkeeper(canonical_id) else OUTFIELD_AXIS_ORDER
    labels = [axis for axis in order if axis in scores] + [axis for axis in scores if axis not in order]
    values = [scores[label] for label in labels]
    details = radar_axis_details(canonical_id, profile_key)
    hover = []
    for axis in labels:
        method, coverage = details.get(axis, ("Source profile", ""))
        coverage_text = f"{coverage.split('/')[0]} of {coverage.split('/')[1]} contributing measures" if re.fullmatch(r"\d+/\d+", coverage) else "Coverage not recorded"
        hover.append(
            f"<b>{axis}</b><br>{scores[axis]:.1f} / 100 · {strength_reading(scores[axis])}"
            f"<br>Composite indicator<br>Data coverage: {coverage_text}"
        )
    figure = go.Figure()
    figure.add_trace(
        go.Scatterpolar(
            r=[50] * len(labels),
            theta=labels,
            mode="lines",
            line=dict(color="rgba(148,163,184,.50)", width=1.5, dash="dot"),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    figure.add_trace(
        go.Scatterpolar(
            r=values,
            theta=labels,
            mode="lines+markers",
            line=dict(color=BURGUNDY, width=3.5),
            marker=dict(size=10, color=values, colorscale=[[0, "#B7C4D3"], [.5, GOLD_2], [1, BURGUNDY]],
                        cmin=0, cmax=100, showscale=False, line=dict(color="white", width=2)),
            fill="toself",
            fillcolor="rgba(111,143,139,.12)",
            text=hover,
            hovertemplate="%{text}<extra></extra>",
            showlegend=False,
        )
    )
    figure.update_layout(
        height=485,
        margin=dict(l=60, r=60, t=22, b=24),
        paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[20, 40, 60, 80, 100],
                gridcolor="#E3DBCF",
                linecolor="#CFC4B5",
                tickfont=dict(size=10, color="#526174"),
            ),
            angularaxis=dict(gridcolor="#E8E1D7", linecolor="#D8CDBE", tickfont=dict(size=11, color=NAVY)),
        ),
    )
    return figure


def overlay_radar(rows: list[pd.Series]) -> go.Figure | None:
    palette = [BURGUNDY, NAVY, GOLD, "#0F766E"]
    figure = go.Figure()
    scored_rows = [(row, radar_scores(row["canonical_id"])) for row in rows]
    scored_rows = [(row, scores) for row, scores in scored_rows if scores]
    axis_order = GOALKEEPER_AXIS_ORDER if scored_rows and is_goalkeeper(scored_rows[0][0]["canonical_id"]) else OUTFIELD_AXIS_ORDER
    labels = [axis for axis in axis_order if any(axis in scores for _, scores in scored_rows)]
    for index, (row, scores) in enumerate(scored_rows):
        figure.add_trace(
            go.Scatterpolar(
                r=[scores.get(axis) for axis in labels],
                theta=labels,
                mode="lines+markers",
                name=row["player_name"],
                line=dict(width=2.6, color=palette[index % len(palette)]),
                marker=dict(size=5, color=palette[index % len(palette)]),
                fill="toself",
                fillcolor="rgba(0,0,0,0)",
                hovertemplate="<b>%{theta}</b><br>%{r:.0f}/100<extra></extra>",
            )
        )
    if not scored_rows or not labels:
        return None
    figure.add_trace(
        go.Scatterpolar(
            r=[50] * len(labels),
            theta=labels,
            mode="lines",
            line=dict(color="rgba(148,163,184,.45)", width=1.2, dash="dot"),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    figure.update_layout(
        height=510,
        margin=dict(l=55, r=55, t=25, b=25),
        paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], tickvals=[20, 40, 60, 80, 100], gridcolor="#E3DBCF"),
            angularaxis=dict(gridcolor="#E8E1D7", tickfont=dict(color=NAVY)),
        ),
        legend=dict(orientation="h", y=1.08, x=0, font=dict(size=11, color=NAVY)),
    )
    return figure


# Position intelligence -------------------------------------------------------
# These measures deliberately compare a player with the academy peer group for
# the same positional lane.  They are not averages across unrelated football
# attributes and unknown values are never converted to a weak score.
POSITION_DNA = {
    "GK": {
        "Shot stopping": ["Reflexes", "Handling", "One On Ones", "Agility"],
        "Area command": ["Aerial Reach", "Command Of Area", "Communication", "Punching"],
        "Distribution": ["Kicking", "Throwing", "Passing", "First Touch"],
        "Sweeping": ["Rushing Out", "Anticipation", "Decisions", "Pace"],
        "Reliability": ["Positioning", "Concentration", "Composure"],
    },
    "ST": {
        "Box finishing": ["Finishing", "Composure", "First Touch", "Technique"],
        "Movement": ["Off The Ball", "Anticipation", "Acceleration", "Agility"],
        "Link play": ["Passing", "Vision", "Teamwork", "First Touch"],
        "Running power": ["Acceleration", "Pace", "Agility", "Balance"],
        "Aerial threat": ["Heading", "Jumping Reach", "Strength", "Bravery"],
        "Pressing work": ["Work Rate", "Stamina", "Aggression", "Teamwork"],
    },
    "AM(L/R)": {
        "1v1 threat": ["Dribbling", "Technique", "Agility", "Acceleration"],
        "Chance creation": ["Crossing", "Passing", "Vision", "Decisions"],
        "Goal threat": ["Finishing", "Long Shots", "Off The Ball", "Composure"],
        "Wide running": ["Pace", "Acceleration", "Stamina", "Off The Ball"],
        "Ball security": ["First Touch", "Technique", "Composure", "Balance"],
        "Defensive return": ["Work Rate", "Teamwork", "Stamina", "Anticipation"],
    },
    "AM(C)": {
        "Creative progression": ["Passing", "Vision", "Technique", "Decisions"],
        "Between-lines play": ["First Touch", "Dribbling", "Composure", "Flair"],
        "Goal threat": ["Finishing", "Long Shots", "Off The Ball", "Composure"],
        "Ball security": ["First Touch", "Technique", "Balance", "Composure"],
        "Counterpress": ["Work Rate", "Teamwork", "Anticipation", "Stamina"],
    },
    "M(C)": {
        "Progression": ["Passing", "Vision", "Technique", "Decisions"],
        "Ball security": ["First Touch", "Technique", "Composure", "Balance"],
        "Defensive coverage": ["Tackling", "Positioning", "Anticipation", "Work Rate"],
        "Press resistance": ["Composure", "Balance", "Agility", "First Touch"],
        "Running capacity": ["Stamina", "Work Rate", "Acceleration", "Teamwork"],
    },
    "DM": {
        "Screening": ["Marking", "Tackling", "Positioning", "Concentration"],
        "Defensive coverage": ["Anticipation", "Work Rate", "Stamina", "Teamwork"],
        "Build-up security": ["Passing", "First Touch", "Technique", "Composure"],
        "Progression": ["Passing", "Vision", "Decisions", "Technique"],
        "Duelling": ["Strength", "Balance", "Aggression", "Bravery"],
    },
    "D(L/R)": {
        "Wide defending": ["Marking", "Tackling", "Positioning", "Anticipation"],
        "Recovery defending": ["Acceleration", "Pace", "Agility", "Anticipation"],
        "Wide progression": ["Crossing", "Passing", "Technique", "Dribbling"],
        "Running capacity": ["Stamina", "Work Rate", "Pace", "Acceleration"],
        "Duelling": ["Strength", "Balance", "Aggression", "Bravery"],
    },
    "WB(L/R)": {
        "Wide defending": ["Marking", "Tackling", "Positioning", "Anticipation"],
        "Recovery defending": ["Acceleration", "Pace", "Agility", "Anticipation"],
        "Wide progression": ["Crossing", "Passing", "Technique", "Dribbling"],
        "Running capacity": ["Stamina", "Work Rate", "Pace", "Acceleration"],
        "Duelling": ["Strength", "Balance", "Aggression", "Bravery"],
    },
    "D(C)": {
        "Box defending": ["Marking", "Tackling", "Positioning", "Concentration"],
        "Aerial dominance": ["Heading", "Jumping Reach", "Strength", "Bravery"],
        "Recovery defending": ["Acceleration", "Pace", "Anticipation", "Agility"],
        "Build-up security": ["Passing", "First Touch", "Technique", "Composure"],
        "Duelling resilience": ["Strength", "Balance", "Aggression", "Decisions"],
    },
}


def player_lane(position: object) -> str:
    codes, _ = role_position_codes(position)
    priority = ("GK", "ST", "AM(L/R)", "AM(C)", "M(L/R)", "M(C)", "DM", "WB(L/R)", "D(L/R)", "D(C)")
    return next((code for code in priority if code in codes), "")


@st.cache_data(show_spinner=False)
def peer_attribute_table() -> pd.DataFrame:
    """One normalized, de-duplicated attribute row per player/attribute."""
    raw = sql("""
        SELECT p.canonical_id, p.position, a.attribute, a.score, a.source
        FROM players p JOIN attributes a ON a.canonical_id=p.canonical_id
        WHERE a.attribute NOT LIKE 'Unlabeled slot %' AND a.score IS NOT NULL
    """)
    if raw.empty:
        return raw
    raw["score"] = pd.to_numeric(raw.score, errors="coerce")
    raw = raw.dropna(subset=["score"])
    source_max = raw.groupby(["canonical_id", "source"], dropna=False)["score"].transform("max")
    raw["normalized"] = raw.score.where(source_max >= 25, raw.score * 5.0).clip(0, 100)
    raw["lane"] = raw.position.map(player_lane)
    return raw.groupby(["canonical_id", "lane", "attribute"], as_index=False)["normalized"].max()


@st.cache_data(show_spinner=False)
def peer_percentile_table() -> pd.DataFrame:
    data = peer_attribute_table().copy()
    if data.empty:
        return data
    data["percentile"] = data.groupby(["lane", "attribute"])["normalized"].rank(pct=True, method="average") * 100
    data["peer_count"] = data.groupby(["lane", "attribute"])["canonical_id"].transform("count")
    return data


def player_percentile_attributes(canonical_id: str) -> dict[str, float]:
    table = peer_percentile_table()
    rows = table[table.canonical_id.astype(str) == str(canonical_id)] if not table.empty else table
    return dict(zip(rows.attribute.astype(str), rows.percentile.astype(float))) if not rows.empty else {}


def position_metrics(canonical_id: str) -> tuple[str, dict[str, float], dict[str, tuple[int, int]]]:
    player = sql("SELECT position FROM players WHERE canonical_id=?", (canonical_id,))
    lane = player_lane(player.iloc[0].position) if not player.empty else ""
    template = POSITION_DNA.get(lane, {})
    values = player_percentile_attributes(canonical_id)
    scores: dict[str, float] = {}
    coverage: dict[str, tuple[int, int]] = {}
    for label, attributes in template.items():
        observed = [values[name] for name in attributes if name in values]
        if observed:
            # First two attributes define the action; the remaining ones support it.
            # This prevents a single unrelated high attribute from flattening the profile.
            weights = [2.0 if index < 2 else 1.0 for index, name in enumerate(attributes) if name in values]
            scores[label] = sum(value * weight for value, weight in zip(observed, weights)) / sum(weights)
            coverage[label] = (len(observed), len(attributes))
    return lane, scores, coverage


def role_fit_estimates(canonical_id: str, profile_key: str | None = None) -> pd.DataFrame:
    """Role fit: 55% core + 25% critical floor + 20% support, all peer percentiles."""
    player = sql("SELECT position FROM players WHERE canonical_id=?", (canonical_id,))
    if player.empty:
        return pd.DataFrame()
    lane = player_lane(player.iloc[0].position)
    if not lane:
        return pd.DataFrame()
    values = player_percentile_attributes(canonical_id)
    records: list[dict[str, object]] = []
    for item in ROLE_CRITERIA:
        positions = item.get("position", [])
        positions = [positions] if isinstance(positions, str) else positions
        if lane not in {str(position) for position in positions}:
            continue
        required = [str(name) for name in item["key_attributes"]]
        observed = [values[name] for name in required if name in values]
        coverage = len(observed) / len(required) if required else 0.0
        if len(observed) < 3:
            continue
        core = [values[name] for name in required[:4] if name in values]
        support = [values[name] for name in required[4:] if name in values]
        weighted = [(values[name], 2.0 if index < 4 else 1.0) for index, name in enumerate(required) if name in values]
        # Weighted geometric mean rewards a complete role profile.  A low critical
        # requirement cannot be hidden by several exceptional supporting traits.
        geometric = 100.0 * math.exp(sum(weight * math.log(max(value, 1.0) / 100.0) for value, weight in weighted) / sum(weight for _, weight in weighted))
        critical_floor = min(core) if core else min(observed)
        score = .78 * geometric + .22 * critical_floor
        records.append({
            "phase": str(item.get("phase", "")).replace("_", " ").title(),
            "role": str(item["role_name"]), "score": score, "known": len(observed),
            "required": len(required), "coverage": coverage,
            "key_attributes": ", ".join(required), "position_basis": "peer percentile",
        })
    return pd.DataFrame(records).sort_values(["phase", "score"], ascending=[True, False]) if records else pd.DataFrame()


def radar_scores(canonical_id: str, profile_key: str | None = None) -> dict[str, float] | None:
    _, scores, _ = position_metrics(canonical_id)
    return scores or None


def radar_axis_details(canonical_id: str, profile_key: str | None = None) -> dict[str, tuple[str, str]]:
    _, _, coverage = position_metrics(canonical_id)
    return {axis: ("Peer percentile within positional lane", f"{known}/{total}") for axis, (known, total) in coverage.items()}


def radar_figure(canonical_id: str, profile_key: str | None = None) -> go.Figure | None:
    lane, scores, coverage = position_metrics(canonical_id)
    if len(scores) < 3:
        return None
    labels = list(scores)
    values = [scores[label] for label in labels]
    peer = [50] * len(labels)
    hover = [f"<b>{esc(label)}</b><br>Peer percentile: {value:.0f}<br>Evidence: {coverage[label][0]}/{coverage[label][1]} measures" for label, value in scores.items()]
    figure = go.Figure()
    figure.add_trace(go.Scatterpolar(r=peer + [peer[0]], theta=labels + [labels[0]], mode="lines",
        line=dict(color="rgba(108,117,125,.50)", width=1.5, dash="dot"), fill="toself",
        fillcolor="rgba(108,117,125,.06)", hoverinfo="skip", showlegend=False))
    figure.add_trace(go.Scatterpolar(r=values + [values[0]], theta=labels + [labels[0]], mode="lines+markers",
        line=dict(color=BURGUNDY, width=3), marker=dict(size=8, color=GOLD, line=dict(color="white", width=1.5)),
        fill="toself", fillcolor="rgba(154,109,58,.16)", text=hover + [hover[0]], hovertemplate="%{text}<extra></extra>", showlegend=False))
    figure.update_layout(height=440, margin=dict(l=55, r=55, t=12, b=20), paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(visible=True, range=[0,100], tickvals=[25,50,75,100], gridcolor="#E3DBCF", tickfont=dict(size=9, color=MUTED)),
                   angularaxis=dict(gridcolor="#E8E1D7", linecolor="#D8CDBE", tickfont=dict(size=11, color=NAVY))))
    return figure


def role_fit_scatter_figure(canonical_id: str) -> go.Figure | None:
    """Actual role outcomes: calculated fit on x, available requirement evidence on y."""
    fits = role_fit_estimates(canonical_id)
    if fits.empty:
        return None
    # Keep the board readable while retaining all roles in the hover layer.
    fits = fits.sort_values("score", ascending=False).groupby(["phase", "role"], as_index=False).first()
    fig = go.Figure()
    palette = {"In Possession": BURGUNDY, "Out Of Possession": "#5F8D87"}
    for phase, rows in fits.groupby("phase", sort=False):
        labels = [role if index < 4 else "" for index, role in enumerate(rows.sort_values("score", ascending=False).role.tolist())]
        fig.add_trace(go.Scatter(
            x=rows.score, y=rows.coverage * 100, mode="markers+text", text=labels, textposition="top center",
            textfont=dict(size=10, color=NAVY), name=phase,
            marker=dict(size=8 + (rows.known / rows.required * 8), color=palette.get(phase, NAVY), line=dict(color="white", width=1.5)),
            customdata=list(zip(rows.role, rows.known.astype(int), rows.required.astype(int))),
            hovertemplate="<b>%{customdata[0]}</b><br>Calculated role fit: %{x:.0f}<br>Evidence: %{customdata[1]} of %{customdata[2]} requirements<extra></extra>",
        ))
    fig.update_layout(height=300, margin=dict(l=14,r=12,t=12,b=40), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0,100], title="Calculated role fit", gridcolor="#E8E1D7", zeroline=False),
        yaxis=dict(range=[0,105], title="Evidence coverage", ticksuffix="%", gridcolor="#E8E1D7", zeroline=False),
        legend=dict(orientation="h", y=1.13, x=0, font=dict(size=10)), hovermode="closest")
    return fig


def role_requirement_figure(canonical_id: str) -> tuple[go.Figure | None, str]:
    """Drill-down for the best-supported calculated role; dots are actual attribute percentiles."""
    fits = role_fit_estimates(canonical_id)
    if fits.empty:
        return None, ""
    role = fits.sort_values("score", ascending=False).iloc[0]
    percentiles = player_percentile_attributes(canonical_id)
    required = [name.strip() for name in str(role.key_attributes).split(",") if name.strip()]
    observed = [(name, percentiles[name]) for name in required if name in percentiles]
    if len(observed) < 2:
        return None, ""
    names, values = zip(*observed)
    critical = [index < 4 for index in range(len(names))]
    fig = go.Figure()
    fig.add_vline(x=50, line=dict(color="rgba(104,119,131,.55)", dash="dot", width=1.2), annotation_text="Peer midpoint", annotation_position="top", annotation_font=dict(size=10,color=MUTED))
    fig.add_trace(go.Scatter(x=values, y=list(names), mode="markers", marker=dict(size=12, color=[BURGUNDY if value else "#5F8D87" for value in critical], line=dict(color="white", width=1.5)),
        text=[f"<b>{esc(name)}</b><br>Player percentile: {value:.0f}<br>{'Core requirement' if is_core else 'Supporting requirement'}" for name, value, is_core in zip(names, values, critical)], hovertemplate="%{text}<extra></extra>", showlegend=False))
    fig.update_layout(height=max(260, 38 * len(names) + 85), margin=dict(l=12,r=12,t=35,b=24), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0,100], title="Peer percentile", gridcolor="#E8E1D7", zeroline=False), yaxis=dict(autorange="reversed", tickfont=dict(size=11,color=NAVY), gridcolor="rgba(0,0,0,0)"))
    return fig, f"{role.role} · {role.phase}"


def role_fit_matrix_figure(canonical_id: str) -> go.Figure | None:
    # Kept as a compatibility name for existing profile calls; it is now a real scatter.
    return role_fit_scatter_figure(canonical_id)


@st.cache_data(show_spinner=False)
def peer_capability_frame(lane: str) -> pd.DataFrame:
    """Capability composites for every peer, used to draw real peer bands."""
    table = peer_percentile_table()
    template = POSITION_DNA.get(lane, {})
    if table.empty or not template:
        return pd.DataFrame(columns=["canonical_id", "metric", "score"])
    parts: list[pd.DataFrame] = []
    lane_rows = table[table.lane == lane]
    for metric_name, attributes in template.items():
        part = lane_rows[lane_rows.attribute.isin(attributes)].copy()
        if part.empty:
            continue
        part["weight"] = part.attribute.map({attribute: 2.0 if index < 2 else 1.0 for index, attribute in enumerate(attributes)}).fillna(1.0)
        grouped = part.groupby("canonical_id", as_index=False).apply(
            lambda group: pd.Series({"score": (group.percentile * group.weight).sum() / group.weight.sum(), "evidence": len(group)}),
            include_groups=False,
        ).reset_index()
        grouped["metric"] = metric_name
        parts.append(grouped[["canonical_id", "metric", "score", "evidence"]])
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["canonical_id", "metric", "score"])


def peer_distribution_figure(canonical_id: str) -> go.Figure | None:
    lane, scores, _ = position_metrics(canonical_id)
    if len(scores) < 3:
        return None
    peers = peer_capability_frame(lane)
    if peers.empty:
        return None
    labels = list(scores)
    fig = go.Figure()
    for label in reversed(labels):
        sample = peers.loc[peers.metric == label, "score"]
        if len(sample) < 8:
            continue
        fig.add_trace(go.Box(x=sample, y=[label] * len(sample), orientation="h", boxpoints=False,
            fillcolor="rgba(113,128,150,.14)", line=dict(color="rgba(104,119,131,.55)", width=1),
            marker_color="rgba(104,119,131,.15)", hoverinfo="skip", showlegend=False, width=.52))
    fig.add_trace(go.Scatter(x=[scores[label] for label in labels], y=labels, mode="markers",
        marker=dict(size=13, color=BURGUNDY, line=dict(color="white", width=2)),
        text=[f"<b>{esc(label)}</b><br>Player peer percentile: {scores[label]:.0f}" for label in labels],
        hovertemplate="%{text}<extra></extra>", showlegend=False))
    fig.update_layout(height=max(290, 53 * len(labels) + 55), margin=dict(l=8,r=20,t=15,b=32), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0,100], showticklabels=False, title="Lower peer range                      Peer range                      Leading peer range", title_font=dict(size=10,color=MUTED), gridcolor="#E8E1D7", zeroline=False),
        yaxis=dict(categoryorder="array", categoryarray=list(reversed(labels)), tickfont=dict(size=12, color=NAVY), gridcolor="rgba(0,0,0,0)"))
    return fig


def profile_fingerprint_figure(canonical_id: str) -> go.Figure | None:
    """Show the player's positional shape against real peer profiles, not a generic radar."""
    lane, scores, _ = position_metrics(canonical_id)
    if len(scores) < 3:
        return None
    labels = list(scores)
    peers = peer_capability_frame(lane).pivot(index="canonical_id", columns="metric", values="score").reindex(columns=labels)
    peers = peers.dropna(thresh=max(3, len(labels) - 1))
    if peers.empty:
        return None
    if len(peers) > 150:
        peers = peers.sample(150, random_state=42)
    x = list(range(len(labels)))
    fig = go.Figure()
    for _, row in peers.iterrows():
        observed_x = [index for index, value in enumerate(row.tolist()) if pd.notna(value)]
        observed_y = [row.iloc[index] for index in observed_x]
        if len(observed_x) >= 3:
            fig.add_trace(go.Scatter(x=observed_x, y=observed_y, mode="lines", line=dict(color="rgba(91,120,115,.10)", width=1), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=x, y=[scores[label] for label in labels], mode="lines+markers", name="Selected player",
        line=dict(color=BURGUNDY, width=3.6), marker=dict(size=10, color=GOLD, line=dict(color="white", width=2)),
        text=[f"<b>{esc(label)}</b><br>Player peer percentile: {scores[label]:.0f}" for label in labels], hovertemplate="%{text}<extra></extra>"))
    fig.add_hline(y=50, line=dict(color="rgba(104,119,131,.55)", dash="dot", width=1.3), annotation_text="Peer midpoint", annotation_position="bottom right", annotation_font=dict(size=10,color=MUTED))
    fig.update_layout(height=480, margin=dict(l=12,r=12,t=20,b=64), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickmode="array", tickvals=x, ticktext=labels, tickangle=-24, showgrid=False, zeroline=False, tickfont=dict(size=11,color=NAVY)),
        yaxis=dict(range=[0,100], showticklabels=False, gridcolor="#E8E1D7", zeroline=False), showlegend=False)
    return fig


def role_landscape_figure(canonical_id: str) -> go.Figure | None:
    return role_fit_scatter_figure(canonical_id)


POSITION_CONTEXT_AXES = {
    "GK": (["Distribution", "Sweeping"], ["Shot stopping", "Area command", "Reliability"], "Distribution & sweeping", "Stopping & command"),
    "ST": (["Link play", "Running power"], ["Box finishing", "Movement", "Aerial threat"], "Link & running", "Finishing & threat"),
    "AM(L/R)": (["Chance creation", "Ball security"], ["1v1 threat", "Goal threat", "Wide running"], "Creation & retention", "Direct threat"),
    "AM(C)": (["Creative progression", "Ball security"], ["Between-lines play", "Goal threat"], "Creation & security", "Between-lines & threat"),
    "M(C)": (["Progression", "Ball security", "Press resistance"], ["Defensive coverage", "Running capacity"], "Possession influence", "Defensive & running"),
    "DM": (["Build-up security", "Progression"], ["Screening", "Defensive coverage", "Duelling"], "Build-up influence", "Screening & duels"),
    "D(L/R)": (["Wide progression", "Running capacity"], ["Wide defending", "Recovery defending", "Duelling"], "Wide progression", "Defensive coverage"),
    "WB(L/R)": (["Wide progression", "Running capacity"], ["Wide defending", "Recovery defending", "Duelling"], "Wide progression", "Defensive coverage"),
    "D(C)": (["Build-up security", "Recovery defending"], ["Box defending", "Aerial dominance", "Duelling resilience"], "Build-up & recovery", "Box & aerial defending"),
}


def peer_context_figure(canonical_id: str) -> go.Figure | None:
    lane, scores, _ = position_metrics(canonical_id)
    axis_map = POSITION_CONTEXT_AXES.get(lane)
    if not axis_map:
        return None
    x_metrics, y_metrics, x_title, y_title = axis_map
    peers = peer_capability_frame(lane).pivot(index="canonical_id", columns="metric", values="score")
    needed = list(set(x_metrics + y_metrics))
    peers = peers.reindex(columns=needed)
    x = peers[x_metrics].mean(axis=1, skipna=True)
    y = peers[y_metrics].mean(axis=1, skipna=True)
    available = pd.DataFrame({"x": x, "y": y}).dropna()
    if available.empty:
        return None
    if len(available) > 220:
        available = available.sample(220, random_state=42)
    player_x = sum(scores[name] for name in x_metrics if name in scores) / len([name for name in x_metrics if name in scores])
    player_y = sum(scores[name] for name in y_metrics if name in scores) / len([name for name in y_metrics if name in scores])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=available.x, y=available.y, mode="markers", marker=dict(size=6, color="rgba(91,120,115,.34)"), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=[player_x], y=[player_y], mode="markers", marker=dict(size=16, color=BURGUNDY, line=dict(color="white", width=3)), name="Selected player", hovertemplate="<b>Selected player</b><extra></extra>"))
    fig.add_hline(y=50, line=dict(color="#D8CDBE", dash="dot", width=1))
    fig.add_vline(x=50, line=dict(color="#D8CDBE", dash="dot", width=1))
    fig.update_layout(height=280, margin=dict(l=16,r=12,t=16,b=42), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0,100], title=x_title, showticklabels=False, gridcolor="#E8E1D7", zeroline=False, title_font=dict(size=10,color=MUTED)),
        yaxis=dict(range=[0,100], title=y_title, showticklabels=False, gridcolor="#E8E1D7", zeroline=False, title_font=dict(size=10,color=MUTED)), showlegend=False)
    return fig


def evidence_strip_figure(canonical_id: str) -> go.Figure | None:
    _, scores, coverage = position_metrics(canonical_id)
    if not scores:
        return None
    labels = list(scores)
    z = [[coverage[label][0] / coverage[label][1] for label in labels]]
    text = [[f"{coverage[label][0]} of {coverage[label][1]} supporting measures" for label in labels]]
    fig = go.Figure(go.Heatmap(z=z, x=labels, y=["Recorded evidence"], zmin=0, zmax=1,
        colorscale=[[0, "#ECE6DC"], [.5, "#C5D7D1"], [1, "#5F8D87"]], showscale=False,
        text=text, hovertemplate="<b>%{x}</b><br>%{text}<extra></extra>", xgap=3, ygap=3))
    fig.update_layout(height=132, margin=dict(l=5,r=5,t=16,b=58), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickangle=-23, tickfont=dict(size=10,color=NAVY)), yaxis=dict(showticklabels=False))
    return fig


def render_player_canvas(canonical_id: str) -> None:
    """Hybrid Film Room / Decision Board. Each visual can enter a deliberate focus state."""
    charts = {
        "Profile fingerprint": (profile_fingerprint_figure, "The player is highlighted against actual profiles from the same positional peer group."),
        "Role pathways": (role_landscape_figure, "Colour shows the player’s supported fit across the positional actions required by each tactical pathway."),
        "Peer context": (peer_context_figure, "The selected player is placed among same-position peers using the two most relevant action families."),
        "Position mobility": (position_versatility_figure, "Each point estimates the player against the target position’s peer group; it is not a recommendation on its own."),
    }
    focus_key = f"canvas_focus_{canonical_id}"
    focus = st.session_state.get(focus_key, "")
    if focus:
        if st.button("← Return to analysis board", key=f"canvas_return_{canonical_id}"):
            st.session_state.pop(focus_key, None)
            st.rerun()
        figure, note = charts[focus]
        st.markdown(f"<div class='profile-section-head' style='margin-top:.7rem'>{esc(focus)}</div>", unsafe_allow_html=True)
        chart = figure(canonical_id)
        if chart:
            chart.update_layout(height=650)
            st.plotly_chart(chart, width="stretch", config={"displayModeBar": True}, key=f"canvas_focus_plot_{focus}_{canonical_id}")
            st.caption(note)
            if focus == "Role pathways":
                requirements, role_label = role_requirement_figure(canonical_id)
                if requirements:
                    st.markdown(f"<div class='profile-section-head' style='margin-top:1rem'>Requirement evidence · {esc(role_label)}</div>", unsafe_allow_html=True)
                    st.plotly_chart(requirements, width="stretch", config={"displayModeBar": True}, key=f"canvas_role_requirements_{canonical_id}")
                    st.caption("Each dot is a recorded player attribute expressed against the positional peer group. Bronze marks a core requirement; green marks a supporting one.")
        else:
            st.markdown("<div class='profile-empty'>There is not enough recorded evidence to render this view yet.</div>", unsafe_allow_html=True)
        return

    st.markdown("<div class='profile-section-head'>Scouting analysis board</div>", unsafe_allow_html=True)
    main, side = st.columns([1.62, 1], gap="medium")
    with main:
        with st.container(border=True):
            header, action = st.columns([4, 1])
            header.markdown("<div class='profile-section-head'>Profile fingerprint</div>", unsafe_allow_html=True)
            if action.button("Expand", key=f"canvas_open_fingerprint_{canonical_id}"):
                st.session_state[focus_key] = "Profile fingerprint"
                st.rerun()
            chart = profile_fingerprint_figure(canonical_id)
            if chart:
                chart.update_layout(height=250, margin=dict(l=8, r=8, t=6, b=48))
                st.plotly_chart(chart, width="stretch", config={"displayModeBar": False}, key=f"canvas_fingerprint_{canonical_id}")
            else:
                st.markdown("<div class='profile-empty'>Not enough evidence for a positional fingerprint yet.</div>", unsafe_allow_html=True)
        with st.container(border=True):
            header, action = st.columns([4, 1])
            header.markdown("<div class='profile-section-head'>Position mobility</div>", unsafe_allow_html=True)
            if action.button("Expand", key=f"canvas_open_Position mobility_{canonical_id}"):
                st.session_state[focus_key] = "Position mobility"
                st.rerun()
            chart = position_versatility_figure(canonical_id)
            if chart:
                chart.update_layout(height=160, margin=dict(l=18, r=12, t=5, b=28))
                st.plotly_chart(chart, width="stretch", config={"displayModeBar": False}, key=f"canvas_Position mobility_{canonical_id}")
            else:
                st.caption("Not enough supporting evidence yet.")
    with side:
        for name in ("Role pathways", "Peer context"):
            with st.container(border=True):
                header, action = st.columns([4, 1])
                header.markdown(f"<div class='profile-section-head'>{esc(name)}</div>", unsafe_allow_html=True)
                if action.button("Expand", key=f"canvas_open_{name}_{canonical_id}"):
                    st.session_state[focus_key] = name
                    st.rerun()
                chart = charts[name][0](canonical_id)
                if chart:
                    chart.update_layout(height=195, margin=dict(l=8, r=8, t=5, b=30))
                    st.plotly_chart(chart, width="stretch", config={"displayModeBar": False}, key=f"canvas_{name}_{canonical_id}")
                else:
                    st.caption("Not enough supporting evidence yet.")


def position_versatility_figure(canonical_id: str) -> go.Figure | None:
    """Plot alternative-lane fit from target-lane percentiles, never source-lane averages."""
    current = sql("SELECT position FROM players WHERE canonical_id=?", (canonical_id,))
    if current.empty:
        return None
    current_lane = player_lane(current.iloc[0].position)
    if not current_lane:
        return None
    adjacent = {
        "GK": ["GK"], "ST": ["ST", "AM(C)", "AM(L/R)"],
        "AM(L/R)": ["AM(L/R)", "M(L/R)", "AM(C)", "ST"],
        "AM(C)": ["AM(C)", "M(C)", "ST", "AM(L/R)"],
        "M(C)": ["M(C)", "DM", "AM(C)", "D(C)"],
        "DM": ["DM", "M(C)", "D(C)", "D(L/R)"],
        "D(L/R)": ["D(L/R)", "WB(L/R)", "D(C)", "DM"],
        "WB(L/R)": ["WB(L/R)", "D(L/R)", "M(L/R)", "DM"],
        "D(C)": ["D(C)", "DM", "D(L/R)", "WB(L/R)"],
    }.get(current_lane, [current_lane])
    raw = peer_attribute_table()
    mine = raw[raw.canonical_id.astype(str) == str(canonical_id)]
    if mine.empty:
        return None
    own = dict(zip(mine.attribute.astype(str), mine.normalized.astype(float)))
    records: list[dict[str, object]] = []
    for lane in adjacent:
        template = POSITION_DNA.get(lane, {})
        names = sorted({name for group in template.values() for name in group if name in own})
        if len(names) < 3:
            continue
        percentages = []
        for name in names:
            cohort = raw[(raw.lane == lane) & (raw.attribute == name)].normalized
            if len(cohort) >= 8:
                percentages.append(float((cohort <= own[name]).mean() * 100))
        if len(percentages) < 3:
            continue
        defend_names = {"Marking", "Tackling", "Positioning", "Anticipation", "Concentration", "Heading", "Jumping Reach", "Strength", "Bravery", "Work Rate"}
        defend = [value for name, value in zip(names, percentages) if name in defend_names]
        possession = [value for name, value in zip(names, percentages) if name not in defend_names]
        records.append({"lane": lane, "defensive": sum(defend) / len(defend) if defend else sum(percentages) / len(percentages),
                        "possession": sum(possession) / len(possession) if possession else sum(percentages) / len(percentages),
                        "coverage": len(percentages) / len({name for group in template.values() for name in group}),
                        "primary": lane == current_lane})
    if not records:
        return None
    frame = pd.DataFrame(records)
    fig = go.Figure()
    fig.add_hline(y=50, line=dict(color="#D8CDBE", dash="dot", width=1))
    fig.add_vline(x=50, line=dict(color="#D8CDBE", dash="dot", width=1))
    fig.add_trace(go.Scatter(x=frame.defensive, y=frame.possession, mode="markers+text", text=frame.lane,
        textposition="top center", marker=dict(size=frame.coverage * 22 + 10, color=[BURGUNDY if value else "#69968F" for value in frame.primary],
        line=dict(color="white", width=2)), hovertemplate="<b>%{text}</b><br>Defensive suitability: %{x:.0f}<br>In-possession suitability: %{y:.0f}<extra></extra>"))
    fig.update_layout(height=310, margin=dict(l=28,r=18,t=22,b=35), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0,100], title="Defensive suitability", gridcolor="#E8E1D7", zeroline=False),
        yaxis=dict(range=[0,100], title="In-possession suitability", gridcolor="#E8E1D7", zeroline=False), showlegend=False,
        annotations=[dict(x=82,y=93,text="Natural fit",showarrow=False,font=dict(color=MUTED,size=11)),dict(x=18,y=8,text="Low evidence",showarrow=False,font=dict(color=MUTED,size=11))])
    return fig


def render_role_fit(canonical_id: str, profile_key: str | None = None, detailed: bool = False) -> None:
    fits = role_fit_estimates(canonical_id, profile_key)
    st.markdown("<div class='profile-section-head'>Role fit</div>", unsafe_allow_html=True)
    if fits.empty:
        st.markdown("<div class='profile-empty'>There is not enough positional evidence to calculate a role profile yet.</div>", unsafe_allow_html=True)
        return
    matrix = role_fit_matrix_figure(canonical_id)
    if matrix:
        st.plotly_chart(matrix, width="stretch", config={"displayModeBar": False}, key=f"role_matrix_{'detail' if detailed else 'overview'}_{canonical_id}")
    for phase, label in (("In Possession", "With the ball"), ("Out Of Possession", "Without the ball")):
        row = fits[fits.phase == phase].sort_values("score", ascending=False).head(1)
        if not row.empty:
            best = row.iloc[0]
            st.caption(f"{label}: {best.role} · based on {int(best.known)}/{int(best.required)} available requirements")
    st.caption("Each dot is a calculated role outcome: horizontal position is fit, vertical position is evidence coverage. Missing evidence is excluded, never treated as a low score.")


def attr_rows_html(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "<div class='empty-card'>No detailed attributes available.</div>"
    rows = []
    sort_column = "normalized_score" if "normalized_score" in frame.columns else "score"
    for _, row in frame.sort_values(sort_column, ascending=False).iterrows():
        raw_score = float(row.score)
        normalized = float(row.get("normalized_score", raw_score))
        scale = float(row.get("scale_max", 100) or 100)
        rows.append(
            f"<div class='attribute-card'><div class='attr-row'><div class='attr-name'>{esc(row.attribute)}</div>"
            f"<div class='attr-track'><div class='attr-fill' style='width:{max(0, min(100, normalized)):.0f}%'></div></div>"
            f"<div class='attr-score'>{raw_score:g}/{scale:g}</div></div></div>"
        )
    return "".join(rows)


def options_from(frame: pd.DataFrame, column: str) -> list[str]:
    return ["All"] + sorted(
        {
            str(value).strip()
            for value in frame[column].dropna()
            if str(value).strip() and str(value).strip().lower() not in {"nan", "none"}
        }
    )


def sync_nav() -> None:
    st.session_state.nav = st.session_state.nav_input


def set_nav(page: str, club: str | None = None, player: str | None = None) -> None:
    st.session_state.nav = page
    st.session_state.nav_pending = page
    if club is not None:
        st.session_state.selected_club = club
    if player is not None:
        st.session_state.selected_player = player


if not DB_PATH.is_file():
    st.error("The scouting database is not available. Run build_database.py once before starting the tool.")
    st.stop()

METADATA = load_metadata()
PLAYERS = load_players()
CLUBS = load_clubs()

if PLAYERS.empty or CLUBS.empty:
    st.error("The scouting database opened, but it contains no academies or players.")
    st.stop()

if "nav" not in st.session_state:
    st.session_state.nav = "Academy Directory"
if "nav_input" not in st.session_state:
    st.session_state.nav_input = st.session_state.nav
if "nav_pending" in st.session_state:
    st.session_state.nav = st.session_state.nav_pending
    st.session_state.nav_input = st.session_state.nav_pending
    del st.session_state.nav_pending
if "selected_club" not in st.session_state:
    st.session_state.selected_club = CLUBS.iloc[0].club
if "selected_player" not in st.session_state:
    enriched_players = PLAYERS[PLAYERS.has_scouting_data == 1]
    st.session_state.selected_player = (
        enriched_players.iloc[0].canonical_id if not enriched_players.empty else PLAYERS.iloc[0].canonical_id
    )

position_options = sorted(PLAYERS.position.dropna().astype(str).str.strip().loc[lambda values: values.ne("")].unique().tolist())

with st.sidebar:
    st.markdown("### Player filters")
    selected_position = st.selectbox("Position", ["All positions", *position_options])
    if selected_position == "All positions":
        role_codes_for_filter = {str(code) for item in ROLE_CRITERIA for code in (item.get("position", []) if isinstance(item.get("position"), list) else [item.get("position")])}
    else:
        role_codes_for_filter, _ = role_position_codes(selected_position)
    role_choice_map: dict[str, str] = {}
    for item in ROLE_CRITERIA:
        role_codes = item.get("position", [])
        if isinstance(role_codes, str):
            role_codes = [role_codes]
        if not role_codes_for_filter.intersection(str(code) for code in role_codes):
            continue
        phase_label = str(item.get("phase", "")).replace("_", " ").title()
        role_key = f"{item.get('phase')}|{item.get('role_name')}"
        role_choice_map[f"{phase_label} · {item.get('role_name')}"] = role_key
    role_choice = st.selectbox(
        "Player type (optional)",
        ["Any role", *role_choice_map],
        key=f"global_player_type_{selected_position}",
        disabled=(selected_position == "All positions"),
        help="Choose a position first, then optionally narrow the list to a playing role.",
    )
    selected_role_filter = role_choice_map.get(role_choice, "") if selected_position != "All positions" else ""
    if selected_position == "All positions":
        st.caption("Choose a position to see its role types.")
    st.markdown(
        "<div style='height:.6rem'></div><div style='font-size:.7rem;color:#94A3B8;line-height:1.5'>"
        "Explore U18 and U21 academy squads.<br>"
        "Open a club or player for profiles and history.<br>"
        "Roster scope: academy teams only.</div>",
        unsafe_allow_html=True,
    )


def apply_player_filters(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    mask = pd.Series(True, index=frame.index)
    if selected_position != "All positions":
        mask &= frame.position.fillna("").astype(str).str.strip().eq(selected_position)
    filtered = frame.loc[mask].copy()
    if selected_role_filter and not filtered.empty:
        player_ids = tuple(sorted(filtered.canonical_id.astype(str).unique()))
        role_index = cached_role_fit_index(player_ids)
        phase, role = selected_role_filter.split("|", 1)
        phase = phase.replace("_", " ").title()
        matching_ids = set(
            role_index.loc[(role_index.phase == phase) & (role_index.role == role), "canonical_id"].astype(str)
        ) if not role_index.empty else set()
        filtered = filtered[filtered.canonical_id.astype(str).isin(matching_ids)]
    return filtered


page = st.session_state.nav

with st.container(key="app_top_nav"):
    nav_cols = st.columns([2.25, 1.12, .86, .72, .92])
    with nav_cols[0]:
        st.markdown("<div class='app-brand'>England Academy Scouting</div>", unsafe_allow_html=True)
    with nav_cols[1]:
        st.button("Academy Directory", key="app_nav_directory", width="stretch",
                  type="primary" if page == "Academy Directory" else "secondary",
                  on_click=set_nav, args=("Academy Directory", None, None))
    with nav_cols[2]:
        st.button("Club Profile", key="app_nav_club", width="stretch",
                  type="primary" if page == "Club Profile" else "secondary",
                  on_click=set_nav, args=("Club Profile", st.session_state.selected_club, None))
    with nav_cols[3]:
        st.button("Players", key="app_nav_players", width="stretch",
                  type="primary" if page == "Player Profile" else "secondary",
                  on_click=set_nav, args=("Player Profile", None, None))
    with nav_cols[4]:
        st.button("Compare Players", key="app_nav_compare", width="stretch",
                  type="primary" if page == "Compare Players" else "secondary",
                  on_click=set_nav, args=("Compare Players", None, None))


if page == "Academy Directory":
    @st.cache_data(show_spinner=False)
    def directory_regions():
        path = ROOT / "data" / "england_regions.topojson"
        if not path.exists():
            return {}
        topology = json.loads(path.read_text(encoding="utf-8"))
        transform = topology["transform"]
        decoded = []
        for raw_arc in topology["arcs"]:
            x = y = 0
            arc = []
            for dx, dy in raw_arc:
                x += dx; y += dy
                arc.append((x * transform["scale"][0] + transform["translate"][0],
                            y * transform["scale"][1] + transform["translate"][1]))
            decoded.append(arc)
        def ring(indices):
            result = []
            for index in indices:
                arc = decoded[index] if index >= 0 else list(reversed(decoded[~index]))
                result.extend(arc if not result else arc[1:])
            return result
        result = {}
        for geometry in topology["objects"]["Eregion"]["geometries"]:
            polygons = geometry["arcs"] if geometry["type"] == "MultiPolygon" else [geometry["arcs"]]
            result[geometry["properties"]["AREANM"]] = [[ring(r) for r in polygon] for polygon in polygons]
        return result

    def directory_inside_ring(lon, lat, ring):
        inside = False
        j = len(ring) - 1
        for i, (x, y) in enumerate(ring):
            xj, yj = ring[j]
            if ((y > lat) != (yj > lat)) and lon < (xj - x) * (lat - y) / (yj - y) + x:
                inside = not inside
            j = i
        return inside

    def directory_region_for(lon, lat, regions):
        if pd.isna(lon) or pd.isna(lat):
            return "Location not recorded"
        for name, polygons in regions.items():
            for polygon in polygons:
                if polygon and directory_inside_ring(float(lon), float(lat), polygon[0]) and not any(
                    directory_inside_ring(float(lon), float(lat), hole) for hole in polygon[1:]
                ):
                    return name
        return "Outside mapped regions"

    regions = directory_regions()
    directory = CLUBS.copy()
    directory["region"] = [directory_region_for(row.lon, row.lat, regions) for _, row in directory.iterrows()]
    def directory_logo_src(item):
        logo = safe(item.academy_logo_url, "")
        for candidate in (logo, safe(item.academy_logo_fallback, "")):
            if candidate:
                cached = ROOT / "data" / "club_logos" / (hashlib.sha256(candidate.encode("utf-8")).hexdigest() + ".png")
                if cached.is_file():
                    return "data:image/png;base64," + base64.b64encode(cached.read_bytes()).decode("ascii")
        return logo

    # The directory deliberately uses the full-width regional workspace from the approved concept.
    st.markdown("""
    <style>
    section[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {display:none !important;}
    header[data-testid="stHeader"] {height:0 !important; min-height:0 !important;}
    [data-testid="stToolbar"], [data-testid="stDecoration"] {display:none !important;}
    .block-container {max-width:none !important; padding:0 1.35rem 1.1rem !important;}
    .st-key-app_top_nav {margin:0 -1.35rem .15rem;padding:.42rem 1.7rem .25rem;}
    .st-key-directory_top_nav {border-bottom:1px solid #DDD8CF; margin:0 -1.35rem; padding:.42rem 1.7rem .25rem; background:rgba(250,249,246,.98);}
    .st-key-directory_top_nav [data-testid="stHorizontalBlock"] {align-items:center;}
    .directory-brand {display:flex;align-items:center;gap:11px;font-size:1.08rem;font-weight:950;color:#1F3446;white-space:nowrap;}
    .st-key-directory_top_nav .stButton>button {border:0 !important;border-radius:0 !important;background:transparent !important;min-height:2.55rem;font-size:.84rem !important;padding:.25rem .35rem !important;}
    .st-key-directory_top_nav .stButton>button:hover {color:#A8793F !important;}
    .st-key-directory_top_nav button[kind="primary"] {color:#1F3446 !important;border-bottom:4px solid #A8793F !important;}
    .directory-title-row {display:flex;align-items:flex-end;justify-content:space-between;gap:24px;padding:1.05rem .45rem .9rem;}
    .directory-kicker {font-size:.68rem;letter-spacing:.13em;text-transform:uppercase;font-weight:950;color:#A8793F;}
    .directory-title-line {display:flex;align-items:center;gap:22px;margin-top:.15rem;}
    .directory-title-main {margin:0;color:#1F3446;font-size:2rem;letter-spacing:-.045em;line-height:1;font-weight:950;white-space:nowrap;}
    .directory-title-line span {border-left:1px solid #C9C0B3;padding-left:20px;color:#687783;font-size:.82rem;}
    .directory-stats {display:flex;align-items:center;justify-content:flex-end;gap:0;}
    .directory-stat {min-width:92px;text-align:center;padding:0 16px;border-left:1px solid #C9C0B3;}
    .directory-stat.coverage {display:flex;align-items:center;gap:8px;text-align:left;min-width:150px;}
    .directory-pin {font-size:1.55rem;color:#A8793F;line-height:1;}
    .directory-stat b {display:block;color:#1F3446;font-size:1.28rem;line-height:1;font-weight:950;}
    .directory-stat small {display:block;color:#687783;font-size:.68rem;margin-top:5px;}
    .directory-stat.coverage b {font-size:.88rem;line-height:1.05;}
    .st-key-directory_workspace {border:1px solid #DDD8CF;border-radius:13px;overflow:hidden;background:#FAF9F6;box-shadow:0 8px 28px rgba(31,52,70,.055);}
    .st-key-directory_workspace > div[data-testid="stHorizontalBlock"] {gap:0 !important;align-items:stretch;}
    .st-key-directory_filters {padding:12px 13px 0;background:#FAF9F6;border-right:1px solid #DDD8CF;min-height:755px;}
    .st-key-directory_filters [data-testid="stTextInputRootElement"] {min-height:2.45rem;border:1px solid #C9C0B3 !important;border-radius:7px !important;background:#F7F4EE !important;box-shadow:0 0 0 1px rgba(169,151,128,.12) !important;padding:0 .6rem;}
    .st-key-directory_filters .react-aria-ComboBox [role="group"] {min-height:2.25rem;border:1px solid #C9C0B3 !important;border-radius:7px !important;background:#F7F4EE !important;box-shadow:0 0 0 1px rgba(169,151,128,.12) !important;padding:0 .45rem;}
    .directory-filter-title {display:flex;justify-content:space-between;align-items:center;margin:.1rem 0 .45rem;color:#1F3446;font-size:.95rem;font-weight:950;}
    .directory-filter-title a {font-size:.7rem;color:#A8793F;text-decoration:none;}
    .directory-filter-label {font-size:.7rem;color:#1F3446;font-weight:900;margin:.42rem 0 .2rem;}
    .st-key-directory_filters label p {font-size:.68rem !important;font-weight:780 !important;color:#1F3446 !important;}
    .st-key-directory_filters [data-testid="stCheckbox"] {margin-top:-.25rem;}
    .st-key-directory_list {margin:10px -13px 0;border-top:1px solid #DDD8CF;padding:11px 10px 0;background:#FAF9F6;}
    .directory-list-head {display:flex;justify-content:space-between;align-items:center;padding:0 5px 7px;color:#0B1F3A;font-weight:950;font-size:.86rem;}
    .directory-list-head span {font-size:.66rem;font-weight:700;color:#475569;}
    .st-key-directory_list [data-testid="stVerticalBlockBorderWrapper"] {border:0 !important;border-radius:0 !important;}
    .st-key-directory_list .stButton>button {text-align:left !important;justify-content:flex-start !important;border:0 !important;border-bottom:1px solid #E5DED4 !important;border-radius:0 !important;min-height:3.55rem;padding:.42rem .35rem !important;font-size:.72rem !important;}
    .dir-list-logo {width:34px;height:34px;border-radius:7px;background:#FAF9F6;display:flex;align-items:center;justify-content:center;}
    .dir-list-logo img {max-width:29px;max-height:29px;object-fit:contain;}.dir-list-logo .club-logo-fallback{font-size:.55rem;}
    .st-key-directory_map {background:#EAF0EF;min-height:755px;border-right:1px solid #DDD8CF;}
    .st-key-directory_map [data-testid="stPlotlyChart"] {margin:0 !important;}
    .st-key-directory_map .js-plotly-plot {height:755px !important;}
    .st-key-directory_details {padding:19px 18px 16px;background:#FAF9F6;min-height:755px;}
    .directory-detail-head {display:flex;align-items:center;gap:14px;padding:3px 0 12px;}
    .directory-detail-logo {width:64px;height:64px;border-radius:14px;border:1px solid #DDD8CF;display:flex;align-items:center;justify-content:center;background:#F7F4EE;flex:0 0 auto;}
    .directory-detail-logo img {max-width:52px;max-height:52px;object-fit:contain;}.directory-detail-logo .club-logo-fallback{font-size:.7rem;}
    .directory-detail-name {font-size:1.36rem;line-height:1.02;font-weight:950;color:#0B1F3A;letter-spacing:-.025em;}
    .directory-detail-region {font-size:.73rem;color:#415A77;margin-top:7px;}
    .directory-tabs {display:grid;grid-template-columns:1fr 1.15fr .8fr;border-bottom:1px solid #DDD8CF;margin:4px -18px 13px;}
    .directory-tab {text-align:center;font-size:.72rem;color:#0B1F3A;font-weight:820;padding:.72rem .1rem;}
    .directory-tab.active {border-bottom:3px solid #A8793F;}
    .directory-overview {font-size:.76rem;line-height:1.45;color:#334B68;margin:0 0 12px;}
    .directory-fact-grid {display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:15px;}
    .directory-fact {border:1px solid #DDD8CF;border-radius:9px;padding:10px 9px;min-height:88px;background:#F5F1EA;}
    .directory-fact i {font-style:normal;color:#A8793F;font-size:1.05rem;}.directory-fact span{display:block;color:#687783;font-size:.62rem;margin-top:5px;}.directory-fact b{display:block;color:#1F3446;font-size:.78rem;line-height:1.15;margin-top:4px;}
    .directory-section-title {font-size:.91rem;color:#0B1F3A;font-weight:950;margin:15px 0 8px;}
    .directory-squad-card {border:1px solid #DDD8CF;border-radius:9px;background:linear-gradient(90deg,#FAF9F6,#F1ECE4);padding:10px 12px;display:flex;align-items:center;justify-content:space-between;}
    .directory-squad-card b {font-size:.78rem;color:#0B1F3A;}.directory-squad-card span {font-size:.68rem;color:#536B83;}.directory-squad-total{text-align:center;border-left:1px solid #CCD5DE;padding-left:22px}.directory-squad-total strong{display:block;font-size:1.25rem;color:#0B1F3A;}
    .directory-breakdown {display:grid;grid-template-columns:repeat(4,1fr);border:1px solid #DDD8CF;border-radius:9px;padding:9px 0;margin-top:8px;background:#F5F1EA;}
    .directory-breakdown div{text-align:center;border-right:1px solid #DCE4EC;font-size:.64rem;color:#415A77}.directory-breakdown div:last-child{border-right:0}.directory-breakdown b{display:block;color:#0B1F3A;font-size:1rem;margin-top:3px;}
    .st-key-directory_details .stRadio [role="radiogroup"] {justify-content:flex-end;background:#F1ECE4;border:1px solid #DDD8CF;border-radius:999px;padding:2px;gap:0;}
    .st-key-directory_details .stRadio label {padding:.25rem .75rem;border-radius:999px;}.st-key-directory_details .stRadio label:has(input:checked){background:#A8793F;}.st-key-directory_details .stRadio label:has(input:checked) p{color:white !important;}
    .st-key-directory_details .stButton>button {margin-top:13px;border:1px solid #A8793F !important;color:#805A2E !important;background:#FAF9F6 !important;}
    .directory-brand,.directory-title-main,.directory-stat b,.directory-filter-title,.directory-filter-label,.directory-list-head,.directory-detail-name,.directory-tab,.directory-fact b,.directory-section-title,.directory-squad-card b,.directory-breakdown b {color:#1F3446 !important;}
    .directory-kicker,.directory-pin {color:#A8793F !important;}
    .directory-title-line span,.directory-stat small,.directory-detail-region,.directory-overview,.directory-fact span,.directory-squad-card span,.directory-breakdown div {color:#687783 !important;}
    @media(max-width:1100px){.directory-title-row{align-items:flex-start;flex-direction:column}.directory-stats{width:100%;justify-content:flex-start}.directory-stat{min-width:78px}.st-key-directory_workspace>div[data-testid="stHorizontalBlock"]{flex-direction:column}.st-key-directory_filters,.st-key-directory_map,.st-key-directory_details{min-height:auto;border-right:0;border-bottom:1px solid #DDD8CF}.st-key-directory_map .js-plotly-plot{height:620px !important;}}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        f"<div class='directory-title-row'><div><div class='directory-kicker'>03 Regional scouting</div>"
        f"<div class='directory-title-line'><div class='directory-title-main'>Academy Directory</div><span>Geographic intelligence for England's player pathway.</span></div></div>"
        f"<div class='directory-stats'><div class='directory-stat coverage'><div class='directory-pin'>●</div><b>England<br>Coverage</b></div>"
        f"<div class='directory-stat'><b>{len(regions)}</b><small>Regions</small></div>"
        f"<div class='directory-stat'><b>{len(directory)}</b><small>Academies</small></div>"
        f"<div class='directory-stat'><b>{int((directory.u18_count > 0).sum())}</b><small>U18 Squads</small></div>"
        f"<div class='directory-stat'><b>{int((directory.u21_count > 0).sum())}</b><small>U21 Squads</small></div></div></div>",
        unsafe_allow_html=True,
    )

    with st.container(key="directory_workspace"):
        filters_col, map_col, details_col = st.columns([1.02, 1.78, 1.12], gap=None)
        with filters_col:
            with st.container(key="directory_filters"):
                search = st.text_input("Search", placeholder="Search academy or region", key="directory_search_v3", label_visibility="collapsed")
                st.markdown("<div class='directory-filter-title'>Filters <a>Clear all</a></div>", unsafe_allow_html=True)
                region_options = ["All regions"] + sorted(directory.region.unique().tolist())
                selected_region = st.selectbox("Region", region_options, key="directory_region_v3")
                category_options = [f"Category {number}" for number in range(1, 5)]
                extra_categories = [str(x) for x in directory.academy_category.dropna().unique() if str(x) not in category_options]
                all_categories = category_options + sorted(extra_categories)
                st.markdown("<div class='directory-filter-label'>Category</div>", unsafe_allow_html=True)
                category_cols = st.columns(2)
                selected_categories = []
                for index, category in enumerate(all_categories):
                    with category_cols[index % 2]:
                        if st.checkbox(category, value=True, key=f"directory_category_check_{category}"):
                            selected_categories.append(category)
                st.markdown("<div class='directory-filter-label'>Youth squad</div>", unsafe_allow_html=True)
                squad_filters = st.columns(2)
                with squad_filters[0]:
                    only_u18 = st.checkbox("U18", value=True, key="directory_u18_v3")
                with squad_filters[1]:
                    only_u21 = st.checkbox("U21", value=True, key="directory_u21_v3")

                shown = directory[directory.academy_category.isin(selected_categories)].copy()
                if selected_region != "All regions":
                    shown = shown[shown.region == selected_region]
                if search.strip():
                    query = search.strip()
                    mask = shown.club.str.contains(query, case=False, na=False, regex=False) | shown.region.str.contains(query, case=False, na=False, regex=False)
                    shown = shown[mask]
                if only_u18 and not only_u21:
                    shown = shown[shown.u18_count > 0]
                elif only_u21 and not only_u18:
                    shown = shown[shown.u21_count > 0]
                shown = shown.sort_values("club")

                with st.container(key="directory_list"):
                    st.markdown(f"<div class='directory-list-head'>Academies ({len(shown)})<span>Sort: Relevance⌄</span></div>", unsafe_allow_html=True)
                    with st.container(height=420, border=True):
                        for _, item in shown.iterrows():
                            selected = st.session_state.get("directory_selected_v3") == item.club
                            icon_col, club_col = st.columns([.18, 1], vertical_alignment="center", gap="small")
                            with icon_col:
                                st.markdown(logo_html(directory_logo_src(item), item.club, "dir-list-logo", item.academy_logo_fallback), unsafe_allow_html=True)
                            with club_col:
                                label = f"{'●  ' if selected else ''}{item.club} Academy  ·  {safe(item.academy_category)}  ›"
                                if st.button(label, key=f"directory_select_v3_{item.club}", width="stretch"):
                                    st.session_state.directory_selected_v3 = item.club
                                    st.session_state.selected_club = item.club
                                    st.session_state.directory_last_map_click_v3 = None
                                    st.rerun()
                        if shown.empty:
                            st.caption("No academies match these filters.")
    if st.session_state.get("directory_selected_v3") not in shown.club.tolist():
        preferred = st.session_state.get("selected_club", "")
        st.session_state.directory_selected_v3 = preferred if preferred in shown.club.tolist() else (shown.iloc[0].club if not shown.empty else None)
    if st.session_state.get("directory_selected_v3") in directory.club.tolist():
        st.session_state.selected_club = st.session_state.directory_selected_v3
    with map_col, st.container(key="directory_map"):
        fig = go.Figure()
        for name, polygons in regions.items():
            for polygon in polygons:
                if not polygon or not polygon[0]:
                    continue
                ring = polygon[0]
                fig.add_trace(go.Scattermap(
                    lon=[point[0] for point in ring], lat=[point[1] for point in ring],
                    mode="lines", fill="toself", fillcolor="rgba(250,251,250,.94)",
                    line=dict(color="#92AAA7", width=1.05), hoverinfo="skip", showlegend=False, name=name,
                ))
        category_colors = {"Category 1":"#B79A64", "Category 2":"#6F9993", "Category 3":"#607A92", "Category 4":"#A9B5BD"}
        mapped = shown.dropna(subset=["lat", "lon"]).copy()
        # Place each regional label at a point inside its real boundary.
        region_anchors = {"North East": (-1.9, 55.0), "North West": (-2.7, 53.95),
                          "Yorkshire and The Humber": (-1.4, 53.95), "East Midlands": (-0.9, 52.95),
                          "West Midlands": (-2.25, 52.55), "East of England": (.25, 52.3),
                          "London": (-.12, 51.51), "South East": (-.6, 51.1), "South West": (-3.4, 50.85)}
        label_positions = []
        for region_name, (lon, lat) in region_anchors.items():
            count = int((shown.region == region_name).sum())
            if count and directory_region_for(lon, lat, regions) == region_name:
                label_positions.append((region_name, lon, lat, count))
        if label_positions:
            region_text = [f"{name}<br>{count} academies" for name, lon, lat, count in label_positions]
            fig.add_trace(go.Scattermap(
                lon=[v[1] for v in label_positions], lat=[v[2] for v in label_positions], mode="text",
                text=region_text, textfont=dict(size=9, color="#5F807D"), hoverinfo="skip", showlegend=False,
            ))
        chosen_map = mapped[mapped.club == st.session_state.get("directory_selected_v3")]
        if not chosen_map.empty:
            point = chosen_map.iloc[0]
            fig.add_trace(go.Scattermap(
                lon=[point.lon], lat=[point.lat], mode="markers+text", text=[point.club], textposition="bottom center",
                textfont=dict(size=10, color="#243447"), marker=dict(size=27, color="#D8C39B", opacity=.52),
                hoverinfo="skip", showlegend=False,
            ))
        # Exact coincident locations share a marker; the detail panel exposes all clubs there.
        for category_name in category_options + sorted(extra_categories):
            group = mapped[mapped.academy_category == category_name]
            if group.empty:
                continue
            points = [(lat, lon, group_at.club.tolist()) for (lat, lon), group_at in group.groupby(["lat", "lon"], sort=False)]
            common = dict(mode="markers+text", text=[str(len(p[2])) if len(p[2]) > 1 else "" for p in points],
                textposition="middle center", textfont=dict(size=10, color="white"), customdata=[p[2][0] for p in points],
                hovertext=["<br>".join(esc(n) for n in p[2]) for p in points], hovertemplate="%{hovertext}<extra>"+esc(category_name)+"</extra>",
                name=f"{category_name} ({len(group)})")
            fig.add_trace(go.Scattermap(
                lon=[p[1] for p in points], lat=[p[0] for p in points],
                marker=dict(size=[17 if len(p[2]) > 1 else 9 for p in points], color=category_colors.get(category_name, "#A9B5BD"), opacity=.82),
                **common,
            ))
        if regions or not mapped.empty:
            fig.update_layout(
                height=755, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor="#EAF0EF",
                map=dict(style="open-street-map", center=dict(lat=52.65, lon=-1.55), zoom=5.4),
                legend=dict(
                    title=dict(text="<b>Academy Category</b>"), orientation="v", y=.985, yanchor="top", x=.985, xanchor="right",
                    bgcolor="rgba(255,255,255,.94)", bordercolor="#D7E1EA", borderwidth=1, font=dict(size=10, color="#0B1F3A"),
                ),
                clickmode="event+select", uirevision="directory_regional_map_v4",
            )
            event = st.plotly_chart(
                fig, width="stretch", config={"displayModeBar": False, "displaylogo": False},
                key="directory_map_regional_v4", on_select="rerun", selection_mode="points",
            )
            points = event.selection.points if event and event.selection else []
            if points:
                clicked = points[0].get("customdata")
                if isinstance(clicked, str) and clicked in shown.club.tolist() and clicked != st.session_state.get("directory_last_map_click_v3"):
                    st.session_state.directory_selected_v3 = clicked
                    st.session_state.selected_club = clicked
                    st.session_state.directory_last_map_click_v3 = clicked
        else:
            st.info("Map boundaries and club coordinates are not available.")
    with details_col, st.container(key="directory_details"):
        chosen = st.session_state.get("directory_selected_v3")
        if chosen and chosen in shown.club.tolist():
            meta = shown[shown.club == chosen].iloc[0]
            logo = directory_logo_src(meta)
            st.markdown(
                f"<div class='directory-detail-head'>"
                f"{logo_html(logo, chosen, 'directory-detail-logo', meta.academy_logo_fallback)}"
                f"<div><div class='directory-detail-name'>{esc(chosen)}<br>Academy</div>"
                f"<div class='directory-detail-region'>⌖ {esc(meta.region)}</div>"
                f"<span class='pill'>{esc(meta.academy_category)}</span></div></div>"
                f"<div class='directory-tabs'><div class='directory-tab active'>Overview</div>"
                f"<div class='directory-tab'>Squad Context</div><div class='directory-tab'>Location</div></div>"
                f"<div class='directory-overview'>Academy programme in {esc(meta.region)} with recorded youth-squad coverage shown from the current scouting database.</div>"
                f"<div class='directory-fact-grid'>"
                f"<div class='directory-fact'><i>⌂</i><span>Academy Category</span><b>{esc(meta.academy_category)}</b></div>"
                f"<div class='directory-fact'><i>♙</i><span>Youth Squads</span><b>{'U18 & U21' if int(meta.u18_count)>0 and int(meta.u21_count)>0 else ('U18' if int(meta.u18_count)>0 else ('U21' if int(meta.u21_count)>0 else 'Not recorded'))}</b></div>"
                f"<div class='directory-fact'><i>⌖</i><span>Region</span><b>{esc(meta.region)}</b></div></div>",
                unsafe_allow_html=True,
            )
            squad_title, squad_toggle = st.columns([1.2, 1], vertical_alignment="center")
            with squad_title:
                st.markdown("<div class='directory-section-title'>Squad Context</div>", unsafe_allow_html=True)
            with squad_toggle:
                squad = st.radio("Squad", ["U18", "U21"], horizontal=True, key="directory_detail_squad_v3", label_visibility="collapsed")
            count = int(meta.u18_count if squad == "U18" else meta.u21_count)
            status = safe(meta.u18_roster_status if squad == "U18" else meta.u21_roster_status, "Not recorded")
            members = load_team_players(chosen, squad)
            groups = pd.Series(dtype="int64")
            if not members.empty:
                def detail_group(value):
                    value = safe(value, "").casefold()
                    if "goalkeeper" in value or value == "gk": return "GK"
                    if any(word in value for word in ("defender", "back")): return "DEF"
                    if "midfield" in value: return "MID"
                    if any(word in value for word in ("attack", "winger", "forward", "striker")): return "FWD"
                    return "Unknown"
                groups = members.position.map(detail_group).value_counts()
            st.markdown(
                f"<div class='directory-squad-card'><div><b>♙ &nbsp;{esc(squad)} Squad</b><br>"
                f"<span>{esc(status)}</span></div><div class='directory-squad-total'><span>Total</span><strong>{count}</strong></div></div>"
                f"<div class='directory-filter-label'>Squad breakdown</div>"
                f"<div class='directory-breakdown'>"
                f"<div>GK<b>{int(groups.get('GK',0))}</b></div><div>DEF<b>{int(groups.get('DEF',0))}</b></div>"
                f"<div>MID<b>{int(groups.get('MID',0))}</b></div><div>FWD<b>{int(groups.get('FWD',0))}</b></div></div>",
                unsafe_allow_html=True,
            )
            if members.empty:
                st.caption("No player roster is recorded for this squad.")
            elif groups.get("Unknown", 0):
                st.caption(f"{int(groups['Unknown'])} recorded position(s) are not grouped.")
            if pd.notna(meta.lat) and pd.notna(meta.lon):
                same = shown[(shown.lat == meta.lat) & (shown.lon == meta.lon) & (shown.club != chosen)]
                if not same.empty:
                    st.caption("Shared recorded location: " + ", ".join(same.club.tolist()))
            st.button("Open academy profile", key="directory_open_v3", width="stretch",
                      on_click=set_nav, args=("Club Profile", chosen, None))
        else:
            st.info("Choose an academy from the list or map.")


elif page == "Club Profile":
    club_names = CLUBS.club.tolist()
    selected_index = club_names.index(st.session_state.selected_club) if st.session_state.selected_club in club_names else 0
    club = st.selectbox("Academy", club_names, index=selected_index, key="club_profile_academy")
    st.session_state.selected_club = club
    meta = CLUBS[CLUBS.club == club].iloc[0]
    st.markdown("""<style>
    .squad-heading {font-size:1.15rem;font-weight:850;color:#243447;margin:1rem 0 .5rem;}
    .squad-unit-head {display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #DDD8CF;padding:.35rem .1rem .5rem;margin:.9rem 0 .55rem;color:#1F3446;font-size:.84rem;font-weight:900;}
    .squad-unit-head span {display:inline-flex;align-items:center;justify-content:center;min-width:25px;height:25px;border-radius:999px;background:#EDF2F1;color:#688F8B;font-size:.7rem;}
    [class*="st-key-roster_card_"] {background:linear-gradient(145deg,#FAF9F6,#F5F1EA);border-color:#DDD8CF !important;box-shadow:0 5px 16px rgba(31,52,70,.04);min-height:160px;}
    .roster-card-photo.photo-wrap {width:72px;height:84px;aspect-ratio:auto;border-radius:11px;margin-top:2px;}
    .roster-card-name {font-size:.91rem;font-weight:900;color:#243447;line-height:1.15;margin-top:2px;}
    .roster-card-meta {font-size:.69rem;color:#718096;line-height:1.45;margin-top:5px;}
    .roster-card-position {display:inline-block;font-size:.65rem;font-weight:800;color:#526D6A;background:#EDF4F2;padding:.25rem .48rem;border-radius:7px;margin-top:6px;}
    .roster-card-signals {display:flex;flex-wrap:wrap;gap:5px;margin-top:7px;}
    .roster-card-signal {display:inline-flex;align-items:center;border:1px solid #DDD8CF;border-radius:999px;padding:.18rem .42rem;font-size:.6rem;color:#687783;background:#FAF9F6;}
    [class*="st-key-roster_card_"] .stButton>button {min-height:1.95rem !important;font-size:.68rem !important;margin-top:.35rem;}
    </style>""", unsafe_allow_html=True)
    club_logo = safe(meta.academy_logo_url, "")
    for candidate in (club_logo, safe(meta.academy_logo_fallback, "")):
        if candidate:
            local_logo = ROOT / "data" / "club_logos" / (hashlib.sha256(candidate.encode("utf-8")).hexdigest() + ".png")
            if local_logo.is_file():
                club_logo = "data:image/png;base64," + base64.b64encode(local_logo.read_bytes()).decode("ascii")
                break
    st.markdown(
        f"<div class='panel club-hero'>{logo_html(club_logo, club, fallback_url=meta.academy_logo_fallback)}<div>"
        f"<div class='page-kicker'>Academy profile · {esc(meta.academy_category)}</div>"
        f"<div class='club-name'>{esc(club)}</div><div class='meta-line'>Explore the academy squads and their players</div></div></div>",
        unsafe_allow_html=True,
    )
    squad_level = st.radio("Academy team", ["U18", "U21"], horizontal=True, key="club_squad_level")
    roster = load_team_players(club, squad_level)
    if roster.empty:
        status = safe(meta[f"{squad_level.lower()}_roster_status"], "Not recorded")
        st.info(f"No {squad_level} roster is recorded for {club} in the current database.")
        st.caption(f"Roster status: {status}")
        sources = load_roster_sources(club, squad_level)
        for _, source in sources.iterrows():
            url = safe(source.source_url, "")
            if url.startswith("https://"):
                st.link_button("Open recorded roster source", url)
        st.stop()
    pool = apply_player_filters(roster)
    if pool.empty:
        st.info("No players in this squad match the current position and player-type filters.")
        st.stop()
    ages = pd.to_numeric(roster.age, errors="coerce").dropna()
    summary_cols = st.columns(4)
    summary_values = [("Squad", len(roster), f"{squad_level} roster"),
                      ("Average age", f"{ages.mean():.1f}" if not ages.empty else "—", "Known ages only"),
                      ("Scouting profiles", int(roster.has_scouting_data.sum()), "Players with data"),
                      ("Nationalities", roster.nationality.replace("", pd.NA).nunique(), "Recorded nationalities")]
    for col, (label, value, note) in zip(summary_cols, summary_values):
        with col:
            st.markdown(metric(label, value, note), unsafe_allow_html=True)

    def squad_position_group(value):
        value = safe(value, "").casefold()
        if "goalkeeper" in value or value == "gk": return "Goalkeepers"
        if any(token in value for token in ("defender", "back")): return "Defenders"
        if "midfield" in value: return "Midfielders"
        if any(token in value for token in ("attack", "winger", "forward", "striker")): return "Forwards"
        return "Other players"

    roster_col, overview_col = st.columns([2.05, 1], gap="large")
    with roster_col:
        st.markdown(f"<div class='squad-heading'>{esc(squad_level)} squad</div>", unsafe_allow_html=True)
        filter_cols = st.columns([1, 1, 1.3])
        with filter_cols[0]:
            position = st.selectbox("Squad position", options_from(pool, "position"), key=f"club_position_{club}")
        with filter_cols[1]:
            nationality = st.selectbox("Nationality", options_from(pool, "nationality"), key=f"club_nationality_{club}")
        with filter_cols[2]:
            query = st.text_input("Search squad", placeholder="Player name...", key=f"club_search_{club}")
        work = pool.copy()
        if position != "All":
            work = work[work.position == position]
        if nationality != "All":
            work = work[work.nationality == nationality]
        if query.strip():
            work = work[work.player_name.str.contains(query.strip(), case=False, na=False)]
        st.caption(f"Showing {len(work)} of {len(roster)} recorded players")
        if work.empty:
            st.info("No squad players match these filters.")
        if not work.empty:
            work = work.copy()
            work["squad_unit"] = work.position.map(squad_position_group)
            for unit in ["Goalkeepers", "Defenders", "Midfielders", "Forwards", "Other players"]:
                unit_players = work[work.squad_unit == unit].sort_values("player_name")
                if unit_players.empty:
                    continue
                st.markdown(f"<div class='squad-unit-head'>{esc(unit)}<span>{len(unit_players)}</span></div>", unsafe_allow_html=True)
                card_columns = st.columns(2, gap="small")
                for card_index, (_, row) in enumerate(unit_players.iterrows()):
                    with card_columns[card_index % 2]:
                        with st.container(border=True, key=f"roster_card_{squad_level}_{row.canonical_id}"):
                            photo_col, info_col = st.columns([.32, .68], vertical_alignment="top", gap="small")
                            with photo_col:
                                st.markdown(photo_html(row, "roster-card-photo"), unsafe_allow_html=True)
                            with info_col:
                                meta_parts = []
                                if safe(row.nationality, ""):
                                    meta_parts.append(safe(row.nationality))
                                if age_number(row.age) is not None:
                                    meta_parts.append(f"Age {int(age_number(row.age))}")
                                value_label = format_market_value(row.market_value)
                                signals = []
                                if int(row.has_scouting_data or 0):
                                    signals.append("Scouting profile")
                                if value_label != "No value recorded":
                                    signals.append(value_label)
                                signal_html = "".join(f"<span class='roster-card-signal'>{esc(item)}</span>" for item in signals)
                                st.markdown(
                                    f"<div class='roster-card-name'>{esc(row.player_name)}</div>"
                                    f"<div class='roster-card-meta'>{esc(' · '.join(meta_parts))}</div>"
                                    f"<span class='roster-card-position'>{esc(safe(row.position, 'Position not recorded'))}</span>"
                                    f"<div class='roster-card-signals'>{signal_html}</div>",
                                    unsafe_allow_html=True,
                                )
                                st.button("Open profile", key=f"club_row_{club}_{squad_level}_{row.canonical_id}", width="stretch",
                                          on_click=set_nav, args=("Player Profile", club, row.canonical_id))
    with overview_col:
        st.markdown(f"<div class='squad-heading'>Squad overview · {esc(squad_level)}</div>", unsafe_allow_html=True)
        distribution = roster.position.map(squad_position_group).value_counts()
        fig = go.Figure(go.Pie(labels=distribution.index.tolist(), values=distribution.values.tolist(), hole=.7,
                               marker=dict(colors=["#66798A", "#7E8A83", "#A8793F", "#C5A77F", "#A49C91"]),
                               textinfo="none", sort=False, hovertemplate="%{label}: %{value}<extra></extra>"))
        fig.update_layout(height=275, margin=dict(l=5,r=5,t=8,b=10), paper_bgcolor="rgba(0,0,0,0)",
                          legend=dict(orientation="h", y=-.15), showlegend=True,
                          annotations=[dict(text=str(len(roster)), x=.5, y=.5, font_size=23, showarrow=False)])
        st.plotly_chart(fig, width="stretch", config={"displayModeBar":False}, key=f"squad_distribution_{club}_{squad_level}")
        st.caption("Position groups use the recorded main position; unrecorded positions remain separate.")
        with st.expander("Roster sources"):
            sources = load_roster_sources(club, squad_level)
            if sources.empty:
                st.caption("No additional roster source is recorded for this squad.")
            for _, source in sources.iterrows():
                url = safe(source.source_url, "")
                if url.startswith("https://"):
                    st.link_button(f"Open source · {safe(source.coverage)}", url)


elif page == "Player Profile":
    ordered = apply_player_filters(PLAYERS).sort_values(["club", "player_name"]).copy()
    if ordered.empty:
        st.info("No players match the selected position and player-type filters. Reset a filter to see more players.")
        st.stop()
    labels = {row.canonical_id: f"{row.player_name} · {row.club}" for _, row in ordered.iterrows()}
    player_ids = ordered.canonical_id.tolist()
    current_player = st.session_state.selected_player if st.session_state.selected_player in player_ids else player_ids[0]
    player_index = player_ids.index(current_player)
    canonical_id = st.selectbox(
        "Select player",
        player_ids,
        index=player_index,
        format_func=lambda value: labels.get(value, value),
    )
    st.session_state.selected_player = canonical_id
    player = PLAYERS[PLAYERS.canonical_id == canonical_id].iloc[0]
    profile_key = best_attribute_profile_key(canonical_id)
    page_head("Player Profile", "A focused view of player identity, on-pitch profile, career and market history.")
    current_club = safe(player.tm_current_club, safe(player.club))
    position = safe(player.position, "Position not recorded")
    nationality = safe(player.nationality, "Not recorded")
    second_nationality = safe(player.second_nationality, "")
    if second_nationality:
        nationality = f"{nationality} / {second_nationality}"

    values = load_history(canonical_id, "market_values")
    if not values.empty:
        values["market_value_numeric"] = pd.to_numeric(values.market_value_numeric, errors="coerce")
        values["date"] = pd.to_datetime(values.value_date, errors="coerce")
        dated_values = values.sort_values("date", ascending=False, na_position="last")
        latest_value = format_market_value(dated_values.iloc[0].market_value, dated_values.iloc[0].market_value_numeric)
    else:
        dated_values = values
        latest_value = format_market_value(player.market_value)

    with st.container(border=True):
        portrait_column, identity_column = st.columns([.16, .84], gap="large")
        with portrait_column:
            st.markdown(photo_html(player, "profile-photo-wide"), unsafe_allow_html=True)
        with identity_column:
            st.markdown(
                f"<div class='profile-player-name'>{esc(player.player_name)}</div>"
                f"<div class='profile-academy'>{esc(player.club)} · {esc(safe(player.academy_clubs, 'Academy squad'))}</div>",
                unsafe_allow_html=True,
            )
            chips = [("position", position if safe(player.position, "") else "Position not listed")]
            parsed_age = age_number(player.age)
            if parsed_age is not None:
                chips.append(("", f"Age {int(parsed_age)}"))
            if nationality != "Not recorded":
                chips.append(("", nationality))
            if current_club and current_club != safe(player.club, ""):
                chips.append(("", f"Current club · {current_club}"))
            if safe(player.foot, ""):
                chips.append(("", f"{safe(player.foot).title()} foot"))
            height_label = format_height(player.height)
            if height_label != "—":
                chips.append(("", height_label))
            if safe(player.contract_expiry, ""):
                chips.append(("", f"Contract · {safe(player.contract_expiry)}"))
            if latest_value != "No value recorded":
                chips.append(("", f"Value · {latest_value}"))
            visible_chips = [
                f"<span class='profile-chip {kind}'>{esc(label)}</span>"
                for kind, label in chips if label
            ]
            if visible_chips:
                st.markdown(f"<div class='profile-chip-row'>{''.join(visible_chips)}</div>", unsafe_allow_html=True)
            header_roles = role_fit_estimates(canonical_id, profile_key)
            if not header_roles.empty:
                role_tags = []
                for phase, phase_label in (("In Possession", "With the ball"), ("Out Of Possession", "Without the ball")):
                    best = header_roles[header_roles.phase == phase].sort_values("score", ascending=False).head(1)
                    if not best.empty:
                        row = best.iloc[0]
                        role_tags.append(
                            f"<span class='role-identity-chip'><span>{phase_label}</span>"
                            f"<b>{esc(row.role)}</b></span>"
                        )
                if role_tags:
                    st.markdown(f"<div class='role-identity-row'>{''.join(role_tags)}</div>", unsafe_allow_html=True)
            tm_profile = transfermarkt_profile_url(player)
            if tm_profile:
                st.link_button("Open Transfermarkt profile", tm_profile, icon="↗")
            if len(chips) == 1 and parsed_age is None and nationality == "Not recorded":
                st.caption("Additional player details are not available yet.")

    with st.container():
        tabs = st.tabs(["Overview", "Technical profile", "Career", "Market", "Availability"])
        with tabs[0]:
            render_player_canvas(canonical_id)
        with tabs[1]:
            with st.container(border=True):
                st.markdown("<div class='profile-section-head'>Position DNA</div>", unsafe_allow_html=True)
                radar = radar_figure(canonical_id, profile_key)
                if radar:
                    st.plotly_chart(radar, width="stretch", config={"displayModeBar": False}, key=f"detail_radar_{canonical_id}")
                    st.caption("This is the player’s shape across the actions required by the recorded position. The centre line represents the academy peer midpoint.")
                else:
                    st.markdown("<div class='profile-empty'>No supported indicators are available for this player yet.</div>", unsafe_allow_html=True)
            render_role_fit(canonical_id, profile_key, detailed=True)
            versatility = position_versatility_figure(canonical_id)
            if versatility:
                with st.container(border=True):
                    st.markdown("<div class='profile-section-head'>Position versatility</div>", unsafe_allow_html=True)
                    st.plotly_chart(versatility, width="stretch", config={"displayModeBar": False}, key=f"versatility_detail_{canonical_id}")
        with tabs[2]:
            transfers = load_history(canonical_id, "transfers").sort_values("transfer_date", ascending=False, na_position="last")
            performances = load_history(canonical_id, "performances")
            st.markdown("<div class='profile-section-head'>Club journey</div>", unsafe_allow_html=True)
            if transfers.empty:
                st.markdown("<div class='profile-empty'>No club-movement events have been imported for this player yet.</div>", unsafe_allow_html=True)
            else:
                for _, move in transfers.iterrows():
                    date = safe(move.transfer_date, safe(move.season, "Date not listed"))
                    from_club = safe(move.from_club, "Club not listed")
                    to_club = safe(move.to_club, "Club not listed")
                    with st.container(border=True):
                        st.markdown(f"**{esc(from_club)}**　→　**{esc(to_club)}**")
                        st.caption(f"{date} · {safe(move.fee, 'Fee not listed')} · {safe(move.age_at_transfer, 'Age not listed')}")
            st.markdown("<div class='profile-section-head' style='margin-top:1.2rem'>Season record</div>", unsafe_allow_html=True)
            if performances.empty:
                st.markdown("<div class='profile-empty'>No season record has been imported for this player yet. This is an import gap, not an indication of no appearances.</div>", unsafe_allow_html=True)
                if tm_profile:
                    st.link_button("Open complete season record", tm_profile, icon="↗")
            else:
                performances["minutes"] = pd.to_numeric(performances.minutes, errors="coerce").fillna(0)
                season_data = performances.groupby("season", as_index=False).agg(minutes=("minutes", "sum"), appearances=("appearances", "sum"), goals=("goals", "sum"), assists=("assists", "sum"))
                figure = go.Figure(go.Bar(x=season_data.season, y=season_data.minutes, marker_color=BURGUNDY, text=season_data.minutes, textposition="outside"))
                figure.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=15), yaxis=dict(gridcolor=BORDER, title="Minutes"), xaxis_title="Season", paper_bgcolor=SURFACE, plot_bgcolor=SURFACE)
                st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
                for _, season in season_data.sort_values("season", ascending=False).iterrows():
                    with st.expander(f"{safe(season.season)} · {int(season.appearances)} apps · {int(season.goals)} goals · {int(season.assists)} assists"):
                        season_rows = performances[performances.season == season.season]
                        for _, record in season_rows.iterrows():
                            st.caption(f"{safe(record.competition, 'Competition not listed')} · {safe(record.club, 'Club not listed')} · {number_int(record.minutes):,} minutes · {number_int(record.starts)} starts")
        with tabs[3]:
            st.markdown("<div class='profile-section-head'>Market value history</div>", unsafe_allow_html=True)
            if dated_values.empty:
                current_value = format_market_value(player.market_value)
                if current_value != "No value recorded":
                    st.markdown(metric("Current recorded value", current_value), unsafe_allow_html=True)
                    st.caption("A current value is available; historical valuation checkpoints are not recorded.")
                else:
                    st.markdown("<div class='profile-empty'>No market value is recorded for this player.</div>", unsafe_allow_html=True)
            else:
                dated_chart = dated_values.dropna(subset=["date", "market_value_numeric"]).sort_values("date")
                latest = dated_values.iloc[0]
                peak = dated_values.loc[dated_values.market_value_numeric.idxmax()] if dated_values.market_value_numeric.notna().any() else None
                summary1, summary2 = st.columns(2, gap="medium")
                with summary1:
                    st.markdown(metric("Latest value", format_market_value(latest.market_value, latest.market_value_numeric), f"{safe(latest.value_date)} · {safe(latest.club)}"), unsafe_allow_html=True)
                with summary2:
                    st.markdown(metric("Highest recorded", format_market_value(peak.market_value, peak.market_value_numeric) if peak is not None else "—", f"{safe(peak.value_date)} · {safe(peak.club)}" if peak is not None else "No numeric checkpoint"), unsafe_allow_html=True)
                if not dated_chart.empty:
                    dated_chart = dated_chart.copy()
                    dated_chart["market_label"] = [format_market_value(row.market_value, row.market_value_numeric) for _, row in dated_chart.iterrows()]
                    figure = go.Figure(go.Scatter(x=dated_chart.date, y=dated_chart.market_value_numeric, mode="lines+markers", line=dict(color=BURGUNDY, width=3), marker=dict(size=8, color=GOLD), text=dated_chart.market_label, hovertemplate="%{x|%d %b %Y}<br>%{text}<extra></extra>"))
                    figure.update_layout(height=360, margin=dict(l=10, r=15, t=25, b=25), yaxis=dict(gridcolor=BORDER, tickprefix="€", title="Market value"), xaxis_title="", paper_bgcolor=SURFACE, plot_bgcolor=SURFACE)
                    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
                st.markdown("#### Valuation checkpoints")
                for _, value in dated_values.iterrows():
                    label = f"{safe(value.value_date, 'Date not listed')} · {format_market_value(value.market_value, value.market_value_numeric)}"
                    with st.expander(label):
                        cols = st.columns(3, gap="small")
                        for col, name, detail in [(cols[0], "Club", safe(value.club)), (cols[1], "Age", safe(value.age_at_valuation)), (cols[2], "Numeric value", f"€{value.market_value_numeric:,.0f}" if pd.notna(value.market_value_numeric) else "Not recorded")]:
                            with col:
                                st.markdown(metric(name, detail), unsafe_allow_html=True)
        with tabs[4]:
            injuries = load_history(canonical_id, "injuries").sort_values(["from_date", "season"], ascending=False, na_position="last")
            st.markdown("<div class='profile-section-head'>Availability record</div>", unsafe_allow_html=True)
            if injuries.empty:
                st.markdown("<div class='profile-empty'>No injury events are recorded. This does not imply the player has never been injured.</div>", unsafe_allow_html=True)
            else:
                missed = pd.to_numeric(injuries.games_missed, errors="coerce").fillna(0).sum()
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(metric("Recorded events", len(injuries)), unsafe_allow_html=True)
                with c2:
                    st.markdown(metric("Games missed", int(missed)), unsafe_allow_html=True)
                with c3:
                    st.markdown(metric("Availability indicator", f"{availability_score(canonical_id):.0f}/100", "Based on recorded events"), unsafe_allow_html=True)
                for _, injury in injuries.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{esc(safe(injury.injury, 'Injury not specified'))}** · {esc(safe(injury.season))}")
                        st.caption(f"{safe(injury.from_date, 'Start not recorded')} → {safe(injury.until_date, 'End not recorded')} · {safe(injury.days_out, 'Duration not recorded')} · {safe(injury.games_missed, 'Games missed not recorded')} games missed")


elif page == "Compare Players":
    page_head("Compare Players", "Compare player profiles in the context of a role and phase of play.")
    work = apply_player_filters(PLAYERS)
    if work.empty:
        st.info("No players match the selected filters. Adjust the position or player type to continue.")
        st.stop()

    search_cols = st.columns([1, 1, 1, 1.25])
    with search_cols[0]:
        category = st.selectbox("Category", options_from(work, "academy_category"), key="compare_category")
    if category != "All":
        work = work[work.academy_category == category]
    with search_cols[1]:
        club = st.selectbox("Academy", options_from(work, "club"), key="compare_academy")
    if club != "All":
        work = work[work.club == club]
    with search_cols[2]:
        position = st.selectbox("Position", options_from(work, "position"), key="compare_position")
    if position != "All":
        work = work[work.position == position]
    with search_cols[3]:
        query = st.text_input("Find a player", placeholder="Name...", key="compare_search")
    if query.strip():
        work = work[work.player_name.str.contains(query.strip(), case=False, na=False)]
    choices = work.sort_values(["has_scouting_data", "player_name"], ascending=[False, True]).canonical_id.tolist()
    labels = {row.canonical_id: f"{row.player_name} · {row.club}" for _, row in work.iterrows()}
    example_ids = ["TM:1334338", "TM:1266270"]
    defaults = example_ids if all(player_id in choices for player_id in example_ids) else choices[:2]
    selected = st.multiselect("Select 2–4 players", choices, default=defaults, max_selections=4,
                              format_func=lambda value: labels.get(value, value), key="compare_players_v2")
    if len(selected) < 2:
        st.info("Select at least two players to compare.")
        st.stop()
    rows = [PLAYERS[PLAYERS.canonical_id == player_id].iloc[0] for player_id in selected]
    keeper_flags = {is_goalkeeper(row.canonical_id) for row in rows}
    mixed_keepers = len(keeper_flags) > 1
    lanes = [role_position_codes(row.position)[0] for row in rows]
    common_lanes = set.intersection(*lanes) if lanes and all(lanes) else set()
    control_cols = st.columns([1.2, 1, 1])
    with control_cols[0]:
        phase_label = st.radio("Phase", ["With the ball", "Without the ball"], horizontal=True, key="compare_phase_v2")
    phase_key = "in_possession" if phase_label == "With the ball" else "out_of_possession"
    phase_name = "In Possession" if phase_key == "in_possession" else "Out Of Possession"
    eligible = []
    for item in ROLE_CRITERIA:
        codes = item.get("position", [])
        codes = [codes] if isinstance(codes, str) else codes
        if item.get("phase") == phase_key and common_lanes.intersection(str(code) for code in codes):
            eligible.append(item)
    role_names = list(dict.fromkeys(str(item["role_name"]) for item in eligible))
    with control_cols[1]:
        role_name = st.selectbox("Role context", role_names if role_names else ["General profile"], key="compare_role_v2")
    role_item = next((item for item in eligible if item["role_name"] == role_name), None)
    if mixed_keepers:
        st.warning("Goalkeepers and outfield players use different measures. Choose players from the same group for a shared radar.")
    elif not role_item:
        st.caption("No shared role context is available for the selected positions. The general profile uses the available dimensions.")

    # The same role dimensions and contributing criteria are used for every player.
    all_keeper = bool(keeper_flags == {True})
    mapping = GOALKEEPER_RADAR_ATTRIBUTES if all_keeper else OUTFIELD_RADAR_ATTRIBUTES
    if role_item:
        required = {str(name).casefold() for name in role_item["key_attributes"]}
        dimension_rules = {axis: [name for name in names if name.casefold() in required]
                           for axis, names in mapping.items()}
        dimension_rules = {axis: names for axis, names in dimension_rules.items() if names}
        profile_data = []
        for row in rows:
            attrs = {str(name).casefold(): value for name, value in attr_dict(row.canonical_id).items()}
            scores = {}
            coverage = {}
            for axis, names in dimension_rules.items():
                available = [attrs[name.casefold()] for name in names if name.casefold() in attrs]
                if available:
                    scores[axis] = sum(available) / len(available)
                coverage[axis] = (len(available), len(names))
            fits = role_fit_estimates(row.canonical_id)
            match = fits[(fits.phase == phase_name) & (fits.role == role_name)] if not fits.empty else pd.DataFrame()
            present = sum(name in attrs for name in required)
            profile_data.append({"row": row, "scores": scores, "coverage": coverage,
                                 "fit": match.iloc[0] if not match.empty else None,
                                 "present": present, "required": len(required)})
        axis_order = list(dimension_rules)
    else:
        profile_data = [{"row": row, "scores": radar_scores(row.canonical_id) or {},
                         "coverage": {}, "fit": None, "present": None, "required": None} for row in rows]
        axis_order = list(dict.fromkeys(axis for item in profile_data for axis in item["scores"]))

    colors = ["#C99A28", "#0FA995", "#8B2434", "#347FA5"]
    st.markdown("""<style>
    .comparison-person {border:1px solid #DDD8CF;border-radius:16px;padding:15px;background:#FAF9F6;min-height:250px;}
    .comparison-person .photo-wrap.small {width:115px;margin:0 0 12px;}
    .comparison-name {font-size:1.2rem;font-weight:850;color:#0B1F3A;line-height:1.15;}
    .comparison-sub {font-size:.78rem;color:#64748B;margin-top:6px;line-height:1.5;}
    .comparison-section {font-size:.75rem;font-weight:850;color:#64748B;text-transform:uppercase;letter-spacing:.07em;margin-top:16px;}
    .comparison-fit {font-size:1.15rem;font-weight:850;color:#0B1F3A;margin-top:4px;}
    .comparison-note {font-size:.72rem;color:#64748B;margin-top:6px;line-height:1.45;}
    </style>""", unsafe_allow_html=True)

    def player_card(item, color):
        row = item["row"]
        facts = [safe(row.position, "Position unavailable"), safe(row.club, "Academy unavailable"),
                 safe(row.nationality, ""), f"Age {format_age(row.age)}" if format_age(row.age) not in ("—", "Unknown") else ""]
        facts = " · ".join(esc(fact) for fact in facts if fact)
        fit = item["fit"]
        fit_text = f"{float(fit.score):.0f} / 100" if fit is not None else "Not enough evidence"
        coverage = f"{item['present']} of {item['required']} role indicators available" if item["required"] else "Role evidence unavailable"
        return (f"<div class='comparison-person' style='border-top:3px solid {color}'>"
                f"{photo_html(row, 'small')}<div class='comparison-name'>{esc(row.player_name)}</div>"
                f"<div class='comparison-sub'>{facts}</div><div class='comparison-section'>{esc(role_name)}</div>"
                f"<div class='comparison-fit'>{esc(fit_text)}</div><div class='comparison-note'>{esc(coverage)}</div></div>")

    if len(rows) == 2:
        left, center, right = st.columns([1, 1.7, 1], gap="medium")
        with left:
            st.markdown(player_card(profile_data[0], colors[0]), unsafe_allow_html=True)
        with right:
            st.markdown(player_card(profile_data[1], colors[1]), unsafe_allow_html=True)
        radar_container = center
    else:
        for i, col in enumerate(st.columns(len(rows), gap="small")):
            with col:
                st.markdown(player_card(profile_data[i], colors[i]), unsafe_allow_html=True)
        radar_container = st.container()

    with radar_container:
        st.markdown("<div class='profile-section-head'>Role comparison</div>", unsafe_allow_html=True)
        if mixed_keepers:
            st.info("A shared radar is not available for this selection.")
        elif not axis_order or not any(item["scores"] for item in profile_data):
            st.info("No supported radar dimensions are available for the selected players.")
        else:
            fig = go.Figure()
            for i, item in enumerate(profile_data):
                scores = item["scores"]
                values = [scores.get(axis) for axis in axis_order]
                complete = all(value is not None for value in values) and len(values) >= 3
                trace_values = values + [values[0]] if complete else values
                trace_axes = axis_order + [axis_order[0]] if complete else axis_order
                fig.add_trace(go.Scatterpolar(r=trace_values, theta=trace_axes, mode="lines+markers" if complete else "markers",
                    name=safe(item["row"].player_name), line=dict(color=colors[i], width=3),
                    marker=dict(color=colors[i], size=8), fill="toself" if complete else None,
                    opacity=.8, connectgaps=False, hovertemplate="%{theta}: %{r:.0f} / 100<extra>%{fullData.name}</extra>"))
            fig.update_layout(height=480, margin=dict(l=55, r=55, t=25, b=35), paper_bgcolor="rgba(0,0,0,0)",
                polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(range=[0,100], tickvals=[20,40,60,80,100], gridcolor="#E3DBCF"),
                           angularaxis=dict(gridcolor="#E8E1D7", tickfont=dict(size=11, color=NAVY))),
                legend=dict(orientation="h", y=-.12))
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key="comparison_role_radar")
            st.caption("The chart uses available supporting indicators on a 0–100 scale. Gaps are not zero; incomplete profiles appear as points.")

    st.markdown("<div class='profile-section-head' style='margin-top:1rem'>Evidence coverage</div>", unsafe_allow_html=True)
    coverage_cols = st.columns(len(profile_data))
    for col, item in zip(coverage_cols, profile_data):
        with col:
            if item["required"]:
                fraction = item["present"] / item["required"]
                st.markdown(f"**{esc(item['row'].player_name)}** · {item['present']} / {item['required']}")
                st.progress(min(1.0, fraction))
                st.caption("Role indicators available")
            else:
                st.markdown(f"**{esc(item['row'].player_name)}**")
                st.caption("Role coverage unavailable")

    st.markdown("<div class='profile-section-head' style='margin-top:1rem'>Key comparison</div>", unsafe_allow_html=True)
    if mixed_keepers:
        st.caption("Select players from the same position group to compare dimensions.")
    else:
        common_axes = [axis for axis in axis_order if all(axis in item["scores"] for item in profile_data)]
        if not common_axes:
            st.info("No shared dimensions are available for these players.")
        else:
            if len(profile_data) == 2:
                common_axes.sort(key=lambda axis: abs(profile_data[0]["scores"][axis] - profile_data[1]["scores"][axis]), reverse=True)
            for axis in common_axes[:5]:
                entries = " · ".join(f"{esc(item['row'].player_name)} {item['scores'][axis]:.0f}" for item in profile_data)
                st.markdown(f"**{esc(axis)}**　{entries}", unsafe_allow_html=True)
            st.caption("These are supported profile dimensions, not match statistics or an overall player ranking.")
    with st.expander("Player details and links"):
        for item in profile_data:
            row = item["row"]
            st.markdown(f"**{esc(row.player_name)}** · {esc(safe(row.club))} · {esc(safe(row.position))}")
            url = transfermarkt_profile_url(row)
            if url:
                st.link_button(f"Open {safe(row.player_name)} profile", url)
