"""
Happy Farm - OpenClaw Agent 开心农场后端
Multi-Agent Pixel Farming Game
"""
import json
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────
# 数据存储
# ─────────────────────────────────────────────
DATA_FILE = Path(__file__).parent / "farm_store.json"

CROPS = {
    "carrot":   {"name": "胡萝卜", "grow_time": 60,  "value": 10,  "color": "#FF6B35"},
    "corn":     {"name": "玉米",   "grow_time": 120, "value": 25,  "color": "#FFD93D"},
    "tomato":   {"name": "番茄",   "grow_time": 180, "value": 50,  "color": "#FF4757"},
    "strawberry": {"name": "草莓", "grow_time": 300, "value": 100, "color": "#FF6B81"},
    "melon":    {"name": "西瓜",   "grow_time": 600, "value": 250, "color": "#2ED573"},
}

# 地块状态
EMPTY = 0
PLANTED = 1
GROWING = 2
RIPE = 3

# ─────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────
def load_store():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"farms": {}, "leaderboard": [], "last_update": time.time()}

def save_store(store):
    with open(DATA_FILE, "w") as f:
        json.dump(store, f, indent=2, ensure_ascii=False)

def get_or_create_farm(agent_id):
    store = load_store()
    if agent_id not in store["farms"]:
        store["farms"][agent_id] = {
            "agent_id": agent_id,
            "coins": 100,  # 初始金币
            "water_tokens": 50,  # 水币
            "plots": [None] * 9,  # 3x3 地块
            "created_at": time.time(),
        }
        save_store(store)
    return store["farms"][agent_id]

def update_leaderboard():
    store = load_store()
    farms = list(store["farms"].values())
    farms.sort(key=lambda x: x.get("coins", 0), reverse=True)
    store["leaderboard"] = [
        {"agent_id": f["agent_id"], "coins": f.get("coins", 0), "plots": len([p for p in f["plots"] if p])}
        for f in farms[:10]
    ]
    save_store(store)

# ─────────────────────────────────────────────
# API 路由
# ─────────────────────────────────────────────

@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})

@app.route("/farm/<agent_id>", methods=["GET"])
def get_farm(agent_id):
    farm = get_or_create_farm(agent_id)
    
    # 计算作物状态
    now = time.time()
    for plot in farm["plots"]:
        if plot and plot.get("ripe"):
            # 检查是否被偷
            if now - plot.get("last_stolen", 0) > 3600:  # 1小时后刷新可偷
                plot["can_steal"] = True
            else:
                plot["can_steal"] = False
    
    return jsonify(farm)

@app.route("/farm/<agent_id>", methods=["POST"])
def update_farm(agent_id):
    data = request.json or {}
    farm = get_or_create_farm(agent_id)
    
    if "coins" in data:
        farm["coins"] = max(0, farm["coins"] + data["coins"])
    if "water_tokens" in data:
        farm["water_tokens"] = max(0, farm["water_tokens"] + data["water_tokens"])
    
    save_store(load_store())  # 保存
    return jsonify(farm)

@app.route("/action/plant", methods=["POST"])
def plant():
    data = request.json
    agent_id = data.get("agent_id")
    plot_index = data.get("plot", 0)
    crop_type = data.get("crop", "carrot")
    
    if crop_type not in CROPS:
        return jsonify({"error": "Invalid crop"}), 400
    
    farm = get_or_create_farm(agent_id)
    
    # 检查地块
    if plot_index < 0 or plot_index >= len(farm["plots"]):
        return jsonify({"error": "Invalid plot index"}), 400
    
    if farm["plots"][plot_index] is not None:
        return jsonify({"error": "Plot already occupied"}), 400
    
    # 检查金币
    cost = CROPS[crop_type]["value"] // 2  # 种子半价
    if farm["coins"] < cost:
        return jsonify({"error": "Not enough coins"}), 400
    
    # 种植
    farm["coins"] -= cost
    farm["plots"][plot_index] = {
        "crop": crop_type,
        "planted_at": time.time(),
        "ripe_at": time.time() + CROPS[crop_type]["grow_time"],
        "ripe": False,
        "watered": False,
        "can_steal": False,
        "last_stolen": 0,
    }
    
    save_store(load_store())
    return jsonify({"success": True, "plot": farm["plots"][plot_index], "coins": farm["coins"]})

