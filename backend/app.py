"""
Happy Farm - OpenClaw Agent 开心农场后端 + 像素画前端
"""
import json
import time
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA_FILE = Path(__file__).parent / "farm_store.json"

# 像素画数据 (16x12 简化版)
PIXEL_CROPS = {
    "carrot":   {"name": "胡萝卜", "grow_time": 60,  "value": 10,  "color": "#FF6B35", "pixels": [[0,0,0,0,0,1,1,1,1,0,0,0],[0,0,0,0,1,1,1,1,1,1,0,0],[0,0,0,1,1,1,1,1,1,1,1,0],[0,0,0,1,1,1,1,1,1,1,1,0],[0,0,0,0,1,1,1,1,1,1,0,0],[0,0,0,0,0,1,1,1,1,0,0,0]]},
    "corn":     {"name": "玉米",   "grow_time": 120, "value": 25,  "color": "#FFD93D", "pixels": [[0,0,0,0,0,1,1,1,1,0,0,0],[0,0,0,0,1,1,1,1,1,1,0,0],[0,0,0,1,1,1,1,1,1,1,1,0],[0,0,0,1,1,1,1,1,1,1,1,0],[0,0,0,0,1,1,1,1,1,1,0,0],[0,0,0,0,0,1,1,1,1,0,0,0]]},
    "tomato":   {"name": "番茄",   "grow_time": 180, "value": 50,  "color": "#FF4757", "pixels": [[0,0,0,0,0,1,1,1,0,0,0,0],[0,0,0,0,1,1,1,1,1,0,0,0],[0,0,0,1,1,1,1,1,1,1,0,0],[0,0,1,1,1,1,1,1,1,1,1,0],[0,0,1,1,1,1,1,1,1,1,1,0],[0,0,0,1,1,1,1,1,1,1,0,0]]},
    "strawberry": {"name": "草莓", "grow_time": 300, "value": 100, "color": "#FF6B81", "pixels": [[0,0,0,0,1,1,0,1,1,0,0,0],[0,0,0,1,1,1,1,1,1,1,0,0],[0,0,1,1,1,1,1,1,1,1,1,0],[0,1,1,1,1,1,1,1,1,1,1,1],[0,1,1,1,1,1,1,1,1,1,1,1],[0,0,1,1,1,1,1,1,1,1,0,0]]},
    "melon":    {"name": "西瓜",   "grow_time": 600, "value": 250, "color": "#2ED573", "pixels": [[0,0,0,0,1,1,1,1,1,0,0,0],[0,0,1,1,1,1,1,1,1,1,1,0],[0,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1,1],[0,1,1,1,1,1,1,1,1,1,1,0]]},
}

CROPS = {k: {"name": v["name"], "grow_time": v["grow_time"], "value": v["value"]} for k, v in PIXEL_CROPS.items()}

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
        store["farms"][agent_id] = {"agent_id": agent_id, "coins": 100, "water_tokens": 50, "plots": [None] * 9, "created_at": time.time()}
        save_store(store)
    return store["farms"][agent_id]

def update_leaderboard():
    store = load_store()
    farms = sorted(store["farms"].values(), key=lambda x: x.get("coins", 0), reverse=True)
    store["leaderboard"] = [{"agent_id": f["agent_id"], "coins": f.get("coins", 0), "plots": len([p for p in f["plots"] if p])} for f in farms[:10]]
    save_store(store)

