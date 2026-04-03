from models.inagents import AgentType
from services.words_list.list_inagents import ListInagents


class ListInagentsFIZ(ListInagents):
    agent_types = [AgentType.FIZ]
    title: str = "Иноагенты (ФИО)"
    description: str = "Список физических лиц, включённых в реестр иностранных агентов Минюста России"

    def __init__(
        self,
        *,
        search_text: bool = True,
        search_surnames: bool = True,
        search_full_names: bool = True,
    ) -> None:
        super().__init__()
        self.search_text = search_text
        self.search_surnames = search_surnames
        self.search_full_names = search_full_names
