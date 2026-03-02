from models.extremists_terrorists import ExtremistArea, ExtremistType
from services.words_list.list_extremists_base import ListExtremistsTerroristsBase


class ListExtremistsInternationalUR(ListExtremistsTerroristsBase):
    area = ExtremistArea.INTERNATIONAL
    status = ExtremistType.UR
