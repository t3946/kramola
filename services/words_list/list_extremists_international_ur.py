from models.extremists_terrorists import ExtremistArea, ExtremistType
from services.words_list.list_extremists_base import ListExtremistsTerroristsBase


class ListExtremistsInternationalUR(ListExtremistsTerroristsBase):
    area = ExtremistArea.INTERNATIONAL
    status = ExtremistType.UR
    title: str = "Экстремисты и террористы (Международные): ЮЛ"
    description: str = (
        "Список организаций из перечня Росфинмониторинга, в отношении которых "
        "имеются сведения о причастности к экстремистской деятельности или терроризму"
    )
