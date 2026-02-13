from services.fulltext_search.fulltext_search import FulltextSearch
from services.tokenization import TokenType


class TestFulltextSearch:
    test_cases_compare_token_sequences = [
        {
            'source': 'привет мир',
            'search': 'привет мир',
            'result': True
        },
        {
            'source': 'привет мир',
            'search': 'привет, мир',
            'result': False
        },
        {
            'source': 'привет мир',
            'search': 'привет',
            'result': False
        },
        {
            'source': 'привет мир',
            'search': 'привет мир как дела',
            'result': False
        },
        {
            'source': 'привет, мир!',
            'search': 'привет мир',
            'result': False
        },
        {
            'source': 'Hello world',
            'search': 'hello world',
            'result': True
        },
        {
            'source': 'машина едет',
            'search': 'машины едут',
            'result': True
        },
        {
            'source': 'кот сидит',
            'search': 'собака бежит',
            'result': False
        },
        {
            'source': 'тест',
            'search': 'тест',
            'result': True
        },
        {
            'source': 'тест',
            'search': 'теста',
            'result': True
        }
    ]

    def test_compare_token_sequences(self):
        for i, test_case in enumerate(self.test_cases_compare_token_sequences):
            source_text = test_case['source']
            search_text = test_case['search']
            expected_result = test_case['result']

            source_tokens = FulltextSearch.tokenize_text(source_text)
            search_tokens = FulltextSearch.tokenize_text(search_text)

            result = FulltextSearch._compare_token_sequences(source_tokens, search_tokens)

            assert result == expected_result, (
                f"Test case {i + 1} failed:\n"
                f"  Source: '{source_text}'\n"
                f"  Search: '{search_text}'\n"
                f"  Expected: {expected_result}\n"
                f"  Got: {result}\n"
                f"  Source tokens: {source_tokens}\n"
                f"  Search tokens: {search_tokens}"
            )

            print(f"Test case {i + 1} passed: '{source_text}' vs '{search_text}' -> {result}")

    test_cases_tokenize_text = [
        {
            'text': 'машины',
            'expected_lemma': 'машина',
            'description': 'Plural form should have singular lemma'
        },
        {
            'text': 'машина',
            'expected_lemma': 'машина',
            'description': 'Singular form should have same lemma'
        },
        {
            'text': 'едет',
            'expected_lemma': 'ехать',
            'description': 'Verb form should have infinitive lemma'
        },
        {
            'text': 'едут',
            'expected_lemma': 'ехать',
            'description': 'Plural verb form should have infinitive lemma'
        },
        {
            'text': 'теста',
            'expected_lemma': 'тест',
            'description': 'Genitive form should have nominative lemma'
        },
        {
            'text': 'привет мир',
            'expected_structure': {
                'word_count': 2,
                'space_count': 1,
                'has_lemma': True
            },
            'description': 'Should tokenize multiple words correctly'
        },
        {
            'text': 'привет, мир!',
            'expected_structure': {
                'word_count': 2,
                'punct_count': 2,
                'has_lemma': True
            },
            'description': 'Should handle punctuation correctly'
        },
        {
            'text': 'Hello world',
            'expected_structure': {
                'word_count': 2,
                'has_lemma': True
            },
            'description': 'Should handle English words'
        }
    ]

    def test_tokenize_text(self):
        for i, test_case in enumerate(self.test_cases_tokenize_text):
            text = test_case['text']
            description = test_case.get('description', f'Test case {i + 1}')

            tokens = FulltextSearch.tokenize_text(text)

            assert len(tokens) > 0, (
                f"Test case {i + 1} failed ({description}):\n"
                f"  Text: '{text}'\n"
                f"  Expected: at least 1 token\n"
                f"  Got: {len(tokens)} tokens"
            )

            word_tokens = [t for t in tokens if t.type == TokenType.WORD]

            if 'expected_lemma' in test_case:
                expected_lemma = test_case['expected_lemma']

                assert len(word_tokens) > 0, (
                    f"Test case {i + 1} failed ({description}):\n"
                    f"  Text: '{text}'\n"
                    f"  Expected: at least 1 word token\n"
                    f"  Got: {len(word_tokens)} word tokens"
                )

                first_word_lemma = word_tokens[0].lemma

                assert first_word_lemma is not None, (
                    f"Test case {i + 1} failed ({description}):\n"
                    f"  Text: '{text}'\n"
                    f"  Expected: lemma should not be None\n"
                    f"  Got: lemma = {first_word_lemma}\n"
                    f"  Token: {word_tokens[0]}"
                )

                assert first_word_lemma == expected_lemma, (
                    f"Test case {i + 1} failed ({description}):\n"
                    f"  Text: '{text}'\n"
                    f"  Expected lemma: '{expected_lemma}'\n"
                    f"  Got lemma: '{first_word_lemma}'\n"
                    f"  Token: {word_tokens[0]}"
                )

            if 'expected_structure' in test_case:
                structure = test_case['expected_structure']

                if 'word_count' in structure:
                    actual_word_count = len(word_tokens)
                    expected_word_count = structure['word_count']

                    assert actual_word_count == expected_word_count, (
                        f"Test case {i + 1} failed ({description}):\n"
                        f"  Text: '{text}'\n"
                        f"  Expected word count: {expected_word_count}\n"
                        f"  Got word count: {actual_word_count}\n"
                        f"  Tokens: {tokens}"
                    )

                if 'space_count' in structure:
                    space_tokens = [t for t in tokens if t.type == TokenType.SPACE]
                    actual_space_count = len(space_tokens)
                    expected_space_count = structure['space_count']

                    assert actual_space_count == expected_space_count, (
                        f"Test case {i + 1} failed ({description}):\n"
                        f"  Text: '{text}'\n"
                        f"  Expected space count: {expected_space_count}\n"
                        f"  Got space count: {actual_space_count}"
                    )

                if 'punct_count' in structure:
                    punct_tokens = [t for t in tokens if t.type == TokenType.PUNCTUATION]
                    actual_punct_count = len(punct_tokens)
                    expected_punct_count = structure['punct_count']

                    assert actual_punct_count >= expected_punct_count, (
                        f"Test case {i + 1} failed ({description}):\n"
                        f"  Text: '{text}'\n"
                        f"  Expected punct count: >= {expected_punct_count}\n"
                        f"  Got punct count: {actual_punct_count}"
                    )

                if structure.get('has_lemma'):
                    for word_token in word_tokens:
                        assert word_token.lemma is not None, (
                            f"Test case {i + 1} failed ({description}):\n"
                            f"  Text: '{text}'\n"
                            f"  Expected: all word tokens should have lemma\n"
                            f"  Got: token without lemma: {word_token}"
                        )

            for token in tokens:
                assert hasattr(token, 'text'), f"Token missing 'text' field: {token}"
                assert hasattr(token, 'start'), f"Token missing 'start' field: {token}"
                assert hasattr(token, 'end'), f"Token missing 'end' field: {token}"
                assert hasattr(token, 'type'), f"Token missing 'type' field: {token}"
                assert hasattr(token, 'lemma'), f"Token missing 'lemma' field: {token}"
                assert hasattr(token, 'stem'), f"Token missing 'stem' field: {token}"

            print(f"Test case {i + 1} passed ({description}): '{text}'")

    test_cases_search_token_sequences = [
        {
            'source': 'привет мир',
            'search': 'привет',
            'expected_matches': 1,
            'expected_indices': [(0, 0)]
        },
        {
            'source': 'привет мир привет',
            'search': 'привет',
            'expected_matches': 2,
            'expected_indices': [(0, 0), (4, 4)]
        },
        {
            'source': 'привет мир как дела',
            'search': 'привет мир',
            'expected_matches': 1,
            'expected_indices': [(0, 2)]
        },
        {
            'source': 'привет мир привет мир',
            'search': 'привет мир',
            'expected_matches': 2,
            'expected_indices': [(0, 2), (4, 6)]
        },
        {
            'source': 'машина едет быстро',
            'search': 'машины едут',
            'expected_matches': 1,
            'expected_indices': [(0, 2)]
        },
        {
            'source': 'кот сидит на стуле',
            'search': 'собака бежит',
            'expected_matches': 0,
            'expected_indices': []
        },
        {
            'source': 'тест теста тесту',
            'search': 'тест',
            'expected_matches': 3,
            'expected_indices': [(0, 0), (2, 2), (4, 4)]
        },
        {
            'source': 'привет',
            'search': 'привет мир',
            'expected_matches': 0,
            'expected_indices': []
        },
        {
            'source': 'Hello world hello',
            'search': 'hello',
            'expected_matches': 2,
            'expected_indices': [(0, 0), (4, 4)]
        },
        {
            'source': 'один два три один два',
            'search': 'один два',
            'expected_matches': 2,
            'expected_indices': [(0, 2), (6, 8)]
        }
    ]

    def test_search_token_sequences(self):
        for i, test_case in enumerate(self.test_cases_search_token_sequences):
            source_text = test_case['source']
            search_text = test_case['search']
            expected_matches_count = test_case['expected_matches']
            expected_indices = test_case['expected_indices']

            source_tokens = FulltextSearch.tokenize_text(source_text)
            search_tokens = FulltextSearch.tokenize_text(search_text)

            matches = FulltextSearch.search_token_sequences(source_tokens, search_tokens)

            assert len(matches) == expected_matches_count, (
                f"Test case {i + 1} failed:\n"
                f"  Source: '{source_text}'\n"
                f"  Search: '{search_text}'\n"
                f"  Expected matches count: {expected_matches_count}\n"
                f"  Got matches count: {len(matches)}\n"
                f"  Matches: {matches}\n"
                f"  Source tokens: {[(t.text, t.type) for t in source_tokens]}\n"
                f"  Search tokens: {[(t.text, t.type) for t in search_tokens]}"
            )

            for j, (expected_start, expected_end) in enumerate(expected_indices):
                assert j < len(matches), (
                    f"Test case {i + 1} failed:\n"
                    f"  Source: '{source_text}'\n"
                    f"  Search: '{search_text}'\n"
                    f"  Expected match {j + 1} at indices ({expected_start}, {expected_end})\n"
                    f"  Got: only {len(matches)} matches"
                )

                match = matches[j]
                actual_start, actual_end = match

                assert actual_start == expected_start, (
                    f"Test case {i + 1} failed:\n"
                    f"  Source: '{source_text}'\n"
                    f"  Search: '{search_text}'\n"
                    f"  Match {j + 1}: expected start = {expected_start}\n"
                    f"  Got: {actual_start}\n"
                    f"  Match: {match}\n"
                    f"  Source tokens: {[(t.text, t.type) for t in source_tokens]}"
                )

                assert actual_end == expected_end, (
                    f"Test case {i + 1} failed:\n"
                    f"  Source: '{source_text}'\n"
                    f"  Search: '{search_text}'\n"
                    f"  Match {j + 1}: expected end = {expected_end}\n"
                    f"  Got: {actual_end}\n"
                    f"  Match: {match}\n"
                    f"  Source tokens: {[(t.text, t.type) for t in source_tokens]}"
                )

            print(f"Test case {i + 1} passed: '{source_text}' search '{search_text}' -> {len(matches)} matches")


if __name__ == '__main__':
    test_instance = TestFulltextSearch()
    test_instance.test_compare_token_sequences()
    test_instance.test_tokenize_text()
    test_instance.test_search_token_sequences()
    print("All tests passed!")
