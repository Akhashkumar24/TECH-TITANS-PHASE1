# agents/base_agent.py
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any
from agents.agent_protocol import AgentMessage, MessageType, AgentProtocol
from utils.logger import get_logger

class BaseAgent(ABC):
    def __init__(self, name: str, protocol: AgentProtocol):
        self.name = name
        self.protocol = protocol
        self.logger = get_logger(f"agent.{name}")
        self.protocol.register_agent(name, self)
    
    def send_message(self, receiver: str, message_type: MessageType, payload: Dict[str, Any], correlation_id: str = None):
        """Send message to another agent"""
        message = AgentMessage(
            sender=self.name,
            receiver=receiver,
            message_type=message_type,
            payload=payload,
            message_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            correlation_id=correlation_id
        )
        self.protocol.send_message(message)
        self.logger.info(f"Sent {message_type.value} message to {receiver}")
    
    @abstractmethod
    def receive_message(self, message: AgentMessage):
        """Receive and process message from another agent"""
        pass
    
    @abstractmethod
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process assigned task"""
        pass
    
    def log_activity(self, action: str, details: Dict[str, Any] = None):
        """Log agent activity to database"""
        from config.database import db_connection
        
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO agent_logs (agent_type, action, job_id, application_id, message, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    self.name,
                    action,
                    details.get('job_id') if details else None,
                    details.get('application_id') if details else None,
                    str(details) if details else None,
                    'success'
                ))
        except Exception as e:
            self.logger.error(f"Failed to log activity: {e}")
