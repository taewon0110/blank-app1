import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime, timezone

def hex_to_rgba(h, a=0.28):
    r,g,b = int(h[1:3],16),int(h[3:5],16),int(h[5:7],16)
    return f"rgba({r},{g},{b},{a})"

st.set_page_config(
    page_title="🔥 미국-이란 전쟁 전황 대시보드 2026",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;600;700;900&family=JetBrains+Mono:wght@400;600&display=swap');
html,body,[class*="css"]{font-family:'Noto Sans KR',sans-serif;}
.stApp{background:#060d1a;color:#e2e8f0;}
section[data-testid="stSidebar"]{background:#070e1c;border-right:1px solid #1a3050;}
.block-container{padding-top:1.2rem;}
.war-header{background:linear-gradient(135deg,#1a0505 0%,#2a0808 40%,#071225 100%);
  border:1px solid #7f1d1d;border-radius:12px;padding:1.3rem 2rem;margin-bottom:1rem;text-align:center;
  box-shadow:0 0 40px rgba(239,68,68,0.12);}
.war-header h1{font-size:2rem;font-weight:900;color:#ef4444;margin:0;}
.war-header .sub{color:#94a3b8;margin:0.3rem 0 0;font-size:0.88rem;}
.war-header .live{display:inline-block;background:#ef4444;color:white;font-size:0.65rem;
  font-weight:700;padding:2px 8px;border-radius:20px;margin-right:8px;animation:pulse 1.5s infinite;}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.5;}}
.kpi-card{background:linear-gradient(135deg,#0f1825,#141f30);border-radius:10px;
  padding:0.85rem 1rem;border-left:4px solid;margin-bottom:0.45rem;}
.kpi-label{font-size:0.68rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;}
.kpi-value{font-size:1.7rem;font-weight:900;margin:0.05rem 0;font-family:'JetBrains Mono',monospace;}
.kpi-sub{font-size:0.73rem;color:#475569;}
.red{border-color:#ef4444;} .red .kpi-value{color:#ef4444;}
.amber{border-color:#f59e0b;} .amber .kpi-value{color:#f59e0b;}
.blue{border-color:#3b82f6;} .blue .kpi-value{color:#60a5fa;}
.green{border-color:#22c55e;} .green .kpi-value{color:#4ade80;}
.cyan{border-color:#06b6d4;} .cyan .kpi-value{color:#22d3ee;}
.purple{border-color:#a855f7;} .purple .kpi-value{color:#c084fc;}
.event-card{background:#0f1825;border-radius:8px;padding:0.75rem 0.9rem;
  margin-bottom:0.5rem;border-left:3px solid;transition:all .2s;}
.event-card:hover{transform:translateX(3px);background:#13202f;}
.event-card.critical{border-color:#ef4444;}.event-card.high{border-color:#f59e0b;}
.event-card.medium{border-color:#3b82f6;}.event-card.econ{border-color:#22c55e;}
.event-date{font-size:0.68rem;color:#475569;font-weight:700;font-family:'JetBrains Mono',monospace;}
.event-title{font-size:0.9rem;color:#e2e8f0;font-weight:700;margin:0.1rem 0;}
.event-detail{font-size:0.79rem;color:#94a3b8;line-height:1.55;}
.badge{display:inline-block;font-size:0.6rem;font-weight:700;padding:1px 7px;border-radius:20px;margin-bottom:0.2rem;text-transform:uppercase;}
.badge.critical{background:#7f1d1d;color:#fca5a5;}.badge.high{background:#78350f;color:#fcd34d;}
.badge.medium{background:#1e3a5f;color:#93c5fd;}.badge.econ{background:#14532d;color:#86efac;}
.tracker-box{background:#0a1020;border:1px solid #1a3050;border-radius:10px;padding:0.8rem 1rem;margin-bottom:0.5rem;}
.tracker-title{font-size:0.78rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:0.5rem;}
.flight-row{display:flex;justify-content:space-between;align-items:center;padding:0.3rem 0;border-bottom:1px solid #0f1825;font-size:0.78rem;}
.flight-row:last-child{border-bottom:none;}
.callsign{font-family:'JetBrains Mono',monospace;color:#60a5fa;font-weight:600;}
.flight-data{color:#64748b;font-size:0.72rem;}
.divider{height:1px;background:linear-gradient(90deg,transparent,#1a3050,transparent);margin:.7rem 0;}
.stTabs [data-baseweb="tab-list"]{background:#070e1c;border-radius:8px;padding:3px;gap:3px;}
.stTabs [data-baseweb="tab"]{background:transparent;color:#64748b;border-radius:6px;font-weight:600;font-size:0.82rem;padding:6px 14px;}
.stTabs [aria-selected="true"]{background:#1a3050!important;color:#60a5fa!important;}
</style>
""", unsafe_allow_html=True)

# ── 실시간 데이터 ──────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_opensky_flights():
    url = "https://opensky-network.org/api/states/all?lamin=21&lomin=44&lamax=38&lomax=65"
    try:
        r = requests.get(url, timeout=12, headers={"User-Agent": "WarDashboard/1.0"})
        raw = r.json()
        flights = []
        for s in raw.get("states", []):
            if s[5] is None or s[6] is None: continue
            flights.append({
                "icao24": s[0], "callsign": (s[1] or "").strip() or "N/A",
                "country": s[2] or "Unknown", "lon": s[5], "lat": s[6],
                "altitude": round(s[7] or 0), "on_ground": bool(s[8]),
                "velocity": round((s[9] or 0) * 3.6), "heading": round(s[10] or 0),
            })
        return flights
    except:
        return []

def get_flag(country):
    flags = {"United States":"🇺🇸","Israel":"🇮🇱","Iran":"🇮🇷","United Kingdom":"🇬🇧",
             "Saudi Arabia":"🇸🇦","UAE":"🇦🇪","Qatar":"🇶🇦","Kuwait":"🇰🇼","Bahrain":"🇧🇭",
             "China":"🇨🇳","Russia":"🇷🇺","India":"🇮🇳","Turkey":"🇹🇷","Jordan":"🇯🇴",
             "Iraq":"🇮🇶","France":"🇫🇷","Germany":"🇩🇪","Pakistan":"🇵🇰"}
    for k,v in flags.items():
        if k.lower() in country.lower(): return v
    return "✈️"

# ── 헤더 ──────────────────────────────────────────────────
now_kst = datetime.now(timezone.utc)
st.markdown(f"""
<div class="war-header">
  <h1>🔴 미국-이란 전쟁 전황 대시보드</h1>
  <p class="sub"><span class="live">● LIVE</span>
    2026년 2월 28일 개전 ~ 2026년 3월 18일 현재 | Operation Epic Fury / Roaring Lion |
    갱신: {now_kst.strftime('%H:%M UTC')}</p>
</div>""", unsafe_allow_html=True)

# ── 사이드바 ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎯 전황 제어판")
    if st.button("🔄 실시간 데이터 갱신", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.markdown("---")
    show_attacks = st.multiselect("공격 유형 필터",
        ["미군/이스라엘 공습","이란 미사일·드론","헤즈볼라 로켓","해상 봉쇄"],
        default=["미군/이스라엘 공습","이란 미사일·드론","헤즈볼라 로켓","해상 봉쇄"])
    map_zoom = st.selectbox("지도 뷰",["호르무즈 집중 (×6)","중동 전체 (×4)","광역 (×2.5)"], index=0)
    zoom_scale = {"호르무즈 집중 (×6)":6,"중동 전체 (×4)":4,"광역 (×2.5)":2.5}[map_zoom]
    st.markdown("---")
    st.markdown("**⏱️ 교전 일수:** `19일`")
    st.markdown("**📅** `2026.02.28 → 03.18`")
    st.markdown("---")
    st.caption("항공: OpenSky Network\n선박: ISW·Reuters 보도기반\n군사배치: CENTCOM·ISW·IranIntl")

# ── KPI ───────────────────────────────────────────────────
c1,c2,c3,c4,c5 = st.columns(5)
for col,(cl,lb,val,sub) in zip([c1,c2,c3,c4,c5],[
    ("red","이란 사망","1,444+","부상 18,551명"),
    ("amber","레바논 사망","880+","헤즈볼라 전선"),
    ("blue","미군 전사","13명","부상 200+명"),
    ("green","브렌트유","$103/bbl","개전 전比 +50%"),
    ("cyan","탱커 통행량","↓70%","3/2 봉쇄선언")]):
    with col:
        st.markdown(f"""<div class="kpi-card {cl}">
            <div class="kpi-label">{lb}</div><div class="kpi-value">{val}</div>
            <div class="kpi-sub">{sub}</div></div>""", unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── 탭 ────────────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5 = st.tabs([
    "🗺️ 전황 지도+실시간항공","🪖 군사 배치도","📅 타임라인","💀 피해 현황","📈 경제 충격"
])

# ════════════════════════════════════════════════════════
# TAB 1 : 전황 지도 + OpenSky 실시간
# ════════════════════════════════════════════════════════
with tab1:
    with st.spinner("✈️ OpenSky Network 실시간 데이터 수신 중..."):
        flights = fetch_opensky_flights()
    air_flights = [f for f in flights if not f["on_ground"] and f["altitude"] > 500]

    map_col, info_col = st.columns([3,1])

    attack_events = [
        dict(lat=35.69,lon=51.39,name="테헤란 (리더십 타격)",size=26,color="#ef4444",symbol="star",cat="미군/이스라엘 공습",note="2/28 하메네이 사망, 핵·군사시설 동시 타격"),
        dict(lat=32.43,lon=53.69,name="이스파한 (핵시설)",size=20,color="#ef4444",symbol="star",cat="미군/이스라엘 공습",note="2/28 핵 농축시설 정밀타격"),
        dict(lat=29.23,lon=50.35,name="카르크섬 (해군기지)",size=20,color="#ef4444",symbol="star",cat="미군/이스라엘 공습",note="3/13 IRGC 기뢰·미사일 저장고 파괴"),
        dict(lat=28.97,lon=50.84,name="부셰르 (미사일기지)",size=20,color="#ef4444",symbol="star",cat="미군/이스라엘 공습",note="3/17 5,000lb 벙커버스터 투하"),
        dict(lat=30.28,lon=57.07,name="케르만 (라리자니 제거)",size=16,color="#ef4444",symbol="star",cat="미군/이스라엘 공습",note="3/17 IRGC 안보책임자 사망"),
        dict(lat=32.08,lon=34.78,name="텔아비브 (이란 미사일)",size=20,color="#f97316",symbol="triangle-up",cat="이란 미사일·드론",note="3/10 집속탄두→예후드 민간인 2명 사망"),
        dict(lat=25.11,lon=51.31,name="카타르 알우데이드 (미군)",size=18,color="#f97316",symbol="triangle-up",cat="이란 미사일·드론",note="탄도미사일 180발+ 공격"),
        dict(lat=25.20,lon=55.27,name="두바이 (이란 드론)",size=15,color="#f97316",symbol="triangle-up",cat="이란 미사일·드론",note="3/13 시티뱅크 빌딩 타격"),
        dict(lat=26.22,lon=50.59,name="마나마 (이란 드론)",size=15,color="#f97316",symbol="triangle-up",cat="이란 미사일·드론",note="3/13 UAE 사망 8명"),
        dict(lat=33.34,lon=44.40,name="바그다드 (미 대사관)",size=14,color="#f97316",symbol="triangle-up",cat="이란 미사일·드론",note="3/17 드론 공격"),
        dict(lat=33.89,lon=35.50,name="레바논-이스라엘 전선",size=18,color="#eab308",symbol="triangle-up",cat="헤즈볼라 로켓",note="3/11~12 로켓200발+드론20대"),
        dict(lat=26.57,lon=56.27,name="호르무즈 해협 봉쇄",size=28,color="#06b6d4",symbol="diamond",cat="해상 봉쇄",note="3/2 IRGC 전면봉쇄, 탱커 70% 급감"),
    ]

    with map_col:
        fig = go.Figure()
        if "해상 봉쇄" in show_attacks:
            fig.add_trace(go.Scattergeo(
                lon=[55.3,55.3,58.8,58.8,55.3],lat=[25.5,27.3,27.3,25.5,25.5],mode="lines",fill="toself",
                fillcolor="rgba(6,182,212,0.13)",line=dict(color="#06b6d4",width=1.8),
                name="⛔ 호르무즈 봉쇄구역",hoverinfo="name"))
            fig.add_trace(go.Scattergeo(
                lon=[56.0,56.5,57.0,57.5,58.0],lat=[26.3,26.5,26.6,26.5,26.2],mode="lines",
                line=dict(color="#06b6d4",width=3,dash="dot"),name="🚢 호르무즈 항로",hoverinfo="name"))
        for cat in show_attacks:
            pts=[e for e in attack_events if e["cat"]==cat]
            if not pts: continue
            fig.add_trace(go.Scattergeo(
                lon=[p["lon"] for p in pts],lat=[p["lat"] for p in pts],mode="markers",
                marker=dict(size=[p["size"] for p in pts],color=[p["color"] for p in pts],
                            symbol=[p["symbol"] for p in pts],line=dict(width=1.5,color="rgba(255,255,255,0.6)"),opacity=0.92),
                name=cat,text=[f"<b>{p['name']}</b><br>{p['note']}" for p in pts],
                hovertemplate="%{text}<extra></extra>"))
        fig.add_trace(go.Scattergeo(
            lon=[58.5,60.0],lat=[23.5,21.0],mode="markers+text",
            marker=dict(size=16,color="#3b82f6",symbol="pentagon",line=dict(color="white",width=1.5)),
            text=["USS Abraham Lincoln","USS Gerald R. Ford"],
            textfont=dict(size=8,color="#93c5fd"),textposition="top right",
            name="🛡️ 미 항모전단",hovertemplate="<b>%{text}</b><br>미 해군 5함대<extra></extra>"))
        if air_flights:
            mil_kw=["RCH","JTAC","USAF","UAF","IAF","MRTT","SNTF"]
            mil=[f for f in air_flights if any(k in f["callsign"].upper() for k in mil_kw)]
            civ=[f for f in air_flights if f not in mil]
            if civ:
                fig.add_trace(go.Scattergeo(
                    lon=[f["lon"] for f in civ],lat=[f["lat"] for f in civ],mode="markers",
                    marker=dict(size=7,color="#94a3b8",symbol="triangle-up",opacity=0.65,line=dict(width=0.5,color="white")),
                    name=f"✈️ 민간항공 ({len(civ)}편)",
                    text=[f"<b>{f['callsign']}</b><br>{get_flag(f['country'])} {f['country']}<br>고도:{f['altitude']:,}m|속도:{f['velocity']}km/h" for f in civ],
                    hovertemplate="%{text}<extra></extra>"))
            if mil:
                fig.add_trace(go.Scattergeo(
                    lon=[f["lon"] for f in mil],lat=[f["lat"] for f in mil],mode="markers",
                    marker=dict(size=11,color="#22c55e",symbol="triangle-up",opacity=0.9,line=dict(width=1.5,color="white")),
                    name=f"🛩️ 군용의심기 ({len(mil)}편)",
                    text=[f"<b>{f['callsign']}</b><br>{get_flag(f['country'])} {f['country']}<br>고도:{f['altitude']:,}m" for f in mil],
                    hovertemplate="%{text}<extra></extra>"))
        center_lon=55.0 if "호르무즈" in map_zoom else 50.0
        center_lat=27.0 if "호르무즈" in map_zoom else 29.0
        fig.update_layout(
            height=620,paper_bgcolor="#060d1a",plot_bgcolor="#060d1a",
            font=dict(color="#e2e8f0",family="Noto Sans KR"),
            geo=dict(scope="asia",showland=True,landcolor="#131f35",showocean=True,oceancolor="#0a1628",
                     showlakes=True,lakecolor="#0a1628",showcountries=True,countrycolor="#1e3a5f",
                     showcoastlines=True,coastlinecolor="#1e3a5f",bgcolor="#060d1a",
                     center=dict(lat=center_lat,lon=center_lon),projection_scale=zoom_scale),
            legend=dict(bgcolor="rgba(6,13,26,0.9)",bordercolor="#1a3050",borderwidth=1,font=dict(size=9),x=0.01,y=0.99),
            margin=dict(l=0,r=0,t=35,b=0),
            title=dict(text=f"🗺️ 2026 미국-이란 전황 + OpenSky 실시간 항공기 ({len(air_flights)}편)",
                       font=dict(size=12,color="#64748b"),x=0.5))
        st.plotly_chart(fig,use_container_width=True)

    with info_col:
        st.markdown(f"""<div class="tracker-box">
            <div class="tracker-title">✈️ OpenSky 실시간</div>
            <div style="font-size:0.75rem;color:#475569">중동·걸프 | TTL 60초</div>
            <div style="font-size:2rem;font-weight:900;color:#60a5fa;margin:.3rem 0">{len(air_flights)}</div>
            <div style="font-size:0.72rem;color:#64748b">비행 중 항공기</div></div>""",unsafe_allow_html=True)
        if air_flights:
            from collections import Counter
            cnt=Counter(f["country"] for f in air_flights)
            top=cnt.most_common(7)
            rows=""
            for country,n in top:
                bw=int(n/max(c for _,c in top)*80)
                rows+=f"""<div style="margin-bottom:5px">
                    <div style="display:flex;justify-content:space-between;font-size:0.76rem">
                        <span>{get_flag(country)} {country[:14]}</span><span style="color:#60a5fa;font-weight:700">{n}</span>
                    </div><div style="height:3px;background:#1a3050;border-radius:2px;margin-top:2px">
                        <div style="width:{bw}%;height:100%;background:#3b82f6;border-radius:2px"></div></div></div>"""
            st.markdown(f"""<div class="tracker-box"><div class="tracker-title">🌍 국가별</div>{rows}</div>""",unsafe_allow_html=True)
            top12=sorted(air_flights,key=lambda x:x["altitude"],reverse=True)[:12]
            rows2=""
            for f in top12:
                rows2+=f"""<div class="flight-row">
                    <span class="callsign">{get_flag(f['country'])}{f['callsign'][:8]}</span>
                    <span class="flight-data">{f['altitude']/1000:.1f}km|{f['velocity']}km/h</span></div>"""
            st.markdown(f"""<div class="tracker-box"><div class="tracker-title">📡 고고도 TOP12</div>{rows2}</div>""",unsafe_allow_html=True)
        st.markdown("""<div class="tracker-box"><div class="tracker-title">🚢 호르무즈 선박</div>
            <div style="font-size:0.72rem;color:#475569;margin-bottom:0.4rem">보도자료 기반 | 2026.03.18</div>""",unsafe_allow_html=True)
        for dot,status,detail in [("🔴","봉쇄구역 억류","탱커 12척"),("🟡","우회 항행","희망봉 경유 31척"),
            ("🟢","우방국 통행","중·러 8척"),("⭕","UAE 대기","탱커 22척"),("🔵","미 해군 호위","구축함 4척")]:
            st.markdown(f"""<div style="margin-bottom:5px;border-bottom:1px solid #0f1825;padding-bottom:4px">
                <div style="font-size:0.78rem">{dot} <b style="color:#e2e8f0">{status}</b></div>
                <div style="font-size:0.7rem;color:#64748b;margin-left:1.2rem">{detail}</div></div>""",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>',unsafe_allow_html=True)
    hc1,hc2,hc3,hc4=st.columns(4)
    for col,cl,lb,val,sub in zip([hc1,hc2,hc3,hc4],
        ["blue","red","amber","cyan"],
        ["세계 원유 통과","봉쇄 후 감소","선택적 개방","미 항모전단"],
        ["20%","-70%","3월 15일~","2척 배치"],
        ["일 ~1,700만 배럴","3/2 IRGC 선언","중·러·인도만","CVN-72·CVN-78"]):
        with col:
            st.markdown(f"""<div class="kpi-card {cl}"><div class="kpi-label">{lb}</div>
                <div class="kpi-value">{val}</div><div class="kpi-sub">{sub}</div></div>""",unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# TAB 2 : 군사 배치도
# ════════════════════════════════════════════════════════
with tab2:
    st.markdown("#### 🪖 미군·이란군 군사 배치도 (2026.03.18 기준)")
    deploy_col,legend_col=st.columns([3,1])
    with deploy_col:
        layer_opts=st.multiselect("표시 레이어",
            ["🔵 미군 확인 배치 (팩트)","🔵 미군 예측 배치","🔴 이란군 확인 배치 (팩트)","🟠 이란군 예측 배치"],
            default=["🔵 미군 확인 배치 (팩트)","🔵 미군 예측 배치","🔴 이란군 확인 배치 (팩트)","🟠 이란군 예측 배치"])
        us_confirmed=[
            dict(lat=21.0,lon=60.0,name="USS Abraham Lincoln (CVN-72)",sz=22,note="아라비아해 오만 연안 | 1월 배치 확인 (Wikipedia)"),
            dict(lat=28.0,lon=35.0,name="USS Gerald R. Ford (CVN-78)",sz=22,note="홍해 작전 | 3/5 수에즈 운하 통과 (Reuters)"),
            dict(lat=25.11,lon=51.31,name="Al Udeid AB (카타르) — CENTCOM 전방사령부",sz=20,note="PAC-3 배치 | 이란 미사일 공격 (CENTCOM)"),
            dict(lat=26.19,lon=50.59,name="NSA Juffair (바레인) — 5함대사령부",sz=18,note="이란 드론 공격 피해 (Times of Israel)"),
            dict(lat=29.37,lon=47.98,name="Camp Arifjan + Ali Al Salem AB (쿠웨이트)",sz=18,note="미 육군중부사 전방HQ | 이란 타격 (IndianExpress)"),
            dict(lat=24.25,lon=55.61,name="Al Dhafra AB (UAE) — 380 AEW",sz=18,note="이란 드론 공격 | 포트 제벨알리 병참 (CENTCOM)"),
            dict(lat=31.78,lon=35.98,name="Ovda AB (이스라엘) — F-22 12대",sz=16,note="F-22 랩터 12대 배치 확인 (Wikipedia)"),
            dict(lat=30.56,lon=37.22,name="Muwaffaq Salti AB (요르단) — F-15E·F-35",sz=16,note="이란 타격 받음 | F-15E·F-35 확인 (Israel Hayom)"),
            dict(lat=33.40,lon=44.24,name="Al Asad AB (이라크) — 미 지상군",sz=14,note="이란 드론 대응 부대 (IndianExpress)"),
            dict(lat=36.30,lon=43.90,name="Erbil AB (이라크) — SOF",sz=14,note="특수작전군 전진기지 (IndianExpress)"),
            dict(lat=34.59,lon=32.98,name="Akrotiri AB (키프로스) — 미·영 공군",sz=16,note="헤즈볼라 드론 공격 | B-52 스테이징 (Parliament.uk)"),
            dict(lat=23.0,lon=59.5,name="2,500 해병대 — 호르무즈 대기",sz=18,note="호르무즈 재개방 임무 | 상륙함 탑승 (CBC)"),
        ]
        us_predicted=[
            dict(lat=19.5,lon=58.5,name="[예측] USS George H.W. Bush (CVN-77) 접근",sz=18,note="전개 훈련 완료 → 파견 가능성 (Forbes·Quwa)"),
            dict(lat=25.5,lon=57.0,name="[예측] SEAL팀 호르무즈 수중작전",sz=12,note="기뢰 제거·특수작전 (ISW 분석)"),
            dict(lat=22.5,lon=60.5,name="[예측] B-2 Spirit 전진기지",sz=14,note="Diego Garcia → 이란 반복 출격 추정"),
            dict(lat=24.0,lon=53.0,name="[예측] MQ-9 리퍼 드론 작전구역",sz=12,note="UAE 알드파라 기반 ISR·타격"),
        ]
        ir_confirmed=[
            dict(lat=29.23,lon=50.35,name="카르크섬 — IRGC 해군 112여단",sz=22,note="고속정·대함미사일 | 3/13 미군 타격 (IranIntl)"),
            dict(lat=26.96,lon=56.27,name="반다르아바스 — IRGC 해군사령부",sz=20,note="수상전투함·잠수함 기지 (ISW)"),
            dict(lat=26.55,lon=55.90,name="케슘섬 — 지하 미사일도시",sz=22,note="위성 확인 미사일 시설 | '가라앉지 않는 항모' (Al Jazeera)"),
            dict(lat=27.06,lon=56.89,name="시리크 — 샤히드 마지드 해군기지",sz=18,note="위성 포착: 고속정 40+ 집결 (Euro-Times)"),
            dict(lat=28.97,lon=50.84,name="부셰르 미사일기지 — 크루즈미사일",sz=20,note="3/17 미군 5,000lb 벙커버스터 타격 (Guardian)"),
            dict(lat=35.69,lon=51.39,name="테헤란 — IRGC 지휘부 (타격됨)",sz=18,note="2/28 하메네이 사망 (Wikipedia)"),
            dict(lat=32.43,lon=53.69,name="이스파한 — 핵시설 (타격됨)",sz=18,note="2/28 핵 농축시설 (Britannica)"),
            dict(lat=36.30,lon=59.60,name="마슈하드 — IRGC 미사일여단",sz=16,note="샤하브-3·파타흐-110 기지 (ISW)"),
            dict(lat=33.89,lon=35.50,name="레바논 — 헤즈볼라 (이란 프록시)",sz=18,note="로켓200발+드론20대 | IRGC 지원 (ISW)"),
        ]
        ir_predicted=[
            dict(lat=26.80,lon=55.50,name="[예측] IRGC 고속정 호르무즈 배치",sz=18,note="40+ 고속정 분산 배치 (ISW 분석)"),
            dict(lat=27.40,lon=57.30,name="[예측] 이란 잠수함 (가딜급) 작전구역",sz=14,note="기뢰 부설·선제공격 태세"),
            dict(lat=34.80,lon=48.50,name="[예측] IRGC 방공망 잔존구역",sz=12,note="잔존 S-300 배치 추정"),
            dict(lat=30.50,lon=56.80,name="[예측] 지하 미사일 사일로 (케르만)",sz=14,note="ISW 분석"),
            dict(lat=33.0,lon=46.50,name="[예측] 이란 지원 이라크 PMF",sz=12,note="카타이브 헤즈볼라 → 미군 기지 드론"),
        ]
        fig_mil=go.Figure()
        fig_mil.add_trace(go.Scattergeo(
            lon=[55.3,55.3,58.8,58.8,55.3],lat=[25.5,27.3,27.3,25.5,25.5],
            mode="lines",fill="toself",fillcolor="rgba(239,68,68,0.08)",
            line=dict(color="#ef4444",width=1.5,dash="dash"),name="⛔ 호르무즈 봉쇄구역",hoverinfo="name"))
        fig_mil.add_trace(go.Scattergeo(
            lon=[56.0,56.5,57.0,57.5,58.0],lat=[26.3,26.5,26.6,26.5,26.2],
            mode="lines",line=dict(color="#06b6d4",width=3,dash="dot"),name="🚢 항로",hoverinfo="name"))
        if "🔵 미군 확인 배치 (팩트)" in layer_opts:
            fig_mil.add_trace(go.Scattergeo(
                lon=[p["lon"] for p in us_confirmed],lat=[p["lat"] for p in us_confirmed],mode="markers",
                marker=dict(size=[p["sz"] for p in us_confirmed],color="#3b82f6",symbol="pentagon",
                            line=dict(width=1.5,color="white"),opacity=0.95),
                name="🔵 미군 확인 (팩트)",
                text=[f"<b>🔵 {p['name']}</b><br><span style='color:#93c5fd'>{p['note']}</span>" for p in us_confirmed],
                hovertemplate="%{text}<extra></extra>"))
        if "🔵 미군 예측 배치" in layer_opts:
            fig_mil.add_trace(go.Scattergeo(
                lon=[p["lon"] for p in us_predicted],lat=[p["lat"] for p in us_predicted],mode="markers",
                marker=dict(size=[p["sz"] for p in us_predicted],color="#93c5fd",symbol="pentagon-open",
                            line=dict(width=2.5,color="#3b82f6"),opacity=0.8),
                name="🔵 미군 예측",
                text=[f"<b>{p['name']}</b><br><span style='color:#60a5fa'>{p['note']}</span>" for p in us_predicted],
                hovertemplate="%{text}<extra></extra>"))
        if "🔴 이란군 확인 배치 (팩트)" in layer_opts:
            fig_mil.add_trace(go.Scattergeo(
                lon=[p["lon"] for p in ir_confirmed],lat=[p["lat"] for p in ir_confirmed],mode="markers",
                marker=dict(size=[p["sz"] for p in ir_confirmed],color="#ef4444",symbol="star",
                            line=dict(width=1.5,color="white"),opacity=0.95),
                name="🔴 이란군 확인 (팩트)",
                text=[f"<b>🔴 {p['name']}</b><br><span style='color:#fca5a5'>{p['note']}</span>" for p in ir_confirmed],
                hovertemplate="%{text}<extra></extra>"))
        if "🟠 이란군 예측 배치" in layer_opts:
            fig_mil.add_trace(go.Scattergeo(
                lon=[p["lon"] for p in ir_predicted],lat=[p["lat"] for p in ir_predicted],mode="markers",
                marker=dict(size=[p["sz"] for p in ir_predicted],color="#f97316",symbol="star-open",
                            line=dict(width=2.5,color="#f97316"),opacity=0.82),
                name="🟠 이란군 예측",
                text=[f"<b>{p['name']}</b><br><span style='color:#fed7aa'>{p['note']}</span>" for p in ir_predicted],
                hovertemplate="%{text}<extra></extra>"))
        fig_mil.update_layout(
            height=650,paper_bgcolor="#060d1a",plot_bgcolor="#060d1a",
            font=dict(color="#e2e8f0",family="Noto Sans KR"),
            geo=dict(scope="asia",showland=True,landcolor="#131f35",showocean=True,oceancolor="#0a1628",
                     showlakes=True,lakecolor="#0a1628",showcountries=True,countrycolor="#1e3a5f",
                     showcoastlines=True,coastlinecolor="#1e3a5f",bgcolor="#060d1a",
                     center=dict(lat=28,lon=52),projection_scale=4.5),
            legend=dict(bgcolor="rgba(6,13,26,0.92)",bordercolor="#1a3050",borderwidth=1,font=dict(size=9.5),x=0.01,y=0.99),
            margin=dict(l=0,r=0,t=35,b=0),
            title=dict(text="🪖 미군(🔵)·이란군(🔴) — 실선=팩트 확인 / 점선=분석 예측",
                       font=dict(size=12,color="#64748b"),x=0.5))
        st.plotly_chart(fig_mil,use_container_width=True)

    with legend_col:
        for title,items,color in [
            ("🔵 미군 주요 전력",[("항모전단 2척","CVN-72 아라비아해/CVN-78 홍해"),
              ("F-22 12대","오브다 AB(이스라엘)"),("F-15E·F-35","무와파크 살티 AB(요르단)"),
              ("해병대 2,500명","아라비아해 대기"),("Patriot PAC-3","카타르·쿠웨이트·UAE")],"#60a5fa"),
            ("🔴 이란군 주요 배치",[("카르크섬 IRGC해군","고속정+대함미사일(3/13 타격)"),
              ("케슘섬 지하기지","위성 확인 미사일시설"),("시리크 해군기지","고속정 40+ 위성 포착"),
              ("부셰르 미사일기지","크루즈미사일(3/17 타격)"),("헤즈볼라(레바논)","로켓200발+드론20대")],"#f87171"),
        ]:
            rows=""
            for lb,detail in items:
                rows+=f"""<div style="margin-bottom:5px;border-bottom:1px solid #0f1825;padding-bottom:4px">
                    <div style="font-size:0.77rem;color:{color};font-weight:700">{lb}</div>
                    <div style="font-size:0.69rem;color:#475569">{detail}</div></div>"""
            st.markdown(f"""<div class="tracker-box"><div class="tracker-title">{title}</div>{rows}</div>""",unsafe_allow_html=True)
        rows_b=""
        for domain,status,c in [("제공권","미군 장악","#22c55e"),("해상","이란 봉쇄·미군 대응","#f59e0b"),
            ("미사일","이란 잔존","#f87171"),("핵시설","70%+ 무력화","#22c55e"),("리더십","하메네이 사망","#22c55e")]:
            rows_b+=f"""<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #0f1825;font-size:0.76rem">
                <span style="color:#94a3b8">{domain}</span><span style="color:{c};font-weight:700">{status}</span></div>"""
        st.markdown(f"""<div class="tracker-box"><div class="tracker-title">⚖️ 전력 균형</div>{rows_b}</div>""",unsafe_allow_html=True)
        st.markdown("""<div style="font-size:0.65rem;color:#334155;margin-top:0.3rem;text-align:center">
            출처: CENTCOM·ISW·Wikipedia·IranIntl·Al Jazeera</div>""",unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# TAB 3 : 타임라인
# ════════════════════════════════════════════════════════
with tab3:
    st.markdown("#### 📅 주요 교전 타임라인 (2026.02.28 ~ 03.18)")
    events=[
        ("2026.02.28","critical","⚡ 개전 — Operation Epic Fury / Roaring Lion",
         "미국+이스라엘 기습공습. 하메네이 사망 확인. 핵시설·군사인프라·리더십 동시 타격. 이란 보복 미사일·드론 발사."),
        ("2026.03.01","critical","🟥 미군 첫 사망 / 영국 참전 / 아마존 데이터센터 피격",
         "미군 3명 전사·5명 중상. 영국 카타르·요르단·이라크·키프로스에 전투기 배치. 이란 드론 → 아마존 DC 3곳 파괴."),
        ("2026.03.02","critical","🚢 호르무즈 전면 봉쇄 + 미 제공권 장악",
         "IRGC 전면봉쇄 선언. 탱커 70% 급감. 브렌트유 $100 돌파. 미 CENTCOM 테헤란 서부 제공권 확보."),
        ("2026.03.08","econ","💸 브렌트유 $126/배럴 고점",
         "호르무즈 봉쇄+이란 산유시설 우려. 글로벌 에너지 위기. 한국 코스피 급락·원화 절하."),
        ("2026.03.10","high","🚀 이란 집속탄두 → 이스라엘 중부 예후드",
         "아이언돔 부분 침투. 예후드 민간인 2명 사망. 이스라엘 의회 긴급 소집."),
        ("2026.03.11","high","🔥 헤즈볼라 로켓 200발 + 드론 20대",
         "이스라엘 레바논 남부 지상작전 개시. 레바논 총 사망 880명+."),
        ("2026.03.13","critical","💣 카르크섬 타격 / 두바이·마나마 드론 보복",
         "IRGC 기뢰·미사일 저장고 파괴. 이란 드론 → 두바이·마나마 시티뱅크. UAE 사망 8명."),
        ("2026.03.15","medium","🛳️ 이란 선택적 봉쇄 전환",
         "중·러·인도 선박만 호르무즈 통행 허용. 미·이·영 선박 여전히 위협."),
        ("2026.03.17","critical","🎯 이란 고위급 연쇄 제거 + 호르무즈 미사일기지 타격",
         "라리자니 안보책임자·IRGC 바시즈 사령관 사망. 5,000lb GBU-57 투하. 바그다드 미 대사관 드론 공격."),
        ("2026.03.18","high","📡 현재 — 전투 지속 / 비공식 외교채널",
         "트럼프: '목표 달성 전까지 지속'. 이란 임시 지도부 구성. 대테러센터장 사임."),
    ]
    lv={"critical":"critical","high":"high","medium":"medium","econ":"econ"}
    lb_map={"critical":"🔴 위기","high":"🟠 고조","medium":"🔵 군사","econ":"🟢 경제"}
    for date,level,title,detail in events:
        st.markdown(f"""<div class="event-card {lv[level]}">
          <span class="badge {lv[level]}">{lb_map[level]}</span>
          <div class="event-date">{date}</div>
          <div class="event-title">{title}</div>
          <div class="event-detail">{detail}</div></div>""",unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# TAB 4 : 피해 현황
# ════════════════════════════════════════════════════════
with tab4:
    st.markdown("#### 💀 국가별 피해 현황 (2026.03.18)")
    ca1,ca2=st.columns([3,2])
    with ca1:
        cas=pd.DataFrame({"국가":["이란","레바논","UAE·걸프","이스라엘","미군"],
                          "사망":[1444,880,28,12,13],"부상":[18551,2200,200,350,200],
                          "color":["#ef4444","#f97316","#eab308","#3b82f6","#6366f1"]})
        fc=go.Figure()
        fc.add_trace(go.Bar(name="사망",x=cas["국가"],y=cas["사망"],marker_color=cas["color"],
            text=cas["사망"],textposition="outside",textfont=dict(color="#e2e8f0",size=11)))
        fc.add_trace(go.Bar(name="부상",x=cas["국가"],y=cas["부상"],
            marker_color=[hex_to_rgba(c) for c in cas["color"]],text=cas["부상"],
            textposition="outside",textfont=dict(color="#64748b",size=10)))
        fc.update_layout(barmode="group",height=300,paper_bgcolor="#060d1a",plot_bgcolor="#060d1a",
            font=dict(color="#e2e8f0",family="Noto Sans KR"),
            xaxis=dict(gridcolor="#1a3050"),yaxis=dict(gridcolor="#1a3050"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),margin=dict(t=20,b=0,l=0,r=0))
        st.plotly_chart(fc,use_container_width=True)
        days=pd.date_range("2026-02-28","2026-03-18")
        killed=[0,170,250,380,520,650,780,900,1050,1150,1250,1300,1320,1350,1380,1400,1420,1440,1444]
        fl=go.Figure()
        fl.add_trace(go.Scatter(x=days,y=killed,mode="lines+markers",
            line=dict(color="#ef4444",width=2.5),fill="tozeroy",fillcolor="rgba(239,68,68,0.1)"))
        fl.update_layout(height=200,paper_bgcolor="#060d1a",plot_bgcolor="#060d1a",
            font=dict(color="#e2e8f0",family="Noto Sans KR"),
            xaxis=dict(gridcolor="#1a3050"),yaxis=dict(gridcolor="#1a3050",title="사망자"),
            margin=dict(t=25,b=0),showlegend=False,
            title=dict(text="이란 누적 사망자 추이",font=dict(size=12,color="#64748b"),x=0.5))
        st.plotly_chart(fl,use_container_width=True)
    with ca2:
        for cl,lb2,val,sub in [("red","이란 사망","1,444+","부상 18,551명"),
            ("amber","레바논 사망","880+","헤즈볼라 교전"),
            ("blue","미군 전사","13명","부상 200+명"),
            ("green","이스라엘","12명","이란 보복"),
            ("purple","UAE·걸프","28명","이란 드론·미사일")]:
            st.markdown(f"""<div class="kpi-card {cl}"><div class="kpi-label">{lb2}</div>
                <div class="kpi-value">{val}</div><div class="kpi-sub">{sub}</div></div>""",unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# TAB 5 : 경제 충격
# ════════════════════════════════════════════════════════
with tab5:
    st.markdown("#### 📈 글로벌 경제 충격")
    ec1,ec2=st.columns(2)
    with ec1:
        oil_days=pd.date_range("2026-02-25","2026-03-18")
        oil=[63,64,63,65,90,98,102,106,112,116,119,121,126,124,120,116,112,108,104,101,100,103]
        oil=oil[:len(oil_days)]
        fo=go.Figure()
        fo.add_hline(y=65,line_dash="dash",line_color="#22c55e",annotation_text="개전 전 $65",annotation_font_size=10)
        fo.add_trace(go.Scatter(x=oil_days[:len(oil)],y=oil,mode="lines+markers",
            line=dict(color="#f59e0b",width=3),fill="tozeroy",fillcolor="rgba(245,158,11,0.08)"))
        fo.update_layout(height=260,paper_bgcolor="#060d1a",plot_bgcolor="#060d1a",
            font=dict(color="#e2e8f0",family="Noto Sans KR"),
            xaxis=dict(gridcolor="#1a3050"),yaxis=dict(gridcolor="#1a3050",title="$/배럴"),
            margin=dict(t=30,b=0),showlegend=False,
            title=dict(text="브렌트 원유 가격 추이",font=dict(size=12,color="#64748b"),x=0.5))
        st.plotly_chart(fo,use_container_width=True)
        tank_days=pd.date_range("2026-02-25","2026-03-18")
        tank=[100,100,100,100,85,60,30,12,8,8,8,10,10,12,15,15,15,15,15,15,15,15]
        tank=tank[:len(tank_days)]
        ft=go.Figure()
        ft.add_vline(x="2026-03-02",line_dash="dash",line_color="#ef4444",annotation_text="봉쇄선언",annotation_font_size=10)
        ft.add_trace(go.Scatter(x=tank_days[:len(tank)],y=tank,mode="lines+markers",
            line=dict(color="#06b6d4",width=3),fill="tozeroy",fillcolor="rgba(6,182,212,0.08)"))
        ft.update_layout(height=230,paper_bgcolor="#060d1a",plot_bgcolor="#060d1a",
            font=dict(color="#e2e8f0",family="Noto Sans KR"),
            xaxis=dict(gridcolor="#1a3050"),yaxis=dict(gridcolor="#1a3050",title="통행량(기준=100)"),
            margin=dict(t=30,b=0),showlegend=False,
            title=dict(text="🚢 호르무즈 탱커 통행량",font=dict(size=12,color="#64748b"),x=0.5))
        st.plotly_chart(ft,use_container_width=True)
    with ec2:
        st.markdown("**글로벌 경제 주요 지표**")
        for cl,lb3,val,sub in [
            ("amber","브렌트유 고점","$126/bbl","3/8 기록 | +94%"),
            ("amber","현재 브렌트유","$103/bbl","3/17 기준 | +50%"),
            ("red","WTI 원유","$95/bbl","개전 전 $60~65"),
            ("cyan","호르무즈 봉쇄","-70%","세계 원유 20% 차단"),
            ("red","코스피·원화","급락·절하","한국 직접 충격"),
            ("purple","LNG 가격","사상 최고","UAE 가스전 피격"),
        ]:
            st.markdown(f"""<div class="kpi-card {cl}"><div class="kpi-label">{lb3}</div>
                <div class="kpi-value" style="font-size:1.3rem">{val}</div>
                <div class="kpi-sub">{sub}</div></div>""",unsafe_allow_html=True)
        st.markdown("""<div class="event-card medium" style="margin-top:0.3rem">
          <div class="event-title">📡 전망</div>
          <div class="event-detail">
          • 예측 시장: 2026년 6월 종전 가능성 우세<br>
          • 비공식 외교채널 가동 (중재국 미정)<br>
          • 美 대테러센터장 사임 → 내부 균열<br>
          • 트럼프: "목표 달성 전까지 지속"
          </div></div>""",unsafe_allow_html=True)

# ── 푸터 ──────────────────────────────────────────────────
st.markdown('<div class="divider"></div>',unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;color:#1e3050;font-size:0.72rem;padding:0.4rem 0;">
✈️ 항공: OpenSky Network — 🚢 선박: ISW·Reuters 보도기반 — 🪖 군사배치: CENTCOM·ISW·IranIntl·Wikipedia·Al Jazeera<br>
⚠️ 본 대시보드는 공개 보도자료 기반 정보 분석 목적으로 제작되었습니다. (2026.03.18)
</div>""",unsafe_allow_html=True)
