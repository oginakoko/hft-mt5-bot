"""WebSocket server for HFT strategy dashboard."""

import asyncio
import json
import logging
from typing import Dict, Set
import websockets
from ..strategy import HFTStrategy

logger = logging.getLogger(__name__)

class DashboardServer:
    """WebSocket server for HFT strategy dashboard."""
    
    def __init__(self, strategy: HFTStrategy, host: str = "localhost", port: int = 8000):
        self.strategy = strategy
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.last_positions = []
        self.update_task = None
        
    async def start(self):
        """Start the WebSocket server."""
        async with websockets.serve(self._handle_client, self.host, self.port):
            logger.info(f"Dashboard server running on ws://{self.host}:{self.port}")
            
            # Start the broadcast updates task
            self.update_task = asyncio.create_task(self.broadcast_updates())
            
            try:
                await asyncio.Future()  # run forever
            except asyncio.CancelledError:
                if self.update_task:
                    self.update_task.cancel()
                    try:
                        await self.update_task
                    except asyncio.CancelledError:
                        pass
            
    async def _handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle new WebSocket client connection."""
        try:
            self.clients.add(websocket)
            logger.info(f"New client connected. Total clients: {len(self.clients)}")
            
            # Send initial data
            await self._send_update(websocket)
            
            # Keep connection alive and handle disconnection
            try:
                await websocket.wait_closed()
            finally:
                self.clients.remove(websocket)
                logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
                
        except Exception as e:
            logger.error(f"Error handling client: {str(e)}")
            if websocket in self.clients:
                self.clients.remove(websocket)
    
    async def broadcast_updates(self):
        """Broadcast updates to all connected clients."""
        while True:
            try:
                if self.clients:
                    for client in self.clients.copy():  # Use copy to avoid modification during iteration
                        try:
                            await self._send_update(client)
                        except websockets.exceptions.ConnectionClosed:
                            self.clients.remove(client)
                            logger.info(f"Removed closed client. Total clients: {len(self.clients)}")
            except Exception as e:
                logger.error(f"Error broadcasting updates: {str(e)}")
            
            await asyncio.sleep(1)  # Update every second
    
    async def _send_update(self, websocket: websockets.WebSocketServerProtocol):
        """Send dashboard update to client."""
        try:
            # Get account info
            account_info = self.strategy.mt5_handler.get_account_info()
            if not account_info or "error" in account_info:
                account_info = {
                    'balance': 0,
                    'equity': 0,
                    'margin': 0,
                    'profit': 0
                }
            
            # Get current positions
            positions = self.strategy.mt5_handler.get_positions()
            if "error" in positions:
                positions = []
            
            # Check for position changes
            events = []
            current_positions = [(p['symbol'], p['type'], p['volume']) for p in positions]
            last_positions = [(p['symbol'], p['type'], p['volume']) for p in self.last_positions]
            
            # Check for closed positions
            for pos in last_positions:
                if pos not in current_positions:
                    symbol, type_, volume = pos
                    events.append(f'<span class="text-warning">Closed {type_} position on {symbol} ({volume} lots)</span>')
            
            # Check for new positions
            for pos in current_positions:
                if pos not in last_positions:
                    symbol, type_, volume = pos
                    events.append(f'<span class="text-success">Opened {type_} position on {symbol} ({volume} lots)</span>')
            
            self.last_positions = positions
            
            # Add profit/loss events
            if account_info['profit'] != 0:
                profit_color = 'success' if account_info['profit'] > 0 else 'danger'
                events.append(
                    f'<span class="text-{profit_color}">Current P/L: {account_info["profit"]:.2f}</span>'
                )
            
            # Prepare update data
            update = {
                'account': account_info,
                'positions': positions,
                'events': events,
                'status': {
                    'connected': self.strategy.mt5_handler.connected,
                    'running': self.strategy.is_running
                }
            }
            
            await websocket.send(json.dumps(update))
            
        except Exception as e:
            logger.error(f"Error sending update: {str(e)}")
            if websocket in self.clients:
                self.clients.remove(websocket) 