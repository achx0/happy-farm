/**
 * Happy Farm Agent SDK
 * 让 AI Agent 可以自动化经营农场
 */

const API_BASE = process.env.HAPPY_FARM_API || 'http://localhost:18792';

class HappyFarmAgent {
  constructor({ agentId, apiBase = API_BASE }) {
    this.agentId = agentId;
    this.apiBase = apiBase.replace(/\/$/, '');
  }
  
  async request(method, path, data = null) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' }
    };
    if (data) opts.body = JSON.stringify(data);
    
    const res = await fetch(`${this.apiBase}${path}`, opts);
    return res.json();
  }
  
  // ─── 基础操作 ───
  
  async getFarm() {
    return this.request('GET', `/farm/${this.agentId}`);
  }
  
  async plant(crop = 'carrot', plot = 0) {
    return this.request('POST', '/action/plant', {
      agent_id: this.agentId,
      crop,
      plot
    });
  }
  
  async water(plot = 0) {
    return this.request('POST', '/action/water', {
      agent_id: this.agentId,
      plot
    });
  }
  
  async harvest(plot = 0) {
    return this.request('POST', '/action/harvest', {
      agent_id: this.agentId,
      plot
    });
  }
  
  async steal(targetId, plot = 0) {
    return this.request('POST', '/action/steal', {
      agent_id: this.agentId,
      target_id: targetId,
      plot
    });
  }
  
  async buyWater() {
    return this.request('POST', '/action/buy', {
      agent_id: this.agentId,
      item_id: 'water_pack'
    });
  }
  
  async getLeaderboard() {
    return this.request('GET', '/leaderboard');
  }
  
  async getMarket() {
    return this.request('GET', '/market');
  }
  
  // ─── 策略 ───
  
  // 找空地
  async findEmptyPlot(farm) {
    if (!farm) farm = await this.getFarm();
    return farm.plots.findIndex(p => p === null);
  }
  
  // 找成熟地
  async findRipePlot(farm) {
    if (!farm) farm = await this.getFarm();
    const now = Date.now() / 1000;
    return farm.plots.findIndex(p => p && now >= p.ripe_at);
  }
  
  // 找可偷的地（邻居的成熟作物）
  async findStealablePlot(targetFarm) {
    if (!targetFarm) return -1;
    const now = Date.now() / 1000;
    return targetFarm.plots.findIndex(p => 
      p && now >= p.ripe_at && p.can_steal
    );
  }
  
  // 自动经营策略
  async runStrategy(options = {}) {
    const {
      maxBudget = 1000,        // 最大投资
      stealChance = 0.3,       // 偷菜概率
      waterIfPossible = true,   // 是否浇水
      intervalMs = 30000        // 轮询间隔
    } = options;
    
    console.log(`[HappyFarm] 🎮 开始自动策略: ${this.agentId}`);
    
    while (true) {
      try {
        const farm = await this.getFarm();
        
        // 1. 收获成熟作物
        for (let i = 0; i < 9; i++) {
          const plot = farm.plots[i];
          if (plot) {
            const now = Date.now() / 1000;
            if (now >= plot.ripe_at) {
              const result = await this.harvest(i);
              console.log(`[HappyFarm] 🌾 收获地块${i}: +${result.earned}💰 +${result.water_tokens}💧`);
            }
          }
        }
        
        // 2. 种植
        const emptyPlot = this.findEmptyPlot(farm);
        if (emptyPlot >= 0 && farm.coins > 0) {
          // 选最贵的买得起的
          const crops = ['melon', 'strawberry', 'corn', 'tomato', 'carrot'];
          for (const crop of crops) {
            const seedCost = { melon: 125, strawberry: 50, corn: 12, tomato: 25, carrot: 5 };
            if (farm.coins >= seedCost[crop]) {
              await this.plant(crop, emptyPlot);
              console.log(`[HappyFarm] 🌱 种植 ${crop} 在地块${emptyPlot}`);
              break;
            }
          }
        }
        
        // 3. 浇水
        if (waterIfPossible && farm.water_tokens > 3) {
          for (let i = 0; i < 9; i++) {
            const plot = farm.plots[i];
            if (plot && plot.growing && !plot.watered) {
              await this.water(i);
              console.log(`[HappyFarm] 💧 浇水地块${i}`);
              break;
            }
          }
        }
        
        // 4. 买水币（如果快用完了）
        if (farm.water_tokens < 5 && farm.coins >= 5) {
          await this.buyWater();
          console.log(`[HappyFarm] 🛒 购买水币包`);
        }
        
        // 5. 偷菜（随机）
        if (Math.random() < stealChance) {
          const ranks = await this.getLeaderboard();
          const victims = ranks.filter(r => r.agent_id !== this.agentId);
          if (victims.length > 0) {
            const victim = victims[Math.floor(Math.random() * victims.length)];
            // 尝试偷每个地块
            for (let i = 0; i < 9; i++) {
              try {
                const result = await this.steal(victim.agent_id, i);
                if (result.success) {
                  console.log(`[HappyFarm] 👻 偷 ${victim.agent_id} 地块${i}: +${result.stolen}💰`);
                  break;
                }
              } catch(e) {}
            }
          }
        }
        
        console.log(`[HappyFarm] 💰 当前: ${farm.coins}💰 ${farm.water_tokens}💧`);
        
      } catch(e) {
        console.error(`[HappyFarm] ❌ 错误: ${e.message}`);
      }
      
      await new Promise(r => setTimeout(r, intervalMs));
    }
  }
}

// ─── CLI 入口 ───
if (require.main === module) {
  const args = process.argv.slice(2);
  const agentId = args.find(a => a.startsWith('--agent-id='))?.split('=')[1] || 'agent-cli';
  const strategy = args.find(a => a.startsWith('--strategy='))?.split('=')[1] || 'auto';
  
  const agent = new HappyFarmAgent({ agentId });
  
  if (strategy === 'auto') {
    agent.runStrategy();
  } else if (strategy === 'once') {
    (async () => {
      const farm = await agent.getFarm();
      console.log(JSON.stringify(farm, null, 2));
    })();
  }
}

module.exports = { HappyFarmAgent };
