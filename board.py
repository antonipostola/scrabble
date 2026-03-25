from collections import Counter
import random
import re

import time

import numpy as np
import numpy.typing as npt

from typing import Literal, final, override



words: str

with open("./words/english_1k.txt", "r") as f:
    words = f.read()


class Move:
    pos: tuple[int, int]
    direction: Literal["down", "right"]
    word: str 
    score: int

    def __init__(self, pos: tuple[int, int], direction: Literal["down", "right"], word: str, score: int):
        self.pos = pos
        self.direction = direction
        self.word = word
        self.score = score

    @override
    def __str__(self) -> str:
        return str([self.word, self.pos, self.direction])


@final
class Board:
    @staticmethod
    def generate_letter_multiplier_grid() -> npt.NDArray[np.int_]:

        # 15x15 array of 1s
        letter_mul = np.ones((15, 15), dtype=int)

        # Rotational symmetry means we can set the DLS and TLS squares for a quarter of the board, and repeat with 4 different rotations
        for quarter in range(4):

            for double_pos in [(0, 3), (3, 0), (2, 6), (6, 2), (6, 6), (3, 7)]:
                letter_mul[double_pos] = 2

            for triple_pos in [(1, 5), (5, 1), (5, 5)]:
                letter_mul[triple_pos] = 3

            letter_mul = np.rot90(letter_mul)

        return letter_mul

    @staticmethod
    def generate_word_multiplier_grid() -> npt.NDArray[np.int_]:
        word_mul = np.ones((15, 15), dtype=int)

        # rotational symmetry means we can set the DWS and TWS squares for a quarter of the board, and repeat with 4 different rotations
        for quarter in range(4):

            for double_pos in [(1, 1), (2, 2), (3, 3), (4, 4)]:
                word_mul[double_pos] = 2

            for triple_pos in [(0, 0), (0, 7)]:
                word_mul[triple_pos] = 3

            word_mul = np.rot90(word_mul)

        # double centre
        word_mul[7, 7] = 2

        return word_mul


    LETTER_MUL = generate_letter_multiplier_grid()
    WORD_MUL = generate_word_multiplier_grid()

    grid: npt.NDArray[np.str_]

    def __init__(self) -> None:
        self.grid = np.full((15, 15), " ", dtype="U1")

    def get_row(self, row: int) -> str:
        return "".join(self.grid[row].tolist())

    def get_column(self, column: int) -> str:
        return "".join(np.rot90(self.grid)[14 - column].tolist())

    def apply_move(self, move: Move) -> None:
        if move.direction == "right":
            for i, tile in enumerate(move.word):
                self.grid[move.pos[0], move.pos[1]+i] = tile

        if move.direction == "down":
            for i, tile in enumerate(move.word):
                self.grid[move.pos[0]+i, move.pos[1]] = tile

    @staticmethod
    def get_matches(pattern: str, optional_count: int, rack: list[str]) -> list[str]:
        """ The 'pattern' str will have spaces for empty grid squares and letters for where tiles are already place: e.g. ' n    s'"""

        tiles_left = list(filter(str.isalpha, pattern)) + rack

        rack_tile_reg = f"[{''.join(rack)}]"
        
        regex = f"^{pattern.replace(" ", rack_tile_reg)}{rack_tile_reg}{{0,{optional_count}}}$"

        matches = list(filter(lambda word: Counter(tiles_left) >= Counter(word), re.findall(regex, words, re.MULTILINE)))
        return matches

    def get_possible_moves(self, rack: list[str]) -> list[Move]:

        possible_moves: list[Move] = []

        def get_moves_on_line(line: str) -> list[tuple[int, str]]:
            """ Return a list of tuples containing a word and its starting position in the line (row/column) """
            moves: list[tuple[int, str]] = []

            anchors = [element.span() for element in re.finditer(r"\S+", line)]

            possible_lefts: list[int] = list(range(15))

            possible_rights: list[int] = []

            for anchor in anchors:
                # cannot start between the second letter of a word and the first blank space succeeding it
                possible_lefts = [pos for pos in possible_lefts if not (anchor[0] < pos <= anchor[1]+1)]

                possible_rights = [anchor[1] for anchor in anchors]

            for i, anchor in enumerate(anchors):
                max_left = 0 if i == 0 else anchors[i-1][1] + 2

                if anchor[0] - len(rack) > max_left:
                    max_left = anchor[0] - len(rack)


                valid_lefts = [left for left in possible_lefts if max_left <= left <= anchor[0]]
                valid_rights = [right for right in possible_rights if right >= anchor[1]]

                for left in valid_lefts:
                    for right_i, right in enumerate(valid_rights):
                        if left == anchor[0] and right == anchor[1]:
                            right += 1

                        max_right = valid_rights[right_i+1] if right_i < len(valid_rights)-1 else 14

                        matching_words = self.get_matches(line[left:right], max_right-right, rack)
                        moves = moves + [(left, word) for word in matching_words]

            return moves

        for row_n in range(15):
            row = self.get_row(row_n)
            possible_moves.extend(
                Move((row_n, move[0]), "right", move[1], 0) 
                for move in get_moves_on_line(row)
            )

        for column_n in range(15):
            column = self.get_column(column_n)
            possible_moves.extend(
                Move((move[0], column_n), "down", move[1], 0) 
                for move in get_moves_on_line(column)
            )

        return possible_moves



def main():
    board = Board()
    board.apply_move(Move((4, 7), "down", "qwertyuiop", 0))

    rack = list("eeauinms")

    print(f"{rack = }")

    for row_n in range(15):
        print(" ".join(board.get_row(row_n).replace(" ", "-")))

    for i in range(1):

        t_before = time.time()

        moves = board.get_possible_moves(rack)
        chosen_move = random.choice(moves)

        for move in moves:
            print(move)

        # print(chosen_move)

        # board.apply_move(chosen_move)


        # for row in range(15):
        #     print(" ".join(board.get_row(row).replace(" ", "-")))

        t_after = time.time()

        print(f"Time taken = {t_after - t_before :.3f} seconds")

if __name__ == "__main__":
    main()
