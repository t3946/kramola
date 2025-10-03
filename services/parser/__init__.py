class ParserFedsFM:
    def parse(self, data):
        # Загрузка страницы
        url = 'http://example.com'
        response = requests.get(url)
        html_content = response.text

        # Разбор HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # Поиск элемента по CSS-селектору
        element = soup.select_one('css-селектор')  # например, '#id' или '.class'
        if element:
            print(element.text)  # вывод текста найденного элемента
        else:
            print("Элемент не найден")