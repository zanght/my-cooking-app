import json
import base64
from pathlib import Path

import streamlit as st


APP_TITLE = "很好吃"
DATA_PATH = Path(__file__).with_name("recipes.json")
ASSETS_DIR = Path(__file__).with_name("assets")

NAV_ICONS = {
    "home": ASSETS_DIR / "home.png",
    "fridge": ASSETS_DIR / "fridge.png",
    "discover": ASSETS_DIR / "discovery.png",
    "mine": ASSETS_DIR / "profile.png",
}


# 示例：其他用户上传的菜谱（发现页面用）
COMMUNITY_RECIPES = [
    {
        "name": "蒜香黄油虾",
        "author": "用户 A",
        "image": "https://images.pexels.com/photos/1114425/pexels-photo-1114425.jpeg",
        "ingredients": ["鲜虾 500g", "黄油 30g", "大蒜 5瓣", "盐 少许", "黑胡椒 少许"],
        "steps": [
            "鲜虾剪须去虾线洗净，沥干水分。",
            "黄油小火融化，下蒜末炒香。",
            "倒入鲜虾，大火翻炒至变色，撒盐和黑胡椒调味。",
            "收汁后装盘，可以再撒点香菜。"
        ],
    },
    {
        "name": "香煎三文鱼",
        "author": "用户 B",
        "image": "https://images.pexels.com/photos/3296273/pexels-photo-3296273.jpeg",
        "ingredients": [
            "三文鱼排 2块",
            "海盐 少许",
            "黑胡椒 少许",
            "橄榄油 适量",
            "柠檬片 若干",
        ],
        "steps": [
            "三文鱼排用厨房纸吸干表面水分，两面撒上海盐和黑胡椒，腌制 5–10 分钟。",
            "平底锅中倒入少量橄榄油，小火加热。",
            "将三文鱼皮朝下放入锅中，中小火慢煎至鱼皮金黄酥脆。",
            "翻面再煎 1–2 分钟至刚刚熟，旁边可以一起煎几片柠檬。",
            "出锅装盘，配上柠檬片即可食用。",
        ],
    },
]


def load_recipes() -> dict:
    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("recipes.json 的根节点必须是一个对象（dict）。")
    return data


def normalize(s: str) -> str:
    return "".join(str(s).strip().lower().split())


def search(recipes: dict, query: str) -> list[tuple[str, dict]]:
    q = normalize(query)
    if not q:
        return []
    results: list[tuple[str, dict]] = []
    for name, detail in recipes.items():
        if q in normalize(name):
            results.append((name, detail))
    return results


def parse_ingredients(text: str) -> set[str]:
    """把用户输入的食材字符串拆成集合，例如：'鸡蛋, 番茄 肉' -> {'鸡蛋', '番茄', '肉'}"""
    if not text.strip():
        return set()
    # 按逗号、顿号、空格等分隔
    raw = (
        text.replace("，", ",")
        .replace("、", ",")
        .replace("；", ",")
        .replace(";", ",")
    )
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return {normalize(p) for p in parts}


def ingredients_of_recipe(detail: dict) -> set[str]:
    items = detail.get("食材", [])
    normed: set[str] = set()
    for item in items:
        # 只取每一项中比较“核心”的前几个词
        base = (
            str(item)
            .replace("，", " ")
            .replace(",", " ")
            .replace("（", " ")
            .replace("(", " ")
        )
        for token in base.split():
            t = normalize(token)
            if t:
                normed.add(t)
    return normed


def recommend_by_ingredients(recipes: dict, user_text: str) -> list[tuple[str, dict, int, int]]:
    """根据用户现有食材推荐菜谱，返回：菜名、详情、匹配数量、所需总数。"""
    user_set = parse_ingredients(user_text)
    if not user_set:
        return []

    candidates: list[tuple[str, dict, int, int]] = []
    for name, detail in recipes.items():
        need = ingredients_of_recipe(detail)
        if not need:
            continue
        match_count = len(user_set & need)
        if match_count == 0:
            continue
        candidates.append((name, detail, match_count, len(need)))

    # 先按匹配数量从高到低，再按所需食材总数从少到多排序
    candidates.sort(key=lambda x: (-x[2], x[3], x[0]))
    return candidates


