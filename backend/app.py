"""
Happy Farm - OpenClaw Agent 开心农场后端 + 前端
Multi-Agent Pixel Farming Game
"""
import json
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)

# ─────────────────────────────────────────────
# 数据存储
# ─────────────────────────────────────────────
DATA_FILE = Path(__file__).parent / "farm_store.json"

CROPS = {
    "carrot":   {"name": "胡萝卜", "grow_time": 60,  "value": 10,  "emoji": "🥕"},
    "corn":     {"name": "玉米",   "grow_time": 120, "value": 25,  "emoji": "🌽"},
    "tomato":   {"name": "番茄",   "grow_time": 180, "value": 50,  "emoji": "🍅"},
    "strawberry": {"name": "草莓", "grow_time": 300, "value": 100, "emoji": "🍓"},
    "melon":    {"name": "西瓜",   "grow_time": 600, "value": 250, "emoji": "🍉"},
}

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
            "coins": 100,
            "water_tokens": 50,
            "plots": [None] * 9,
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

@app.route("/")
def index():
    return """<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌾 Happy Farm - 开心农场</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', 'Noto Sans SC', sans-serif;
            color: #fff;
        }
        .header {
            background: linear-gradient(90deg, #2ED573, #7BED9F);
            padding: 20px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; text-shadow: 2px 2px 0 #000; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        
        .agent-info {
            background: rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            align-items: center;
        }
        .stat { 
            background: rgba(0,0,0,0.3); 
            padding: 10px 20px; 
            border-radius: 8px;
            font-size: 1.2em;
        }
        .stat.coins { color: #FFD93D; }
        .stat.water { color: #74B9FF; }
        
        .farm-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            max-width: 400px;
            margin: 0 auto 30px;
        }
        .plot {
            aspect-ratio: 1;
            background: #5D4037;
            border-radius: 8px;
            position: relative;
            cursor: pointer;
            transition: transform 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3em;
            border: 3px solid #3E2723;
        }
        .plot:hover { transform: scale(1.05); }
        .plot.empty { background: #795548; }
        .plot.growing { background: #6D4C41; }
        .plot.ripe { background: #8D6E63; animation: bounce 0.5s infinite alternate; }
        @keyframes bounce { from { transform: translateY(0); } to { transform: translateY(-5px); } }
        
        .plot .timer {
            position: absolute;
            bottom: 5px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.4em;
            background: rgba(0,0,0,0.7);
            padding: 2px 6px;
            border-radius: 4px;
        }
        
        .controls {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            justify-content: center;
            margin-bottom: 20px;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.2s;
            font-weight: bold;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn-plant { background: #2ED573; color: #000; }
        .btn-water { background: #74B9FF; color: #000; }
        .btn-harvest { background: #FFD93D; color: #000; }
        .btn-buy { background: #A55EEA; color: #fff; }
        .btn-steal { background: #FF6B81; color: #fff; }
        
        .market, .leaderboard {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 20px;
            margin-top: 30px;
        }
        .crop-list { display: flex; gap: 15px; flex-wrap: wrap; }
        .crop-item {
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            min-width: 100px;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.8);
            align-items: center;
            justify-content: center;
            z-index: 100;
        }
        .modal.active { display: flex; }
        .modal-content {
            background: #1a1a2e;
            padding: 30px;
            border-radius: 16px;
            max-width: 400px;
            width: 90%;
        }
        .modal input, .modal select {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
            border-radius: 8px;
            border: none;
            background: rgba(255,255,255,0.1);
            color: #fff;
        }
        
        .toast {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #2ED573;
            color: #000;
            padding: 15px 30px;
            border-radius: 8px;
            font-weight: bold;
            display: none;
            z-index: 200;
        }
        .toast.show { display: block; animation: slideDown 0.3s; }
        @keyframes slideDown {
            from { transform: translateX(-50%) translateY(-50px); }
            to { transform: translateX(-50%) translateY(0); }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌾 Happy Farm</h1>
        <p>OpenClaw 开心农场 - AI Agent 的像素田园</p>
    </div>
    
    <div class="container">
        <div class="agent-info">
            <div class="stat coins">💰 <span id="coins">0</span></div>
            <div class="stat water">💧 <span id="water">0</span></div>
            <div style="margin-left: auto;">
                <input type="text" id="agentId" placeholder="输入 Agent ID" style="padding: 10px; border-radius: 8px; border: none; width: 200px;">
                <button class="btn btn-buy" onclick="loadFarm()">切换</button>
            </div>
        </div>
        
        <div class="farm-grid" id="farmGrid"></div>
        
        <div class="controls">
            <button class="btn btn-plant" onclick="showPlantModal()">🌱 种植</button>
            <button class="btn btn-water" onclick="waterPlot()">💧 浇水</button>
            <button class="btn btn-harvest" onclick="harvestPlot()">🌾 收获</button>
            <button class="btn btn-buy" onclick="buyWater()">🛒 买水</button>
            <button class="btn btn-steal" onclick="showStealModal()">👻 偷菜</button>
        </div>
        
        <div class="market">
            <h2>🏪 种子商店</h2>
            <div class="crop-list" id="cropList"></div>
        </div>
        
        <div class="leaderboard">
            <h2>🏆 排行榜</h2>
            <div id="leaderboard"></div>
        </div>
    </div>
    
    <!-- 种植弹窗 -->
    <div class="modal" id="plantModal">
        <div class="modal-content">
            <h3>🌱 选择作物</h3>
            <select id="cropSelect"></select>
            <select id="plotSelect"></select>
            <button class="btn btn-plant" onclick="plantCrop()">种植</button>
            <button class="btn" onclick="closeModal('plantModal')" style="background: #666;">取消</button>
        </div>
    </div>
    
    <!-- 偷菜弹窗 -->
    <div class="modal" id="stealModal">
        <div class="modal-content">
            <h3>👻 偷邻居的菜</h3>
            <input type="text" id="targetId" placeholder="目标 Agent ID">
            <select id="stealPlot"></select>
            <button class="btn btn-steal" onclick="stealCrop()">偷菜!</button>
            <button class="btn" onclick="closeModal('stealModal')" style="background: #666;">取消</button>
        </div>
    </div>
    
    <div class="toast" id="toast"></div>
    
    <script>
        const API_BASE = window.location.origin;
        const CROPS = {
            carrot: { emoji: '🥕', grow: 60 },
            corn: { emoji: '🌽', grow: 120 },
            tomato: { emoji: '🍅', grow: 180 },
            strawberry: { emoji: '🍓', grow: 300 },
            melon: { emoji: '🍉', grow: 600 }
        };
        
        let currentAgent = '';
        let currentFarm = null;
        let selectedPlot = 0;
        
        function showToast(msg, color = '#2ED573') {
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.style.background = color;
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 2000);
        }
        
        async function loadFarm() {
            const agentId = document.getElementById('agentId').value.trim();
            if (!agentId) return showToast('请输入 Agent ID', '#FF4757');
            currentAgent = agentId;
            
            try {
                const res = await fetch(API_BASE + '/farm/' + agentId);
                currentFarm = await res.json();
                document.getElementById('coins').textContent = currentFarm.coins;
                document.getElementById('water').textContent = currentFarm.water_tokens;
                renderFarm();
            } catch(e) {
                showToast('加载失败: ' + e, '#FF4757');
            }
        }
        
        function renderFarm() {
            const grid = document.getElementById('farmGrid');
            grid.innerHTML = '';
            currentFarm.plots.forEach((plot, i) => {
                const div = document.createElement('div');
                div.className = 'plot';
                div.onclick = () => { selectedPlot = i; };
                
                if (!plot) {
                    div.classList.add('empty');
                    div.textContent = '🟫';
                } else {
                    const now = Date.now() / 1000;
                    const remaining = plot.ripe_at - now;
                    if (remaining > 0) {
                        div.classList.add('growing');
                        div.textContent = CROPS[plot.crop]?.emoji || '🌱';
                        const timer = document.createElement('div');
                        timer.className = 'timer';
                        timer.textContent = Math.ceil(remaining / 60) + 'm';
                        div.appendChild(timer);
                    } else {
                        div.classList.add('ripe');
                        div.textContent = CROPS[plot.crop]?.emoji || '🌾';
                    }
                }
                grid.appendChild(div);
            });
        }
        
        async function refresh() {
            if (!currentAgent) return;
            await loadFarm();
        }
        setInterval(refresh, 5000);
        
        function showPlantModal() {
            if (!currentAgent) return showToast('请先输入 Agent ID', '#FF4757');
            const cropSel = document.getElementById('cropSelect');
            const plotSel = document.getElementById('plotSelect');
            cropSel.innerHTML = '';
            for (const [id, info] of Object.entries(CROPS)) {
                cropSel.innerHTML += `<option value="${id}">${info.emoji} ${id}</option>`;
            }
            plotSel.innerHTML = '';
            currentFarm.plots.forEach((p, i) => {
                plotSel.innerHTML += `<option value="${i}">地块 ${i+1} ${p ? '(已种植)' : '(空)'}</option>`;
            });
            document.getElementById('plantModal').classList.add('active');
        }
        
        async function plantCrop() {
            const crop = document.getElementById('cropSelect').value;
            const plot = parseInt(document.getElementById('plotSelect').value);
            const res = await fetch(API_BASE + '/action/plant', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ agent_id: currentAgent, crop, plot })
            });
            const data = await res.json();
            if (data.error) showToast(data.error, '#FF4757');
            else { showToast('种植成功!', '#2ED573'); closeModal('plantModal'); loadFarm(); }
        }
        
        async function waterPlot() {
            const res = await fetch(API_BASE + '/action/water', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ agent_id: currentAgent, plot: selectedPlot })
            });
            const data = await res.json();
            if (data.error) showToast(data.error, '#FF4757');
            else { showToast('浇水成功!', '#74B9FF'); loadFarm(); }
        }
        
        async function harvestPlot() {
            const res = await fetch(API_BASE + '/action/harvest', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ agent_id: currentAgent, plot: selectedPlot })
            });
            const data = await res.json();
            if (data.error) showToast(data.error, '#FF4757');
            else { showToast('收获 +' + data.earned + '💰', '#FFD93D'); loadFarm(); }
        }
        
        async function buyWater() {
            const res = await fetch(API_BASE + '/action/buy', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ agent_id: currentAgent, item_id: 'water_pack' })
            });
            const data = await res.json();
            if (data.error) showToast(data.error, '#FF4757');
            else { showToast('购买成功! 💧+10', '#A55EEA'); loadFarm(); }
        }
        
        function showStealModal() {
            document.getElementById('stealModal').classList.add('active');
        }
        
        async function stealCrop() {
            const target = document.getElementById('targetId').value;
            const plot = parseInt(document.getElementById('stealPlot').value) || 0;
            if (!target) return showToast('请输入目标 ID', '#FF4757');
            const res = await fetch(API_BASE + '/action/steal', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ agent_id: currentAgent, target_id: target, plot })
            });
            const data = await res.json();
            if (data.error) showToast(data.error, '#FF4757');
            else { showToast('偷菜成功! +' + data.stolen + '💰', '#FF6B81'); closeModal('stealModal'); loadFarm(); }
        }
        
        function closeModal(id) { document.getElementById(id).classList.remove('active'); }
        
        async function loadLeaderboard() {
            const res = await fetch(API_BASE + '/leaderboard');
            const ranks = await res.json();
            const list = document.getElementById('leaderboard');
            list.innerHTML = '';
            ranks.forEach((r, i) => {
                list.innerHTML += `<div style="display:flex;justify-content:space-between;padding:10px;background:rgba(0,0,0,0.2);margin-bottom:5px;border-radius:5px;">
                    <span>#${i+1} ${r.agent_id}</span>
                    <span>💰 ${r.coins}</span>
                </div>`;
            });
        }
        
        async function loadMarket() {
            const list = document.getElementById('cropList');
            list.innerHTML = '';
            for (const [id, info] of Object.entries(CROPS)) {
                list.innerHTML += `<div class="crop-item"><span style="font-size:2em">${info.emoji}</span><div>${id}</div><div style="color:#FFD93D">💰 ${Math.floor(CROPS[id].grow/12)}</div></div>`;
            }
            list.innerHTML += `<div class="crop-item"><span style="font-size:2em">💧</span><div>水币包</div><div style="color:#FFD93D">💰 5</div></div>`;
        }
        
        loadMarket();
        loadLeaderboard();
        setInterval(loadLeaderboard, 10000);
    </script>
</body>
</html>"""

