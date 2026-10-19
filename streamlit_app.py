
import os, re, json, joblib
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
px.defaults.template = "plotly_dark"
from pitch_extractor import extract_pitch

ROOT=os.path.dirname(os.path.abspath(__file__))
MODEL_DIR=os.path.join(ROOT,"models")
DATA=os.path.join(ROOT,"data.csv")

st.set_page_config(page_title="Shark Tank AI",page_icon="🦈",layout="wide",initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap');
:root{color-scheme:dark;--bg:#080d17;--panel:#101a2a;--panel2:#142237;--border:#24374f;--text:#edf7ff;--muted:#9bb0c8;--cyan:#3de4ff;--cyan2:#00b8d9;--purple:#8275ff}
#MainMenu,footer,header{visibility:hidden}
.stApp{background:radial-gradient(ellipse at 50% -18%,#16344a 0%,#0a1322 42%,#070b13 100%);color:var(--text);font-family:'DM Sans',sans-serif}
.block-container{max-width:1280px;padding:1.1rem 2rem 4rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0d1726 0%,#09111d 100%);border-right:1px solid #20334a}
[data-testid="stSidebar"] *{color:var(--text)}
[data-testid="stSidebar"] [data-testid="stRadio"] label{background:#111f31;border:1px solid #21364d;border-radius:12px;padding:.58rem .72rem;margin:.22rem 0;transition:all .18s ease}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{border-color:var(--cyan);box-shadow:0 0 16px #3de4ff1f;transform:translateX(2px)}
[data-testid="stSidebar"] [data-testid="stRadio"] label p{font-weight:700}
[data-testid="stSidebar"] [data-testid="stRadio"] input:checked+div{color:var(--cyan)}
.hero{padding:2.4rem 0 1.6rem;background:transparent;color:var(--text);margin-bottom:1rem;text-align:center}
.hero h1{font-family:'Manrope',sans-serif;font-size:clamp(2.25rem,4vw,3.4rem);font-weight:800;letter-spacing:-.055em;line-height:1.08;margin:.25rem 0 .8rem;color:var(--text)}
.hero p{font-size:1.05rem;line-height:1.65;color:var(--muted);max-width:690px;margin:0 auto}
.eyebrow{text-transform:uppercase;letter-spacing:.15em;font-size:.72rem;font-weight:800;color:var(--cyan);margin-bottom:.65rem}
.panel{border:1px solid var(--border);border-radius:18px;padding:1.15rem 1.25rem;background:linear-gradient(145deg,#122137,#0e1727);box-shadow:0 10px 35px #00000020}
.tag{display:inline-block;padding:.34rem .62rem;margin:.18rem .18rem .18rem 0;border-radius:999px;background:#172b40;color:#bdefff;font-size:.82rem;border:1px solid #28465e}
.detected{background:#123b3c;border:1px solid #1c7779;color:#91fff4}.estimated{background:#3a2c18;border:1px solid #785a2b;color:#ffe0a0}
.small{font-size:.82rem;color:var(--muted)}.result-title{font-size:1.45rem;font-weight:800}.big{font-size:2.2rem;font-weight:850}
.stButton>button{border-radius:12px;font-weight:750;min-height:2.75rem;border:1px solid #2c526a;background:#14243a;color:var(--text);transition:all .18s ease}
.stButton>button:hover{border-color:var(--cyan);color:var(--cyan);box-shadow:0 0 20px #3de4ff26;transform:translateY(-1px)}
.stButton>button[kind="primary"]{background:linear-gradient(100deg,#00a9c7,#3de4ff);color:#04111b;border:1px solid #3de4ff;box-shadow:0 0 22px #3de4ff30}
.stButton>button[kind="primary"]:hover{background:linear-gradient(100deg,#27d4ec,#8af3ff);color:#04111b}
[data-testid="stMetric"]{background:linear-gradient(145deg,#142338,#0e1727);border:1px solid var(--border);border-radius:16px;padding:14px 16px;box-shadow:0 8px 28px #00000020}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p{color:var(--muted)!important}[data-testid="stMetricValue"]{color:var(--text)!important}
[data-testid="stTextArea"] textarea,[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stSelectbox"]>div>div,[data-testid="stMultiSelect"]>div>div{border-radius:10px!important;background:#0b1422!important;color:var(--text)!important;border-color:#294057!important}
[data-baseweb="select"] div,[data-baseweb="popover"] li{background:#0d1929;color:var(--text)}
h1,h2,h3,h4{font-family:'Manrope',sans-serif;letter-spacing:-.025em;color:var(--text)}p,li,label{color:var(--text)}.stMarkdown small{color:var(--muted)}
hr{border-color:#24374f}div[data-testid="stExpander"]{background:#0f1a2a;border:1px solid var(--border);border-radius:13px}
[data-testid="stProgressBar"]>div>div{background:linear-gradient(90deg,var(--cyan2),var(--cyan))}
.topbrand{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:.45rem 0 1rem;border-bottom:1px solid #24374f;margin-bottom:1.2rem}
.brandmark{font-family:'Manrope',sans-serif;font-weight:800;font-size:1.2rem;letter-spacing:-.04em;color:var(--text);white-space:nowrap}.brandmark span{color:var(--cyan)}
.toplinks{font-size:.86rem;font-weight:700;color:#b8cde2}.homehero,.analyzer-hero{text-align:center;padding:2.1rem 0 1.5rem}
.homehero h1,.analyzer-hero h1{font-family:'Manrope',sans-serif;font-size:clamp(2.3rem,4vw,3.65rem);font-weight:800;letter-spacing:-.06em;line-height:1.04;margin:.25rem 0 .85rem;color:var(--text);text-shadow:0 0 36px #3de4ff18}
.homehero p,.analyzer-hero p{font-size:1.02rem;line-height:1.65;color:var(--muted);max-width:680px;margin:0 auto}
.entity-card,.company-card{border:1px solid #24374f;border-radius:17px;padding:1rem;background:linear-gradient(145deg,#142338,#0c1523);min-height:120px;margin:.25rem 0 .75rem;box-shadow:0 9px 30px #00000022;transition:all .2s ease}
.entity-card:hover,.company-card:hover{border-color:#3de4ff;box-shadow:0 0 0 1px #3de4ff35,0 0 26px #3de4ff15;transform:translateY(-3px)}.company-card{min-height:190px}
.avatar{font-size:1.65rem;margin-bottom:.4rem}.entity-name{font-weight:800;font-size:1.02rem;color:var(--text);letter-spacing:-.025em}.entity-meta,.footer-note{font-size:.79rem;color:var(--muted);margin-top:.35rem}
.company-kicker{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--cyan);font-weight:800;margin-bottom:.45rem}.company-card p{font-size:.82rem;line-height:1.5;color:#b0c2d5;margin:.55rem 0 0}
.shark-photo-wrap{display:flex;justify-content:center;align-items:center;margin:.2rem 0 .75rem}[data-testid="stImage"] img{width:108px;height:108px;object-fit:cover;border-radius:50%;border:2px solid #3de4ff;box-shadow:0 0 0 5px #3de4ff12,0 0 24px #3de4ff25;margin:0 auto;transition:transform .2s ease,box-shadow .2s ease}[data-testid="stImage"] img:hover{transform:scale(1.06);box-shadow:0 0 0 7px #3de4ff20,0 0 34px #3de4ff55}div[data-testid="stVerticalBlockBorderWrapper"]{background:linear-gradient(145deg,#142338,#0c1523);border:1px solid #24374f;border-radius:17px;box-shadow:0 9px 30px #00000022;transition:all .2s ease}div[data-testid="stVerticalBlockBorderWrapper"]:hover{border-color:#3de4ff;box-shadow:0 0 0 1px #3de4ff35,0 0 26px #3de4ff15;transform:translateY(-2px)}.shark-caption{text-align:center;font-size:.76rem;color:var(--muted);margin-top:.15rem}
[data-testid="stDataFrame"]{border:1px solid var(--border);border-radius:12px;overflow:hidden}
[data-testid="stAlert"]{background:#11263a;border:1px solid #28506a;color:var(--text)}
</style>
""",unsafe_allow_html=True)

@st.cache_resource
def load():
    names=["deal_model","offer_model","valuation_model","deal_amount_model","equity_model","num_sharks_model"]
    m={n:joblib.load(os.path.join(MODEL_DIR,n+".pkl")) for n in names}
    for s in ["Namita","Vineeta","Anupam","Aman","Peyush"]:
        m["shark_"+s.lower()]=joblib.load(os.path.join(MODEL_DIR,"shark_"+s.lower()+".pkl"))
    return m,joblib.load(os.path.join(MODEL_DIR,"metadata.pkl"))
@st.cache_data
def data():
    return pd.read_csv(DATA)

models,meta=load()
df=data()
SHARKS=meta["sharks"]
FEATURES=meta["features"]
INDUSTRIES=sorted(df["Industry"].dropna().unique())
STATES=sorted(df["Pitchers State"].dropna().astype(str).str.split(",").str[0].unique())

def money(x):
    if x is None:return "—"
    return f"₹{x:,.1f} lakh"
def pct(x):return f"{x*100:.1f}%"
def age_text(x):return {0:"Young",1:"Middle",2:"Old"}.get(int(x),"Middle")

# Dataset-derived fallback values, instead of arbitrary hard-coded business values.
NUM_DEFAULTS={
    "ask":float(df["Original Ask Amount"].median()),
    "equity":float(df["Original Offered Equity"].median()),
    "valuation":float(df["Valuation Requested"].median()),
    "revenue":float(df["Yearly Revenue"].median()),
    "monthly_sales":float(df["Monthly Sales"].median()),
    "gross_margin":float(df["Gross Margin"].median()),
    "net_margin":float(df["Net Margin"].median()),
    "ebitda":float(df["EBITDA"].median()),
    "skus":int(df["SKUs"].median()),
    "started_in":int(df["Started in"].median()),
    "presenters":int(df["Number of Presenters"].median()),
    "age": int(pd.to_numeric(df["Pitchers Average Age"], errors="coerce").median()) if pd.to_numeric(df["Pitchers Average Age"], errors="coerce").notna().any() else 30,
}
CAT_DEFAULTS={
    "industry":df["Industry"].mode().iloc[0],
    "state":df["Pitchers State"].dropna().astype(str).str.split(",").str[0].mode().iloc[0],
}

def resolve(ex):
    p={}
    estimated=[]
    for k in NUM_DEFAULTS:
        if ex.get(k) is not None:p[k]=ex[k]
        else:p[k]=NUM_DEFAULTS[k];estimated.append(k)
    for k in CAT_DEFAULTS:
        if ex.get(k) is not None:p[k]=ex[k]
        else:p[k]=CAT_DEFAULTS[k];estimated.append(k)
    p["bootstrapped"]=0 if ex.get("bootstrapped") is None else ex["bootstrapped"]
    p["patents"]=0 if ex.get("patents") is None else ex["patents"]
    p["cash_burn"]=0 if ex.get("cash_burn") is None else ex["cash_burn"]
    p["estimated_fields"]=estimated
    # Logical derived fallbacks.
    if ex.get("valuation") is None and ex.get("ask") is not None and ex.get("equity",0)>0:
        p["valuation"]=ex["ask"]*100/ex["equity"]; estimated.append("valuation (derived from ask/equity)")
    if ex.get("monthly_sales") is None and ex.get("revenue") is not None:
        p["monthly_sales"]=ex["revenue"]/12; estimated.append("monthly sales (derived from annual revenue)")
    return p

def build_row(p,sharks):
    row={
        "Season Number":5,"Episode Number":10,"Pitch Number":3,
        "Started in":p["started_in"],"Number of Presenters":p["presenters"],
        "Male Presenters":p["presenters"],"Female Presenters":0,"Transgender Presenters":0,"Couple Presenters":0,
        "Pitchers Average Age":p["age"],"Yearly Revenue":p["revenue"],"Monthly Sales":p["monthly_sales"],
        "Gross Margin":p["gross_margin"],"Net Margin":p["net_margin"],"EBITDA":p["ebitda"],
        "Cash Burn":p["cash_burn"],"SKUs":p["skus"],"Has Patents":p["patents"],"Part of Match off":0,
        "Original Ask Amount":p["ask"],"Original Offered Equity":p["equity"],"Valuation Requested":p["valuation"],
        "Namita Present":int("Namita" in sharks),"Vineeta Present":int("Vineeta" in sharks),
        "Anupam Present":int("Anupam" in sharks),"Aman Present":int("Aman" in sharks),
        "Peyush Present":int("Peyush" in sharks),"Ritesh Present":0,"Amit Present":0,"Guest Present":0,
        "Industry":p["industry"],"Pitchers State":p["state"],"Bootstrapped":p["bootstrapped"],
        "days_into_season":30,"ask_log":np.log1p(max(0,p["ask"])),
        "valuation_requested_log":np.log1p(max(0,p["valuation"])),
        "ask_equity_ratio":p["equity"]/(p["ask"]+1),
        "valuation_ask_ratio":p["valuation"]/(p["ask"]+1),
        "sharks_present_count":len(sharks)
    }
    return pd.DataFrame([row])

def predict(p,sharks):
    X=build_row(p,sharks)
    deal=float(models["deal_model"].predict_proba(X)[:,1][0])
    offer=float(models["offer_model"].predict_proba(X)[:,1][0])
    valuation=max(0,float(np.expm1(models["valuation_model"].predict(X)[0])))
    amount=max(0,float(np.expm1(models["deal_amount_model"].predict(X)[0])))
    equity=max(0,float(np.expm1(models["equity_model"].predict(X)[0])))
    ns=float(np.clip(models["num_sharks_model"].predict(X)[0],0,5))
    shark_probs={s:float(models["shark_"+s.lower()].predict_proba(X)[:,1][0]) for s in sharks}
    return dict(deal=deal,offer=offer,valuation=valuation,amount=amount,equity=equity,num_sharks=ns,sharks=shark_probs)

def attractiveness(pred,p):
    traction=min(1,(p["revenue"]/(max(p["ask"],1)*2.0)))
    margin=np.clip((p["gross_margin"]+max(p["net_margin"],-20))/100,0,1)
    valuation_pressure=1-np.clip(p["valuation"]/(max(p["revenue"]*10,1)),0,1)
    return float(np.clip(100*(.50*pred["deal"]+.18*traction+.17*margin+.15*valuation_pressure),0,100))

SAMPLE="""We are building a D2C healthy snack brand in Maharashtra for young professionals.
We have been operating since 2023 and generate ₹50 lakh annual revenue with around
4,000 customers. We are asking for ₹50 lakh in exchange for 5% equity at a requested
valuation of ₹1000 lakh. Our products are sold through our website and Amazon, and
we plan to expand into retail stores. We have strong gross margins and a differentiated product."""

# Dark Sharkary-inspired shell with clearly labelled icon navigation.
NAV_ITEMS = {
    "🏠  Home": "Home",
    "🏢  Companies": "Companies",
    "📊  Analytics": "Analytics",
    "🧪  Pitch Analyzer": "Pitch Analyzer",
    "🦈  Compare Sharks": "Compare Sharks",
    "🎛️  Scenario Simulator": "Scenario Simulator",
    "🗂️  Dataset Insights": "Dataset Insights",
    "🧠  Model Card": "Model Card",
}
with st.sidebar:
    st.markdown("<div class='brandmark' style='padding:.4rem .2rem 1rem'>🦈 Shark Tank <span>AI</span></div>", unsafe_allow_html=True)
    st.caption("PITCH INTELLIGENCE PLATFORM")
    if st.session_state.pop("nav_to_pitch", False):
        st.session_state["nav_page"] = "🧪  Pitch Analyzer"
    if st.session_state.get("nav_page") not in NAV_ITEMS:
        st.session_state["nav_page"] = "🏠  Home"
    selected_nav = st.radio("Navigate", list(NAV_ITEMS.keys()), key="nav_page", label_visibility="collapsed")
    st.markdown("---")
    st.markdown("<div class='small'>Historical data · Model-assisted insights</div>", unsafe_allow_html=True)
page = NAV_ITEMS[selected_nav]
st.markdown("""
<div class="topbrand">
  <div class="brandmark">🦈 Shark Tank <span>AI</span></div>
  <div class="toplinks">Deal intelligence <span style="color:#3de4ff">●</span> India edition</div>
  <div class="small">Explore · Compare · Predict</div>
</div>
""",unsafe_allow_html=True)

if page=="Home":
    st.markdown("""
    <div class="homehero">
      <div class="eyebrow">THE DATA BEHIND THE HANDSHAKE</div>
      <h1>Every pitch. Every shark.<br>Every outcome.</h1>
      <p>Explore Indian Shark Tank pitches, compare investor patterns, and test your startup against historical deal data.</p>
    </div>
    """,unsafe_allow_html=True)
    search=st.text_input("Search sharks, companies, products…",placeholder="Search startups, industries, or founders",label_visibility="collapsed",key="home_search")
    total=len(df)
    deals=int(pd.to_numeric(df.get("Received Offer",0),errors="coerce").fillna(0).astype(bool).sum()) if "Received Offer" in df else 0
    invested=float(pd.to_numeric(df.get("Total Deal Amount",pd.Series(dtype=float)),errors="coerce").fillna(0).sum())
    s1,s2,s3,s4=st.columns(4)
    s1.metric("Pitches in dataset",f"{total:,}")
    s2.metric("Pitches with offers",f"{deals:,}")
    s3.metric("Total deal amount",f"₹{invested:,.0f} lakh")
    s4.metric("Industries",f"{df['Industry'].nunique()}")
    st.markdown("### Meet the original sharks")
    photo_count = sum((os.path.exists(os.path.join(ROOT, "assets", "sharks", f"{slug}.jpg"))) for slug in ["aman", "anupam", "ashneer", "ghazal", "namita", "peyush", "vineeta"])
    st.caption("Season 1 investors · circular portraits are stored locally" if photo_count == 7 else "Season 1 investors · run `python download_shark_photos.py` once to fetch portraits for offline use")
    original_sharks = [
        ("Aman Gupta", "Aman", "boAt"),
        ("Anupam Mittal", "Anupam", "Shaadi.com"),
        ("Ashneer Grover", "Ashneer", "BharatPe"),
        ("Ghazal Alagh", "Ghazal", "Mamaearth"),
        ("Namita Thapar", "Namita", "Emcure"),
        ("Peyush Bansal", "Peyush", "Lenskart"),
        ("Vineeta Singh", "Vineeta", "SUGAR Cosmetics"),
    ]
    asset_dir = os.path.join(ROOT, "assets", "sharks")
    avatar_dir = os.path.join(asset_dir, "placeholders")
    shark_cols = st.columns(4)
    for i, (display_name, shark_key, company) in enumerate(original_sharks):
        slug = shark_key.lower()
        photo_path = os.path.join(asset_dir, f"{slug}.jpg")
        if not os.path.exists(photo_path):
            photo_path = os.path.join(avatar_dir, f"{slug}.png")
        colname = f"{shark_key} Investment Amount"
        deal_count = int((pd.to_numeric(df.get(colname, pd.Series(index=df.index, dtype=float)), errors="coerce").fillna(0) > 0).sum()) if colname in df else None
        with shark_cols[i % 4]:
            with st.container(border=True):
                st.image(photo_path, width=108)
                st.markdown(f"**{display_name}**")
                st.caption(company)
                st.caption(f"{deal_count:,} recorded investments" if deal_count is not None else "Original Season 1 shark")
    st.markdown("### Popular Companies")
    company_df=df.copy()
    if search.strip():
        mask=company_df.astype(str).apply(lambda col: col.str.contains(search.strip(),case=False,na=False)).any(axis=1)
        company_df=company_df[mask]
    display_cols=[c for c in ["Startup Name","Industry","Received Offer","Total Deal Amount","Business Description"] if c in company_df.columns]
    company_df=company_df.drop_duplicates(subset=["Startup Name"]) if "Startup Name" in company_df else company_df
    if len(company_df):
        cards=company_df.head(6)
        grid=st.columns(3)
        for i,(_,r) in enumerate(cards.iterrows()):
            name=str(r.get("Startup Name","Startup"))
            industry=str(r.get("Industry","—"))
            got=str(r.get("Received Offer","—"))
            amount=pd.to_numeric(r.get("Total Deal Amount",0),errors="coerce")
            amount_text=f"₹{amount:,.1f} lakh deal" if pd.notna(amount) and amount>0 else "No recorded deal amount"
            desc=str(r.get("Business Description", ""))
            with grid[i%3]:
                st.markdown(f"<div class='company-card'><div class='company-kicker'>{industry}</div><div class='entity-name'>{name}</div><div class='entity-meta'>{amount_text}</div><p>{desc[:135] + ('…' if len(desc)>135 else '')}</p></div>",unsafe_allow_html=True)
    else:
        st.info("No companies matched your search. Try another name or industry.")
    st.markdown("### Test your pitch against the data")
    st.markdown("Use the AI Pitch Analyzer to estimate deal probability, likely deal terms, and potential shark matches.")
    if st.button("Open Pitch Analyzer →",type="primary",use_container_width=True):
        st.session_state["nav_to_pitch"]=True
        st.rerun()
    st.markdown("<div class='footer-note'>Historical patterns are informative, not guarantees of future investment decisions.</div>",unsafe_allow_html=True)

elif page=="Companies":
    st.markdown("## Companies")
    query=st.text_input("Search companies",placeholder="Company name, industry, or business description")
    view=df.copy()
    if query.strip():
        mask=view.astype(str).apply(lambda col: col.str.contains(query.strip(),case=False,na=False)).any(axis=1)
        view=view[mask]
    cols=[c for c in ["Startup Name","Industry","Season Number","Received Offer","Accepted Offer","Total Deal Amount","Total Deal Equity","Business Description"] if c in view.columns]
    st.caption(f"Showing {len(view):,} matching pitch records")
    st.dataframe(view[cols].drop_duplicates(subset=["Startup Name"]) if "Startup Name" in view else view[cols],use_container_width=True,hide_index=True)

elif page=="Analytics":
    st.markdown("## Analytics")
    c1,c2=st.columns(2)
    with c1:
        counts=df["Industry"].value_counts().head(12).reset_index(); counts.columns=["Industry","Pitches"]
        st.plotly_chart(px.bar(counts,x="Pitches",y="Industry",orientation="h",title="Pitches by industry"),use_container_width=True)
    with c2:
        if "Received Offer" in df:
            offer_by_industry=df.groupby("Industry",dropna=False)["Received Offer"].mean().mul(100).sort_values(ascending=False).reset_index(name="Offer rate (%)")
            st.plotly_chart(px.bar(offer_by_industry,x="Offer rate (%)",y="Industry",orientation="h",title="Offer rate by industry"),use_container_width=True)
    st.markdown("### Deal trends")
    if "Season Number" in df and "Total Deal Amount" in df:
        trend=df.groupby("Season Number",dropna=True).agg(Pitches=("Startup Name","count"),Deal_Amount=("Total Deal Amount","sum")).reset_index()
        st.plotly_chart(px.line(trend,x="Season Number",y="Pitches",markers=True,title="Pitch volume by season"),use_container_width=True)

elif page=="Pitch Analyzer":
    st.markdown("""
    <div class="analyzer-hero"><div class="eyebrow">AI PITCH ANALYZER</div><h1>Would you get a deal?</h1><p>Test your startup against the patterns behind real Shark Tank pitches.</p></div>
    """,unsafe_allow_html=True)
    st.markdown("### Tell us about your startup")
    c1,c2=st.columns([5,1])
    with c1:
        pitch=st.text_area("Pitch",value=st.session_state.get("pitch",""),height=210,
                           placeholder="Describe what your startup sells, your customers, revenue, the amount you are asking for, and the equity you are offering…",label_visibility="collapsed")
    with c2:
        st.markdown("**Try the demo**")
        if st.button("✨ Load sample",use_container_width=True):
            st.session_state.pitch=SAMPLE
            st.rerun()
        st.markdown("<div class='small'>Tip: include your ask, equity, revenue, valuation, customers, industry and traction.</div>",unsafe_allow_html=True)

    if pitch.strip():
        ex=extract_pitch(pitch)
        st.markdown("### What we understood from your pitch")
        chips=[]
        labels={"industry":"Industry","state":"State","ask":"Ask","equity":"Equity","valuation":"Valuation","revenue":"Revenue","started_in":"Started","customers":"Customers"}
        for k,l in labels.items():
            if ex.get(k) is not None:
                v=ex[k]
                if k=="ask":v=f"₹{v:g}L"
                elif k=="valuation":v=f"₹{v:g}L"
                elif k=="revenue":v=f"₹{v:g}L"
                elif k=="equity":v=f"{v:g}%"
                chips.append(f"{l}: {v}")
        st.markdown(" ".join(f"<span class='tag detected'>{x}</span>" for x in chips),unsafe_allow_html=True)
        coverage=ex["extraction_coverage"]
        st.progress(coverage,text=f"Pitch information captured: {coverage*100:.0f}%")
        if coverage<.45:
            st.warning("Your pitch is still missing several structured facts. You can continue, but adding financials and traction will make the scenario more specific.")

        with st.expander("✏️ Verify the AI-extracted information",expanded=True):
            st.caption("Green = found in your pitch. Amber = estimated from the training dataset or logically derived.")
            # Defaults
            p=resolve(ex)
            a,b,c=st.columns(3)
            with a:
                industry=st.selectbox("Industry",INDUSTRIES,index=INDUSTRIES.index(p["industry"]) if p["industry"] in INDUSTRIES else 0)
                ask=st.number_input("Ask amount (₹ lakh)",0.0,100000.0,float(p["ask"]),step=5.0)
                equity=st.number_input("Equity offered (%)",0.0,100.0,float(p["equity"]),step=.5)
                valuation=st.number_input("Requested valuation (₹ lakh)",0.0,1000000.0,float(p["valuation"]),step=10.0)
            with b:
                revenue=st.number_input("Annual revenue (₹ lakh)",0.0,1000000.0,float(p["revenue"]),step=10.0)
                monthly=st.number_input("Monthly sales (₹ lakh)",0.0,100000.0,float(p["monthly_sales"]),step=1.0)
                gross=st.number_input("Gross margin (%)",0.0,100.0,float(p["gross_margin"]))
                net=st.number_input("Net margin (%)",-100.0,100.0,float(p["net_margin"]))
            with c:
                state=st.selectbox("Founder state",STATES,index=STATES.index(p["state"]) if p["state"] in STATES else 0)
                started=st.number_input("Started in",1980,2026,int(p["started_in"]))
                presenters=st.number_input("Presenters",1,10,int(p["presenters"]))
                skus=st.number_input("SKUs / products",0,100000,int(p["skus"]))
            d,e,f=st.columns(3)
            with d:
                age=st.selectbox("Average age group",[0,1,2],index=int(p["age"]),format_func=age_text)
            with e:
                boot=st.checkbox("Bootstrapped",bool(p["bootstrapped"]))
                patents=st.checkbox("Patent / IP",bool(p["patents"]))
            with f:
                burn=st.checkbox("Cash burn",bool(p["cash_burn"]))
                ebitda=st.number_input("EBITDA (₹ lakh)",-100000.0,100000.0,float(p["ebitda"]))

            sharks=st.multiselect("Sharks to evaluate",SHARKS,default=SHARKS)
            p.update(dict(industry=industry,state=state,ask=ask,equity=equity,valuation=valuation,revenue=revenue,
                          monthly_sales=monthly,gross_margin=gross,net_margin=net,started_in=started,presenters=presenters,
                          skus=skus,age=age,bootstrapped=int(boot),patents=int(patents),cash_burn=int(burn),ebitda=ebitda))

            estimated=p.get("estimated_fields",[])
            if estimated:
                st.caption("Estimated/derived fields: "+", ".join(estimated))

        if st.button("🧠 ANALYZE MY PITCH",type="primary",use_container_width=True):
            st.session_state.result=p
            st.session_state.ex=ex
            st.session_state.sharks=sharks
            st.rerun()

    if "result" in st.session_state and st.session_state.get("pitch")==pitch:
        p=st.session_state.result; ex=st.session_state.ex; sharks=st.session_state.sharks
        pred=predict(p,sharks)
        score=attractiveness(pred,p)
        st.divider()
        st.markdown("### Your pitch analysis")
        if pred["deal"]>=.70: headline="Strong deal signal"
        elif pred["deal"]>=.50: headline="Positive deal signal"
        else: headline="High no-deal risk"
        st.markdown(f"<div class='panel'><div class='result-title'>{headline}</div><div class='small'>Based on the verified pitch inputs and historical training data.</div></div>",unsafe_allow_html=True)

        a,b,c,d=st.columns(4)
        a.metric("Deal probability",pct(pred["deal"]))
        b.metric("Offer probability",pct(pred["offer"]))
        c.metric("Expected valuation",money(pred["valuation"]))
        d.metric("Expected deal amount",money(pred["amount"]))

        left,right=st.columns([1.05,.95])
        with left:
            st.markdown("#### Deal probability")
            fig=go.Figure(go.Indicator(mode="gauge+number",value=pred["deal"]*100,
                number={"suffix":"%"},gauge={"axis":{"range":[0,100]}}))
            fig.update_layout(height=250,margin=dict(l=20,r=20,t=20,b=0))
            st.plotly_chart(fig,use_container_width=True)
        with right:
            st.markdown("#### Pitch health")
            st.metric("Derived attractiveness",f"{score:.0f}/100")
            st.progress(int(score))
            st.caption("Dashboard heuristic — not a trained target.")
            if p["valuation"]>p["revenue"]*10:
                st.warning("Valuation is high relative to stated annual revenue. This can increase negotiation pressure.")
            if p["equity"]<3:
                st.warning("The offered equity is very low; the requested valuation should be especially well supported.")

        st.markdown("#### Potential deal structure")
        a,b,c,d=st.columns(4)
        a.metric("Predicted valuation",money(pred["valuation"]))
        b.metric("Predicted deal",money(pred["amount"]))
        c.metric("Predicted equity",f"{pred['equity']:.1f}%")
        d.metric("Expected sharks",f"{pred['num_sharks']:.1f}")

        st.markdown("#### 🦈 Shark match")
        if pred["sharks"]:
            sdf=pd.DataFrame({"Shark":list(pred["sharks"].keys()),"Probability":list(pred["sharks"].values())}).sort_values("Probability",ascending=False)
            fig=px.bar(sdf,x="Probability",y="Shark",orientation="h",range_x=[0,1],
                       text=sdf["Probability"].map(pct),title="Who is most likely to invest?")
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig,use_container_width=True)
            best=sdf.iloc[0]
            st.success(f"Top predicted match: **{best.Shark}** — {best.Probability*100:.1f}%")

        st.markdown("#### 🔍 Why this pitch looks this way")
        sigs=ex["signals"]
        if sigs:
            cols=st.columns(min(3,len(sigs)))
            for i,s in enumerate(sigs): cols[i%len(cols)].markdown(f"<div class='panel'><b>{s}</b><br><span class='small'>Detected from your pitch.</span></div>",unsafe_allow_html=True)
        else: st.info("Add details about customers, revenue, margins, distribution, growth and defensibility to generate stronger qualitative signals.")

        with st.expander("What should I improve in the pitch?"):
            advice=[]
            if ex.get("customers") is None: advice.append("Add customer/user traction (for example, number of customers or subscribers).")
            if ex.get("growth") is None: advice.append("Add growth, such as month-on-month or year-on-year growth.")
            if ex.get("gross_margin") is None: advice.append("State your gross margin.")
            if ex.get("net_margin") is None: advice.append("State profitability or net margin if available.")
            if ex.get("valuation") is None: advice.append("State the valuation you are asking for, or make the ask/equity relationship explicit.")
            if ex.get("started_in") is None: advice.append("Mention when the business was founded/launched.")
            if not advice: st.success("Your pitch contains the main structured facts supported by this extractor.")
            for x in advice: st.write("•",x)

        with st.expander("How the AI works"):
            st.markdown("""
**Pitch → Information extraction → Verification → Tabular ML → Shark Tank analysis**

The current trained models are structured-data models. They do not directly understand arbitrary sentences. The natural-language layer therefore extracts business facts first, and the verified structured facts are then passed into the trained models.

This is intentionally transparent: the app shows which information came from the pitch and which values were estimated from the training data.
""")

elif page=="Compare Sharks":
    st.markdown("## Compare Sharks")
    shark_cols=st.columns(2)
    chosen=st.multiselect("Choose sharks to compare",SHARKS,default=SHARKS[:min(5,len(SHARKS))])
    records=[]
    for shark in chosen:
        amount_col=f"{shark} Investment Amount"
        equity_col=f"{shark} Investment Equity"
        invested=pd.to_numeric(df[amount_col],errors="coerce").fillna(0) if amount_col in df else pd.Series(0,index=df.index)
        records.append({"Shark":shark,"Recorded investments":int((invested>0).sum()),"Total invested (₹ lakh)":float(invested.sum()),"Average investment (₹ lakh)":float(invested[invested>0].mean()) if (invested>0).any() else 0})
    if records:
        compare_df=pd.DataFrame(records).sort_values("Recorded investments",ascending=False)
        st.dataframe(compare_df,use_container_width=True,hide_index=True)
        st.plotly_chart(px.bar(compare_df,x="Shark",y="Recorded investments",title="Recorded investments by shark"),use_container_width=True)

elif page=="Scenario Simulator":
    st.markdown("### Scenario simulator")
    st.caption("Change the terms of the same startup and see how the model responds.")
    if "result" not in st.session_state:
        st.info("Analyze a pitch first, then open the Scenario Simulator.")
    else:
        base=st.session_state.result.copy()
        sharks=st.session_state.sharks
        c1,c2,c3=st.columns(3)
        with c1:
            ask=st.slider("Ask amount (₹ lakh)",10.0,1000.0,float(base["ask"]),5.0)
        with c2:
            eq=st.slider("Equity offered (%)",1.0,30.0,float(base["equity"]),.5)
        with c3:
            val=st.slider("Requested valuation (₹ lakh)",50.0,10000.0,float(base["valuation"]),50.0)
        base.update(ask=ask,equity=eq,valuation=val)
        pred=predict(base,sharks)
        a,b,c=st.columns(3)
        a.metric("Deal probability",pct(pred["deal"]))
        b.metric("Offer probability",pct(pred["offer"]))
        c.metric("Valuation requested",money(val))
        st.info(f"At ₹{ask:,.0f} lakh ask for {eq:.1f}% equity, the implied valuation is ₹{ask*100/eq:,.0f} lakh. The model's deal probability is {pred['deal']*100:.1f}%.")

elif page=="Dataset Insights":
    st.markdown("### Dataset insights")
    a,b,c,d=st.columns(4)
    a.metric("Historical pitches",len(df))
    b.metric("Industries",df["Industry"].nunique())
    c.metric("Median ask",money(df["Original Ask Amount"].median()))
    d.metric("Median equity",f"{df['Original Offered Equity'].median():.1f}%")
    x=df["Industry"].value_counts().head(12).reset_index()
    x.columns=["Industry","Pitches"]
    st.plotly_chart(px.bar(x,x="Pitches",y="Industry",orientation="h",title="Most represented industries"),use_container_width=True)

elif page=="Model Card":
    st.markdown("### Model card")
    st.caption("Metrics are those stored with the included trained models.")
    rows=[]
    for k,v in meta.get("results",{}).items():
        if k=="sharks": continue
        m=v.get("metrics",{})
        rows.append({"Task":k.replace("_"," ").title(),"Model":v.get("model","—"),
                      "F1":m.get("f1"),"ROC-AUC":m.get("roc_auc"),"R²":m.get("r2"),"MAE":m.get("mae")})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.warning("Individual shark predictions are best interpreted as ranking signals. They should not be presented as certain investment decisions.")