st.set_page_config(
    page_title=APP_TITLE,
    page_icon=str(ASSETS_DIR / "app_icons" / "app_icon_180.png"),
    layout="centered",
)

# 自定义整体样式：日系治愈风（奶黄色主基调）
CREAMY_CSS = """
<style>
/* 整体背景：奶黄色为主，柔和暖调 */
html, body, [data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 12% 0%, #FFFDF6 0, #FFF7E4 34%, transparent 62%),
        radial-gradient(circle at 88% 100%, #FFF3D8 0, #FFEBC8 30%, transparent 58%),
        linear-gradient(180deg, #FFF9EC 0%, #FFF3DB 58%, #FFE9C2 100%);
}

/* 顶部标题区域更干净，隐藏默认彩色条 */
[data-testid="stHeader"] {
    background: transparent;
    height: 0;
    padding: 0;
}

/* 隐藏底部 “Made with Streamlit” 等工具栏，让页面更像原生 App */
footer, [data-testid="stToolbar"] {
    display: none !important;
}
/* 隐藏侧边栏，避免页面横向偏移 */
[data-testid="stSidebar"] {
    display: none !important;
}


/* 背景插画层容器 */
.bg-illustrations {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 1; /* 底部层：在最底但高于浏览器默认背景 */
}
.bg-illustrations .trex {
    position: absolute;
    left: -80px;
    bottom: -40px;
    width: min(700px, 60vw);
    opacity: 0.92;
    transform: rotate(-3deg);
}
.bg-illustrations .baby {
    position: absolute;
    right: 6vw;
    top: 6vh;
    width: min(210px, 21vw);
    opacity: 0.96;
    transform: translateY(-10px) translateX(-6px) rotate(5deg);
    z-index: 2; /* 顶部层：滞空的小恐龙 */
}
/* 让主要内容（搜索框、按钮等）处于最高层 */
[data-testid="stAppViewContainer"] > .main {
    position: relative;
    z-index: 10;
}

/* 缩小主页面内容宽度并居中 */
[data-testid="stAppViewContainer"] > .main .block-container {
    max-width: 760px !important;
    margin: 0 auto !important;
}

/* 主体内容区域：奶油黄卡片（不改底部导航胶囊） */
[data-testid="stAppViewContainer"] > .main {
    background: linear-gradient(145deg, rgba(255, 250, 235, 0.95), rgba(255, 243, 216, 0.96));
    padding: 1.5rem 2rem 2.5rem 2rem;
    border-radius: 24px;
    box-shadow:
        0 18px 40px rgba(191, 146, 86, 0.2),
        0 0 0 1px rgba(255, 255, 255, 0.6);
}

/* 所有“块”类型组件的统一圆角与轻阴影 */
[data-testid="stVerticalBlock"] {
    border-radius: 18px;
}

/* 标签页背景：柔和奶油白 */
[data-testid="stTabs"] {
    background: rgba(255, 252, 241, 0.9);
    padding: 0.5rem 0.8rem 0.2rem 0.8rem;
    border-radius: 16px;
    box-shadow: 0 8px 20px rgba(205, 150, 100, 0.18);
}

/* 标签文字：柔和墨绿 */
[data-testid="stTabs"] button {
    color: #425935 !important;
    font-weight: 600;
}

/* 按钮：清新草绿 + 奶油黄，高明度治愈风 */
button[kind="primary"], button[kind="secondary"], .stButton>button {
    border-radius: 999px !important;
    border: 1px solid rgba(131, 182, 119, 0.95) !important;
    background: linear-gradient(135deg, #FDF4D7, #8ECF82) !important;
    color: #3E4A30 !important;
    font-weight: 600 !important;
    box-shadow:
        0 10px 22px rgba(190, 130, 70, 0.28),
        0 0 0 1px rgba(255, 255, 255, 0.6);
}

button[kind="primary"]:hover, button[kind="secondary"]:hover, .stButton>button:hover {
    background: linear-gradient(135deg, #FFF8E4, #7FBE73) !important;
    transform: translateY(-1px);
    box-shadow:
        0 14px 28px rgba(190, 130, 70, 0.35),
        0 0 0 1px rgba(255, 255, 255, 0.9);
}

/* 输入框 & 文本域：淡绿+奶油边框与背景 */
input, textarea {
    border-radius: 14px !important;
    border: 1px solid rgba(176, 205, 150, 0.95) !important;
    background: rgba(255, 252, 241, 0.98) !important;
}

input:focus, textarea:focus {
    outline: none !important;
    border-color: #7FBF71 !important;
    box-shadow: 0 0 0 1px rgba(127, 191, 113, 0.6);
}

/* 主页搜索区域：整体容器居中，内部 75/25 比例同一行 */
.search-bar-container {
    width: 100%;
    margin: 0.65rem auto 1.15rem auto;
    padding: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    border: none;
    background: transparent;
    height: auto;
    box-shadow: none;
}
.search-bar-container [data-testid="stHorizontalBlock"] {
    width: min(90%, 350px);
    margin: 0 auto !important;
    display: flex !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 0 !important; /* 去除多余间距，让组合更紧凑 */
}
.search-bar-container [data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child {
    flex: 3 1 0 !important;   /* 约 75% */
    min-width: 0 !important;
}
.search-bar-container [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child {
    flex: 1 0 0 !important;   /* 约 25% */
    min-width: 86px !important;
}
.search-bar-container > div {
    margin-bottom: 0 !important;
}
.search-bar-container input {
    width: 100%;
    padding: 10px !important; /* iPhone 点击触感更好 */
    border: 1px solid #8D6E63 !important;
    border-radius: 22px !important;
    background: #FFFFFF !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.12) !important;
}
.search-bar-container [data-testid="stTextInputRoot"] {
    margin-bottom: 0;
}
.search-bar-container .stButton {
    margin-bottom: 0;
}
.search-bar-container .stButton > button {
    position: static;
    transform: none;
    width: 100%;
    min-width: 0;
    height: 42px;
    padding: 10px !important;
    border-radius: 22px !important;
    border: none !important;
    background: linear-gradient(135deg, #FFC58A, #F39C4A) !important;
    box-shadow: 0 4px 10px rgba(170, 110, 60, 0.28) !important;
    color: #333333 !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
}

/* 冰箱页：分类横向滚动 + 物品矩形卡片 */
.fridge-category-scroll [role="radiogroup"] {
    display: flex !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    gap: 8px !important;
    padding-bottom: 6px !important;
}
.fridge-category-scroll [role="radio"] {
    background: #ffffffcc !important;
    border: 1px solid #b8c7a5 !important;
    border-radius: 999px !important;
    padding: 4px 10px !important;
    white-space: nowrap !important;
}
.fridge-category-scroll [role="radio"][aria-checked="true"] {
    background: #dff0d2 !important;
    border-color: #89a56b !important;
}
.fridge-items-shell {
    border: 1px solid rgba(203, 215, 191, 0.9);
    border-radius: 24px;
    background: rgba(255, 255, 255, 0.72);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    padding: 10px;
}
.fridge-item-card {
    border: 1px solid #d8e3cb;
    border-radius: 10px;
    background: #fff;
    padding: 8px 10px;
    min-height: 52px;
    display: flex;
    align-items: center;
}
.fridge-item-row {
    margin-bottom: 8px;
}
.fridge-qty-wrap [data-testid="stNumberInputContainer"] {
    margin-top: 0 !important;
}
.fridge-qty-wrap input {
    text-align: center !important;
    min-height: 32px !important;
    padding: 6px 8px !important;
}

@media (max-width: 430px) {
    .search-bar-container [data-testid="stHorizontalBlock"] { width: min(90%, 350px); }
    .search-bar-container .stButton > button {
        height: 40px !important;
        padding: 10px !important;
        font-size: 0.88rem !important;
    }
}

/* 提示信息卡片：轻微绿色边框 */
.stAlert {
    border-radius: 18px;
    background: rgba(252, 255, 246, 0.98) !important;
    border: 1px solid rgba(188, 214, 164, 0.9) !important;
}

/* 标题和正文字体颜色、行距：深灰 */
h1, h2, h3, h4, h5, h6 {
    color: #333333 !important;
    letter-spacing: 0.03em;
}

p, li, label, span, .stMarkdown, .stText {
    color: #333333 !important;
    line-height: 1.6;
}

/* 底部导航按钮容器留出一点空间 */
.cream-bottom-nav {
    margin-top: 1.2rem;
    padding-top: 0.6rem;
}

/* 底部恐龙导航按钮：一排横向，黑色线条简笔风，图案在上文字在下 */
.cream-bottom-nav .stButton>button {
    border-radius: 999px !important;
    padding: 0.45rem 0 !important;
    background: rgba(255, 255, 255, 0.9) !important;
    border: 1px solid #222222 !important;
    color: #222222 !important;
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.12);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.15rem;
    font-size: 0.8rem !important;        /* 整体偏小，像图标+小字 */
    line-height: 1.25 !important;
    white-space: pre-line !important;    /* 识别换行：上面一行是简笔图案，下面一行是文字 */
}

.cream-bottom-nav .dino-icon {
    display: inline-flex;
    width: 1.8rem;
    height: 1.8rem;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: #1C8B8B;
    color: #FFEFD8;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.12);
    font-size: 1.2rem;
}

/* 底部固定导航栏占位，防止内容被遮挡 */
.fixed-nav-spacer { height: 92px; }

/* 隐藏 Streamlit 默认底部间距 & 为导航栏留白，避免遮挡 */
[data-testid="stAppViewContainer"] > .main .block-container { padding-bottom: 110px !important; }

/* 底部导航栏：日系浅绿色，无玻璃效果 */
#icon-navbar {
    position: fixed;
    left: 50%;
    transform: translateX(-50%);
    bottom: 14px;
    width: min(350px, calc(100vw - 56px));
    height: 66px;
    z-index: 9999;
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;  /* 强制横向一行，不允许换行 */
    align-items: center;
    justify-content: space-between;
    gap: 0;
    padding: 8px 16px;
    background: #DDF3D8;
    border-radius: 999px;
    box-shadow: 0 6px 16px rgba(0,0,0,0.12);
    border: none !important;
    overflow: hidden;
}
/* 强制关闭内部横线（分割线/伪元素） */
#icon-navbar::before,
#icon-navbar::after {
    content: none !important;
    display: none !important;
}
#icon-navbar a {
    width: 62px;
    height: 50px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    border-radius: 14px;
    text-decoration: none;
    transition: transform 120ms ease, filter 160ms ease, background 160ms ease;
    user-select: none;
}
#icon-navbar a:hover {
    transform: scale(1.03);
    background: transparent;
}
#icon-navbar a:active {
    transform: scale(0.9);
}
#icon-navbar img {
    height: 24px;
    width: auto;
    display: block;
    margin: 0;
    padding: 0;
}
#icon-navbar .nav-label {
    margin-top: 2px;
    font-size: 0.62rem;
    line-height: 1;
    color: #4A3728;
    letter-spacing: 0.01em;
}
/* 当前选中：淡淡背光/阴影 */
#icon-navbar a.active img {
    filter: drop-shadow(0 0 4px rgba(255, 255, 255, 0.8))
            drop-shadow(0 2px 5px rgba(0, 0, 0, 0.18));
}
</style>
"""

