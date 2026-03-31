from models.extremists_terrorists import ExtremistArea, ExtremistType
from services.words_list.list_extremists_base import ListExtremistsTerroristsBase


class ListExtremistsRussianFIZ(ListExtremistsTerroristsBase):
    area = ExtremistArea.RUSSIAN
    status = ExtremistType.FIZ
    title: str = "Экстремисты и террористы (Российские): ФЛ"
    description: str = (
        "Список физических лиц из перечня Росфинмониторинга, в отношении которых "
        "имеются сведения о причастности к экстремистской деятельности или терроризму"
    )