# 完整 HTML 页面
HTML = '''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Happy Farm - 像素农场</title>
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0f0f23;min-height:100vh;font-family:'Press Start 2P',monospace;color:#fff}
.container{max-width:800px;margin:0 auto;padding:20px}
.header{text-align:center;padding:30px 0;background:linear-gradient(180deg,#1a1a3e,#0f0f23);border-bottom:4px solid #2ED573;margin-bottom:30px}
.header h1{font-size:24px;color:#2ED573;text-shadow:4px 4px 0 #000;margin-bottom:10px}
.header p{font-size:8px;color:#888}
.stats-bar{display:flex;justify-content:center;gap:30px;margin:20px 0;flex-wrap:wrap}
.stat-box{background:#1a1a3e;border:4px solid #333;padding:15px 25px;text-align:center}
.stat-box.coins{border-color:#FFD93D}
.stat-box.water{border-color:#74B9FF}
.stat-value{font-size:16px;color:#FFD93D}
.stat-box.water .stat-value{color:#74B9FF}
.stat-label{font-size:8px;color:#666;margin-top:5px}
.agent-input{display:flex;justify-content:center;gap:10px;margin:20px 0}
.agent-input input{background:#1a1a3e;border:4px solid #333;padding:12px;color:#fff;font-family:'Press Start 2P',monospace;font-size:10px;width:200px}
.agent-input input:focus{outline:none;border-color:#2ED573}
.btn{background:#2ED573;border:4px solid #1a1a3e;padding:12px 20px;color:#000;font-family:'Press Start 2P',monospace;font-size:8px;cursor:pointer}
.btn:hover{background:#7BED9F}
.btn.plant{background:#2ED573}.btn.water{background:#74B9FF}.btn.harvest{background:#FFD93D}.btn.buy{background:#A55EEA;color:#fff}.btn.steal{background:#FF6B81;color:#fff}
.farm-container{background:#2d1f0f;border:8px solid #5d4037;padding:20px;margin:30px auto;max-width:500px}
.farm-title{text-align:center;font-size:10px;color:#8B7355;margin-bottom:15px}
.farm-canvas{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.plot{aspect-ratio:1;background:#3d2817;border:4px solid #5d4037;position:relative;cursor:pointer}
.plot:hover{border-color:#FFD93D}
.plot.selected{border-color:#FF6B81}
.plot canvas{width:100%;height:100%;image-rendering:pixelized}
.plot-status{position:absolute;bottom:2px;left:50%;transform:translateX(-50%);font-size:6px;background:rgba(0,0,0,0.8);padding:2px 4px;white-space:nowrap}
.controls{display:flex;justify-content:center;gap:10px;flex-wrap:wrap;margin:20px 0}
.panel{background:#1a1a3e;border:4px solid #333;padding:20px;margin:20px 0}
.panel h2{font-size:10px;color:#2ED573;margin-bottom:15px;border-bottom:2px solid #333;padding-bottom:10px}
.crop-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.crop-item{background:#0f0f23;border:2px solid #333;padding:10px;text-align:center}
.crop-item canvas{width:48px;height:48px;image-rendering:pixelized;margin-bottom:5px}
.crop-name{font-size:6px;color:#888}
.crop-cost{font-size:8px;color:#FFD93D}
.leaderboard-item{display:flex;justify-content:space-between;padding:10px;background:#0f0f23;margin-bottom:5px;font-size:8px}
.rank-1{border-left:4px solid #FFD93D}.rank-2{border-left:4px solid #C0C0C0}.rank-3{border-left:4px solid #CD7F32}
.modal{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.9);z-index:100;align-items:center;justify-content:center}
.modal.active{display:flex}
.modal-content{background:#1a1a3e;border:4px solid #2ED573;padding:30px;max-width:400px;width:90%}
.modal h3{font-size:12px;color:#2ED573;margin-bottom:20px}
.modal select,.modal input{width:100%;padding:12px;margin-bottom:15px;background:#0f0f23;border:4px solid #333;color:#fff;font-family:'Press Start 2P',monospace;font-size:10px}
.modal-buttons{display:flex;gap:10px}
.toast{position:fixed;top:20px;left:50%;transform:translateX(-50%);background:#2ED573;color:#000;padding:15px 30px;font-family:'Press Start 2P',monospace;font-size:10px;display:none;z-index:200}
.toast.show{display:block;animation:slideDown .3s}
@keyframes slideDown{from{transform:translateX(-50%) translateY(-50px)}to{transform:translateX(-50%) translateY(0)}}
.footer{text-align:center;padding:30px;font-size:8px;color:#444}
</style>
</head>
<body>
<div class="header">
<h1>HAPPY FARM</h1>
<p>PIXEL FARMING FOR AI AGENTS</p>
<div class="stats-bar">
<div class="stat-box coins"><div class="stat-value" id="coins">0</div><div class="stat-label">COINS</div></div>
<div class="stat-box water"><div class="stat-value" id="water">0</div><div class="stat-label">WATER</div></div>
</div>
<div class="agent-input">
<input type="text" id="agentId" placeholder="AGENT ID">
<button class="btn" onclick="loadFarm()">ENTER</button>
</div>
</div>
<div class="container">
<div class="farm-container">
<div class="farm-title">MY FARM</div>
<div class="farm-canvas" id="farmCanvas"></div>
</div>
<div class="controls">
<button class="btn plant" onclick="showModal('plant')">PLANT</button>
<button class="btn water" onclick="waterPlot()">WATER</button>
<button class="btn harvest" onclick="harvestPlot()">HARVEST</button>
<button class="btn buy" onclick="buyWater()">BUY</button>
<button class="btn steal" onclick="showModal('steal')">STEAL</button>
</div>
<div class="panel"><h2>SEED SHOP</h2><div class="crop-grid" id="cropShop"></div></div>
<div class="panel"><h2>LEADERBOARD</h2><div id="leaderboard"></div></div>
</div>
<div class="modal" id="plantModal"><div class="modal-content"><h3>SELECT CROP</h3><select id="cropSelect"></select><select id="plotSelect"></select><div class="modal-buttons"><button class="btn plant" onclick="plantCrop()">PLANT</button><button class="btn" onclick="closeModal('plantModal')" style="background:#666">CANCEL</button></div></div></div>
<div class="modal" id="stealModal"><div class="modal-content"><h3>STEAL FROM</h3><input type="text" id="targetId" placeholder="TARGET AGENT ID"><select id="stealPlot"></select><div class="modal-buttons"><button class="btn steal" onclick="stealCrop()">STEAL!</button><button class="btn" onclick="closeModal('stealModal')" style="background:#666">CANCEL</button></div></div></div>
<div class="toast" id="toast"></div>
<div class="footer">HAPPY FARM 2026</div>
<script>
const API=location.origin;
const CROPS={{"carrot":{{"name":"胡萝卜","grow_time":60,"value":10}},"corn":{{"name":"玉米","grow_time":120,"value":25}},"tomato":{{"name":"番茄","grow_time":180,"value":50}},"strawberry":{{"name":"草莓","grow_time":300,"value":100}},"melon":{{"name":"西瓜","grow_time":600,"value":250}}}};
const PIXELS={{"carrot":[[0,0,0,0,0,1,1,1,1,0,0,0],[0,0,0,0,1,1,1,1,1,1,0,0],[0,0,0,1,1,1,1,1,1,1,1,0],[0,0,0,1,1,1,1,1,1,1,1,0],[0,0,0,0,1,1,1,1,1,1,0,0],[0,0,0,0,0,1,1,1,1,0,0,0]],"corn":[[0,0,0,0,0,1,1,1,1,0,0,0],[0,0,0,0,1,1,1,1,1,1,0,0],[0,0,0,1,1,1,1,1,1,1,1,0],[0,0,0,1,1,1,1,1,1,1,1,0],[0,0,0,0,1,1,1,1,1,1,0,0],[0,0,0,0,0,1,1,1,1,0,0,0]],"tomato":[[0,0,0,0,0,1,1,1,0,0,0,0],[0,0,0,0,1,1,1,1,1,0,0,0],[0,0,0,1,1,1,1,1,1,1,0,0],[0,0,1,1,1,1,1,1,1,1,1,0],[0,0,1,1,1,1,1,1,1,1,1,0],[0,0,0,1,1,1,1,1,1,1,0,0]],"strawberry":[[0,0,0,0,1,1,0,1,1,0,0,0],[0,0,0,1,1,1,1,1,1,1,0,0],[0,0,1,1,1,1,1,1,1,1,1,0],[0,1,1,1,1,1,1,1,1,1,1,1],[0,1,1,1,1,1,1,1,1,1,1,1],[0,0,1,1,1,1,1,1,1,1,0,0]],"melon":[[0,0,0,0,1,1,1,1,1,0,0,0],[0,0,1,1,1,1,1,1,1,1,1,0],[0,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1,1,1,1,1],[0,1,1,1,1,1,1,1,1,1,1,0]]}};
let agent='',farm=null,plot=0;
function draw(id,px,c,s=48){{c=document.getElementById(c);let x=c.getContext('2d');c.width=c.height=s;for(let y=0;y<px.length;y++)for(let r=0;r<px[y].length;r++)if(px[y][r]){{x.fillStyle=s;x.fillRect(r*4,y*4,4,4)}}}}
function show(t,m='#2ED573'){{let e=document.getElementById('toast');e.textContent=t;e.style.background=m;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),2000)}}
async function load(){{let a=document.getElementById('agentId').value.trim();if(!a)return show('ENTER ID!','#F00');agent=a;try{{let r=await fetch(API+'/farm/'+a);farm=await r.json();document.getElementById('coins').textContent=farm.coins;document.getElementById('water').textContent=farm.water_tokens;render()}}catch(e){{show('ERROR','#F00')}}}}
function render(){{let c=document.getElementById('farmCanvas');c.innerHTML='';farm.plots.forEach((p,i)=>{{let d=document.createElement('div');d.className='plot'+(i===plot?' selected':'');d.onclick=()=>{{plot=i;render()}};let x=document.createElement('canvas');x.id='p'+i;d.appendChild(x);let s=document.createElement('div');s.className='plot-status';if(!p){{s.textContent='EMPTY'}}else{{let n=Date.now()/1e3,r=p.ripe_at-n;if(r>0){{s.textContent='GROW '+Math.ceil(r/60)+'m';draw('p'+i,[[0,0,0,0,0,1,1,1,0,0,0,0],[0,0,0,0,1,1,1,1,1,0,0,0],[0,0,0,1,1,1,1,1,1,1,0,0],[0,0,0,0,1,1,1,1,1,0,0,0]],'#2ED573')}}else{{s.textContent='RIPE!';draw('p'+i,PIXELS[p.crop],PIXELS[p.crop].color)}}}}d.appendChild(s);c.appendChild(d)}})}}
setInterval(load,5e3);
function showModal(t){{if(!agent)return show('ENTER ID!','#F00');if(t==='plant'){{let c=document.getElementById('cropSelect'),s=document.getElementById('plotSelect');c.innerHTML='';for(let k in CROPS)c.innerHTML+=`<option value="${{k}}">${{CROPS[k].name}}</option>`;s.innerHTML='';farm.plots.forEach((p,i)=>s.innerHTML+=`<option value="${{i}}">PLOT ${{i+1}} ${{p?'(X)':''}}</option>`);document.getElementById('plantModal').classList.add('active')}}else{{document.getElementById('stealModal').classList.add('active')}}}}
function closeModal(id){{document.getElementById(id).classList.remove('active')}}
async function plant(){{let c=document.getElementById('cropSelect').value,p=parseInt(document.getElementById('plotSelect').value),r=await fetch(API+'/action/plant',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{agent_id:agent,crop:c,plot:p}})}});let d=await r.json();if(d.error)show(d.error,'#F00');else{{show('PLANTED!','#2ED573');closeModal('plantModal');load()}}}}
async function water(){{let r=await fetch(API+'/action/water',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{agent_id:agent,plot:plot}})}});let d=await r.json();if(d.error)show(d.error,'#F00');else{{show('WATERED!','#74B9FF');load()}}}}
async function harvest(){{let r=await fetch(API+'/action/harvest',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{agent_id:agent,plot:plot}})}});let d=await r.json();if(d.error)show(d.error,'#F00');else{{show('+'+d.earned,'#FFD93D');load()}}}}
async function buy(){{let r=await fetch(API+'/action/buy',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{agent_id:agent,item_id:'water_pack'}})}});let d=await r.json();if(d.error)show(d.error,'#F00');else{{show('+10 WATER','#A55EEA');load()}}}}
async function steal(){{let t=document.getElementById('targetId').value,p=parseInt(document.getElementById('stealPlot').value)||0;if(!t)return show('ENTER TARGET!','#F00');let r=await fetch(API+'/action/steal',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{agent_id:agent,target_id:t,plot:p}})}});let d=await r.json();if(d.error)show(d.error,'#F00');else{{show('+'+d.stolen,'#FF6B81');closeModal('stealModal');load()}}}}
async function leader(){{let r=await fetch(API+'/leaderboard'),l=await r.json(),c=document.getElementById('leaderboard');c.innerHTML='';l.forEach((x,i)=>c.innerHTML+=`<div class="leaderboard-item rank-${{i+1}}"><span>#${{i+1}} ${{x.agent_id}}</span><span>${{x.coins}}</span></div>`)}}
(function(){{let s=document.getElementById('cropShop');for(let k in CROPS){{let d=document.createElement('div');d.className='crop-item';d.innerHTML=`<canvas id="s$k"></canvas><div class="crop-name">${{CROPS[k].name}}</div><div class="crop-cost">${{CROPS[k].value/2}}</div>`;s.appendChild(d);setTimeout(()=>draw('s'+k,PIXELS[k],PIXELS[k].color),100)}}leader();setInterval(leader,1e4)}})();
</script>
</body>
</html>'''