st.markdown(CREAMY_CSS, unsafe_allow_html=True)


# -------- 辅助：图标与搜索触发 --------


def _b64_image(path: Path) -> str:
    try:
        data = path.read_bytes()
        return base64.b64encode(data).decode("ascii")
    except Exception:
        return ""


def render_icon_navbar(active_page: str) -> None:
    icons = {k: _b64_image(v) for k, v in NAV_ICONS.items()}
    st.markdown('<div class="fixed-nav-spacer"></div>', unsafe_allow_html=True)
    st.markdown(
        f"""
<div id="icon-navbar">
  <a href="?page=home" class="{'active' if active_page=='home' else ''}">
    <img alt="home" src="data:image/png;base64,{icons.get('home','')}" />
    <span class="nav-label">home</span>
  </a>
  <a href="?page=fridge" class="{'active' if active_page=='fridge' else ''}">
    <img alt="fridge" src="data:image/png;base64,{icons.get('fridge','')}" />
    <span class="nav-label">fridge</span>
  </a>
  <a href="?page=discover" class="{'active' if active_page=='discover' else ''}">
    <img alt="discover" src="data:image/png;base64,{icons.get('discover','')}" />
    <span class="nav-label">discovery</span>
  </a>
  <a href="?page=mine" class="{'active' if active_page=='mine' else ''}">
    <img alt="mine" src="data:image/png;base64,{icons.get('mine','')}" />
    <span class="nav-label">mine</span>
  </a>
</div>
""",
        unsafe_allow_html=True,
    )


