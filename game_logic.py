import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypedDict, Union

ALPHABET_RU = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
ALPHABET_EN = "abcdefghijklmnopqrstuvwxyz"


@dataclass
class PlayerState:
    lives: int = 5
    score: int = 0
    coins: int = 0
    current_level_type: Optional[str] = None
    current_question_data: Optional["CaesarQuestion"] = None

    def decrease_life(self) -> None:
        if self.lives > 0:
            self.lives -= 1

    def add_score(self, points: int) -> None:
        self.score += points

    def add_coins(self, amount: int) -> None:
        self.coins += amount

    def is_game_over(self) -> bool:
        return self.lives == 0

    def reset_state(self) -> None:
        self.lives = 5
        self.score = 0
        self.coins = 0
        self.current_level_type = None
        self.current_question_data = None


class CaesarQuestion(TypedDict):
    original_word: str
    shift: int
    encrypted_word_correct: str
    options: list[str]


def caesar_cipher(text: str, shift: int, encrypt: bool = True) -> str:
    result = []
    shift_value = shift if encrypt else -shift
    alphabets = [
        ALPHABET_RU,
        ALPHABET_EN,
    ]
    lower_maps = []
    upper_maps = []
    alpha_lengths = []
    for alphabet in alphabets:
        lower_maps.append({ch: idx for idx, ch in enumerate(alphabet)})
        upper_maps.append({ch.upper(): idx for idx, ch in enumerate(alphabet)})
        alpha_lengths.append(len(alphabet))

    for ch in text:
        replaced = False
        for alphabet, lower_map, upper_map, alpha_len in zip(
            alphabets, lower_maps, upper_maps, alpha_lengths
        ):
            if ch in lower_map:
                idx = (lower_map[ch] + shift_value) % alpha_len
                result.append(alphabet[idx])
                replaced = True
                break
            if ch in upper_map:
                idx = (upper_map[ch] + shift_value) % alpha_len
                result.append(alphabet[idx].upper())
                replaced = True
                break
        if not replaced:
            result.append(ch)

    return "".join(result)


def _generate_wrong_options(
    correct_answer: str, word: str, correct_shift: int, num_options: int = 3
) -> List[str]:
    wrong_options = set()
    while len(wrong_options) < num_options:
        wrong_shift = random.randint(1, 25)
        if wrong_shift == correct_shift:
            continue
        wrong_answer = caesar_cipher(word, wrong_shift)
        if wrong_answer != correct_answer:
            wrong_options.add(wrong_answer)

    return list(wrong_options)


def _generate_wrong_options_decrypt(
    correct_answer: str, encrypted_word: str, correct_shift: int, num_options: int = 3
) -> List[str]:
    wrong_options = set()
    while len(wrong_options) < num_options:
        wrong_shift = random.randint(1, 25)
        if wrong_shift == correct_shift:
            continue
        wrong_answer = caesar_cipher(encrypted_word, -wrong_shift)
        if wrong_answer != correct_answer:
            wrong_options.add(wrong_answer)

    return list(wrong_options)


def generate_caesar_question(difficulty_level: str = "easy") -> CaesarQuestion:
    words_easy = [
        "apple",
        "banana",
        "cat",
        "dog",
        "house",
        "jump",
        "king",
        "lamp",
        "mouse",
        "night",
        "paper",
        "queen",
        "river",
        "sun",
        "tree",
        "bread",
        "chair",
        "cloud",
        "flower",
        "green",
        "happy",
    ]
    words_medium = [
        "forest",
        "garden",
        "happy",
        "island",
        "jungle",
        "kitten",
        "lemon",
        "magic",
        "ocean",
        "planet",
        "puzzle",
        "rabbit",
        "silver",
        "tomato",
        "window",
        "camera",
        "dragon",
        "guitar",
        "muffin",
        "rocket",
    ]
    words_hard = [
        "xylophone",
        "yacht",
        "zeppelin",
        "quokka",
        "pneumonia",
        "rhythm",
        "sphinx",
        "topaz",
        "unicorn",
        "vortex",
        "zephyr",
        "awkward",
        "jazzy",
        "mystify",
        "cryptic",
        "mnemonic",
        "puzzling",
        "syndrome",
        "transfix",
        "vaporize",
    ]

    if difficulty_level == "easy":
        original_word = random.choice(words_easy)
        shift = random.randint(1, 7)
    elif difficulty_level == "medium":
        original_word = random.choice(words_medium)
        shift = random.randint(5, 15)
    else:
        original_word = random.choice(words_hard)
        shift = random.randint(10, 20)

    encrypted_word_correct = caesar_cipher(original_word, shift)

    wrong_options = _generate_wrong_options(
        encrypted_word_correct, original_word, shift, num_options=3
    )
    options_list = [encrypted_word_correct, *wrong_options]
    random.shuffle(options_list)

    return {
        "original_word": original_word,
        "shift": shift,
        "encrypted_word_correct": encrypted_word_correct,
        "options": options_list,
    }


def generate_caesar_decrypt_question(difficulty_level: str = "easy") -> CaesarQuestion:
    words_easy = [
        "apple",
        "banana",
        "cat",
        "dog",
        "house",
        "jump",
        "king",
        "lamp",
        "mouse",
        "night",
        "paper",
        "queen",
        "river",
        "sun",
        "tree",
        "bread",
        "chair",
        "cloud",
        "flower",
        "green",
        "happy",
    ]
    words_medium = [
        "forest",
        "garden",
        "happy",
        "island",
        "jungle",
        "kitten",
        "lemon",
        "magic",
        "ocean",
        "planet",
        "puzzle",
        "rabbit",
        "silver",
        "tomato",
        "window",
        "camera",
        "dragon",
        "guitar",
        "muffin",
        "rocket",
    ]
    words_hard = [
        "xylophone",
        "yacht",
        "zeppelin",
        "quokka",
        "pneumonia",
        "rhythm",
        "sphinx",
        "topaz",
        "unicorn",
        "vortex",
        "zephyr",
        "awkward",
        "jazzy",
        "mystify",
        "cryptic",
        "mnemonic",
        "puzzling",
        "syndrome",
        "transfix",
        "vaporize",
    ]

    if difficulty_level == "easy":
        decrypted_word = random.choice(words_easy)
        shift = random.randint(1, 7)
    elif difficulty_level == "medium":
        decrypted_word = random.choice(words_medium)
        shift = random.randint(5, 15)
    else:
        decrypted_word = random.choice(words_hard)
        shift = random.randint(10, 20)

    original_word = caesar_cipher(decrypted_word, shift)
    decrypted_word_correct = caesar_cipher(original_word, -shift)

    wrong_options = _generate_wrong_options_decrypt(
        decrypted_word_correct, original_word, shift, num_options=3
    )
    options_list = [decrypted_word_correct, *wrong_options]
    random.shuffle(options_list)

    return {
        "original_word": original_word,
        "shift": shift,
        "encrypted_word_correct": decrypted_word_correct,
        "options": options_list,
    }
