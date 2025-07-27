# agents/agent_protocol.py
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
import threading
import time
import queue
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    ACK = "acknowledgment"

class MessagePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class AgentStatus(Enum):
    ACTIVE = "active"
    BUSY = "busy"
    INACTIVE = "inactive"
    ERROR = "error"

@dataclass
class AgentCapability:
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

@dataclass
class AgentMessage:
    sender: str
    receiver: str
    message_type: MessageType
    payload: Dict[str, Any]
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    priority: MessagePriority = MessagePriority.NORMAL
    retry_count: int = 0
    expires_at: Optional[datetime] = None
    requires_ack: bool = False
    
    def __post_init__(self):
        if self.expires_at is None:
            self.expires_at = self.timestamp + timedelta(seconds=settings.A2A_MESSAGE_TIMEOUT)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'message_type': self.message_type.value,
            'payload': self.payload,
            'message_id': self.message_id,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id,
            'priority': self.priority.value,
            'retry_count': self.retry_count,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'requires_ack': self.requires_ack
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary"""
        return cls(
            sender=data['sender'],
            receiver=data['receiver'],
            message_type=MessageType(data['message_type']),
            payload=data['payload'],
            message_id=data['message_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            correlation_id=data.get('correlation_id'),
            priority=MessagePriority(data.get('priority', MessagePriority.NORMAL.value)),
            retry_count=data.get('retry_count', 0),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
            requires_ack=data.get('requires_ack', False)
        )
    
    def is_expired(self) -> bool:
        """Check if message has expired"""
        return self.expires_at and datetime.now() > self.expires_at

@dataclass
class AgentRegistration:
    agent_name: str
    agent_instance: Any
    capabilities: List[AgentCapability] = field(default_factory=list)
    status: AgentStatus = AgentStatus.ACTIVE
    last_heartbeat: datetime = field(default_factory=datetime.now)
    message_handler: Optional[Callable] = None
    message_queue: queue.Queue = field(default_factory=queue.Queue)
    
    def is_alive(self) -> bool:
        """Check if agent is considered alive based on heartbeat"""
        timeout = timedelta(seconds=settings.A2A_MESSAGE_TIMEOUT * 2)
        return datetime.now() - self.last_heartbeat < timeout

class AgentProtocol:
    """Enhanced Agent-to-Agent communication protocol with synchronous message delivery"""
    
    def __init__(self):
        self.registered_agents: Dict[str, AgentRegistration] = {}
        self.message_history: List[AgentMessage] = []
        self.failed_messages: List[AgentMessage] = []
        
        # Thread safety
        self._lock = threading.RLock()
        self._running = True
        
        # Start background tasks
        self._start_background_tasks()
        
        logger.info("Enhanced A2A Agent Protocol initialized")
    
    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        # Message cleanup task
        cleanup_thread = threading.Thread(target=self._cleanup_expired_messages, daemon=True)
        cleanup_thread.start()
        
        # Heartbeat monitor task
        heartbeat_thread = threading.Thread(target=self._monitor_agent_heartbeats, daemon=True)
        heartbeat_thread.start()
        
        logger.info("Background tasks started")
    
    def register_agent(self, agent_name: str, agent_instance, 
                      capabilities: List[AgentCapability] = None,
                      message_handler: Callable = None):
        """Register an agent with enhanced capabilities"""
        with self._lock:
            if agent_name in self.registered_agents:
                logger.warning(f"Agent {agent_name} already registered, updating...")
            
            registration = AgentRegistration(
                agent_name=agent_name,
                agent_instance=agent_instance,
                capabilities=capabilities or [],
                message_handler=message_handler
            )
            
            self.registered_agents[agent_name] = registration
            logger.info(f"Agent registered: {agent_name} with {len(registration.capabilities)} capabilities")
            
            # Send registration notification to other agents
            self._broadcast_agent_event(agent_name, "agent_registered")
    
    def unregister_agent(self, agent_name: str):
        """Unregister an agent"""
        with self._lock:
            if agent_name in self.registered_agents:
                del self.registered_agents[agent_name]
                logger.info(f"Agent unregistered: {agent_name}")
                
                # Send unregistration notification
                self._broadcast_agent_event(agent_name, "agent_unregistered")
    
    def send_message(self, message: AgentMessage) -> bool:
        """Send message with immediate synchronous delivery"""
        with self._lock:
            # Validate message
            if not self._validate_message(message):
                return False
            
            # Check if receiver exists
            if message.receiver not in self.registered_agents:
                logger.error(f"Receiver agent not found: {message.receiver}")
                self.failed_messages.append(message)
                return False
            
            # Add to history
            self.message_history.append(message)
            
            # Attempt immediate delivery
            success = self._deliver_message_sync(message)
            
            if success:
                if settings.A2A_ENABLE_LOGGING:
                    logger.info(f"Message delivered: {message.sender} -> {message.receiver} [{message.message_type.value}]")
            else:
                # Handle delivery failure
                self._handle_delivery_failure(message)
            
            return success
    
    def _deliver_message_sync(self, message: AgentMessage) -> bool:
        """Deliver message synchronously to target agent"""
        try:
            receiver_reg = self.registered_agents[message.receiver]
            
            # Update receiver status
            old_status = receiver_reg.status
            receiver_reg.status = AgentStatus.BUSY
            
            try:
                # Use custom message handler if available
                if receiver_reg.message_handler:
                    result = receiver_reg.message_handler(message)
                else:
                    # Use default receive_message method
                    result = receiver_reg.agent_instance.receive_message(message)
                
                # Reset status
                receiver_reg.status = old_status
                logger.debug(f"Message delivered synchronously to {message.receiver}")
                return True
                
            except Exception as e:
                logger.error(f"Error in message handler for {message.receiver}: {e}")
                receiver_reg.status = AgentStatus.ERROR
                return False
            
        except Exception as e:
            logger.error(f"Message delivery failed: {e}")
            return False
    
    def _handle_delivery_failure(self, message: AgentMessage):
        """Handle message delivery failure with retry logic"""
        if message.retry_count < settings.A2A_MAX_RETRIES:
            message.retry_count += 1
            # Add delay before retry
            retry_delay = min(2 ** message.retry_count, 5)  # Exponential backoff, max 5s
            
            def retry_later():
                time.sleep(retry_delay)
                with self._lock:
                    # Try delivery again
                    if self._deliver_message_sync(message):
                        logger.info(f"Message retry succeeded: {message.message_id} (attempt {message.retry_count})")
                    else:
                        self._handle_delivery_failure(message)
            
            retry_thread = threading.Thread(target=retry_later, daemon=True)
            retry_thread.start()
            
            logger.info(f"Message retry scheduled: {message.message_id} (attempt {message.retry_count})")
        else:
            self.failed_messages.append(message)
            logger.error(f"Message delivery permanently failed: {message.message_id}")
    
    def _validate_message(self, message: AgentMessage) -> bool:
        """Validate message format and content"""
        if not message.sender or not message.receiver:
            logger.error("Invalid message: missing sender or receiver")
            return False
        
        if message.is_expired():
            logger.warning(f"Message expired: {message.message_id}")
            return False
        
        if not isinstance(message.payload, dict):
            logger.error("Invalid message: payload must be a dictionary")
            return False
        
        return True
    
    def _broadcast_agent_event(self, agent_name: str, event_type: str):
        """Broadcast agent lifecycle events"""
        for reg_name, registration in self.registered_agents.items():
            if reg_name != agent_name and registration.status == AgentStatus.ACTIVE:
                event_message = AgentMessage(
                    sender="system",
                    receiver=reg_name,
                    message_type=MessageType.NOTIFICATION,
                    payload={
                        "event_type": event_type,
                        "agent_name": agent_name,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                # Use synchronous delivery for events
                self._deliver_message_sync(event_message)
    
    def _cleanup_expired_messages(self):
        """Background task to clean up expired messages"""
        while self._running:
            try:
                with self._lock:
                    # Limit history size
                    if len(self.message_history) > 1000:
                        self.message_history = self.message_history[-500:]
                    
                    # Clean failed messages older than 1 hour
                    current_time = datetime.now()
                    one_hour_ago = current_time - timedelta(hours=1)
                    self.failed_messages = [
                        msg for msg in self.failed_messages 
                        if msg.timestamp >= one_hour_ago
                    ]
                
                time.sleep(300)  # Clean every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                time.sleep(300)
    
    def _monitor_agent_heartbeats(self):
        """Monitor agent heartbeats and update status"""
        while self._running:
            try:
                with self._lock:
                    for agent_name, registration in self.registered_agents.items():
                        if not registration.is_alive():
                            if registration.status == AgentStatus.ACTIVE:
                                registration.status = AgentStatus.INACTIVE
                                logger.warning(f"Agent heartbeat timeout: {agent_name}")
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")
                time.sleep(30)
    
    def send_heartbeat(self, agent_name: str):
        """Update agent heartbeat"""
        with self._lock:
            if agent_name in self.registered_agents:
                self.registered_agents[agent_name].last_heartbeat = datetime.now()
                if self.registered_agents[agent_name].status == AgentStatus.INACTIVE:
                    self.registered_agents[agent_name].status = AgentStatus.ACTIVE
                    logger.info(f"Agent reactivated: {agent_name}")
    
    def get_agent_capabilities(self, agent_name: str) -> List[AgentCapability]:
        """Get capabilities of a specific agent"""
        with self._lock:
            if agent_name in self.registered_agents:
                return self.registered_agents[agent_name].capabilities
            return []
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        with self._lock:
            return {
                "total_agents": len(self.registered_agents),
                "active_agents": sum(1 for reg in self.registered_agents.values() 
                                   if reg.status == AgentStatus.ACTIVE),
                "queued_messages": 0,  # No queue in sync mode
                "failed_messages": len(self.failed_messages),
                "message_history_size": len(self.message_history),
                "agents": {
                    name: {
                        "status": reg.status.value,
                        "capabilities": len(reg.capabilities),
                        "last_heartbeat": reg.last_heartbeat.isoformat()
                    }
                    for name, reg in self.registered_agents.items()
                }
            }
    
    def shutdown(self):
        """Gracefully shutdown the protocol"""
        logger.info("Shutting down A2A Protocol...")
        self._running = False