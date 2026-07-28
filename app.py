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
    "雷撃塔 (Tesla)": {
        "cost": 45,
        "hp": 35,
        "atk": 18,
        "range": 2,
        "icon": "⚡",
        "desc": "射程2、複数攻撃（範囲）",
    },
    "スナイパー (Sniper)": {
        "cost": 60,
        "hp": 25,
        "atk": 35,
        "range": 4,
        "icon": "🎯",
        "desc": "超長射程4、高単体火力",
    },
    "バリスタ (Ballista)": {
        "cost": 55,
        "hp": 30,
        "atk": 20,
        "range": 4,
        "icon": "🚀",
        "desc": "同一ライン上の敵を貫通攻撃",
    },
    "地雷放射機 (Mine)": {
        "cost": 25,
        "hp": 25,
        "atk": 40,
        "range": 0,
        "icon": "⚠️",
        "desc": "踏み込んだ敵に大ダメージ",
    },
    "シールド発生器 (Shield)": {
        "cost": 40,
        "hp": 40,
        "atk": 0,
        "range": 1,
        "icon": "🛡️",
        "desc": "周囲の味方にシールド（回復）付与",
    },
    "減速魔方陣 (Frost)": {
        "cost": 25,
        "hp": 30,
        "atk": 0,
        "range": 0,
        "icon": "❄️",
        "desc": "攻撃なし、敵を足止め/減速",
    },
    "治癒の祭壇 (Healer)": {
        "cost": 40,
        "hp": 50,
        "atk": 0,
        "range": 1,
        "icon": "💖",
        "desc": "周囲の味方HPを毎ターン回復",
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
# --- 敵（魔物）の種類の定義 ---
ENEMY_TYPES = {
    "ゴブリン・スカウト": {
        "hp_base": 25,
        "atk": 8,
        "speed": 2,  # 1ターンに2マス進む仕様にする場合などに活用
        "icon": "🏃",
    },
    "スケルトン・ソルジャー": {
        "hp_base": 30,
        "atk": 10,
        "speed": 1,
        "icon": "👹",
    },
    "アーマード・オーク": {
        "hp_base": 60,
        "atk": 15,
        "speed": 1,
        "icon": "🛡️",
    },
    "ボム・インプ": {
        "hp_base": 20,
        "atk": 25,  # 攻撃力高め
        "speed": 1,
        "icon": "💣",
    },
    "ダーク・ウィザード": {
        "hp_base": 25,
        "atk": 12,
        "speed": 1,
        "range": 2,  # 遠隔攻撃の射程
        "icon": "🧙‍♂️",
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
    "ゴブリン・スカウト": "assets/goblin.png",
    "スケルトン・ソルジャー": "assets/enemy.png",
    "アーマード・オーク": "assets/orc.png",
    "ボム・インプ": "assets/imp.png",
    "ダーク・ウィザード": "assets/mage.png",
    "砲台 (Archer)": "assets/archer.png",
    "魔導キャノン (Cannon)": "assets/cannon.png",
    "雷撃塔 (Tesla)": "assets/tesla.png",  # 画像があれば用意
    "スナイパー (Sniper)": "assets/sniper.png",
    "バリスタ (Ballista)": "assets/ballista.png",
    "地雷放射機 (Mine)": "assets/mine.png",
    "シールド発生器 (Shield)": "assets/shield.png",
    "減速魔方陣 (Frost)": "assets/frost.png",
    "治癒の祭壇 (Healer)": "assets/healer.png",
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

            # 背景画像
            bg_data = B64_IMAGES.get("plain")
            if bg_data:
                bg_style = f"background-image: url('{bg_data}'); background-size: cover; background-position: center;"
            else:
                bg_style = "background-color: #333;"

            # 状態に応じた表示要素の切り分け
            if cell_enemy:
                border_color = "#ff4d4d"
                # 敵の名前から個別画像を取得（なければ共通のenemy画像、それもなければ絵文字）
                enemy_data = B64_IMAGES.get(cell_enemy["name"]) or B64_IMAGES.get("enemy")
                
                if enemy_data and len(enemy_data) > 100:
                    img_tag = f'<img src="{enemy_data}" style="width: 80px; height: 80px; object-fit: contain;">'
                else:
                    img_tag = f'<span style="font-size: 26px;">{cell_enemy["icon"]}</span>'
                
                hp_text = f"HP:{cell_enemy['hp']}"
            elif cell_unit:
                border_color = "#2ecc71"
                unit_data = B64_IMAGES.get(cell_unit["name"])
                if unit_data and len(unit_data) > 100:
                    img_tag = f'<img src="{unit_data}" style="width: 80px; height: 80px; object-fit: contain;">'
                else:
                    img_tag = (
                        f'<span style="font-size: 26px;">{cell_unit["icon"]}</span>'
                    )
                hp_text = f"HP:{cell_unit['hp']}"
            else:
                border_color = "#aaa"
                img_tag = '<span style="font-size: 26px; visibility: hidden;">・</span>'
                hp_text = f"({x},{y})"

            # 安全に組み立てたHTMLを出力
            html_code = f"""
            <div style="{bg_style} border: 2px solid {border_color}; border-radius: 6px; height: 90px; width: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; overflow: hidden; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                {img_tag}
                <div style="color: white; background-color: rgba(0,0,0,0.8); font-size: 10px; font-weight: bold; border-radius: 4px; padding: 1px 4px; margin-top: 2px;">
                    {hp_text}
                </div>
            </div>
            """
            st.markdown(html_code, unsafe_allow_html=True)
st.divider()


# --- ターン進行処理 ---
def next_turn():
    # 1. 敵の出現（ランダムに種類を選択）
    # --- 1. 敵の出現フェーズ ---
    if st.session_state.turn <= MAX_TURNS:
        spawn_y = random.randint(0, GRID_SIZE - 1)
        
        # 敵の種類をランダムに選択
        enemy_name = random.choice(list(ENEMY_TYPES.keys()))
        e_info = ENEMY_TYPES[enemy_name]
        
        hp_val = e_info["hp_base"] + (st.session_state.turn * 3)
        
        st.session_state.enemies.append(
            {
                "id": random.randint(1000, 9999),
                "name": enemy_name,
                "x": GRID_SIZE - 1,
                "y": spawn_y,
                "hp": hp_val,
                "max_hp": hp_val,
                "atk": e_info["atk"],
                "speed": e_info.get("speed", 1),
                "range": e_info.get("range", 1),
                "icon": e_info["icon"],
            }
        )

    # 2. ユニットの攻撃・特殊フェーズ
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            unit = st.session_state.board[y][x]
            if not unit:
                continue

            # A. バリスタの直線貫通攻撃（同じY座標にいる敵すべてを攻撃）
            if unit["name"] == "バリスタ (Ballista)":
                for e in st.session_state.enemies:
                    if e["y"] == y and 0 <= (e["x"] - x) <= unit["range"]:
                        e["hp"] -= unit["atk"]

            # B. 治癒の祭壇やシールド発生器の効果（周囲の味方のHP回復）
            elif unit["name"] in ["治癒の祭壇 (Healer)", "シールド発生器 (Shield)"]:
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < GRID_SIZE and 0 <= nx < GRID_SIZE:
                            target_friend = st.session_state.board[ny][nx]
                            if target_friend and target_friend["hp"] < target_friend["max_hp"]:
                                target_friend["hp"] = min(
                                    target_friend["max_hp"], target_friend["hp"] + 15
                                )

            # B. 攻撃系ユニットの処理
            elif unit["atk"] > 0:
                # 雷撃塔（Tesla）の場合：射程内のすべての敵にダメージ
                if unit["name"] == "雷撃塔 (Tesla)":
                    for e in st.session_state.enemies:
                        dist = abs(e["x"] - x) + abs(e["y"] - y)
                        if dist <= unit["range"]:
                            e["hp"] -= unit["atk"]
                
                # その他の単体攻撃ユニット（Archer, Cannon, Sniper）
                else:
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

    # --- 3. 敵の移動・特殊攻撃フェーズ ---
    new_enemies = []
    for e in st.session_state.enemies:
        e_name = e.get("name", "通常の魔物")
        is_dead = False

        # ボム・インプの自爆判定（正面にユニットがいる場合）
        if e_name == "ボム・インプ" and e["x"] > 0:
            front_unit = st.session_state.board[e["y"]][e["x"] - 1]
            if front_unit:
                # 自爆実行：ユニットと周囲のマスに大ダメージ（例: 攻撃力の2倍）
                explosion_dmg = e["atk"] * 2
                front_unit["hp"] -= explosion_dmg
                
                # （オプション）周囲の上下マスにいるユニットにも巻き込みダメージを与える場合
                for dy in [-1, 1]:
                    ny = e["y"] + dy
                    if 0 <= ny < GRID_SIZE:
                        splash_unit = st.session_state.board[ny][e["x"] - 1]
                        if splash_unit:
                            splash_unit["hp"] -= int(explosion_dmg * 0.5)

                # ボム・インプ自身は自爆して消滅するため、再登録しない（is_dead = True）
                is_dead = True
                
        if is_dead:
            continue
        # A. ダーク・ウィザードの遠隔攻撃（射程内にユニットがいれば近づかずに攻撃）
        if e_name == "ダーク_ウィザード" or e.get("range", 0) > 1:
            target_unit = None
            # 射程内（例: 前方2マス以内）に味方ユニットがいるか探す
            for d in range(1, e.get("range", 2) + 1):
                check_x = e["x"] - d
                if 0 <= check_x < GRID_SIZE:
                    found_unit = st.session_state.board[e["y"]][check_x]
                    if found_unit:
                        target_unit = found_unit
                        break
            
            if target_unit:
                # 遠隔攻撃を実行（自分は移動しない）
                target_unit["hp"] -= e["atk"]
                new_enemies.append(e)
                continue

        # B. 通常の移動処理（ゴブリン・スカウトは speed=2 なので2マス進む）
        speed = e.get("speed", 1)
        moved = False
        
        for _ in range(speed):
            if e["x"] > 0:
                # 正面にユニットがいるか確認
                front_unit = st.session_state.board[e["y"]][e["x"] - 1]
                if front_unit:
                    # 【追加】もし進む先に「地雷放射機」があった場合
                    if front_unit["name"] == "地雷放射機 (Mine)":
                        # 地雷の攻撃力分のダメージを敵に与える
                        e["hp"] -= front_unit["atk"]
                        # 地雷（ユニット）を消滅させる（空きマスにする）
                        st.session_state.board[next_y][next_x] = None
                        
                        # 地雷の爆発で敵のHPが0以下になっていなければ、そのまま1マス進む
                        if e["hp"] > 0:
                            e["x"] = next_x
                        else:
                            # 敵も死亡
                            is_dead = True
                        break
                    else:
                        # 通常のユニットや壁への攻撃
                        front_unit["hp"] -= e["atk"]
                        break
                else:
                    # 進めるなら左へ1マス進む
                    e["x"] -= 1
                    moved = True
            else:
                # X=0を突破されたらゲームオーバー
                st.session_state.game_over = True
                break

        # 画面内に生存している敵をリストに保持
        if not st.session_state.game_over:
            new_enemies.append(e)

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