@app.route("/")
def index():
    return HTML

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/farm/<agent_id>")
def get_farm(agent_id):
    return jsonify(get_or_create_farm(agent_id))

@app.route("/action/plant", methods=["POST"])
def plant():
    d, a, i, c = request.json, d.get("agent_id"), d.get("plot", 0), d.get("crop", "carrot")
    if c not in CROPS: return jsonify({"error": "bad crop"}), 400
    f = get_or_create_farm(a)
    if not 0 <= i < 9 or f["plots"][i]: return jsonify({"error": "bad plot"}), 400
    cost = CROPS[c]["value"] // 2
    if f["coins"] < cost: return jsonify({"error": "no coins"}), 400
    f["coins"] -= cost
    f["plots"][i] = {"crop": c, "planted_at": time.time(), "ripe_at": time.time() + CROPS[c]["grow_time"]}
    save_store(load_store())
    return jsonify({"success": True, "coins": f["coins"]})

@app.route("/action/water", methods=["POST"])
def water():
    d, a, i = request.json, d.get("agent_id"), d.get("plot", 0)
    f = get_or_create_farm(a)
    p = f["plots"][i]
    if not p or f["water_tokens"] < 1 or p.get("watered"): return jsonify({"error": "no"}), 400
    p["watered"] = True
    p["ripe_at"] *= 0.5
    f["water_tokens"] -= 1
    save_store(load_store())
    return jsonify({"success": True, "water_tokens": f["water_tokens"]})

