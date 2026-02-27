from services.parser_feds_fm.process_raw_international import ProcessRawInternational
from services.parser_feds_fm.process_raw_russian import ProcessRawRussian


class ProcessRaw (ProcessRawInternational, ProcessRawRussian):
    pass