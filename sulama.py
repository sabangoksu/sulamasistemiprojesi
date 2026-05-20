"""
╔══════════════════════════════════════════════════════════════════╗
║   Bulanık Mantık Tabanlı Fidelik Sisleme Sulama Sistemi         ║
║   Fuzzy Logic Seedling Irrigation Controller                     ║
║   Girişler: Toprak Nemi, Hava Sıcaklığı, Bağıl Nem             ║
║   Çıkış   : Sulama Süresi (dakika)                              ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────
# SAYFA AYARLARI
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Fidelik Sulama – Bulanık Kontrolcü",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────
# ÖZEL CSS
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap');

  :root {
    --green-dark: #1a3a2a;
    --green-mid:  #2d6a4f;
    --green-light:#52b788;
    --green-pale: #b7e4c7;
    --sand:       #f4e9cd;
    --text-dark:  #0d1f18;
    --accent:     #e76f51;
  }

  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

  /* Sidebar */
  section[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0d2818 0%, #1a3a2a 60%, #0d2818 100%);
    border-right: 2px solid var(--green-light);
  }
  section[data-testid="stSidebar"] * { color: #d8f3dc !important; }
  section[data-testid="stSidebar"] .stSlider > div > div > div { background: var(--green-light) !important; }

  /* Metric kartları */
  div[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1a3a2a, #2d6a4f);
    border-radius: 12px;
    border: 1px solid var(--green-light);
    padding: 10px 16px;
    color: white !important;
  }
  div[data-testid="metric-container"] label { color: #b7e4c7 !important; font-size: 0.78rem; }
  div[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #ffffff !important; font-family: 'Space Mono'; }

  /* Başlık */
  h1 { font-family: 'Space Mono', monospace; color: #1a3a2a; letter-spacing: -1px; }
  h2, h3 { font-family: 'Space Mono', monospace; color: #2d6a4f; }

  .result-box {
    background: linear-gradient(135deg, #1a3a2a 0%, #2d6a4f 100%);
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    border: 2px solid #52b788;
    margin: 12px 0;
  }
  .result-value {
    font-family: 'Space Mono', monospace;
    font-size: 3.5rem;
    color: #b7e4c7;
    line-height: 1.1;
  }
  .result-label {
    color: #74c69d;
    font-size: 0.9rem;
    margin-top: 4px;
    letter-spacing: 2px;
    text-transform: uppercase;
  }
  .tag {
    display: inline-block;
    background: var(--green-mid);
    color: #d8f3dc;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.78rem;
    margin: 2px;
  }
  .rule-active {
    background: #d8f3dc;
    border-left: 4px solid #52b788;
    border-radius: 6px;
    padding: 6px 12px;
    margin: 4px 0;
    font-size: 0.82rem;
    color: #0d2818;
  }
  .rule-inactive {
    background: #f5f5f5;
    border-left: 4px solid #ccc;
    border-radius: 6px;
    padding: 6px 12px;
    margin: 4px 0;
    font-size: 0.82rem;
    color: #999;
  }
  hr { border: 1px solid #b7e4c7; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# ÜYELİK FONKSİYONLARI
# ═══════════════════════════════════════════════════════════════

def trimf(x, a, b, c):
    """Üçgen üyelik fonksiyonu."""
    x = np.asarray(x, dtype=float)
    left  = np.where(b > a, (x - a) / (b - a), 0.0)
    right = np.where(c > b, (c - x) / (c - b), 0.0)
    return np.clip(np.minimum(left, right), 0, 1)

def trapmf(x, a, b, c, d):
    """Trapez üyelik fonksiyonu."""
    x = np.asarray(x, dtype=float)
    left  = np.where(b > a, (x - a) / (b - a), 1.0)
    right = np.where(d > c, (d - x) / (d - c), 1.0)
    mid   = np.ones_like(x, dtype=float)
    return np.clip(np.minimum(np.minimum(left, right), mid), 0, 1)


# ─────────────────────────────────────────────────────────────────
# GİRİŞ EVRENSEL KÜMELERİ VE ÜYELİK FONKSİYONLARI
# ─────────────────────────────────────────────────────────────────

# 1) TOPRAK NEMİ (%) — 0 to 100
TN_universe = np.linspace(0, 100, 1000)

def mf_toprak(x):
    """Toprak nemi üyelik fonksiyonları → Kuru, Orta, Nemli"""
    kuru   = trapmf(x,  0,  0, 25, 45)
    orta   = trimf  (x, 30, 50, 70)
    nemli  = trapmf (x, 55, 75,100,100)
    return {"Kuru": kuru, "Orta": orta, "Nemli": nemli}

# 2) HAVA SICAKLIĞI (°C) — 0 to 45
HS_universe = np.linspace(0, 45, 1000)

def mf_sicaklik(x):
    """Hava sıcaklığı → Serin, Ilık, Sıcak, Çok Sıcak"""
    serin     = trapmf(x,  0,  0, 12, 20)
    ilik      = trimf (x, 14, 22, 30)
    sicak     = trimf (x, 25, 32, 38)
    cok_sicak = trapmf(x, 35, 40, 45, 45)
    return {"Serin": serin, "Ilık": ilik, "Sıcak": sicak, "Çok Sıcak": cok_sicak}

# 3) BAĞIL NEM (%) — 0 to 100
BN_universe = np.linspace(0, 100, 1000)

def mf_bagil(x):
    """Bağıl nem → Düşük, Orta, Yüksek"""
    dusuk   = trapmf(x,  0,  0, 30, 50)
    orta    = trimf (x, 35, 55, 75)
    yuksek  = trapmf(x, 60, 80,100,100)
    return {"Düşük": dusuk, "Orta": orta, "Yüksek": yuksek}

# 4) ÇIKIŞ: SULAMA SÜRESİ (dakika) — 0 to 30
SS_universe = np.linspace(0, 30, 1000)

def mf_sulama(x):
    """Sulama süresi → Yok, Az, Orta, Fazla, Çok Fazla"""
    yok       = trapmf(x,  0,  0,  2,  5)
    az        = trimf (x,  3,  7, 11)
    orta      = trimf (x,  9, 14, 19)
    fazla     = trimf (x, 17, 22, 27)
    cok_fazla = trapmf(x, 24, 28, 30, 30)
    return {"Yok": yok, "Az": az, "Orta": orta, "Fazla": fazla, "Çok Fazla": cok_fazla}


# ═══════════════════════════════════════════════════════════════
# KURAL TABANI — 20 KURAL
# ═══════════════════════════════════════════════════════════════

RULES = [
    # (toprak_nemi_terimi, hava_sıcaklığı_terimi, bağıl_nem_terimi, sulama_terimi)
    # ── Toprak Kuru ──────────────────────────────────────────────
    ("Kuru",  "Serin",    "Düşük",   "Fazla"),        # R01
    ("Kuru",  "Serin",    "Orta",    "Orta"),          # R02
    ("Kuru",  "Serin",    "Yüksek",  "Az"),            # R03
    ("Kuru",  "Ilık",     "Düşük",   "Çok Fazla"),     # R04
    ("Kuru",  "Ilık",     "Orta",    "Fazla"),         # R05
    ("Kuru",  "Ilık",     "Yüksek",  "Orta"),          # R06
    ("Kuru",  "Sıcak",    "Düşük",   "Çok Fazla"),     # R07
    ("Kuru",  "Sıcak",    "Orta",    "Çok Fazla"),     # R08
    ("Kuru",  "Sıcak",    "Yüksek",  "Fazla"),         # R09
    ("Kuru",  "Çok Sıcak","Düşük",   "Çok Fazla"),     # R10
    ("Kuru",  "Çok Sıcak","Orta",    "Çok Fazla"),     # R11
    ("Kuru",  "Çok Sıcak","Yüksek",  "Fazla"),         # R12
    # ── Toprak Orta ──────────────────────────────────────────────
    ("Orta",  "Serin",    "Düşük",   "Az"),            # R13
    ("Orta",  "Serin",    "Orta",    "Az"),             # R14
    ("Orta",  "Serin",    "Yüksek",  "Yok"),           # R15
    ("Orta",  "Ilık",     "Düşük",   "Orta"),          # R16
    ("Orta",  "Ilık",     "Orta",    "Az"),             # R17
    ("Orta",  "Ilık",     "Yüksek",  "Yok"),           # R18
    ("Orta",  "Sıcak",    "Düşük",   "Fazla"),         # R19
    ("Orta",  "Sıcak",    "Orta",    "Orta"),          # R20
    ("Orta",  "Sıcak",    "Yüksek",  "Az"),            # R21
    ("Orta",  "Çok Sıcak","Düşük",   "Fazla"),         # R22
    ("Orta",  "Çok Sıcak","Orta",    "Fazla"),         # R23
    ("Orta",  "Çok Sıcak","Yüksek",  "Orta"),          # R24
    # ── Toprak Nemli ─────────────────────────────────────────────
    ("Nemli", "Serin",    "Düşük",   "Yok"),           # R25
    ("Nemli", "Serin",    "Orta",    "Yok"),            # R26
    ("Nemli", "Serin",    "Yüksek",  "Yok"),           # R27
    ("Nemli", "Ilık",     "Düşük",   "Yok"),           # R28
    ("Nemli", "Ilık",     "Orta",    "Yok"),            # R29
    ("Nemli", "Ilık",     "Yüksek",  "Yok"),           # R30
    ("Nemli", "Sıcak",    "Düşük",   "Az"),            # R31
    ("Nemli", "Sıcak",    "Orta",    "Yok"),            # R32
    ("Nemli", "Sıcak",    "Yüksek",  "Yok"),           # R33
    ("Nemli", "Çok Sıcak","Düşük",   "Az"),            # R34
    ("Nemli", "Çok Sıcak","Orta",    "Az"),             # R35
    ("Nemli", "Çok Sıcak","Yüksek",  "Yok"),           # R36
]


# ═══════════════════════════════════════════════════════════════
# BULANIKLAŞTIRMA — noktasal üyelik
# ═══════════════════════════════════════════════════════════════

def fuzzify_point(value, mf_dict, universe):
    """Verilen skaler değer için her terimin üyelik derecesini döndürür."""
    result = {}
    for term, mf_vals in mf_dict.items():
        # Üyelik fonksiyonu evren üzerinde hesaplanmış; en yakın noktayı al
        idx = np.argmin(np.abs(universe - value))
        result[term] = float(mf_vals[idx])
    return result


# ═══════════════════════════════════════════════════════════════
# ÇIKARIM MOTORU (Mamdani — min operatörü)
# ═══════════════════════════════════════════════════════════════

def infer(toprak_val, sicaklik_val, bagil_val):
    """
    Her kural için:
      - Öncül üyelikleri al (AND → min)
      - Çıkış MF'sini bu değere kırp (min ile)
    Tüm kırpılmış MF'leri max ile birleştir → toplamlaşmış çıkış.
    """
    # Evren üzerinde MF'leri hesapla
    tn_mfs = mf_toprak(TN_universe)
    hs_mfs = mf_sicaklik(HS_universe)
    bn_mfs = mf_bagil(BN_universe)
    ss_mfs = mf_sulama(SS_universe)

    # Noktasal bulanıklaştırma
    tn_deg = fuzzify_point(toprak_val,   tn_mfs, TN_universe)
    hs_deg = fuzzify_point(sicaklik_val, hs_mfs, HS_universe)
    bn_deg = fuzzify_point(bagil_val,    bn_mfs, BN_universe)

    # Toplamlaşmış çıkış başlangıçta sıfır
    aggregated = np.zeros_like(SS_universe)

    active_rules = []

    for i, (tn_t, hs_t, bn_t, ss_t) in enumerate(RULES):
        firing = min(tn_deg[tn_t], hs_deg[hs_t], bn_deg[bn_t])
        # Kırpma
        clipped = np.minimum(ss_mfs[ss_t], firing)
        # Birleştirme (maksimum)
        aggregated = np.maximum(aggregated, clipped)
        if firing > 0.001:
            active_rules.append({
                "idx": i + 1,
                "rule": f"R{i+1:02d}: EĞER Toprak={tn_t} VE Sıcaklık={hs_t} VE Nem={bn_t} → Sulama={ss_t}",
                "firing": firing,
                "output": ss_t
            })

    return aggregated, active_rules, tn_deg, hs_deg, bn_deg


# ═══════════════════════════════════════════════════════════════
# DURULAŞTIRMA — Ağırlık Merkezi (Centroid)
# ═══════════════════════════════════════════════════════════════

def defuzzify_centroid(aggregated, universe):
    """COG yöntemi: Σ(x·μ) / Σ(μ)"""
    denom = np.sum(aggregated)
    if denom < 1e-9:
        return 0.0
    return float(np.sum(universe * aggregated) / denom)


# ═══════════════════════════════════════════════════════════════
# GRAFİK ÇİZİM FONKSİYONLARI
# ═══════════════════════════════════════════════════════════════

COLORS = {
    # toprak nemi
    "Kuru":      "#e76f51",
    "Orta":      "#e9c46a",
    "Nemli":     "#2a9d8f",
    # sıcaklık
    "Serin":     "#90e0ef",
    "Ilık":      "#52b788",
    "Sıcak":     "#f4a261",
    "Çok Sıcak": "#e63946",
    # bağıl nem
    "Düşük":     "#ffb703",
    # "Orta" already defined
    "Yüksek":    "#023e8a",
    # sulama
    "Yok":       "#adb5bd",
    "Az":        "#74c69d",
    # "Orta" already
    "Fazla":     "#2d6a4f",
    "Çok Fazla": "#081c15",
}

def get_color(term):
    return COLORS.get(term, "#888888")


def plot_membership_functions():
    """Tüm giriş/çıkış üyelik fonksiyonlarını tek figürde göster."""
    fig = plt.figure(figsize=(14, 10), facecolor="#f8faf9")
    gs  = GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

    ax1 = fig.add_subplot(gs[0, 0])   # Toprak nemi
    ax2 = fig.add_subplot(gs[0, 1])   # Sıcaklık
    ax3 = fig.add_subplot(gs[1, 0])   # Bağıl nem
    ax4 = fig.add_subplot(gs[1, 1])   # Sulama süresi

    panels = [
        (ax1, TN_universe, mf_toprak(TN_universe),   "Toprak Nemi (%)",         "%"),
        (ax2, HS_universe, mf_sicaklik(HS_universe),  "Hava Sıcaklığı (°C)",    "°C"),
        (ax3, BN_universe, mf_bagil(BN_universe),     "Bağıl Nem (%)",           "%"),
        (ax4, SS_universe, mf_sulama(SS_universe),    "Sulama Süresi (dakika)", "dk"),
    ]

    for ax, uni, mf_dict, title, unit in panels:
        ax.set_facecolor("#f0f7f4")
        ax.set_title(title, fontsize=10, fontweight="bold", color="#1a3a2a", pad=8)
        ax.set_xlabel(unit, fontsize=8, color="#444")
        ax.set_ylabel("Üyelik Derecesi", fontsize=8, color="#444")
        ax.set_ylim(-0.05, 1.15)
        ax.tick_params(labelsize=7, colors="#444")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(True, alpha=0.3, linestyle="--")

        for term, vals in mf_dict.items():
            c = get_color(term)
            ax.plot(uni, vals, label=term, color=c, linewidth=2)
            ax.fill_between(uni, vals, alpha=0.12, color=c)

        ax.legend(fontsize=7, loc="upper right",
                  framealpha=0.7, edgecolor="#ccc")

    fig.suptitle("🌱 Fidelik Sulama Sistemi — Üyelik Fonksiyonları",
                 fontsize=13, fontweight="bold", color="#1a3a2a", y=1.01)
    return fig


def plot_fuzzification(tn_val, hs_val, bn_val, tn_deg, hs_deg, bn_deg):
    """Girişlerin mevcut değerdeki bulanıklaştırma görselleştirmesi."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), facecolor="#f8faf9")

    panels = [
        (axes[0], TN_universe, mf_toprak(TN_universe),   tn_val, tn_deg, "Toprak Nemi (%)"),
        (axes[1], HS_universe, mf_sicaklik(HS_universe),  hs_val, hs_deg, "Sıcaklık (°C)"),
        (axes[2], BN_universe, mf_bagil(BN_universe),     bn_val, bn_deg, "Bağıl Nem (%)"),
    ]

    for ax, uni, mf_dict, val, deg_dict, title in panels:
        ax.set_facecolor("#f0f7f4")
        ax.set_title(title, fontsize=10, fontweight="bold", color="#1a3a2a")
        ax.set_ylim(-0.05, 1.2)
        ax.tick_params(labelsize=7, colors="#444")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(True, alpha=0.3, linestyle="--")

        for term, vals in mf_dict.items():
            c = get_color(term)
            ax.plot(uni, vals, color=c, linewidth=1.8, label=term)
            deg = deg_dict[term]
            if deg > 0.001:
                ax.fill_between(uni, np.minimum(vals, deg),
                                alpha=0.35, color=c)
                ax.hlines(deg, uni[0], val, colors=c,
                           linestyles="--", linewidth=1)
                ax.vlines(val, 0, deg, colors=c,
                           linestyles=":", linewidth=1)
                ax.annotate(f"{deg:.2f}", xy=(uni[0] + 1, deg + 0.03),
                            fontsize=7, color=c, fontweight="bold")

        ax.axvline(val, color="#e76f51", linewidth=2, zorder=5,
                   label=f"Değer = {val}")
        ax.legend(fontsize=7, loc="upper right", framealpha=0.7)

    fig.suptitle("Bulanıklaştırma (Fuzzification)", fontsize=12,
                 fontweight="bold", color="#1a3a2a")
    fig.tight_layout()
    return fig