def _mark_search() -> None:
    """当用户结束编辑或在手机键盘按下 Enter 时，标记一次搜索。"""
    st.session_state["do_search_now"] = True


def load_svg(name: str) -> str:
    path = ASSETS_DIR / name
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


# 背景插画：左下霸王龙 + 右上滞空小恐龙（叠层效果）
trex_svg = load_svg("trex.svg")
baby_svg = load_svg("baby_dino.svg")
if trex_svg or baby_svg:
    st.markdown(
        f"""
<div class="bg-illustrations">
  <div class="trex">{trex_svg}</div>
  <div class="baby">{baby_svg}</div>
</div>
""",
        unsafe_allow_html=True,
    )

if "page" not in st.session_state:
    st.session_state["page"] = "home"  # home / fridge / discover / mine

# 我的冰箱：会话内食材清单
if "fridge" not in st.session_state:
    st.session_state["fridge"] = []  # list[str]

# 用于“查看详情”的临时跳转状态
if "highlight_recipe" not in st.session_state:
    st.session_state["highlight_recipe"] = None  # str | None

# 最近制作：会话内记录
if "recently_made" not in st.session_state:
    st.session_state["recently_made"] = []  # list[dict]

# 通过 URL 参数切换页面
try:
    _query_page = st.query_params.get("page")
    should_rerun = False

    if _query_page in ("home", "fridge", "discover", "mine"):
        st.session_state["page"] = _query_page
        should_rerun = True

    if should_rerun:
        if hasattr(st.query_params, "clear"):
            st.query_params.clear()
        st.rerun()
