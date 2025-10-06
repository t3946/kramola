from services.parser.parser_feds_fm import ParserFedsFM

parser = ParserFedsFM()
data = parser.load()

print(data)
