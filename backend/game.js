// Happy Farm - Canvas Game Renderer
// 仿 Star Office UI 风格

const CANVAS_WIDTH = 800;
const CANVAS_HEIGHT = 600;
const GRID_SIZE = 3; // 3x3 plots

// Sprite frames (loaded from server)
const sprites = {};
const spriteUrls = {
    // Crop growth stages: 0=seed, 1=growing, 2=ripe
    'carrot_0': '/carrot_0.png',
    'carrot_1': '/carrot_1.png', 
    'carrot_2': '/carrot_2.png',
    'corn_0': '/corn_0.png',
    'corn_1': '/corn_1.png',
    'corn_2': '/corn_2.png',
    'tomato_0': '/tomato_0.png',
    'tomato_1': '/tomato_1.png',
    'tomato_2': '/tomato_2.png',
    'strawberry_0': '/strawberry_0.png',
    'strawberry_1': '/strawberry_1.png',
    'strawberry_2': '/strawberry_2.png',
    'melon_0': '/melon_0.png',
    'melon_1': '/melon_1.png',
    'melon_2': '/melon_2.png',
    'empty': '/empty.png',
};

// Animation state
let animationFrame = 0;
let lastFrameTime = 0;
const FRAME_DURATION = 500; // ms per animation frame

// Game state
let gameState = {
    agentId: '',
    coins: 100,
    waterTokens: 50,
    plots: [null, null, null, null, null, null, null, null, null],
    selectedPlot: 0,
};

// Load all sprites
async function loadSprites() {
    const promises = Object.entries(spriteUrls).map(([name, url]) => {
        return new Promise((resolve) => {
            const img = new Image();
            img.onload = () => {
                sprites[name] = img;
                resolve();
            };
            img.onerror = () => {
                console.warn('Failed to load:', url);
                resolve();
            };
            img.src = url;
        });
    });
    await Promise.all(promises);
    console.log('Sprites loaded:', Object.keys(sprites).length);
}

// Get crop sprite based on growth stage
function getCropSprite(crop, ripeAt) {
    if (!crop) return 'empty';
    
    const now = Date.now() / 1000;
    const remaining = ripeAt - now;
    
    let stage;
    if (remaining > 0) {
        // Still growing - show growing stage based on progress
        const cropTimes = { carrot: 60, corn: 120, tomato: 180, strawberry: 300, melon: 600 };
        const totalTime = cropTimes[crop] || 60;
        const progress = 1 - (remaining / totalTime);
        
        if (progress < 0.3) stage = 0;
        else if (progress < 0.7) stage = 1;
        else stage = 1; // stay at stage 1 until ripe
    } else {
        stage = 2; // ripe
    }
    
    return `${crop}_${stage}`;
}

// Draw a sprite centered in a region
function drawSprite(ctx, spriteName, x, y, width, height) {
    const sprite = sprites[spriteName];
    if (!sprite) return;
    
    // Center the sprite
    const sx = x + (width - 64) / 2;
    const sy = y + (height - 64) / 2;
    
    ctx.drawImage(sprite, sx, sy, 64, 64);
}

// Main render function
function render(canvas, state) {
    const ctx = canvas.getContext('2d');
    
    // Clear
    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    
    // Draw header
    ctx.fillStyle = '#2ed573';
    ctx.font = '24px "Press Start 2P", monospace';
    ctx.textAlign = 'center';
    ctx.fillText('🌾 HAPPY FARM', CANVAS_WIDTH / 2, 40);
    
    // Draw stats
    ctx.font = '12px "Press Start 2P", monospace';
    ctx.fillStyle = '#ffd93d';
    ctx.fillText(`💰 ${state.coins}`, 100, 80);
    ctx.fillStyle = '#74b9ff';
    ctx.fillText(`💧 ${state.waterTokens}`, CANVAS_WIDTH - 100, 80);
    
    // Draw farm background
    const farmX = 200;
    const farmY = 120;
    const cellSize = 120;
    const gap = 10;
    
    // Farm container
    ctx.fillStyle = '#2d1f0f';
    ctx.fillRect(farmX - 20, farmY - 20, cellSize * 3 + gap * 2 + 40, cellSize * 3 + gap * 2 + 40);
    ctx.strokeStyle = '#5d4037';
    ctx.lineWidth = 4;
    ctx.strokeRect(farmX - 20, farmY - 20, cellSize * 3 + gap * 2 + 40, cellSize * 3 + gap * 2 + 40);
    
    // Draw plots
    for (let i = 0; i < 9; i++) {
        const row = Math.floor(i / 3);
        const col = i % 3;
        const x = farmX + col * (cellSize + gap);
        const y = farmY + row * (cellSize + gap);
        
        // Plot background
        ctx.fillStyle = '#3d2817';
        ctx.fillRect(x, y, cellSize, cellSize);
        
        // Border
        ctx.strokeStyle = state.selectedPlot === i ? '#ff6b81' : '#5d4037';
        ctx.lineWidth = state.selectedPlot === i ? 4 : 2;
        ctx.strokeRect(x, y, cellSize, cellSize);
        
        // Draw crop sprite
        const plot = state.plots[i];
        const spriteName = plot ? getCropSprite(plot.crop, plot.ripe_at) : 'empty';
        drawSprite(ctx, spriteName, x, y, cellSize, cellSize);
        
        // Status text
        ctx.fillStyle = 'rgba(0,0,0,0.7)';
        ctx.fillRect(x, y + cellSize - 20, cellSize, 20);
        
        ctx.fillStyle = '#fff';
        ctx.font = '8px "Press Start 2P", monospace';
        ctx.textAlign = 'center';
        
        if (!plot) {
            ctx.fillText('EMPTY', x + cellSize / 2, y + cellSize - 6);
        } else {
            const remaining = plot.ripe_at - Date.now() / 1000;
            if (remaining > 0) {
                ctx.fillText(`⏳ ${Math.ceil(remaining / 60)}m`, x + cellSize / 2, y + cellSize - 6);
            } else {
                ctx.fillStyle = '#2ed573';
                ctx.fillText('✅ RIPE', x + cellSize / 2, y + cellSize - 6);
            }
        }
    }
    
    // Draw controls hint
    ctx.fillStyle = '#666';
    ctx.font = '10px "Press Start 2P", monospace';
    ctx.textAlign = 'center';
    ctx.fillText('Click plot to select | Use buttons below', CANVAS_WIDTH / 2, CANVAS_HEIGHT - 30);
}

// Animation loop
function gameLoop(timestamp) {
    if (timestamp - lastFrameTime > FRAME_DURATION) {
        animationFrame = (animationFrame + 1) % 2;
        lastFrameTime = timestamp;
    }
    
    const canvas = document.getElementById('game-canvas');
    if (canvas) {
        render(canvas, gameState);
    }
    
    requestAnimationFrame(gameLoop);
}

// Initialize game
async function initGame() {
    await loadSprites();
    
    const canvas = document.getElementById('game-canvas');
    if (canvas) {
        canvas.width = CANVAS_WIDTH;
        canvas.height = CANVAS_HEIGHT;
    }
    
    // Start game loop
    requestAnimationFrame(gameLoop);
    
    console.log('Happy Farm game initialized');
}

// Export for use
window.HappyFarmGame = {
    initGame,
    updateState: (newState) => {
        gameState = { ...gameState, ...newState };
    },
    setPlot: (index, plot) => {
        gameState.plots[index] = plot;
    },
    selectPlot: (index) => {
        gameState.selectedPlot = index;
    },
};

// Auto-init when DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGame);
} else {
    initGame();
}
