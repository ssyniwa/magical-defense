import random
import streamlit as st

# ページ設定
st.set_page_config(
    page_title="魔導兵器ディフェンス", page_icon="🛡️", layout="centered"
)

# 定数
GRID_SIZE = 6  # 6x6の盤面
MAX_TURNS = 20  # クリアまでのターン数


# セッション状態の初期化
def init_game():
    st.session_state.turn = 1
    st.session_state.gold = 100
    st.session_state.score = 0
    st.session_state.game_over = False
    st.session_state.cleared = False
    # 盤面: None または ユニット情報辞書
    st.session_state.board = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    # 出現中の敵リスト: [{'id': 1, 'x': x, 'y': y, 'hp': 30, 'max_hp': 30, 'atk': 10}]
    st.session_state.enemies = []


if "board" not in st.session_state:
    init_game()

# --- ユニットの定義 ---
UNIT_TYPES = {
    "砲台 (Archer)": {
        "cost": 30,
        "hp": 40,
        "atk": 15,
        "range": 2,
        "icon": "🏹",
        "desc": "射程2、単体攻撃",
    },
    "魔導キャノン (Cannon)": {
        "cost": 50,
        "hp": 30,
        "atk": 25,
        "range": 3,
        "icon": "💣",
        "desc": "射程3、高火力",
    },
    "壁 (Wall)": {
        "cost": 15,
        "hp": 80,
        "atk": 0,
        "range": 0,
        "icon": "🧱",
        "desc": "攻撃しない壁",
    },
}

# UIタイトル
st.title("🛡️ 魔導兵器ディフェンス")
st.markdown("チェス盤のようなマップに魔導兵器を配置し、迫りくる魔物を撃退せよ！")

# ゲーム終了・クリア時の判定
if st.session_state.game_over:
    st.error("💀 拠点が突破されてしまいました…ゲームオーバー！")
    if st.button("もう一度プレイする"):
        init_game()
        st.rerun()
    st.stop()

if st.session_state.cleared:
    st.success(
        f"🎉 すべての波状攻撃を防ぎきりました！クリア！ スコア: {st.session_state.score}"
    )
    if st.button("もう一度プレイする"):
        init_game()
        st.rerun()
    st.stop()

# --- サイドバー：ショップ＆ステータス ---
st.sidebar.header("📊 ステータス")
st.sidebar.write(f"**ターン:** {st.session_state.turn} / {MAX_TURNS}")
st.sidebar.write(f"**ゴールド:** 💰 {st.session_state.gold} G")
st.sidebar.write(f"**スコア:** ⭐ {st.session_state.score}")

st.sidebar.divider()
st.sidebar.header("🛠️ 兵器の購入・配置")
selected_unit_name = st.sidebar.selectbox(
    "兵器を選ぶ", list(UNIT_TYPES.keys())
)
unit_info = UNIT_TYPES[selected_unit_name]
st.sidebar.info(
    f"{unit_info['icon']} **{selected_unit_name}**\n\n"
    f"コスト: {unit_info['cost']}G | HP: {unit_info['hp']} | 攻撃力: {unit_info['atk']}\n\n"
    f"{unit_info['desc']}"
)

st.sidebar.divider()
selected_x = st.sidebar.slider("配置 X座標 (横)", 0, GRID_SIZE - 1, 0)
selected_y = st.sidebar.slider("配置 Y座標 (縦)", 0, GRID_SIZE - 1, 0)

col_b1, col_b2 = st.sidebar.columns(2)


def place_unit():
    cost = UNIT_TYPES[selected_unit_name]["cost"]
    if st.session_state.gold < cost:
        st.sidebar.error("ゴールドが足りません！")
        return

    # すでに何かあるか
    if st.session_state.board[selected_y][selected_x] is not None:
        st.sidebar.error("すでにユニットが配置されています！")
        return

    # 配置（最右列は敵の侵攻ルートとして空けさせる制限も可能だが自由度重視で全域許可）
    base = UNIT_TYPES[selected_unit_name]
    st.session_state.board[selected_y][selected_x] = {
        "name": selected_unit_name,
        "icon": base["icon"],
        "hp": base["hp"],
        "max_hp": base["hp"],
        "atk": base["atk"],
        "range": base["range"],
    }
    st.session_state.gold -= cost
    st.sidebar.success("配置しました！")


if col_b1.button("配置する"):
    place_unit()
    st.rerun()


# --- メイン：マップ（画像グリッド）表示 ---
st.subheader("🗺️ 戦略マップ")
st.caption(
    "💡 右側の列から敵が侵攻してきます。左側（X=0付近）で守り抜け！"
)

# 敵の位置を高速検索するためのマップ作成
enemy_map = {}
for e in st.session_state.enemies:
    enemy_map[(e["x"], e["y"])] = e

# 各ユニットに対応する画像のパス（必要に応じて変更してください）
IMAGE_PATHS = {
    "砲台 (Archer)": "assets/archer.png",
    "魔導キャノン (Cannon)": "assets/cannon.png",
    "壁 (Wall)": "assets/wall.png",
}
PLAIN_IMAGE = "assets/plain.png"
ENEMY_IMAGE = "assets/enemy.png"

