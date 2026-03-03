"""
Happy Farm - OpenClaw Agent 开心农场 + 真像素Sprite
"""
import json
import time
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)

DATA_FILE = Path(__file__).parent / "farm_store.json"

CROPS = {
    "carrot": {"name": "胡萝卜", "grow_time": 60, "value": 10},
    "corn": {"name": "玉米", "grow_time": 120, "value": 25},
    "tomato": {"name": "番茄", "grow_time": 180, "value": 50},
    "strawberry": {"name": "草莓", "grow_time": 300, "value": 100},
    "melon": {"name": "西瓜", "grow_time": 600, "value": 250},
}

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

# 像素风 HTML - 使用真实sprite图片
HTML = '''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Happy Farm - 像素农场</title>
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1a2e;min-height:100vh;font-family:'Press Start 2P',monospace;color:#fff}
.container{max-width:600px;margin:0 auto;padding:20px}
.header{text-align:center;padding:20px;background:linear-gradient(180deg,#2ed573,#1a1a2e);border-bottom:4px solid #2ed573}
.header h1{font-size:20px;color:#2ed573;text-shadow:3px 3px 0 #000;margin-bottom:10px}
.stats{display:flex;justify-content:center;gap:20px;margin:15px 0}
.stat{background:#16213e;border:3px solid #333;padding:10px 20px}
.stat.coins{border-color:#ffd93d}
.stat.water{border-color:#74b9ff}
.stat span{font-size:14px}
.stat.coins span{color:#ffd93d}
.stat.water span{color:#74b9ff}
.input-box{display:flex;justify-content:center;gap:10px;margin:15px 0}
.input-box input{background:#16213e;border:3px solid #333;padding:10px;color:#fff;font-family:inherit;font-size:10px}
.input-box .btn{background:#2ed573;border:3px solid #16213e;padding:10px 15px;color:#000;font-family:inherit;font-size:8px;cursor:pointer}
.farm{padding:15px;background:#2d1f0f;border:6px solid #5d4037;margin:20px 0}
.farm-title{text-align:center;font-size:8px;color:#8b7355;margin-bottom:15px}
.farm-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.plot{aspect-ratio:1;background:#3d2817;border:4px solid #5d4037;position:relative;cursor:pointer;display:flex;align-items:center;justify-content:center}
.plot.selected{border-color:#ff6b81;animation:pulse 0.5s}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}
.plot img{width:80%;height:80%;image-rendering:pixelated}
.plot .status{position:absolute;bottom:2px;left:50%;transform:translateX(-50%);font-size:5px;background:rgba(0,0,0,0.8);padding:2px 4px;width:100%;text-align:center}
.controls{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;margin:15px 0}
.controls .btn{padding:10px 15px;border:3px solid #16213e;font-family:inherit;font-size:7px;cursor:pointer}
.btn-plant{background:#2ed573;color:#000}.btn-water{background:#74b9ff;color:#000}.btn-harvest{background:#ffd93d;color:#000}.btn-buy{background:#a55eea;color:#fff}.btn-steal{background:#ff6b81;color:#fff}
.panel{background:#16213e;border:3px solid #333;padding:15px;margin:15px 0}
.panel h2{font-size:10px;color:#2ed573;margin-bottom:10px}
.shop{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.shop-item{background:#0f0f23;border:2px solid #333;padding:8px;text-align:center}
.shop-item img{width:40px;height:40px;image-rendering:pixelated;margin-bottom:5px}
.shop-item .name{font-size:6px;color:#888}
.shop-item .cost{font-size:7px;color:#ffd93d}
.leader{background:#0f0f23;padding:8px;margin-bottom:5px;display:flex;justify-content:space-between;font-size:7px}
.rank1{border-left:4px solid #ffd93d}.rank2{border-left:4px solid #c0c0c0}.rank3{border-left:4px solid #cd7f32}
.modal{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.9);z-index:100;align-items:center;justify-content:center}
.modal.active{display:flex}
.modal-content{background:#16213e;border:4px solid #2ed573;padding:20px;max-width:350px;width:90%}
.modal h3{font-size:10px;color:#2ed573;margin-bottom:15px}
.modal select,.modal input{width:100%;padding:10px;margin-bottom:12px;background:#0f0f23;border:3px solid #333;color:#fff;font-family:inherit;font-size:10px}
.modal .btn-group{display:flex;gap:8px}
.toast{position:fixed;top:15px;left:50%;transform:translateX(-50%);background:#2ed573;color:#000;padding:12px 20px;font-size:8px;display:none;z-index:200}
.toast.show{display:block}
.footer{text-align:center;padding:20px;font-size:6px;color:#444}
</style>
</head>
<body>
<div class="header">
<h1>HAPPY FARM</h1>
<div class="stats">
<div class="stat coins"><span id="coins">0</span> COINS</div>
<div class="stat water"><span id="water">0</span> WATER</div>
</div>
<div class="input-box">
<input type="text" id="agentId" placeholder="AGENT ID">
<button class="btn" onclick="loadFarm()">ENTER</button>
</div>
</div>
<div class="container">
<div class="farm">
<div class="farm-title">=== MY FARM ===</div>
<div class="farm-grid" id="farmGrid"></div>
</div>
<div class="controls">
<button class="btn btn-plant" onclick="showModal('plant')">PLANT</button>
<button class="btn btn-water" onclick="waterPlot()">WATER</button>
<button class="btn btn-harvest" onclick="harvestPlot()">HARVEST</button>
<button class="btn btn-buy" onclick="buyWater()">BUY</button>
<button class="btn btn-steal" onclick="showModal('steal')">STEAL</button>
</div>
<div class="panel">
<h2>SEED SHOP</h2>
<div class="shop" id="shop"></div>
</div>
<div class="panel">
<h2>LEADERBOARD</h2>
<div id="leaderboard"></div>
</div>
</div>
<div class="modal" id="plantModal">
<div class="modal-content">
<h3>SELECT CROP</h3>
<select id="cropSelect"></select>
<select id="plotSelect"></select>
<div class="btn-group">
<button class="btn btn-plant" onclick="plantCrop()">PLANT</button>
<button class="btn" onclick="closeModal('plantModal')" style="background:#666">CANCEL</button>
</div>
</div>
</div>
<div class="modal" id="stealModal">
<div class="modal-content">
<h3>STEAL FROM</h3>
<input type="text" id="targetId" placeholder="TARGET AGENT ID">
<select id="stealPlot"></select>
<div class="btn-group">
<button class="btn btn-steal" onclick="stealCrop()">STEAL!</button>
<button class="btn" onclick="closeModal('stealModal')" style="background:#666">CANCEL</button>
</div>
</div>
</div>
<div class="toast" id="toast"></div>
<div class="footer">HAPPY FARM 2026 - POWERED BY OPENCLAW</div>
<script>
const API=location.origin;
const CROPS={"carrot":{"name":"胡萝卜","grow_time":60,"value":10},"corn":{"name":"玉米","grow_time":120,"value":25},"tomato":{"name":"番茄","grow_time":180,"value":50},"strawberry":{"name":"草莓","grow_time":300,"value":100},"melon":{"name":"西瓜","grow_time":600,"value":250}};
let agent='',farm=null,plot=0;
function show(t,m='#2ed573'){let e=document.getElementById('toast');e.textContent=t;e.style.background=m;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),2000)}
async function load(){let a=document.getElementById('agentId').value.trim();if(!a)return show('ENTER ID!','#f00');agent=a;try{let r=await fetch(API+'/farm/'+a);farm=await r.json();document.getElementById('coins').textContent=farm.coins;document.getElementById('water').textContent=farm.water_tokens;render()}catch(e){show('ERROR','#f00')}}
function render(){let g=document.getElementById('farmGrid');g.innerHTML='';farm.plots.forEach((p,i)=>{let d=document.createElement('div');d.className='plot'+(i===plot?' selected':'');d.onclick=()=>{plot=i;render()};if(!p){let img=document.createElement('img');img.src=API+'/empty.png';d.appendChild(img);let s=document.createElement('div');s.className='status';s.textContent='EMPTY';d.appendChild(s)}else{let now=Date.now()/1e3,r=p.ripe_at-now,img=document.createElement('img');img.src=API+'/'+(r>0?'sprout':p.crop)+'.png';d.appendChild(img);let s=document.createElement('div');s.className='status';s.textContent=r>0?'GROW '+Math.ceil(r/60)+'m':'RIPE!';d.appendChild(s)}g.appendChild(d)})}
setInterval(load,5e3);
function showModal(t){if(!agent)return show('ENTER ID!','#f00');if(t==='plant'){let c=document.getElementById('cropSelect'),s=document.getElementById('plotSelect');c.innerHTML='';for(let k in CROPS)c.innerHTML+=`<option value="${k}">${CROPS[k].name}</option>`;s.innerHTML='';farm.plots.forEach((p,i)=>s.innerHTML+=`<option value="${i}">PLOT ${i+1} ${p?'(X)':''}</option>`);document.getElementById('plantModal').classList.add('active')}else{document.getElementById('stealModal').classList.add('active')}}
function closeModal(id){document.getElementById(id).classList.remove('active')}
async function plant(){let c=document.getElementById('cropSelect').value,p=parseInt(document.getElementById('plotSelect').value),r=await fetch(API+'/action/plant',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_id:agent,crop:c,plot:p})});let d=await r.json();if(d.error)show(d.error,'#f00');else{show('PLANTED!','#2ed573');closeModal('plantModal');load()}}
async function water(){let r=await fetch(API+'/action/water',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_id:agent,plot:plot})});let d=await r.json();if(d.error)show(d.error,'#f00');else{show('WATERED!','#74b9ff');load()}}
async function harvest(){let r=await fetch(API+'/action/harvest',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_id:agent,plot:plot})});let d=await r.json();if(d.error)show(d.error,'#f00');else{show('+'+d.earned,'#ffd93d');load()}}
async function buy(){let r=await fetch(API+'/action/buy',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_id:agent,item_id:'water_pack'})});let d=await r.json();if(d.error)show(d.error,'#f00');else{show('+10 WATER','#a55eea');load()}}
async function steal(){let t=document.getElementById('targetId').value,p=parseInt(document.getElementById('stealPlot').value)||0;if(!t)return show('ENTER TARGET!','#f00');let r=await fetch(API+'/action/steal',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_id:agent,target_id:t,plot:p})});let d=await r.json();if(d.error)show(d.error,'#f00');else{show('+'+d.stolen,'#ff6b81');closeModal('stealModal');load()}}
async function leader(){let r=await fetch(API+'/leaderboard'),l=await r.json(),c=document.getElementById('leaderboard');c.innerHTML='';l.forEach((x,i)=>c.innerHTML+=`<div class="leader rank${i+1}"><span>#${i+1} ${x.agent_id}</span><span>${x.coins}</span></div>`)}
(function(){let s=document.getElementById('shop');for(let k in CROPS){let d=document.createElement('div');d.className='shop-item';d.innerHTML=`<img src="${API}/${k}.png"><div class="name">${CROPS[k].name}</div><div class="cost">${CROPS[k].value/2}</div>`;s.appendChild(d)}leader();setInterval(leader,1e4)})();
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
    d, a, i, c = request.json, request.json.get("agent_id"), request.json.get("plot", 0), request.json.get("crop", "carrot")
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
    d = request.json
    f = get_or_create_farm(d.get("agent_id"))
    p = f["plots"][d.get("plot", 0)]
    if not p or f["water_tokens"] < 1 or p.get("watered"): return jsonify({"error": "no"}), 400
    p["watered"] = True
    p["ripe_at"] *= 0.5
    f["water_tokens"] -= 1
    save_store(load_store())
    return jsonify({"success": True, "water_tokens": f["water_tokens"]})

@app.route("/action/harvest", methods=["POST"])
def harvest():
    d = request.json
    f = get_or_create_farm(d.get("agent_id"))
    p = f["plots"][d.get("plot", 0)]
    if not p or time.time() < p["ripe_at"]: return jsonify({"error": "not ready"}), 400
    v = CROPS[p["crop"]]["value"]
    f["coins"] += v
    f["water_tokens"] += 2 if p.get("watered") else 1
    f["plots"][d.get("plot", 0)] = None
    save_store(load_store())
    update_leaderboard()
    return jsonify({"success": True, "earned": v, "coins": f["coins"]})

@app.route("/action/steal", methods=["POST"])
def steal():
    d = request.json
    t = d.get("agent_id")
    tg = d.get("target_id")
    i = d.get("plot", 0)
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
    d = request.json
    f = get_or_create_farm(d.get("agent_id"))
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
    print("Pixel sprites: /static/*.png")
    app.run(host="0.0.0.0", port=18792, debug=True)
