from models.extremists_terrorists import ExtremistArea, ExtremistType
from services.words_list.list_extremists_base import ListExtremistsTerroristsBase


class ListExtremistsRussianUR(ListExtremistsTerroristsBase):
    area = ExtremistArea.RUSSIAN
    status = ExtremistType.UR
    title: str = "Экстремисты и террористы (Российские): ЮЛ"
    description: str = (
        "Список организаций из перечня Росфинмониторинга, в отношении которых "
        "имеются сведения о причастности к экстремистской деятельности или терроризму"
    )
