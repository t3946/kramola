from models.inagents import AgentType
from services.words_list.list_inagents import ListInagents


class ListInagentsUR(ListInagents):
    agent_types = [x for x in AgentType if x != AgentType.FIZ]
    title: str = "Иноагенты (Организации)"
    description: str = "Список организаций, включённых в реестр иностранных агентов Минюста России"
