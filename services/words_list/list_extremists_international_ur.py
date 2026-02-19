from models.extremists_terrorists import ExtremistArea, ExtremistStatus
from services.words_list.list_extremists_base import ListExtremistsTerroristsBase


class ListExtremistsInternationalUR(ListExtremistsTerroristsBase):
    area = ExtremistArea.INTERNATIONAL
    status = ExtremistStatus.UR