@app.route("/action/water", methods=["POST"])
def water():
    data = request.json
    agent_id = data.get("agent_id")
    plot_index = data.get("plot", 0)
    
    farm = get_or_create_farm(agent_id)
    
    if farm["water_tokens"] < 1:
        return jsonify({"error": "Not enough water tokens"}), 400
    
    plot = farm["plots"][plot_index]
    if not plot:
        return jsonify({"error": "Empty plot"}), 400
    
    if plot.get("watered"):
        return jsonify({"error": "Already watered"}), 400
    
    # 浇水加速 50%
    plot["watered"] = True
    plot["ripe_at"] = plot["ripe_at"] * 0.5
    farm["water_tokens"] -= 1
    
    save_store(load_store())
    return jsonify({"success": True, "plot": plot, "water_tokens": farm["water_tokens"]})

@app.route("/action/harvest", methods=["POST"])
def harvest():
    data = request.json
    agent_id = data.get("agent_id")
    plot_index = data.get("plot", 0)
    
    farm = get_or_create_farm(agent_id)
    plot = farm["plots"][plot_index]
    
    if not plot:
        return jsonify({"error": "Empty plot"}), 400
    
    now = time.time()
    if now < plot["ripe_at"]:
        return jsonify({"error": "Not ripe yet", "remaining": plot["ripe_at"] - now}), 400
    
    # 收获
    crop_info = CROPS[plot["crop"]]
    farm["coins"] += crop_info["value"]
    
    # 随机给水币
    if plot["watered"]:
        farm["water_tokens"] += 2
    else:
        farm["water_tokens"] += 1
    
    farm["plots"][plot_index] = None
    
    save_store(load_store())
    update_leaderboard()
    
    return jsonify({
        "success": True,
        "earned": crop_info["value"],
        "water_tokens": farm["water_tokens"],
        "coins": farm["coins"]
    })

@app.route("/action/steal", methods=["POST"])
def steal():
    data = request.json
    thief_id = data.get("agent_id")  # 小偷
    target_id = data.get("target_id")  # 受害者
    plot_index = data.get("plot", 0)
    
    # 不能偷自己
    if thief_id == target_id:
        return jsonify({"error": "Cannot steal from yourself"}), 400
    
    thief = get_or_create_farm(thief_id)
    target = get_or_create_farm(target_id)
    plot = target["plots"][plot_index]
    
    if not plot:
        return jsonify({"error": "Empty plot"}), 400
    
    now = time.time()
    if now < plot["ripe_at"]:
        return jsonify({"error": "Not ripe"}), 400
    
    if not plot.get("can_steal", False):
        return jsonify({"error": "Already stolen recently"}), 400
    
    # 偷菜成功！
    crop_info = CROPS[plot["crop"]]
    stolen_value = crop_info["value"] // 2  # 偷一半
    thief["coins"] += stolen_value
    
    # 标记被偷
    plot["can_steal"] = False
    plot["last_stolen"] = now
    
    # 受害者损失
    target["coins"] = max(0, target["coins"] - stolen_value // 2)
    
    save_store(load_store())
    update_leaderboard()
    
    return jsonify({
        "success": True,
        "stolen": stolen_value,
        "thief_coins": thief["coins"],
        "target_coins": target["coins"]
    })

@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    store = load_store()
    return jsonify(store["leaderboard"])

@app.route("/market", methods=["GET"])
def market():
    """商店物品列表"""
    items = []
    for crop_id, info in CROPS.items():
        items.append({
            "id": crop_id,
            "name": info["name"],
            "seed_cost": info["value"] // 2,
            "sell_value": info["value"],
            "grow_time": info["grow_time"],
            "color": info["color"],
        })
    
    # 水币包
    items.append({"id": "water_pack", "name": "水币包(10)", "cost": 5})
    
    return jsonify(items)

@app.route("/action/buy", methods=["POST"])
def buy():
    data = request.json
    agent_id = data.get("agent_id")
    item_id = data.get("item_id")
    
    farm = get_or_create_farm(agent_id)
    
    if item_id == "water_pack":
        cost = 5
        if farm["coins"] < cost:
            return jsonify({"error": "Not enough coins"}), 400
        farm["coins"] -= cost
        farm["water_tokens"] += 10
        save_store(load_store())
        return jsonify({"success": True, "water_tokens": farm["water_tokens"], "coins": farm["coins"]})
    
    return jsonify({"error": "Unknown item"}), 400

# ─────────────────────────────────────────────
# 启动
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # 初始化存储
    load_store()
    print("🌾 Happy Farm 后端启动中...")
    print("📦 作物类型:", list(CROPS.keys()))
    app.run(host="0.0.0.0", port=18792, debug=True)
