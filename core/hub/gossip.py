from __future__ import annotations

import asyncio
import json
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set
from enum import Enum
import uuid

import websockets
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed


class MessageType(Enum):
    """Types of gossip messages exchanged between hubs"""
    PEER_DISCOVERY = "peer_discovery"
    CLAIM_PROPAGATION = "claim_propagation"
    VOTE_PROPAGATION = "vote_propagation"
    CONSENSUS_RESULT = "consensus_result"
    VALIDATOR_UPDATE = "validator_update"
    HEALTH_CHECK = "health_check"


@dataclass
class HubConfig:
    """Configuration for hub communication"""
    hub_id: str
    host: str
    port: int
    max_peers: int = 10
    gossip_interval: float = 0.5
    health_check_interval: float = 30.0
    propagation_timeout: float = 5.0


@dataclass
class GossipMessage:
    """Base gossip message structure"""
    message_id: str
    message_type: str
    source_hub: str
    timestamp: str
    data: dict
    ttl: int = 5


class GossipProtocol:
    """Gossip protocol implementation for inter-hub communication"""
    
    def __init__(self, config: HubConfig):
        self.config = config
        self.peers: Dict[str, WebSocketServerProtocol] = {}
        self.known_peers: Set[str] = set()
        self.sent_messages: Set[str] = set()
        self.received_messages: Set[str] = set()
        self.running = False
        self.server: Optional[websockets.server.Server] = None
        
    async def start(self):
        """Start the gossip server and connect to peers"""
        self.running = True
        self.server = await websockets.serve(
            self._handle_connection,
            self.config.host,
            self.config.port
        )
        
        print(f"Gossip server started on {self.config.host}:{self.config.port}")
        
        # Start periodic peer discovery
        asyncio.create_task(self._periodic_peer_discovery())
        asyncio.create_task(self._periodic_health_check())
        
    async def stop(self):
        """Stop the gossip server and clean up connections"""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            
        for peer_ws in self.peers.values():
            await peer_ws.close()
            
        self.peers.clear()
        print("Gossip server stopped")
        
    async def _handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle incoming connections from other hubs"""
        peer_id = str(uuid.uuid4())
        self.peers[peer_id] = websocket
        
        try:
            async for message in websocket:
                await self._handle_message(peer_id, message)
        except ConnectionClosed:
            pass
        finally:
            del self.peers[peer_id]
            print(f"Disconnected from peer: {peer_id}")
            
    async def _handle_message(self, peer_id: str, raw_message: str):
        """Handle incoming gossip messages"""
        try:
            message_data = json.loads(raw_message)
            message = GossipMessage(**message_data)
            
            # Ignore messages we've already seen
            if message.message_id in self.received_messages:
                return
                
            self.received_messages.add(message.message_id)
            
            # Process the message
            await self._process_message(message)
            
            # Propagate to other peers if TTL > 0
            if message.ttl > 0:
                await self._propagate_message(message)
                
        except Exception as e:
            print(f"Error processing message from {peer_id}: {e}")
            
    async def _process_message(self, message: GossipMessage):
        """Process different types of gossip messages"""
        handler = {
            MessageType.PEER_DISCOVERY: self._handle_peer_discovery,
            MessageType.CLAIM_PROPAGATION: self._handle_claim_propagation,
            MessageType.VOTE_PROPAGATION: self._handle_vote_propagation,
            MessageType.CONSENSUS_RESULT: self._handle_consensus_result,
            MessageType.VALIDATOR_UPDATE: self._handle_validator_update,
            MessageType.HEALTH_CHECK: self._handle_health_check,
        }.get(MessageType(message.message_type))
        
        if handler:
            await handler(message)
        else:
            print(f"Unknown message type: {message.message_type}")
            
    async def _handle_peer_discovery(self, message: GossipMessage):
        """Handle peer discovery messages"""
        peer_info = message.data
        if peer_info["hub_id"] != self.config.hub_id:
            self.known_peers.add((peer_info["host"], peer_info["port"]))
            print(f"Discovered new peer: {peer_info['hub_id']} at {peer_info['host']}:{peer_info['port']}")
            
    async def _handle_claim_propagation(self, message: GossipMessage):
        """Handle claim propagation messages"""
        from core.ledger.service import LedgerService
        
        claim_data = message.data
        print(f"Received claim from {message.source_hub}: {claim_data.get('statement', 'N/A')}")
        
        # Store the claim in local ledger
        try:
            ledger = LedgerService()
            ledger.submit_claim(
                statement=claim_data["statement"],
                domain=claim_data["domain"],
                proposer_id=claim_data["proposer_id"],
                evidence_refs=claim_data.get("evidence_refs", [])
            )
        except Exception as e:
            print(f"Error storing claim: {e}")
            
    async def _handle_vote_propagation(self, message: GossipMessage):
        """Handle vote propagation messages"""
        from core.validation.service import VoteService
        
        vote_data = message.data
        print(f"Received vote from {message.source_hub}")
        
        try:
            vote_service = VoteService()
            vote_service.submit_vote(vote_data)
        except Exception as e:
            print(f"Error storing vote: {e}")
            
    async def _handle_consensus_result(self, message: GossipMessage):
        """Handle consensus result messages"""
        consensus_data = message.data
        print(f"Consensus result for claim {consensus_data['claim_id']}: {consensus_data['outcome']}")
        
    async def _handle_validator_update(self, message: GossipMessage):
        """Handle validator update messages"""
        validator_data = message.data
        print(f"Validator update: {validator_data['validator_id']}")
        
    async def _handle_health_check(self, message: GossipMessage):
        """Handle health check messages"""
        print(f"Health check from {message.source_hub}: {message.data['status']}")
        
    async def _propagate_message(self, message: GossipMessage):
        """Propagate message to all connected peers"""
        # Create new message with TTL decremented
        propagate_message = GossipMessage(
            message_id=message.message_id,
            message_type=message.message_type,
            source_hub=self.config.hub_id,
            timestamp=message.timestamp,
            data=message.data,
            ttl=message.ttl - 1
        )
        
        # Serialize message
        serialized = json.dumps(propagate_message.__dict__)
        
        # Send to all connected peers except the source
        for peer_id, peer_ws in list(self.peers.items()):
            try:
                await peer_ws.send(serialized)
            except Exception as e:
                print(f"Error sending to peer {peer_id}: {e}")
                del self.peers[peer_id]
                
    async def broadcast(self, message_type: MessageType, data: dict):
        """Broadcast a message to all peers"""
        message = GossipMessage(
            message_id=str(uuid.uuid4()),
            message_type=message_type.value,
            source_hub=self.config.hub_id,
            timestamp=datetime.now().isoformat(),
            data=data,
            ttl=5
        )
        
        self.sent_messages.add(message.message_id)
        await self._propagate_message(message)
        
    async def _periodic_peer_discovery(self):
        """Periodically send peer discovery messages"""
        while self.running:
            await asyncio.sleep(self.config.gossip_interval)
            
            # Send discovery message to all known peers
            discovery_data = {
                "hub_id": self.config.hub_id,
                "host": self.config.host,
                "port": self.config.port,
                "timestamp": datetime.now().isoformat(),
                "status": "active"
            }
            
            await self.broadcast(MessageType.PEER_DISCOVERY, discovery_data)
            
    async def _periodic_health_check(self):
        """Periodically send health check messages"""
        while self.running:
            await asyncio.sleep(self.config.health_check_interval)
            
            health_data = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "peers": list(self.known_peers),
                "active_connections": len(self.peers)
            }
            
            await self.broadcast(MessageType.HEALTH_CHECK, health_data)
            
    async def connect_to_peer(self, host: str, port: int):
        """Connect to a specific peer hub"""
        try:
            uri = f"ws://{host}:{port}"
            websocket = await websockets.connect(uri)
            
            peer_id = str(uuid.uuid4())
            self.peers[peer_id] = websocket
            
            # Send initial discovery message
            await self.broadcast(
                MessageType.PEER_DISCOVERY,
                {
                    "hub_id": self.config.hub_id,
                    "host": self.config.host,
                    "port": self.config.port,
                    "timestamp": datetime.now().isoformat(),
                    "status": "connected"
                }
            )
            
            print(f"Connected to peer: {host}:{port}")
            
            asyncio.create_task(self._handle_incoming_connection(peer_id, websocket))
            
        except Exception as e:
            print(f"Failed to connect to peer {host}:{port}: {e}")
            
    async def _handle_incoming_connection(self, peer_id: str, websocket: WebSocketServerProtocol):
        """Handle incoming connections from specific peers"""
        try:
            async for message in websocket:
                await self._handle_message(peer_id, message)
        except Exception as e:
            print(f"Error in peer connection {peer_id}: {e}")
        finally:
            if peer_id in self.peers:
                del self.peers[peer_id]
                
    def get_status(self) -> dict:
        """Get current gossip protocol status"""
        return {
            "hub_id": self.config.hub_id,
            "host": self.config.host,
            "port": self.config.port,
            "running": self.running,
            "active_peers": len(self.peers),
            "known_peers": list(self.known_peers),
            "sent_messages": len(self.sent_messages),
            "received_messages": len(self.received_messages),
            "config": {
                "max_peers": self.config.max_peers,
                "gossip_interval": self.config.gossip_interval,
                "health_check_interval": self.config.health_check_interval
            }
        }