from models.extremists_terrorists import ExtremistArea, ExtremistStatus
from services.words_list.list_extremists_base import ListExtremistsTerroristsBase


class ListExtremistsRussianUR(ListExtremistsTerroristsBase):
    area = ExtremistArea.RUSSIAN
    status = ExtremistStatus.UR
