import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# T-Protocol 로딩: 가식 없는 팩트폭격 카페 시뮬레이터 (매운맛)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="💀 카페 창업 생존 시뮬레이터: 극현실 지옥편",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.kpi-card { background: linear-gradient(135deg, #18181b 0%, #27272a 100%); border: 1px solid #3f3f46; border-radius: 12px; padding: 20px; transition: all 0.3s; }
.kpi-card:hover { border-color: #ef4444; box-shadow: 0 4px 20px rgba(239, 68, 68, 0.2); }
.kpi-title { font-size: 0.85rem; color: #a1a1aa; font-weight: 700; margin-bottom: 5px; }
.kpi-val { font-size: 1.8rem; font-weight: 900; color: #f4f4f5; font-family: monospace; }
.fact-box { border-left: 4px solid #ef4444; background: #27272a; padding: 15px; margin: 15px 0; border-radius: 0 8px 8px 0; }
.fact-title { color: #ef4444; font-weight: 900; font-size: 1.1rem; margin-bottom: 5px; }
.fact-text { color: #d4d4d8; font-size: 0.95rem; line-height: 1.5; }
.header-tprot { background: linear-gradient(90deg, #7f1d1d, #450a0a); padding: 20px; border-radius: 10px; border-left: 5px solid #f87171; margin-bottom: 20px; }
h3 { margin-top: 1.5rem; }
.stSlider > div > div > div > div { background-color: #ef4444; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-tprot">
    <h1 style="color:#f87171; margin:0;">💀 T-Protocol 카페 창업 생존 지옥편</h1>
    <p style="color:#fca5a5; margin-top:5px; font-weight:500;">프차 컨설턴트들이 절대 말 안 하는 진상, 기계 고장, 알바 추노 리스크까지 전부 숫자로 때려 박았다. 멘탈 꽉 잡아라.</p>
</div>
""", unsafe_allow_html=True)

# ── 데이터셋 ──
LOCATIONS = {
    "S급 (메인상권)": {"보증금평당": 350, "월세평당": 25, "권리금평당": 400, "회전율": 6.0, "인테리어": 450},
    "A급 (번화가)": {"보증금평당": 250, "월세평당": 15, "권리금평당": 200, "회전율": 4.5, "인테리어": 350},
    "B급 (오피스/대학가)": {"보증금평당": 150, "월세평당": 10, "권리금평당": 100, "회전율": 3.0, "인테리어": 280},
    "C급 (동네 구석)": {"보증금평당": 100, "월세평당": 6, "권리금평당": 20, "회전율": 1.5, "인테리어": 200},
}

with st.sidebar:
    st.header("1️⃣ 점포 뼈대 세팅")
    loc_sel = st.selectbox("상권 수준 (현실 파악부터)", list(LOCATIONS.keys()), index=2)
    area = st.number_input("매장 평수", 10, 100, 15)
    loc = LOCATIONS[loc_sel]
    
    dep = st.number_input("보증금 (만원)", 0, 100000, int(loc['보증금평당']*area), step=100)
    kwon = st.number_input("바닥/영업 권리금 (만원) - 날릴 확률 농후", 0, 50000, int(loc['권리금평당']*area), step=100)
    rent = st.number_input("월세 (만원) - 비가 오나 눈이 오나 나감", 0, 5000, int(loc['월세평당']*area), step=10)
    
    st.divider()
    st.header("2️⃣ 매출 허상과 실체")
    unit_price = st.number_input("예상 평균 객단가 (원)", 2000, 20000, 6000, step=500)
    material_ratio = st.slider("기본 원가율 (%) + 우유 버리는 건 덤", 15, 60, 35) / 100.0
    delivery_ratio = st.slider("배달 비중 (%) - 할수록 적자", 0, 80, 30) / 100.0
    delivery_fee_ratio = st.slider("배달앱 삥뜯는 수수료 (%)", 10, 50, 30) / 100.0
    
    st.divider()
    st.header("3️⃣ 인간 갈아넣기 & 지옥의 변수")
    work_hrs = 14
    owner_work = st.slider(f"사장 매장 상주시간 (일 기준, 총 {work_hrs}H 중)", 0, 16, 10)
    pt_wage = st.number_input("알바 시급 (원, 주휴+퇴직금리스크 반영)", 9860, 20000, 12500)
    
    st.markdown("🚨 **[숨겨진 현실 리스크 파라미터]**")
    black_consumer = st.slider("진상 손님 (환불/재결제/서비스 요구 비율 %)", 0.0, 10.0, 2.5, step=0.1) / 100.0
    alba_run = st.number_input("알바 추노 손실 (월 / 무단결근 땜빵급여, 구인광고 등 만원)", 0, 100, 15)
    machine_fail = st.number_input("머신 잔고장/정수필터/에어컨 유지보수 (월 만원)", 0, 80, 10)
    
    st.divider()
    st.header("4️⃣ 대출 (빚쟁이 스타트)")
    my_cash = st.number_input("내 쌩돈 (만원)", 0, 200000, 5000, step=1000)
    interest_rate = st.number_input("대출 금리 (%)", 2.0, 15.0, 6.5, step=0.1) / 100.0

# ── 초기비용 ──
int_cost = loc['인테리어'] * area
machine_cost = 2500 
etc_start_cost = 1000 
total_startup = dep + kwon + int_cost + machine_cost + etc_start_cost
loan_amt = max(0, total_startup - my_cash)

# ── 연산 ──
seats = int(area * 0.7) 
daily_cust_offline = seats * loc['회전율']
daily_cust_delivery = daily_cust_offline * (delivery_ratio / max(1 - delivery_ratio, 0.01))

daily_rev_offline = daily_cust_offline * unit_price
daily_rev_delivery = daily_cust_delivery * unit_price
monthly_rev = (daily_rev_offline + daily_rev_delivery) * 30

monthly_material = monthly_rev * material_ratio
monthly_delivery_fee = (daily_rev_delivery * 30) * delivery_fee_ratio

# 인건비
needed_labor_hours = work_hrs * 1.5 
alba_hours = max(0, needed_labor_hours - owner_work)
monthly_labor = alba_hours * pt_wage * 30

# 고정 & 현실 반영 변동비
monthly_interest = loan_amt * interest_rate / 12 * 10000
utility = area * 60000 
card_fee = monthly_rev * 0.015
etc_fixed = 300000 

black_consumer_loss = monthly_rev * black_consumer # 진상 손님 손실액
hidden_risk_cost = (alba_run * 10000) + (machine_fail * 10000) + black_consumer_loss

total_cost = (rent*10000) + monthly_material + monthly_labor + monthly_delivery_fee + monthly_interest + utility + card_fee + etc_fixed + hidden_risk_cost
net_profit = monthly_rev - total_cost

owner_monthly_hours = owner_work * 30
owner_hourly_wage = net_profit / max(owner_monthly_hours, 1) if net_profit > 0 else 0

st.markdown("### 💸 당신의 피눈물 나는 창업 성적표")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">총 창업비용 (대출 포함)</div><div class="kpi-val" style="color:#f87171">{total_startup:,}만</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">매월 숨만쉬어도 나가는 돈</div><div class="kpi-val" style="color:#fbbf24">{int(((rent*10000) + monthly_interest + utility + etc_fixed + (machine_fail*10000))/10000):,}만</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">월 순수익 (니 통장에 꽂히는 돈)</div><div class="kpi-val" style="color:{"#4ade80" if net_profit>0 else "#ef4444"}">{int(net_profit/10000):,}만</div></div>', unsafe_allow_html=True)
with col4:
    color = "#4ade80" if owner_hourly_wage > pt_wage else "#ef4444"
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">사장 실질 시급 (최저시급 미달?)</div><div class="kpi-val" style="color:{color}">{int(owner_hourly_wage):,}원</div></div>', unsafe_allow_html=True)

st.markdown("---")

# T-Protocol 핵심 팩트폭격기 (극현실 진단)
if net_profit < 0:
    st.markdown(f"""<div class="fact-box">
        <div class="fact-title">🚨 폐업각. 장사할수록 빛의 속도로 파산 중 🚨</div>
        <div class="fact-text">매달 <b>{int(abs(net_profit)/10000):,}만 원</b>을 알바와 배달앱 배불리는 데 갖다 바치고 있다. 
        알바 대타 뛰다가 허리 나가고, 기계 고장 날 때 멘탈 터지면 이미 늦는다. 
        당장 월세 깎거나 빚내서 버티는 희망회로 집어치우고 사업 아예 갈아엎어라. 여기 지옥이다.</div>
    </div>""", unsafe_allow_html=True)
elif owner_hourly_wage < pt_wage:
    st.markdown(f"""<div class="fact-box" style="border-color:#fbbf24;">
        <div class="fact-title">⚠️ 자발적 노예 계약 축하한다. "알바만도 못한 사장님" ⚠️</div>
        <div class="fact-text">한 달 <b>{owner_monthly_hours}시간</b> 매장에 묶여서 진상 손님이랑 싸우고 알바 무단결근 땜빵까지 다 메꿨는데, 
        니 손에 떨어지는 순수익 <b>{int(net_profit/10000):,}만 원</b>. 니 시급은 <b>{int(owner_hourly_wage):,}원</b>으로 최저시급(알바 시급 {pt_wage}원)보다 처참하다. 
        이럴 거면 딴 카페에서 알바 뛰는 게 정신건강에 100배 이득이다.</div>
    </div>""", unsafe_allow_html=True)
else:
    months_to_rec = (total_startup * 10000) / net_profit
    st.markdown(f"""<div class="fact-box" style="border-color:#4ade80;">
        <div class="fact-title">✅ 생존했지만 지옥을 걷는 중 ✅</div>
        <div class="fact-text">숨통 트이는 <b>{int(net_profit/10000):,}만 원</b> 벌이는 했다. 근데 넌 이걸 벌기 위해 
        진상 환불로 매달 <b>{int(black_consumer_loss/10000):,}만 원</b> 손해 보고, 알바 관리와 기계 수리에 쓴 <b>{(alba_run+machine_fail):,}만 원</b>의 피로도를 견뎠다. 
        원금 {total_startup:,}만 원 회수까지 <b>{months_to_rec/12:.1f}년 ({int(months_to_rec)}개월)</b> 걸린다. 그 전에 인테리어 질려서 손님 끊기는 데 100원 건다. 정신 바짝 차려라.</div>
    </div>""", unsafe_allow_html=True)

c1, c2 = st.columns([1, 1.2])

with c1:
    st.markdown("### 🧛 실시간 통장 털이범들 (비용 분해)")
    df_cost = pd.DataFrame({
        "원인": ["월세(고정)", "식자재원가", "알바비", "배달삥뜯기", "감춰진손실(진상/기계고장/추노)", "기타기본유지비", "대출이자"],
        "금액": [rent*10000, monthly_material, monthly_labor, monthly_delivery_fee, hidden_risk_cost, card_fee + utility + etc_fixed, monthly_interest]
    })
    fig_pie = px.pie(df_cost, names="원인", values="금액", hole=0.3, color_discrete_sequence=px.colors.sequential.YlOrRd_r)
    fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#d4d4d8"), height=380, legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    st.markdown("### 🎲 지옥 히트맵: 극성 진상 vs 알바 노쇼")
    st.caption("알바가 매주 빵꾸내고 진상이 환불러시를 시전할 때, 니 통장에 남는 극강의 현실 차트")
    
    alba_loss_arr = [0, 150000, 300000, 500000, 800000] # 알바 손실비
    bc_rate_arr = [0.0, 0.02, 0.05, 0.08, 0.12]         # 진상 환불 0~12%
    
    z_data = []
    for al in alba_loss_arr:
        row = []
        for bc in bc_rate_arr:
            c_loss = monthly_rev * bc
            h_loss = al + (machine_fail * 10000) + c_loss
            t_cost = (rent*10000) + monthly_material + monthly_labor + monthly_delivery_fee + monthly_interest + utility + card_fee + etc_fixed + h_loss
            row.append((monthly_rev - t_cost)/10000)
        z_data.append(row)
        
    fig_heat = go.Figure(data=go.Heatmap(
        z=z_data,
        x=[f"진상 {bc*100:.1f}%" for bc in bc_rate_arr],
        y=[f"알바손실 {int(al/10000)}만" for al in alba_loss_arr],
        colorscale="RdYlGn",
        text=[[f"{val:.0f}만" for val in r] for r in z_data],
        texttemplate="%{text}"
    ))
    fig_heat.update_layout(height=380, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e4e4e7"))
    st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("""
<br>
<div style="text-align:right; color:#71717a; font-size:0.8rem;">
T-Protocol Execution complete. (현실 부정 금지)
</div>
""", unsafe_allow_html=True)