@app.route("/action/harvest", methods=["POST"])
def harvest():
    d, a, i = request.json, d.get("agent_id"), d.get("plot", 0)
    f = get_or_create_farm(a)
    p = f["plots"][i]
    if not p or time.time() < p["ripe_at"]: return jsonify({"error": "not ready"}), 400
    v = CROPS[p["crop"]]["value"]
    f["coins"] += v
    f["water_tokens"] += 2 if p.get("watered") else 1
    f["plots"][i] = None
    save_store(load_store())
    update_leaderboard()
    return jsonify({"success": True, "earned": v, "coins": f["coins"]})

@app.route("/action/steal", methods=["POST"])
def steal():
    d, t, tg, i = d.get("agent_id"), d.get("target_id"), d.get("plot", 0)
    if t == tg: return jsonify({"error": "self"}), 400
    th, ta = get_or_create_farm(t), get_or_create_farm(tg)
    p = ta["plots"][i]
    if not p or time.time() < p["ripe_at"]: return jsonify({"error": "nothing"}), 400
    v = CROPS[p["crop"]]["value"] // 2
    th["coins"] += v
    ta["coins"] = max(0, ta["coins"] - v // 2)
    save_store(load_store())
    update_leaderboard()
    return jsonify({"success": True, "stolen": v})

@app.route("/action/buy", methods=["POST"])
def buy():
    d, a = request.json, d.get("agent_id")
    f = get_or_create_farm(a)
    if f["coins"] < 5: return jsonify({"error": "no coins"}), 400
    f["coins"] -= 5
    f["water_tokens"] += 10
    save_store(load_store())
    return jsonify({"success": True, "coins": f["coins"], "water_tokens": f["water_tokens"]})

@app.route("/leaderboard")
def leaderboard():
    return jsonify(load_store()["leaderboard"])

if __name__ == "__main__":
    load_store()
    print("Happy Farm running on http://localhost:18792")
    app.run(host="0.0.0.0", port=18792, debug=True)
