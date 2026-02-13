from models.inagents import AgentType
from services.words_list.list_inagents import ListInagents


class ListInagentsFIZ(ListInagents):
    agent_types = [AgentType.FIZ]