# 視覚的なグリッド描画（画像対応版）
for y in range(GRID_SIZE):
    cols = st.columns(GRID_SIZE)
    for x in range(GRID_SIZE):
        with cols[x]:
            cell_unit = st.session_state.board[y][x]
            cell_enemy = enemy_map.get((x, y))

            # 表示する画像とテキスト（HPなど）の決定
            img_url = PLAIN_IMAGE
            status_text = f"<span style='color:#adb5bd; font-size:10px;'>({x},{y})</span>"
            bg_color = "rgba(0,0,0,0.05)"

            if cell_enemy:
                # 敵がいる場合
                img_url = ENEMY_IMAGE
                status_text = f"<b style='color:red; font-size:11px;'>HP:{cell_enemy['hp']}</b>"
                bg_color = "rgba(255, 0, 0, 0.15)"
            elif cell_unit:
                # 味方ユニットがいる場合
                img_url = IMAGE_PATHS.get(cell_unit["name"], PLAIN_IMAGE)
                status_text = (
                    f"<b style='color:green; font-size:11px;'>HP:{cell_unit['hp']}</b>"
                )
                bg_color = "rgba(0, 255, 0, 0.15)"

            # HTML/CSSを使って画像をタイル状にきれいに表示
            st.markdown(
                f"""
                <div style="
                    background-image: url('{PLAIN_IMAGE}');
                    background-size: cover;
                    background-position: center;
                    border: 2px solid #ccc;
                    border-radius: 8px;
                    height: 85px;
                    text-align: center;
                    position: relative;
                    overflow: hidden;
                ">
                    <div style="
                        background-color: {bg_color};
                        width: 100%;
                        height: 100%;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        padding: 4px;
                    ">
                        <img src="{img_url}" style="width: 35px; height: 35px; object-fit: contain; margin-bottom: 2px;" onerror="this.style.display='none'">
                        {status_text}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.divider()


# --- ターン進行処理 ---
def next_turn():
    # 1. 敵の出現（毎ターン、右端のどこかから出現）
    if st.session_state.turn <= MAX_TURNS:
        # ターンが進むにつれて敵が強くなる
        spawn_y = random.randint(0, GRID_SIZE - 1)
        hp_val = 30 + (st.session_state.turn * 5)
        st.session_state.enemies.append(
            {
                "id": random.randint(1000, 9999),
                "x": GRID_SIZE - 1,
                "y": spawn_y,
                "hp": hp_val,
                "max_hp": hp_val,
                "atk": 10 + int(st.session_state.turn * 1.5),
                "icon": "👹",
            }
        )

    # 2. ユニットの攻撃フェーズ
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            unit = st.session_state.board[y][x]
            if unit and unit["atk"] > 0:
                # 射程内にいる最も近い敵を探す
                target = None
                min_dist = 999
                for e in st.session_state.enemies:
                    dist = abs(e["x"] - x) + abs(e["y"] - y)  # マンハッタン距離
                    if dist <= unit["range"] and dist < min_dist:
                        min_dist = dist
                        target = e

                # 攻撃実行
                if target:
                    target["hp"] -= unit["atk"]

    # 倒された敵の処理とゴールド・スコア加算
    surviving_enemies = []
    for e in st.session_state.enemies:
        if e["hp"] > 0:
            surviving_enemies.append(e)
        else:
        # 撃破
            st.session_state.gold += 20
            st.session_state.score += 50
    st.session_state.enemies = surviving_enemies

    # 3. 敵の移動・攻撃フェーズ
    new_enemies = []
    for e in st.session_state.enemies:
        # 正面（左方向 X-1）にユニットがいるか確認
        target_unit = None
        if e["x"] > 0:
            target_unit = st.session_state.board[e["y"]][e["x"] - 1]

        if target_unit:
            # ユニットがいれば攻撃して進まない
            target_unit["hp"] -= e["atk"]
            new_enemies.append(e)
        else:
            # 前進できるなら左へ移動
            if e["x"] > 0:
                e["x"] -= 1
                new_enemies.append(e)
            else:
                # X=0を突破されたらゲームオーバー
                st.session_state.game_over = True

    st.session_state.enemies = new_enemies

    # 4. 破壊された味方ユニットの撤去
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            unit = st.session_state.board[y][x]
            if unit and unit["hp"] <= 0:
                st.session_state.board[y][x] = None

    # 5. ターン・ゴールドの更新
    st.session_state.gold += 10  
    st.session_state.turn += 1

    # クリア判定
    if st.session_state.turn > MAX_TURNS and len(st.session_state.enemies) == 0:
        st.session_state.cleared = True


if st.button("▶️ ターンを進める (戦闘・敵の移動)", use_container_width=True):
    if not st.session_state.game_over and not st.session_state.cleared:
        next_turn()
        st.rerun()