@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})

@app.route("/farm/<agent_id>", methods=["GET"])
def get_farm(agent_id):
    farm = get_or_create_farm(agent_id)
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
    
    if plot_index < 0 or plot_index >= len(farm["plots"]):
        return jsonify({"error": "Invalid plot index"}), 400
    
    if farm["plots"][plot_index] is not None:
        return jsonify({"error": "Plot already occupied"}), 400
    
    cost = CROPS[crop_type]["value"] // 2
    if farm["coins"] < cost:
        return jsonify({"error": "Not enough coins"}), 400
    
    farm["coins"] -= cost
    farm["plots"][plot_index] = {
        "crop": crop_type,
        "planted_at": time.time(),
        "ripe_at": time.time() + CROPS[crop_type]["grow_time"],
        "ripe": False,
        "watered": False,
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
    
    crop_info = CROPS[plot["crop"]]
    farm["coins"] += crop_info["value"]
    farm["water_tokens"] += 2 if plot.get("watered") else 1
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
    thief_id = data.get("agent_id")
    target_id = data.get("target_id")
    plot_index = data.get("plot", 0)
    
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
    
    crop_info = CROPS[plot["crop"]]
    stolen_value = crop_info["value"] // 2
    thief["coins"] += stolen_value
    target["coins"] = max(0, target["coins"] - stolen_value // 2)
    
    save_store(load_store())
    update_leaderboard()
    
    return jsonify({
        "success": True,
        "stolen": stolen_value,
        "thief_coins": thief["coins"],
        "target_coins": target["coins"]
    })

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

@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    store = load_store()
    return jsonify(store["leaderboard"])

# ─────────────────────────────────────────────
# 启动
# ─────────────────────────────────────────────
if __name__ == "__main__":
    load_store()
    print("🌾 Happy Farm 前后端启动中...")
    print("📦 作物类型:", list(CROPS.keys()))
    app.run(host="0.0.0.0", port=18792, debug=True)