def plot_defuzzification(aggregated, crisp):
    """Toplamlaşmış çıkış ve centroid görselleştirmesi."""
    fig, ax = plt.subplots(figsize=(10, 4), facecolor="#f8faf9")
    ax.set_facecolor("#f0f7f4")

    # Bireysel çıkış MF'leri
    ss_mfs = mf_sulama(SS_universe)
    for term, vals in ss_mfs.items():
        c = get_color(term)
        ax.plot(SS_universe, vals, color=c, linewidth=1.2,
                alpha=0.4, linestyle="--", label=term)

    # Toplamlaşmış çıkış
    ax.fill_between(SS_universe, aggregated, alpha=0.55,
                    color="#2d6a4f", label="Toplamlaşmış Çıkış")
    ax.plot(SS_universe, aggregated, color="#1a3a2a", linewidth=2)

    # Centroid çizgisi
    ax.axvline(crisp, color="#e76f51", linewidth=2.5,
               linestyle="-", label=f"Centroid = {crisp:.2f} dk")
    ax.fill_betweenx([0, 1], crisp - 0.4, crisp + 0.4,
                     alpha=0.25, color="#e76f51")

    ax.set_xlabel("Sulama Süresi (dakika)", fontsize=9)
    ax.set_ylabel("Üyelik Derecesi", fontsize=9)
    ax.set_ylim(-0.05, 1.15)
    ax.set_title("Durulaştırma — Ağırlık Merkezi (Centroid) Yöntemi",
                 fontsize=11, fontweight="bold", color="#1a3a2a")
    ax.legend(fontsize=8, loc="upper right", framealpha=0.8)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def plot_rule_activation(active_rules):
    """Aktif kuralların ateşleme güçlerini yatay bar ile göster."""
    if not active_rules:
        return None

    # En yüksek 12 kuralı al
    sorted_rules = sorted(active_rules, key=lambda r: r["firing"], reverse=True)[:12]
    labels = [r["rule"].split(":")[0] + f" → {r['output']}" for r in sorted_rules]
    values = [r["firing"] for r in sorted_rules]
    colors = [get_color(r["output"]) for r in sorted_rules]

    fig, ax = plt.subplots(figsize=(10, max(3, len(sorted_rules) * 0.55)),
                            facecolor="#f8faf9")
    ax.set_facecolor("#f0f7f4")

    bars = ax.barh(labels[::-1], values[::-1], color=colors[::-1],
                   edgecolor="white", linewidth=0.5, height=0.65)

    for bar, val in zip(bars, values[::-1]):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center", ha="left", fontsize=8,
                color="#1a3a2a", fontweight="bold")

    ax.set_xlim(0, 1.15)
    ax.set_xlabel("Ateşleme Gücü (α)", fontsize=9)
    ax.set_title("Aktif Kural Ateşleme Güçleri", fontsize=11,
                 fontweight="bold", color="#1a3a2a")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=8)
    ax.grid(axis="x", alpha=0.3, linestyle="--")
    fig.tight_layout()
    return fig