except Exception:
    pass

try:
    recipes = load_recipes()
except Exception as e:
    st.error(f"读取菜谱数据失败：{e}")
    st.stop()


FRIDGE_PRESETS: dict[str, list[str]] = {
    "蔬菜": ["番茄", "土豆", "青椒", "洋葱", "胡萝卜", "黄瓜", "生菜", "蘑菇", "葱", "姜", "蒜"],
    "肉类/蛋白": ["鸡蛋", "鸡翅", "鸡胸肉", "猪肉", "牛肉", "虾", "鱼", "火腿", "午餐肉", "豆腐"],
    "调料": ["盐", "糖", "生抽", "老抽", "醋", "料酒", "蚝油", "胡椒", "辣椒", "香油", "番茄酱"],
    "主食": ["米饭", "面条", "面包", "馒头", "粉丝", "土豆淀粉"],
}

# 冰箱页：分类目录与当前分类
if "fridge_catalog" not in st.session_state:
    st.session_state["fridge_catalog"] = {
        "水果": ["苹果", "香蕉", "橙子", "葡萄", "草莓"],
        "肉类": ["鸡胸肉", "牛肉", "猪肉", "鸡翅"],
        "生鲜": ["虾", "鱼", "蛤蜊"],
        "蔬菜": ["番茄", "土豆", "青椒", "黄瓜", "生菜"],
        "调料": ["盐", "糖", "生抽", "蚝油", "胡椒"],
        "其他": [],
    }
if "active_category" not in st.session_state:
    st.session_state["active_category"] = "全部"
if "fridge_show_all" not in st.session_state:
    st.session_state["fridge_show_all"] = False
if "fridge_item_counts" not in st.session_state:
    st.session_state["fridge_item_counts"] = {}  # key: "分类::食材" -> int
if "fridge_item_units" not in st.session_state:
    st.session_state["fridge_item_units"] = {}  # key: "分类::食材" -> str

FRIDGE_UNIT_OPTIONS = ["个", "颗", "g", "kg", "ml", "瓶", "袋", "把", "适量"]


