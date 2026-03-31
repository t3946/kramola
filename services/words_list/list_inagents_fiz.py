from models.inagents import AgentType
from services.words_list.list_inagents import ListInagents


class ListInagentsFIZ(ListInagents):
    agent_types = [AgentType.FIZ]
    title: str = "Иноагенты (ФИО)"
    description: str = "Список физических лиц, включённых в реестр иностранных агентов Минюста России"
