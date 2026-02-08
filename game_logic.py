import random

ALPHABET_RU = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"


def caesar_cipher(text, shift, alphabet=ALPHABET_RU):
    result = []
    alpha_len = len(alphabet)
    lower_map = {ch: idx for idx, ch in enumerate(alphabet)}
    upper_map = {ch.upper(): idx for idx, ch in enumerate(alphabet)}

    for ch in text:
        if ch in lower_map:
            idx = (lower_map[ch] + shift) % alpha_len
            result.append(alphabet[idx])
        elif ch in upper_map:
            idx = (upper_map[ch] + shift) % alpha_len
            result.append(alphabet[idx].upper())
        else:
            result.append(ch)

    return "".join(result)


def generate_caesar_question(difficulty_level="easy"):
    words = ["привет", "машина", "солнце", "книга", "дождь"]
    original_word = random.choice(words)
    shift = random.randint(1, 5)
    encrypted_word_correct = caesar_cipher(original_word, shift)

    options = {encrypted_word_correct}
    while len(options) < 4:
        if random.random() < 0.5:
            wrong_shift = random.choice([s for s in range(1, 6) if s != shift])
            wrong_word = caesar_cipher(original_word, wrong_shift)
        else:
            other_word = random.choice([w for w in words if w != original_word])
            wrong_word = caesar_cipher(other_word, shift)
        options.add(wrong_word)

    options_list = list(options)
    random.shuffle(options_list)

    return {
        "original_word": original_word,
        "shift": shift,
        "encrypted_word_correct": encrypted_word_correct,
        "options": options_list,
    }
