"""
Happy Farm 前端 - 像素农场可视化
Canvas + Emoji 实现，无需外部图片资源
"""
from flask import Flask, render_template, send_from_directory
from pathlib import Path

app = Flask(__name__, template_folder=".", static_folder=".")

# 简单的模板路由
@app.route("/")
def index():
    return """
<!DOCTYPE html>
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
            font-family: 'Pixelify Sans', 'Noto Sans SC', sans-serif;
            color: #fff;
        }
        .header {
            background: linear-gradient(90deg, #2ED573, #7BED9F);
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(46, 213, 115, 0.3);
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
        .plot.ripe { 
            background: #8D6E63;
            animation: bounce 0.5s infinite alternate;
        }
        @keyframes bounce {
            from { transform: translateY(0); }
            to { transform: translateY(-5px); }
        }
        
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
        
        .plot .steal-badge {
            position: absolute;
            top: -5px;
            right: -5px;
            background: #FF4757;
            color: #fff;
            font-size: 0.3em;
            padding: 2px 5px;
            border-radius: 4px;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.2); }
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
        
        .market {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 20px;
            margin-top: 30px;
        }
        .market h2 { margin-bottom: 15px; color: #FFD93D; }
        .crop-list { display: flex; gap: 15px; flex-wrap: wrap; }
        .crop-item {
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            min-width: 100px;
        }
        .crop-item .emoji { font-size: 2em; display: block; margin-bottom: 5px; }
        .crop-item .name { font-size: 0.9em; color: #ccc; }
        .crop-item .cost { color: #FFD93D; font-weight: bold; }
        
        .leaderboard {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 20px;
            margin-top: 30px;
        }
        .leaderboard h2 { margin-bottom: 15px; color: #FF6B81; }
        .rank-item {
            display: flex;
            justify-content: space-between;
            padding: 10px;
            background: rgba(0,0,0,0.2);
            margin-bottom: 5px;
            border-radius: 5px;
        }
        .rank-1 { background: linear-gradient(90deg, #FFD93D33, transparent); }
        .rank-2 { background: rgba(191, 191, 191, 0.2); }
        .rank-3 { background: rgba(205, 127, 50, 0.2); }
        
        .neighbor-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #FF6B81;
            color: #fff;
            padding: 15px 25px;
            border-radius: 30px;
            font-size: 1.1em;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(255, 107, 129, 0.4);
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
        .modal h3 { margin-bottom: 20px; }
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
                <input type="text" id="agentId" placeholder="输入 Agent ID" 
                       style="padding: 10px; border-radius: 8px; border: none; width: 200px;">
                <button class="btn btn-buy" onclick="loadFarm()">切换</button>
            </div>
        </div>
        
        <div class="farm-grid" id="farmGrid"></div>
        
        <div class="controls">
            <button class="btn btn-plant" onclick="showPlantModal()">🌱 种植</button>
            <button class="btn btn-water" onclick="waterPlot()">💧 浇水</button>
            <button class="btn btn-harvest" onclick="harvestPlot()">🌾 收获</button>
            <button class="btn btn-buy" onclick="buyWater()">🛒 买水币</button>
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
    
    <button class="neighbor-btn" onclick="showStealModal()">👻 偷菜</button>
    
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
            <button class="btn" style="background: #FF6B81;" onclick="stealCrop()">偷菜!</button>
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
        
        // Toast 提示
        function showToast(msg, color = '#2ED573') {
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.style.background = color;
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 2000);
        }
        
        // 加载农场
        async function loadFarm() {
            const agentId = document.getElementById('agentId').value.trim();
            if (!agentId) {
                showToast('请输入 Agent ID', '#FF4757');
                return;
            }
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
        
        // 渲染农场
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
                        const crop = CROPS[plot.crop];
                        div.textContent = crop ? crop.emoji : '🌱';
                        
                        const timer = document.createElement('div');
                        timer.className = 'timer';
                        timer.textContent = Math.ceil(remaining / 60) + 'm';
                        div.appendChild(timer);
                        
                        if (plot.watered) {
                            div.style.border = '3px solid #74B9FF';
                        }
                    } else {
                        div.classList.add('ripe');
                        const crop = CROPS[plot.crop];
                        div.textContent = crop ? crop.emoji : '🌾';
                        
                        if (plot.can_steal) {
                            const badge = document.createElement('div');
                            badge.className = 'steal-badge';
                            badge.textContent = '可偷';
                            div.appendChild(badge);
                        }
                    }
                }
                
                grid.appendChild(div);
            });
        }
        
        // 刷新数据
        async function refresh() {
            if (!currentAgent) return;
            await loadFarm();
        }
        
        setInterval(refresh, 5000);
        
        // 种植
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
            if (data.error) {
                showToast(data.error, '#FF4757');
            } else {
                showToast('种植成功! 💰-' + (CROPS[crop].grow/2), '#2ED573');
                closeModal('plantModal');
                loadFarm();
            }
        }
        
        // 浇水
        async function waterPlot() {
            if (selectedPlot === undefined) return showToast('请先点击地块', '#FF4757');
            
            const res = await fetch(API_BASE + '/action/water', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ agent_id: currentAgent, plot: selectedPlot })
            });
            
            const data = await res.json();
            if (data.error) {
                showToast(data.error, '#FF4757');
            } else {
                showToast('浇水成功! 💧-1', '#74B9FF');
                loadFarm();
            }
        }
        
        // 收获
        async function harvestPlot() {
            if (selectedPlot === undefined) return showToast('请先点击地块', '#FF4757');
            
            const res = await fetch(API_BASE + '/action/harvest', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ agent_id: currentAgent, plot: selectedPlot })
            });
            
            const data = await res.json();
            if (data.error) {
                showToast(data.error, '#FF4757');
            } else {
                showToast(`收获成功! 💰+${data.earned} 💧+${data.water_tokens}`, '#FFD93D');
                loadFarm();
            }
        }
        
        // 买水币
        async function buyWater() {
            const res = await fetch(API_BASE + '/action/buy', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ agent_id: currentAgent, item_id: 'water_pack' })
            });
            
            const data = await res.json();
            if (data.error) {
                showToast(data.error, '#FF4757');
            } else {
                showToast('购买成功! 💧+10', '#A55EEA');
                loadFarm();
            }
        }
        
        // 偷菜
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
                body: JSON.stringify({ 
                    agent_id: currentAgent, 
                    target_id: target,
                    plot 
                })
            });
            
            const data = await res.json();
            if (data.error) {
                showToast(data.error, '#FF4757');
            } else {
                showToast(`偷菜成功! 💰+${data.stolen}`, '#FF6B81');
                closeModal('stealModal');
                loadFarm();
            }
        }
        
        function closeModal(id) {
            document.getElementById(id).classList.remove('active');
        }
        
        // 加载商店
        async function loadMarket() {
            const res = await fetch(API_BASE + '/market');
            const items = await res.json();
            
            const list = document.getElementById('cropList');
            list.innerHTML = '';
            
            for (const item of items) {
                if (item.id === 'water_pack') {
                    list.innerHTML += `
                        <div class="crop-item">
                            <span class="emoji">💧</span>
                            <div class="name">水币包</div>
                            <div class="cost">💰 ${item.cost}</div>
                        </div>
                    `;
                } else {
                    const crop = CROPS[item.id];
                    list.innerHTML += `
                        <div class="crop-item">
                            <span class="emoji">${crop ? crop.emoji : '🌾'}</span>
                            <div class="name">${item.name}</div>
                            <div class="cost">💰 ${item.seed_cost}</div>
                        </div>
                    `;
                }
            }
        }
        
        // 加载排行榜
        async function loadLeaderboard() {
            const res = await fetch(API_BASE + '/leaderboard');
            const ranks = await res.json();
            
            const list = document.getElementById('leaderboard');
            list.innerHTML = '';
            
            ranks.forEach((r, i) => {
                list.innerHTML += `
                    <div class="rank-item rank-${i+1}">
                        <span>#${i+1} ${r.agent_id}</span>
                        <span>💰 ${r.coins} | 📦 ${r.plots}</span>
                    </div>
                `;
            });
        }
        
        // 初始化
        async function init() {
            loadMarket();
            loadLeaderboard();
            setInterval(loadLeaderboard, 10000);
        }
        
        init();
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    print("🌾 Happy Farm 前端启动中...")
    app.run(host="0.0.0.0", port=18792, debug=True)
