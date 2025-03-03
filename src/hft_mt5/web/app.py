"""FastAPI application for HFT strategy dashboard."""

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import logging
import json
import asyncio
from typing import List, Dict
from ..strategy import HFTStrategy
from ..core.data_types import Signal
import time

logger = logging.getLogger(__name__)

class TradingActivity:
    def __init__(self, max_size: int = 100):
        self.activities: List[Dict] = []
        self.max_size = max_size
    
    def add_activity(self, activity: Dict):
        self.activities.insert(0, activity)
        if len(self.activities) > self.max_size:
            self.activities.pop()

def create_app(strategy: HFTStrategy, state) -> FastAPI:
    """Create FastAPI application with WebSocket support."""
    app = FastAPI(title="HFT Strategy Dashboard")
    
    # Initialize trading activity
    trading_activity = TradingActivity()
    
    # Mount static files
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    @app.get("/")
    async def get_dashboard():
        """Serve the dashboard HTML."""
        with open(os.path.join(static_dir, "index.html")) as f:
            return HTMLResponse(f.read())
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """Handle WebSocket connections."""
        await websocket.accept()
        logger.info("connection open")
        
        try:
            while True:
                try:
                    # Check for incoming messages
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                    data = json.loads(message)
                    
                    if data.get('action') == 'add_symbol':
                        symbol = data.get('symbol')
                        if symbol and symbol not in strategy.symbols:
                            strategy.add_symbol(symbol)
                            trading_activity.add_activity({
                                'timestamp': int(time.time()),
                                'type': 'system',
                                'action': f'Added trading pair {symbol}',
                                'symbol': symbol
                            })
                    
                    elif data.get('action') == 'remove_symbol':
                        symbol = data.get('symbol')
                        if symbol and symbol in strategy.symbols:
                            strategy.remove_symbol(symbol)
                            trading_activity.add_activity({
                                'timestamp': int(time.time()),
                                'type': 'system',
                                'action': f'Removed trading pair {symbol}',
                                'symbol': symbol
                            })
                
                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                
                # Get current state
                update = {
                    'status': {
                        'connected': bool(state.is_connected.value),
                        'running': bool(state.is_running.value)
                    },
                    'account': {
                        'balance': state.account_info[0],
                        'equity': state.account_info[1],
                        'margin': state.account_info[2],
                        'profit': state.account_info[3]
                    },
                    'symbols': strategy.symbols,
                    'activity': trading_activity.activities
                }
                
                # Get positions
                with state.positions_lock:
                    positions_str = state.positions.value.decode().strip()
                    if positions_str:
                        try:
                            update['positions'] = eval(positions_str)  # Safe since we control the data
                        except:
                            update['positions'] = []
                    else:
                        update['positions'] = []
                
                # Send update
                await websocket.send_json(update)
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            logger.info("connection closed")
    
    return app
