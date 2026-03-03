"""
Happy Farm - OpenClaw Agent 开心农场 + Canvas游戏级渲染
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

# Canvas游戏级HTML
HTML = '''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Happy Farm - 像素农场</title>
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0f0f23;min-height:100vh;font-family:'Press Start 2P',monospace;color:#fff;display:flex;flex-direction:column;align-items:center}
#game-container{position:relative;margin:20px 0}
#game-canvas{border:4px solid #5d4037;image-rendering:pixelated;background:#1a1a2e}
#loading{position:fixed;top:0;left:0;width:100%;height:100%;background:#0f0f23;display:flex;flex-direction:column;justify-content:center;align-items:center;z-index:1000}
#loading h2{color:#2ed573;font-size:16px;margin-bottom:20px}
#loading-bar{width:300px;height:20px;background:#333;border:2px solid #555}
#loading-progress{height:100%;background:linear-gradient(90deg,#e94560,#ffd700);width:0%;transition:width .3s}
.input-bar{display:flex;gap:10px;margin:15px 0;align-items:center}
.input-bar input{background:#1a1a3e;border:3px solid #333;padding:12px;color:#fff;font-family:inherit;font-size:12px}
.input-bar .btn{background:#2ed573;border:3px solid #16213e;padding:12px 20px;color:#000;font-family:inherit;font-size:10px;cursor:pointer}
.input-bar .btn:hover{background:#7bed9f}
.controls{display:flex;gap:10px;margin:15px 0;flex-wrap:wrap;justify-content:center}
.controls .btn{padding:15px 25px;border:3px solid #16213e;font-family:inherit;font-size:10px;cursor:pointer}
.btn-plant{background:#2ed573;color:#000}.btn-water{background:#74b9ff;color:#000}.btn-harvest{background:#ffd93d;color:#000}.btn-buy{background:#a55eea;color:#fff}.btn-steal{background:#ff6b81;color:#fff}
.bottom-panels{display:flex;gap:20px;width:800px;max-width:95vw;margin-top:20px}
.panel{flex:1;background:#16213e;border:3px solid #333;padding:15px}
.panel h3{color:#2ed573;font-size:10px;margin-bottom:10px;border-bottom:2px solid #333;padding-bottom:8px}
.shop-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.shop-item{background:#0f0f23;border:2px solid #333;padding:10px;text-align:center}
.shop-item img{width:48px;height:48px;image-rendering:pixelated;margin-bottom:5px}
.shop-item .name{font-size:7px;color:#888}
.shop-item .cost{font-size:8px;color:#ffd93d}
.leader-item{display:flex;justify-content:space-between;padding:8px;background:#0f0f23;margin-bottom:4px;font-size:8px}
.rank1{border-left:4px solid #ffd93d}.rank2{border-left:4px solid #c0c0c0}.rank3{border-left:4px solid #cd7f32}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);z-index:200;justify-content:center;align-items:center}
.modal.active{display:flex}
.modal-content{background:#16213e;border:4px solid #2ed573;padding:25px;max-width:350px;width:90%}
.modal h3{color:#2ed573;font-size:12px;margin-bottom:15px}
.modal select,.modal input{width:100%;padding:12px;margin-bottom:12px;background:#0f0f23;border:3px solid #333;color:#fff;font-family:inherit;font-size:10px}
.modal-btns{display:flex;gap:10px}
.toast{position:fixed;top:20px;left:50%;transform:translateX(-50%);background:#2ed573;color:#000;padding:15px 25px;font-size:10px;display:none;z-index:300}
.toast.show{display:block}
.footer{color:#444;font-size:8px;margin:20px 0}
</style>
</head>
<body>
<div id="loading"><h2>LOADING SPRITES...</h2><div id="loading-bar"><div id="loading-progress"></div></div></div>
<div id="game-container"><canvas id="game-canvas"></canvas></div>
<div class="input-bar">
<input type="text" id="agentId" placeholder="AGENT ID" value="test-agent">
<button class="btn" onclick="loadFarm()">ENTER FARM</button>
</div>
<div class="controls">
<button class="btn btn-plant" onclick="showModal('plant')">PLANT</button>
<button class="btn btn-water" onclick="waterPlot()">WATER</button>
<button class="btn btn-harvest" onclick="harvestPlot()">HARVEST</button>
<button class="btn btn-buy" onclick="buyWater()">BUY</button>
<button class="btn btn-steal" onclick="showModal('steal')">STEAL</button>
</div>
<div class="bottom-panels">
<div class="panel"><h3>SEED SHOP</h3><div class="shop-grid" id="shop"></div></div>
<div class="panel"><h3>LEADERBOARD</h3><div id="leaderboard"></div></div>
</div>
<div class="modal" id="plantModal">
<div class="modal-content"><h3>SELECT CROP</h3>
<select id="cropSelect"></select><select id="plotSelect"></select>
<div class="modal-btns"><button class="btn btn-plant" onclick="plantCrop()">PLANT</button><button class="btn" onclick="closeModal('plantModal')" style="background:#666">CANCEL</button></div></div></div>
<div class="modal" id="stealModal">
<div class="modal-content"><h3>STEAL FROM</h3>
<input type="text" id="targetId" placeholder="TARGET AGENT ID"><select id="stealPlot"></select>
<div class="modal-btns"><button class="btn btn-steal" onclick="stealCrop()">STEAL!</button><button class="btn" onclick="closeModal('stealModal')" style="background:#666">CANCEL</button></div></div></div>
<div class="toast" id="toast"></div>
<div class="footer">HAPPY FARM 2026 - PIXEL EDITION</div>

<script>
// Sprite loading
const spriteUrls = {
    'carrot_0':'/carrot_0.png','carrot_1':'/carrot_1.png','carrot_2':'/carrot_2.png',
    'corn_0':'/corn_0.png','corn_1':'/corn_1.png','corn_2':'/corn_2.png',
    'tomato_0':'/tomato_0.png','tomato_1':'/tomato_1.png','tomato_2':'/tomato_2.png',
    'strawberry_0':'/strawberry_0.png','strawberry_1':'/strawberry_1.png','strawberry_2':'/strawberry_2.png',
    'melon_0':'/melon_0.png','melon_1':'/melon_1.png','melon_2':'/melon_2.png',
    'empty':'/empty.png'
};
const sprites={};
let loaded=0,total=Object.keys(spriteUrls).length;

function loadSprite(name,url){
    const img=new Image();
    img.onload=()=>{sprites[name]=img;loaded++;document.getElementById('loading-progress').style.width=(loaded/total*100)+'%';if(loaded===total)startGame()};
    img.onerror=()=>{loaded++;if(loaded===total)startGame()};
    img.src=url;
}

Object.entries(spriteUrls).forEach(([n,u])=>loadSprite(n,u));

// Game state
let agent='',farm=null,selectedPlot=0;
const API=location.origin;
const CROPS_DATA={"carrot":{"name":"胡萝卜","grow_time":60,"value":10},"corn":{"name":"玉米","grow_time":120,"value":25},"tomato":{"name":"番茄","grow_time":180,"value":50},"strawberry":{"name":"草莓","grow_time":300,"value":100},"melon":{"name":"西瓜","grow_time":600,"value":250}};

// Canvas
const canvas=document.getElementById('game-canvas');
const ctx=canvas.getContext('2d');
canvas.width=800;canvas.height=500;

function getSprite(crop,ripeAt){
    if(!crop)return'empty';
    const r=ripeAt-Date.now()/1000;
    if(r>0){
        const t=CROPS_DATA[crop].grow_time,p=1-r/t;
        return p<.3?crop+'_0':p<.7?crop+'_1':crop+'_1';
    }
    return crop+'_2';
}

function draw(){
    ctx.fillStyle='#0f0f23';ctx.fillRect(0,0,800,500);
    ctx.fillStyle='#2ed573';ctx.font='20px "Press Start 2P"';ctx.textAlign='center';
    ctx.fillText('HAPPY FARM',400,35);
    ctx.font='10px "Press Start 2P"';
    ctx.fillStyle='#ffd93d';ctx.fillText('COINS: '+(farm?.coins||0),100,65);
    ctx.fillStyle='#74b9ff';ctx.fillText('WATER: '+(farm?.water_tokens||0),700,65);
    
    // Farm bg
    ctx.fillStyle='#2d1f0f';ctx.fillRect(180,90,440,380);
    ctx.strokeStyle='#5d4037';ctx.lineWidth=4;ctx.strokeRect(180,90,440,380);
    
    const cx=200,cy=110,sz=130,gp=10;
    for(let i=0;i<9;i++){
        const r=Math.floor(i/3),c=i%3,x=cx+c*(sz+gp),y=cy+r*(sz+gp);
        ctx.fillStyle='#3d2817';ctx.fillRect(x,y,sz,sz);
        ctx.strokeStyle=selectedPlot===i?'#ff6b81':'#5d4037';ctx.lineWidth=selectedPlot===i?4:2;ctx.strokeRect(x,y,sz,sz);
        
        const p=farm?.plots?.[i];
        const sp=getSprite(p?.crop,p?.ripe_at);
        const s=sprites[sp];
        if(s)ctx.drawImage(s,x+(sz-64)/2,y+(sz-64)/2,64,64);
        
        ctx.fillStyle='rgba(0,0,0,0.7)';ctx.fillRect(x,y+sz-22,sz,22);
        ctx.fillStyle='#fff';ctx.font='7px "Press Start 2P"';ctx.textAlign='center';
        if(!p)ctx.fillText('EMPTY',x+sz/2,y+sz-6);
        else{const rem=p.ripe_at-Date.now()/1000;ctx.fillText(rem>0?'GROW '+Math.ceil(rem/60)+'m':'RIPE!',x+sz/2,y+sz-6)}
    }
    
    ctx.fillStyle='#666';ctx.font='8px "Press Start 2P"';ctx.fillText('Click to select | Use buttons below',400,490);
}

let animFrame=0,lastTime=0;
function loop(t){
    if(t-lastTime>500){animFrame=1-animFrame;lastTime=t;draw()}
    requestAnimationFrame(loop);
}

function startGame(){
    document.getElementById('loading').style.display='none';
    loop(0);loadShop();loadLeader();
}

function show(t,m){const e=document.getElementById('toast');e.textContent=t;e.style.background=m;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),2000)}

async function load(){
    if(!agent)return;
    const r=await fetch(API+'/farm/'+agent);
    farm=await r.json();draw();
}

async function loadFarm(){
    agent=document.getElementById('agentId').value.trim();
    if(!agent)return show('ENTER ID','#f00');
    await load();show('WELCOME!','#2ed573');
}

canvas.onclick=e=>{
    const r=Math.floor((e.offsetY-110)/140),c=Math.floor((e.offsetX-200)/140);
    if(r>=0&&r<3&&c>=0&&c<3){selectedPlot=r*3+c;draw()}
};

async function plant(){
    const c=document.getElementById('cropSelect').value,p=parseInt(document.getElementById('plotSelect').value);
    const r=await fetch(API+'/action/plant',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_id:agent,crop:c,plot:p})});
    const d=await r.json();
    if(d.error)show(d.error,'#f00');else{show('PLANTED!','#2ed573');closeModal('plantModal');load()}
}

async function water(){
    const r=await fetch(API+'/action/water',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_id:agent,plot:selectedPlot})});
    const d=await r.json();
    if(d.error)show(d.error,'#f00');else{show('WATERED!','#74b9ff');load()}
}

async function harvest(){
    const r=await fetch(API+'/action/harvest',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_id:agent,plot:selectedPlot})});
    const d=await r.json();
    if(d.error)show(d.error,'#f00');else{show('+'+d.earned,'#ffd93d');load()}
}

async function buy(){
    const r=await fetch(API+'/action/buy',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_id:agent,item_id:'water_pack'})});
    const d=await r.json();
    if(d.error)show(d.error,'#f00');else{show('+10 WATER','#a55eea');load()}
}

async function steal(){
    const t=document.getElementById('targetId').value,p=parseInt(document.getElementById('stealPlot').value)||0;
    if(!t)return show('ENTER TARGET','#f00');
    const r=await fetch(API+'/action/steal',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_id:agent,target_id:t,plot:p})});
    const d=await r.json();
    if(d.error)show(d.error,'#f00');else{show('+'+d.stolen,'#ff6b81');closeModal('stealModal');load()}
}

function showModal(t){
    if(!agent)return show('ENTER ID','#f00');
    if(t==='plant'){
        document.getElementById('cropSelect').innerHTML='';
        for(let k in CROPS_DATA)document.getElementById('cropSelect').innerHTML+=`<option value="${k}">${CROPS_DATA[k].name}</option>`;
        document.getElementById('plotSelect').innerHTML='';
        for(let i=0;i<9;i++)document.getElementById('plotSelect').innerHTML+=`<option value="${i}">PLOT ${i+1} ${farm?.plots?.[i]?'(X)':''}</option>`;
        document.getElementById('plantModal').classList.add('active');
    }else document.getElementById('stealModal').classList.add('active');
}

function closeModal(id){document.getElementById(id).classList.remove('active')}

function loadShop(){
    const s=document.getElementById('shop');
    for(let k in CROPS_DATA){
        const c=CROPS_DATA[k];
        s.innerHTML+=`<div class="shop-item"><img src="/${k}_2.png"><div class="name">${c.name}</div><div class="cost">${c.value/2}</div></div>`;
    }
}

async function loadLeader(){
    const r=await fetch(API+'/leaderboard'),l=await r.json(),c=document.getElementById('leaderboard');
    c.innerHTML='';l.forEach((x,i)=>c.innerHTML+=`<div class="leader-item rank${i+1}"><span>#${i+1} ${x.agent_id}</span><span>${x.coins}</span></div>`);
}

setInterval(load,5000);
setInterval(loadLeader,10000);
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
    d = request.json
    a, i, c = d.get("agent_id"), d.get("plot", 0), d.get("crop", "carrot")
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
    t, tg, i = d.get("agent_id"), d.get("target_id"), d.get("plot", 0)
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
    print("Happy Farm - Canvas Pixel Game running on http://localhost:18792")
    app.run(host="0.0.0.0", port=18792, debug=True)
