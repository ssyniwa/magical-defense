import base64
import os
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
    # 出現中の敵リスト
    st.session_state.enemies = []


if "board" not in st.session_state:
    init_game()


# ローカル画像をBase64に変換する関数（MIMEタイプを拡張子から自動判定）
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
        b64_str = base64.b64encode(data).decode("utf-8")
        # 拡張子に合わせてMIMEタイプを切り替え
        if path.endswith((".jpg", ".jpeg", ".JPG", ".JPEG")):
            return f"data:image/jpeg;base64,{b64_str}"
        else:
            return f"data:image/png;base64,{b64_str}"
    return None


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

    if st.session_state.board[selected_y][selected_x] is not None:
        st.sidebar.error("すでにユニットが配置されています！")
        return

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

enemy_map = {}
for e in st.session_state.enemies:
    enemy_map[(e["x"], e["y"])] = e

# 画像パスの設定
IMAGE_ASSETS = {
    "plain": "assets/plain.png",
    "enemy": "assets/enemy.png",
    "砲台 (Archer)": "assets/archer.png",
    "魔導キャノン (Cannon)": "assets/cannon.png",
    "壁 (Wall)": "assets/wall.png",
}

# Base64データに変換
B64_IMAGES = {name: get_image_base64(path) for name, path in IMAGE_ASSETS.items()}

# グリッド描画
for y in range(GRID_SIZE):
    cols = st.columns(GRID_SIZE)
    for x in range(GRID_SIZE):
        with cols[x]:
            cell_unit = st.session_state.board[y][x]
            cell_enemy = enemy_map.get((x, y))

            # 1. 背景画像のスタイル設定
            bg_data = B64_IMAGES.get("plain")
            if bg_data:
                bg_style = f"background-image: url('{bg_data}'); background-size: cover; background-position: center;"
            else:
                bg_style = "background-color: #333;"

            # 2. 各状態に応じたコンテンツの構築
            content_html = ""
            border_color = "#aaa"

            if cell_enemy:
                border_color = "#ff4d4d"
                enemy_data = B64_IMAGES.get("enemy")
                if enemy_data and len(enemy_data) > 100:
                    img_tag = f'<img src="{enemy_data}" style="width: 38px; height: 38px; object-fit: contain; filter: drop-shadow(1px 1px 2px black);">'
                else:
                    img_tag = '<div style="font-size: 26px;">👹</div>'

                content_html = f"""
                    {img_tag}
                    <div style="color: white; background-color: rgba(0,0,0,0.8); font-size: 10px; font-weight: bold; border-radius: 4px; padding: 1px 4px; margin-top: 2px;">
                        HP:{cell_enemy['hp']}
                    </div>
                """

            elif cell_unit:
                border_color = "#2ecc71"
                unit_data = B64_IMAGES.get(cell_unit["name"])
                if unit_data and len(unit_data) > 100:
                    img_tag = f'<img src="{unit_data}" style="width: 38px; height: 38px; object-fit: contain; filter: drop-shadow(1px 1px 2px black);">'
                else:
                    img_tag = f'<div style="font-size: 26px;">{cell_unit["icon"]}</div>'

                content_html = f"""
                    {img_tag}
                    <div style="color: white; background-color: rgba(0,0,0,0.8); font-size: 10px; font-weight: bold; border-radius: 4px; padding: 1px 4px; margin-top: 2px;">
                        HP:{cell_unit['hp']}
                    </div>
                """
            else:
                # 空きマスでも他のマスと全く同じ高さをキープするため、ダミーの不可視テキストまたは座標を配置
                content_html = f"""
                    <div style="font-size: 26px; visibility: hidden;">・</div>
                    <div style="color: #eee; font-size: 10px; text-shadow: 1px 1px 2px black; background-color: rgba(0,0,0,0.4); border-radius: 4px; padding: 1px 4px;">
                        ({x},{y})
                    </div>
                """

            # 3. 描画（すべてのマスで高さを 90px に固定）
            st.markdown(
                f"""
                <div style="
                    {bg_style}
                    border: 2px solid {border_color};
                    border-radius: 6px;
                    height: 90px;
                    width: 100%;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    overflow: hidden;
                    margin-bottom: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                ">
                    {content_html}
                </div>
                """,
                unsafe_allow_html=True,
            )
st.divider()


# --- ターン進行処理 ---
def next_turn():
    if st.session_state.turn <= MAX_TURNS:
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

    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            unit = st.session_state.board[y][x]
            if unit and unit["atk"] > 0:
                target = None
                min_dist = 999
                for e in st.session_state.enemies:
                    dist = abs(e["x"] - x) + abs(e["y"] - y)
                    if dist <= unit["range"] and dist < min_dist:
                        min_dist = dist
                        target = e
                if target:
                    target["hp"] -= unit["atk"]

    surviving_enemies = []
    for e in st.session_state.enemies:
        if e["hp"] > 0:
            surviving_enemies.append(e)
        else:
            st.session_state.gold += 20
            st.session_state.score += 50
    st.session_state.enemies = surviving_enemies

    new_enemies = []
    for e in st.session_state.enemies:
        target_unit = None
        if e["x"] > 0:
            target_unit = st.session_state.board[e["y"]][e["x"] - 1]

        if target_unit:
            target_unit["hp"] -= e["atk"]
            new_enemies.append(e)
        else:
            if e["x"] > 0:
                e["x"] -= 1
                new_enemies.append(e)
            else:
                st.session_state.game_over = True

    st.session_state.enemies = new_enemies

    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            unit = st.session_state.board[y][x]
            if unit and unit["hp"] <= 0:
                st.session_state.board[y][x] = None

    st.session_state.gold += 10
    st.session_state.turn += 1

    if st.session_state.turn > MAX_TURNS and len(st.session_state.enemies) == 0:
        st.session_state.cleared = True


if st.button("▶️ ターンを進める (戦闘・敵の移動)", use_container_width=True):
    if not st.session_state.game_over and not st.session_state.cleared:
        next_turn()
        st.rerun()