def sulama_yorumu(dakika):
    if dakika < 2:   return "🔴 Sulama Yok — Toprak yeterince nemli"
    elif dakika < 8: return "🟡 Az Sulama — Hafif nem takviyesi yeterli"
    elif dakika < 16: return "🟢 Orta Sulama — Normal sulama döngüsü"
    elif dakika < 24: return "🔵 Fazla Sulama — Yoğun nem ihtiyacı var"
    else:            return "🟣 Çok Fazla Sulama — Kritik nem açığı!"


# ═══════════════════════════════════════════════════════════════
# STREAMLIT ARAYÜZÜ
# ═══════════════════════════════════════════════════════════════

def main():
    # ── BAŞLIK ──────────────────────────────────────────────────
    col_logo, col_title = st.columns([1, 8])
    with col_logo:
        st.markdown("<div style='font-size:3rem;margin-top:8px'>🌱</div>",
                    unsafe_allow_html=True)
    with col_title:
        st.markdown("""
        <h1 style='margin-bottom:0;font-size:1.8rem'>
            Fidelik Sisleme Sulama Sistemi
        </h1>
        <p style='color:#2d6a4f;margin-top:2px;font-size:0.88rem'>
            Bulanık Mantık Tabanlı Akıllı Sulama Kontrolcüsü
        </p>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── SIDEBAR — SADECE SAYISAL GİRİŞ ─────────────────────────
    with st.sidebar:
        st.markdown("## 🎛️ Giriş Değerleri")
        st.markdown("Değeri girin, **Enter'a basın** — sonuç anında güncellenir.")
        st.markdown("---")

        st.markdown("### 🌍 Toprak Nemi")
        st.caption("Aralık: 0 – 100 %  |  0=Kuru, 100=Suya Doymuş")
        toprak_nemi = st.number_input("Toprak Nemi (%)",
                        min_value=0, max_value=100, value=35, step=1)
        st.markdown("---")

        st.markdown("### 🌡️ Hava Sıcaklığı")
        st.caption("Aralık: 0 – 45 °C")
        sicaklik = st.number_input("Hava Sıcaklığı (°C)",
                        min_value=0, max_value=45, value=28, step=1)
        st.markdown("---")

        st.markdown("### 💧 Bağıl Nem (Atmosfer)")
        st.caption("Aralık: 0 – 100 %")
        bagil_nem = st.number_input("Bağıl Nem (%)",
                        min_value=0, max_value=100, value=40, step=1)
        st.markdown("---")
        st.markdown("""
        <small style='color:#74c69d'>
        <b>Kural Tabanı:</b> 36 IF-THEN kuralı<br>
        <b>Çıkarım:</b> Mamdani (min-max)<br>
        <b>Durulaştırma:</b> Ağırlık Merkezi (COG)
        </small>
        """, unsafe_allow_html=True)

    # ── ÇIKARIM ─────────────────────────────────────────────────
    aggregated, active_rules, tn_deg, hs_deg, bn_deg = infer(
        toprak_nemi, sicaklik, bagil_nem
    )
    sulama_dk = defuzzify_centroid(aggregated, SS_universe)

    # ── ÜST METRİK KARTI SATIRI ─────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("🌍 Toprak Nemi", f"{toprak_nemi} %")
    with m2:
        st.metric("🌡️ Hava Sıcaklığı", f"{sicaklik} °C")
    with m3:
        st.metric("💧 Bağıl Nem", f"{bagil_nem} %")
    with m4:
        st.metric("⏱️ Aktif Kural Sayısı", len(active_rules))

    st.markdown("---")

    # ── SONUÇ KUTUSU ────────────────────────────────────────────
    rc1, rc2 = st.columns([1, 2])
    with rc1:
        yorum = sulama_yorumu(sulama_dk)
        st.markdown(f"""
        <div class="result-box">
          <div class="result-label">Önerilen Sulama Süresi</div>
          <div class="result-value">{sulama_dk:.1f}</div>
          <div class="result-label">dakika</div>
          <hr style='border-color:#52b788;margin:12px 0'>
          <div style='color:#b7e4c7;font-size:0.85rem'>{yorum}</div>
        </div>
        """, unsafe_allow_html=True)

        # Girişlerin bulanık yorumu
        st.markdown("#### 📊 Giriş Bulanıklaştırma")
        for term, deg in tn_deg.items():
            if deg > 0.01:
                st.markdown(
                    f'<span class="tag">🌍 {term}: {deg:.3f}</span>',
                    unsafe_allow_html=True)
        for term, deg in hs_deg.items():
            if deg > 0.01:
                st.markdown(
                    f'<span class="tag">🌡️ {term}: {deg:.3f}</span>',
                    unsafe_allow_html=True)
        for term, deg in bn_deg.items():
            if deg > 0.01:
                st.markdown(
                    f'<span class="tag">💧 {term}: {deg:.3f}</span>',
                    unsafe_allow_html=True)

    with rc2:
        st.markdown("#### Durulaştırma — Centroid")
        fig_defuzz = plot_defuzzification(aggregated, sulama_dk)
        st.pyplot(fig_defuzz, use_container_width=True)
        plt.close(fig_defuzz)

    st.markdown("---")

    # ── SEKMELİ DETAY PANELLERİ ─────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Üyelik Fonksiyonları",
        "🔬 Bulanıklaştırma",
        "📋 Aktif Kurallar",
        "ℹ️ Sistem Hakkında"
    ])

    with tab1:
        st.markdown("### Tüm Değişkenlerin Üyelik Fonksiyonları")
        fig_mf = plot_membership_functions()
        st.pyplot(fig_mf, use_container_width=True)
        plt.close(fig_mf)

    with tab2:
        st.markdown("### Mevcut Giriş Değerlerinin Bulanıklaştırılması")
        st.caption("Kırmızı dikey çizgi → girilen değer | Renkli alan → ateşleme bölgesi")
        fig_fuzz = plot_fuzzification(
            toprak_nemi, sicaklik, bagil_nem,
            tn_deg, hs_deg, bn_deg
        )
        st.pyplot(fig_fuzz, use_container_width=True)
        plt.close(fig_fuzz)

        # Kural aktivasyon barları
        fig_rules = plot_rule_activation(active_rules)
        if fig_rules:
            st.markdown("### Kural Ateşleme Güçleri")
            st.pyplot(fig_rules, use_container_width=True)
            plt.close(fig_rules)

    with tab3:
        st.markdown("### 📋 Tüm Kurallar ve Aktivasyon Durumları")
        st.caption(f"Toplam 36 kural | **{len(active_rules)} tanesi aktif** (α > 0.001)")

        for i, (tn_t, hs_t, bn_t, ss_t) in enumerate(RULES):
            # Ateşleme gücünü bul
            firing_val = 0.0
            for ar in active_rules:
                if ar["idx"] == i + 1:
                    firing_val = ar["firing"]
                    break

            r_label = (
                f"R{i+1:02d}: Toprak={tn_t} ∧ Sıcaklık={hs_t} "
                f"∧ Nem={bn_t} → Sulama={ss_t}"
            )

            if firing_val > 0.001:
                st.markdown(
                    f'<div class="rule-active">✅ {r_label} &nbsp;&nbsp; '
                    f'<b>α = {firing_val:.3f}</b></div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div class="rule-inactive">○ {r_label}</div>',
                    unsafe_allow_html=True)

    with tab4:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("""
            ### 🌱 Sistem Hakkında

            Bu sistem, **fidelik sisleme sulama sistemi** için bulanık mantık
            tabanlı bir karar destek aracıdır.

            #### Giriş Değişkenleri
            | Değişken | Aralık | Dilsel Tanımlar |
            |----------|--------|-----------------|
            | Toprak Nemi | 0–100 % | Kuru / Orta / Nemli |
            | Hava Sıcaklığı | 0–45 °C | Serin / Ilık / Sıcak / Çok Sıcak |
            | Bağıl Nem | 0–100 % | Düşük / Orta / Yüksek |

            #### Çıkış Değişkeni
            | Değişken | Aralık | Dilsel Tanımlar |
            |----------|--------|-----------------|
            | Sulama Süresi | 0–30 dk | Yok / Az / Orta / Fazla / Çok Fazla |

            #### Çıkarım Yöntemi
            - **Motor:** Mamdani (min-max)
            - **AND operatörü:** Minimum
            - **Birleştirme:** Maksimum
            - **Durulaştırma:** Ağırlık Merkezi (COG / Centroid)
            """)

        with col_b:
            st.markdown("""
            #### Kullanım Senaryoları
            
            | Senaryo | TN | Sıcaklık | Bağıl Nem | Beklenen Sulama |
            |---------|----|----------|-----------|-----------------|
            | Kurak gün | 15 % | 38 °C | 20 % | ~28 dk |
            | Normal gün | 50 % | 25 °C | 55 % | ~7 dk |
            | Serin & nemli | 70 % | 12 °C | 80 % | ~0 dk |
            | İlkbahar sabahı | 35 % | 18 °C | 60 % | ~5 dk |
            | Yazın öğle | 20 % | 40 °C | 30 % | ~29 dk |

            #### Güçlü Yönler
            - Uzman bilgisini doğrudan kurallarla kodlar
            - Sürekli çıkış üretir (açma/kapama yok)
            - Yorumlanabilir ve şeffaf

            #### Zayıf Yönler
            - Kural tabanı elle tasarlanır (otomatik öğrenme yok)
            - Çok değişkenli sistemlerde kural patlaması
            - Sensör gürültüsüne hassas olabilir
            """)

    # ── DURUM ÇUBUĞU ────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        f"<center><small style='color:#aaa'>"
        f"Bulanık Mantık Dersi — Dönem Projesi | "
        f"Mamdani Çıkarım Motoru | "
        f"Ağırlık Merkezi Durulaştırma | "
        f"<b>Sonuç: {sulama_dk:.2f} dakika</b>"
        f"</small></center>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()