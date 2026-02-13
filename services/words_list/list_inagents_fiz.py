from models import Inagent
from models.inagents import AgentType


class ListInagentsFIZ:
    def load(self) -> list[str]:
        rows = (
            Inagent.query
            .filter(Inagent.agent_type == AgentType.FIZ)
            .with_entities(Inagent.search_terms)
            .all()
        )

        merged: list[str] = []

        for (terms,) in rows:
            if isinstance(terms, list):
                merged.extend(s.strip() for s in terms if s and str(s).strip())

        return merged
