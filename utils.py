def create_addition_mistakes(sentence):
    MAXIMAL_LENGTH_MINUS_1 = 4
    VARYING_PENALTY_LENGTH = 5
    addition_mistakes_and_penalties = {}
    end_of_word = min(len(sentence), MAXIMAL_LENGTH_MINUS_1)
    max_letters_from_sentence_minus_1 = sentence[:end_of_word]
    for char in "abcdefghijklmnopqrstuvwxyz":
        for i in range(min(end_of_word, VARYING_PENALTY_LENGTH)):
            mistake = max_letters_from_sentence_minus_1[:i] + char + \
                      max_letters_from_sentence_minus_1[i:]
            addition_mistakes_and_penalties[mistake] = -2 * (VARYING_PENALTY_LENGTH - i)
        for i in range(VARYING_PENALTY_LENGTH, end_of_word + 1):
            mistake = max_letters_from_sentence_minus_1[:i] + char + \
                      max_letters_from_sentence_minus_1[i:]
            addition_mistakes_and_penalties[mistake] = -2
    return addition_mistakes_and_penalties


def create_delete_mistakes(sentence):
    MAXIMAL_LENGTH_PLUS_1 = 6
    VARYING_PENALTY_LENGTH = 5
    delete_mistakes_and_penalties = {}
    end_of_word = min(len(sentence), MAXIMAL_LENGTH_PLUS_1)
    max_letters_from_sentence_plus_1 = sentence[:end_of_word]
    for i in range(min(end_of_word, VARYING_PENALTY_LENGTH)):
        mistake = max_letters_from_sentence_plus_1[:i] + max_letters_from_sentence_plus_1[i + 1:]
        delete_mistakes_and_penalties[mistake] = -2 * (VARYING_PENALTY_LENGTH - i)
    for i in range(VARYING_PENALTY_LENGTH, end_of_word):
        mistake = max_letters_from_sentence_plus_1[:i] + max_letters_from_sentence_plus_1[i + 1:]
        delete_mistakes_and_penalties[mistake] = -2
    return delete_mistakes_and_penalties


def create_switch_mistakes(sentence):
    MAXIMAL_LENGTH = 5
    VARYING_PENALTY_LENGTH = 5
    switch_mistakes_and_penalties = {}
    end_of_word = min(len(sentence), MAXIMAL_LENGTH)
    max_letters_from_sentence = sentence[:end_of_word]
    for char in "abcdefghijklmnopqrstuvwxyz":
        for i in range(min(end_of_word, VARYING_PENALTY_LENGTH)):
            mistake = max_letters_from_sentence[:i] + char + max_letters_from_sentence[i + 1:]
            switch_mistakes_and_penalties[mistake] = - 5 + i
        for i in range(VARYING_PENALTY_LENGTH, end_of_word):
            mistake = max_letters_from_sentence[:i] + char + max_letters_from_sentence[i + 1:]
            switch_mistakes_and_penalties[mistake] = - 1
    return switch_mistakes_and_penalties


def get_mistakes_by_penalty(sentence):
    IMPOSSIBLE_PENALTY = -20
    dict1 = create_addition_mistakes(sentence)
    dict2 = create_delete_mistakes(sentence)
    dict3 = create_switch_mistakes(sentence)
    list_of_mistakes = list(dict1.keys()) + list(dict2.keys()) + list(dict3.keys())
    mistakes_without_doubles = set(list_of_mistakes)
    mistakes_and_penalties = []
    for mistake in mistakes_without_doubles:
        pen1 = dict1.get(mistake) if dict1.get(mistake) else IMPOSSIBLE_PENALTY
        pen2 = dict2.get(mistake) if dict2.get(mistake) else IMPOSSIBLE_PENALTY
        pen3 = dict3.get(mistake) if dict3.get(mistake) else IMPOSSIBLE_PENALTY
        min_pen = max(pen1, pen2, pen3)
        mistakes_and_penalties.append((mistake, min_pen))
    mistakes_and_penalties.sort(key=lambda x: x[1], reverse=True)
    return mistakes_and_penalties


# print(get_mistakes_by_penalty("ac"))

