try:
    from .agentpilot import AgentPilotClient, AgentPilotNotConfigured
except ImportError:
    # 如果 agent_pilot 未安装，创建占位类
    class AgentPilotNotConfigured(Exception):
        """Raised when AgentPilot configuration is missing."""
        pass
    
    class AgentPilotClient:
        """占位类，当 agent_pilot 未安装时使用"""
        pass