def render_home(recipes: dict) -> None:
    """主页：居中搜索 + 最近制作"""
    st.title(APP_TITLE)

    # 中间：居中搜索栏（放大镜 + 文本“搜索”，Enter 直接搜索）
    _c1, _c2, _c3 = st.columns([1, 2, 1])
    with _c2:
        st.markdown('<div class="search-bar-container">', unsafe_allow_html=True)
        search_col, btn_col = st.columns([4, 1], gap="small")
        with search_col:
            _q = st.text_input(
                "搜索菜名",
                placeholder="搜搜看你想吃什么...",
                key="name_query",
                label_visibility="collapsed",
                on_change=_mark_search,
            )
        with btn_col:
            clicked = st.button("搜索", key="btn_search_name", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        do_search = clicked or st.session_state.pop("do_search_now", False)

    if do_search and _q.strip():
        matches = search(recipes, _q.strip())
        if matches:
            st.session_state["highlight_recipe"] = matches[0][0]
            if matches[0][0] not in [r.get("name") for r in st.session_state.get("recently_made", [])]:
                st.session_state["recently_made"].insert(
                    0,
                    {"name": matches[0][0], "detail": matches[0][1]},
                )
            st.rerun()

    # 若有高亮菜谱，在主页顶部展示
    highlight = st.session_state.get("highlight_recipe")
    if highlight and highlight in recipes:
        detail = recipes[highlight]
        st.markdown("## 今日推荐详情")
        st.subheader(highlight)
        ingredients = detail.get("食材", [])
        steps = detail.get("步骤", [])
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**所用食材**")
            if ingredients:
                st.write("\n".join([f"- {x}" for x in ingredients]))
            else:
                st.write("（暂无）")
        with c2:
            st.markdown("**制作步骤**")
            if steps:
                for i, step in enumerate(steps, start=1):
                    st.write(f"{i}. {step}")
            else:
                st.write("（暂无）")
        st.divider()
        st.session_state["highlight_recipe"] = None

    # 中部核心区：最近制作（约 50% 高度可滚动）
    st.markdown("### 最近制作")
    recent = st.session_state.get("recently_made", [])[:10]
    if recent:
        try:
            scroll_container = st.container(height=350)
        except TypeError:
            scroll_container = st.container()
        with scroll_container:
            for item in recent:
                name = item.get("name", "")
                detail = item.get("detail", {})
                ings = detail.get("食材", [])
                with st.expander(f"{name}", expanded=False):
                    st.markdown("**配料**")
                    st.write("、".join(ings) if ings else "（暂无）")
                    if st.button("查看做法", key=f"recent_view_{name}"):
                        st.session_state["highlight_recipe"] = name
                        st.rerun()
    else:
        st.info("还没有最近制作的记录，搜索后会出现在这里。")


def _sync_fridge_flat_items() -> None:
    """把分类库存同步到 st.session_state.fridge（用于推荐逻辑）。"""
    all_items: list[str] = []
    for items in st.session_state["fridge_catalog"].values():
        all_items.extend(items)
    dedup: list[str] = []
    seen: set[str] = set()
    for item in all_items:
        if item not in seen:
            seen.add(item)
            dedup.append(item)
    st.session_state["fridge"] = dedup


@st.dialog("➕ 新增分类")
def add_category_dialog() -> None:
    name = st.text_input("分类名称", placeholder="例如：菌菇、饮品、零食")
    if st.button("确认添加", use_container_width=True):
        n = name.strip()
        if not n:
            st.warning("请输入分类名称。")
            return
        if n in st.session_state["fridge_catalog"]:
            st.info("该分类已存在。")
            return
        st.session_state["fridge_catalog"][n] = []
        st.session_state["active_category"] = n
        _sync_fridge_flat_items()
        st.rerun()


def render_fridge() -> None:
    """冰箱管理页：搜索 + 分类轴 + 固定高度图鉴容器。"""
    st.subheader("我的冰箱")

    catalog: dict[str, list[str]] = st.session_state["fridge_catalog"]
    fixed_categories = ["全部", "水果", "肉类", "生鲜", "蔬菜", "调料", "其他"]
    for k in fixed_categories[1:]:
        catalog.setdefault(k, [])
    st.session_state["fridge_catalog"] = catalog
    _sync_fridge_flat_items()
    custom_categories = [k for k in catalog.keys() if k not in fixed_categories and k != "全部"]
    nav_categories = fixed_categories + custom_categories

    if st.session_state["active_category"] not in nav_categories:
        st.session_state["active_category"] = "全部"

    # 第一层：内部搜索栏（实时筛选）
    keyword = st.text_input(
        "在冰箱里搜索",
        placeholder="在冰箱里找找看...",
        key="fridge_search_kw",
        label_visibility="collapsed",
    ).strip()

    # 第二层：横向分类导航轴 + 末尾自定义按钮
    st.markdown('<div class="fridge-category-scroll">', unsafe_allow_html=True)
    cat_options = nav_categories + ["+ 自定义种类"]
    selected = st.radio(
        "分类轴",
        cat_options,
        index=cat_options.index(st.session_state["active_category"]) if st.session_state["active_category"] in cat_options else 0,
        horizontal=True,
        label_visibility="collapsed",
        key="fridge_cat_axis",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if selected == "+ 自定义种类":
        add_category_dialog()
        active = st.session_state["active_category"]
    else:
        st.session_state["active_category"] = selected
        active = selected

    # 支持“特定种类下”新增食材（仅名称 + 添加按钮）
    add_item_c1, add_item_c2 = st.columns([4, 1.6], gap="small")
    with add_item_c1:
        new_item = st.text_input(
            "新增食材",
            placeholder=f"添加到「{active if active != '全部' else '其他'}」",
            key=f"new_item_in_{active}",
            label_visibility="collapsed",
        )
    with add_item_c2:
        if st.button("＋ 增加食材", key=f"btn_add_item_{active}", use_container_width=True):
            target = active if active != "全部" else "其他"
            val = new_item.strip()
            if not val:
                st.warning("请输入食材名称。")
            else:
                catalog.setdefault(target, [])
                if val not in catalog[target]:
                    catalog[target].append(val)
                item_key = f"{target}::{val}"
                st.session_state["fridge_item_counts"].setdefault(item_key, 1)
                st.session_state["fridge_item_units"].setdefault(item_key, "个")
                st.session_state["fridge_catalog"] = catalog
                _sync_fridge_flat_items()
                st.rerun()

    # 第三层：固定高度内容区（450px），内部纵向滚动
    st.markdown('<div class="fridge-items-shell">', unsafe_allow_html=True)
    panel = st.container(height=450)
    with panel:
        if active == "全部":
            merged: list[tuple[str, str]] = []
            for cat, items in catalog.items():
                for item in items:
                    merged.append((cat, item))
            if keyword:
                merged = [(c, i) for c, i in merged if keyword in i]
            display_rows = merged
        else:
            items = catalog.get(active, [])
            if keyword:
                items = [i for i in items if keyword in i]
            display_rows = [(active, i) for i in items]

        if not display_rows:
            st.info("当前分类暂无匹配食材。")
        else:
            for cat, item in display_rows:
                item_key = f"{cat}::{item}"
                if item_key not in st.session_state["fridge_item_counts"]:
                    st.session_state["fridge_item_counts"][item_key] = 1
                if item_key not in st.session_state["fridge_item_units"]:
                    st.session_state["fridge_item_units"][item_key] = "个"

                left, right = st.columns([4, 3], gap="small")
                with left:
                    st.markdown(f'<div class="fridge-item-card">{item}</div>', unsafe_allow_html=True)
                with right:
                    qty_col, unit_col = st.columns([1.2, 1.4], gap="small")
                    with qty_col:
                        st.markdown('<div class="fridge-qty-wrap">', unsafe_allow_html=True)
                        qty = st.number_input(
                            "个数",
                            min_value=0,
                            step=1,
                            key=f"qty_{item_key}",
                            value=st.session_state["fridge_item_counts"][item_key],
                            label_visibility="collapsed",
                        )
                        st.markdown("</div>", unsafe_allow_html=True)
                    with unit_col:
                        unit = st.selectbox(
                            "单位",
                            FRIDGE_UNIT_OPTIONS,
                            index=FRIDGE_UNIT_OPTIONS.index(st.session_state["fridge_item_units"].get(item_key, "个"))
                            if st.session_state["fridge_item_units"].get(item_key, "个") in FRIDGE_UNIT_OPTIONS
                            else 0,
                            key=f"unit_{item_key}",
                            label_visibility="collapsed",
                        )
                    st.session_state["fridge_item_counts"][item_key] = int(qty)
                    st.session_state["fridge_item_units"][item_key] = unit
    st.markdown("</div>", unsafe_allow_html=True)


def render_discover() -> None:
    """发现页面：展示其他用户上传的菜谱和图片（示例数据）"""
    st.subheader("发现 · 大家的拿手菜")
    st.caption("这里展示的是示例数据，将来可以接入真实的用户上传。")

    for item in COMMUNITY_RECIPES:
        st.markdown(f"### {item['name']}")
        st.caption(f"来自：{item['author']}")
        cols = st.columns([2, 3])
        with cols[0]:
            if item.get("image"):
                st.image(item["image"], use_column_width=True)
        with cols[1]:
            st.markdown("**食材**")
            st.write("\n".join([f"- {x}" for x in item["ingredients"]]))
            st.markdown("**步骤**")
            for i, step in enumerate(item["steps"], start=1):
                st.write(f"{i}. {step}")
        st.divider()


def render_mine() -> None:
    """我的页面：上传/管理自己的菜谱（当前会话内保存）"""
    if "my_recipes" not in st.session_state:
        st.session_state["my_recipes"] = []

    st.subheader("我的菜谱")
    st.caption("你可以在这里上传自己的食谱（当前是保存在本次运行内，刷新/重启后会清空）。")
    if st.button("去冰箱管理"):
        st.session_state["page"] = "fridge"
        st.rerun()

    with st.expander("➕ 上传新的食谱", expanded=True):
        name = st.text_input("菜名", placeholder="例如：家常红烧肉")
        ing = st.text_area("食材（每行一种或用逗号分隔）", height=80)
        steps_text = st.text_area("制作步骤（每行一步）", height=120)
        image_file = st.file_uploader("上传成品图片（可选）", type=["png", "jpg", "jpeg"])
        submit = st.button("保存到我的食谱")

        if submit:
            if not name.strip():
                st.warning("至少要填写菜名哦。")
            else:
                ingredients = []
                if ing.strip():
                    tmp = (
                        ing.replace("，", ",")
                        .replace("、", ",")
                        .replace("；", ",")
                        .replace(";", ",")
                    )
                    for part in tmp.split(","):
                        p = part.strip()
                        if p:
                            ingredients.append(p)
                steps = [
                    line.strip()
                    for line in steps_text.splitlines()
                    if line.strip()
                ]
                st.session_state["my_recipes"].append(
                    {
                        "name": name.strip(),
                        "ingredients": ingredients,
                        "steps": steps,
                        "image": image_file,
                    }
                )
                st.success("已保存到本次运行的“我的菜谱”中。")

    if st.session_state["my_recipes"]:
        st.markdown("### 我已经保存的菜谱")
        for idx, item in enumerate(st.session_state["my_recipes"], start=1):
            st.markdown(f"#### {idx}. {item['name']}")
            cols = st.columns([2, 3])
            with cols[0]:
                if item["image"] is not None:
                    st.image(item["image"], use_column_width=True)
            with cols[1]:
                if item["ingredients"]:
                    st.markdown("**食材**")
                    st.write("\n".join([f"- {x}" for x in item["ingredients"]]))
                if item["steps"]:
                    st.markdown("**步骤**")
                    for i, step in enumerate(item["steps"], start=1):
                        st.write(f"{i}. {step}")
            st.divider()
    else:
        st.info("你还没有保存任何菜谱，可以先在上面“上传新的食谱”。")


# 根据当前 page 渲染主体内容
current_page = st.session_state["page"]

if current_page == "home":
    render_home(recipes)
elif current_page == "fridge":
    render_fridge()
elif current_page == "discover":
    render_discover()
elif current_page == "mine":
    render_mine()

# 底部固定导航栏（纯图标）
render_icon_navbar(current_page)