"""API routes for the HFT strategy dashboard."""

from fastapi import APIRouter, WebSocket, HTTPException
from pydantic import BaseModel
import asyncio
from typing import Dict, List
from ..core.strategy_coordinator import StrategyCoordinator
import logging

router = APIRouter()
strategy_instance = None  # Will be set when strategy is initialized

class StrategyConfig(BaseModel):
    """Strategy configuration model."""
    risk_per_trade: float
    max_drawdown: float
    symbols: List[str]

@router.post("/api/strategy/start")
async def start_strategy():
    """Start the trading strategy."""
    global strategy_instance
    if strategy_instance and strategy_instance.running:
        raise HTTPException(status_code=400, message="Strategy already running")
    
    try:
        strategy_instance.start()
        return {"status": "success", "message": "Strategy started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/strategy/stop")
async def stop_strategy():
    """Stop the trading strategy."""
    global strategy_instance
    if not strategy_instance or not strategy_instance.running:
        raise HTTPException(status_code=400, detail="Strategy not running")
    
    try:
        strategy_instance.stop()
        return {"status": "success", "message": "Strategy stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/strategy/config")
async def update_config(config: StrategyConfig):
    """Update strategy configuration."""
    global strategy_instance
    if not strategy_instance:
        raise HTTPException(status_code=400, detail="Strategy not initialized")
    
    try:
        strategy_instance.config.update_trading_params(
            risk_per_trade=config.risk_per_trade,
            max_drawdown=config.max_drawdown,
            symbols=config.symbols
        )
        return {"status": "success", "message": "Configuration updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/trades")
async def websocket_trades(websocket: WebSocket):
    """WebSocket endpoint for real-time trade updates."""
    await websocket.accept()
    try:
        while True:
            if strategy_instance and strategy_instance.running:
                trades = strategy_instance.mt5_handler.get_positions()
                await websocket.send_json([{
                    "ticket": trade.ticket,
                    "symbol": trade.symbol,
                    "type": "BUY" if trade.type == 0 else "SELL",
                    "volume": trade.volume,
                    "openPrice": trade.open_price,
                    "profit": trade.profit,
                    "openTime": trade.open_time
                } for trade in trades])
            await asyncio.sleep(1)
    except:
        await websocket.close()

@router.get("/api/account")
async def get_account_info() -> Dict:
    """Get current account information."""
    if not strategy_instance:
        raise HTTPException(status_code=503, detail="Strategy not initialized")
    return strategy_instance.get_account_info()

@router.get("/api/positions")
async def get_positions() -> List[Dict]:
    """Get current open positions."""
    if not strategy_instance:
        raise HTTPException(status_code=503, detail="Strategy not initialized")
    return strategy_instance.get_positions()

@router.post("/api/positions/close-all")
async def close_all_positions() -> Dict:
    """Close all open positions."""
    if not strategy_instance:
        raise HTTPException(status_code=503, detail="Strategy not initialized")
    success = strategy_instance.close_all_positions()
    return {"success": success}
