"""
A bare minimum ruzzle solver that takes a board as input and finds all words.

This program requires a file called board.txt in the same directory as the program, and board.txt will
contain the letters in the board and information about multipliers (optional). It will write all words
sorted by score into a file called words.txt. The 7 prefix files (prefixes2L.txt -> prefixes8L.txt)
are required, as well as the dictionary (TWL06Trimmed.txt). Type the board into board.txt, copying the 
format of the attached example board. The first 4 lines of board.txt should contain the letters of the board,
all caps and separated by spaces. Line 5 is blank, and lines 6-9 contain information about multipliers. 
2, 3, D, T, and - are DW, TW, DL, TL, and nothing, respectively. If you don't want to input multipliers 
just set all 16 characters to - (scores and word order won't be accurate). There are additional configuration 
options such as changing the main directory, board file name, and whether or not to print extra information.

Author: David Chen
"""
from collections import defaultdict
from pathlib import Path

""" Configure program settings"""
MAIN_DIR = Path('./')
PATH_TO_BOARD = "board.txt"
PRINT_INFO = True

""" Ruzzle Rules """
MIN_WORD_LEN = 2
MAX_WORD_LEN = 12
BOARD_SIZE = 4

""" These options can be tweaked to improve performance if necessary."""
PREFIX_LOWER_BOUND = 2
PREFIX_UPPER_BOUND = 8

""" These store the dictionary and prefixes at run time. """
DICTIONARY = None
PREFIXES = None


class RuzzleSolver:
    __slots__ = ["board", "word_mults", "board_size", "word_int_mults",
                 "points", "graph", "possible_words", "words_info"]

    def __init__(self, board, word_mults, board_size=None):
        if board_size is None:
            board_size = len(board)

        self.board = board
        self.word_mults = word_mults
        self.board_size = board_size
        self.word_int_mults = self.word_mults_to_int_array()
        self.points = self.get_points()
        self.graph = self.gen_graph()
        self.possible_words = []
        self.words_info = {}

        """ Initialize DICTIONARY and PREFIXES if they're not yet read. """
        global DICTIONARY, PREFIXES
        if DICTIONARY is None:
            DICTIONARY = get_dict()
        if PREFIXES is None:
            PREFIXES = get_prefixes()

    @classmethod
    def open(cls, file_path=MAIN_DIR / "board.txt", board_size=None):
        """ Read board from board.txt. If board_size is not set, will automatically infer the size based on the first
        line of text. Expects an empty line between the board letters and the board multiplier information."""

        with open(file_path) as file:
            lines = file.read().splitlines()

            if board_size is None:
                board_size = len(lines[0].split())

            board = [row.split() for row in lines[:board_size]]
            word_mults = [row.split() for row in lines[board_size + 1: 2 * board_size + 1]]

            return cls(board, word_mults, board_size)

    @classmethod
    def solve_file(cls, file_path=MAIN_DIR / "board.txt", board_size=None):
        board = cls.open(file_path, board_size)
        return board.all_combos()

    def dfs(self, visited, s, word, word_pts, word_mult, path):
        """Start at point s and search for words, keeping track of the word, points, and multiplier"""
        len_word = len(word)

        # store all >2 letter possible words in words_info if they are actual words
        if len_word >= MIN_WORD_LEN and word in DICTIONARY:
            score = word_pts * word_mult
            bonus = 0 if len_word < 4 else 5 * (len_word - 4)  # length bonus
            self.possible_words.append((word, score + bonus, path[:]))  # append copy of path

        visited[s] = True  # begin DFS, make sure no overlaps
        path.append(None)

        len_word += 1
        for v in self.graph[s]:  # graph[s] contains the adjacent points
            if not visited[v]:
                x, y = v

                path[-1] = v  # add position to path list
                temp_word = word + self.board[x][y]

                if len_word >= MIN_WORD_LEN:
                    if PREFIX_LOWER_BOUND <= len_word <= PREFIX_UPPER_BOUND\
                            and temp_word not in PREFIXES[len_word - PREFIX_LOWER_BOUND]:
                        continue

                    # there are no words greater than 12 letters (based on ruzzle database), so stop searching
                    if len_word == MAX_WORD_LEN and temp_word in DICTIONARY:
                        score = word_pts * word_mult
                        bonus = 0 if len_word < 4 else 5 * (len_word - 4)  # length bonus
                        self.possible_words.append((word, score + bonus, path))  # append copy of path
                        continue

                visited[v] = True

                # search from this new point
                self.dfs(visited, v, temp_word, word_pts + self.points[x][y],
                         word_mult * self.word_int_mults[x][y], path)

                # reset everything to continue to search in other directions
                visited[v] = False

        del path[-1]

    def all_combos(self):
        """ Returns all possible combinations of letters in board"""
        if self.possible_words:
            return self.possible_words

        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                visited = {(i, j): False for i in range(BOARD_SIZE) for j in range(BOARD_SIZE)}
                self.dfs(visited, (x, y), self.board[x][y], self.points[x][y], self.word_int_mults[x][y], [(x, y)])
        return self.possible_words

    def check_words(self, remove_bases=False):
        """returns actual words and points and removes base words if True (removes 'sleep' if 'sleeping' is a word)"""
        # Keep actual words and sort by score (to keep the best words).
        if not self.possible_words:
            self.all_combos()

        words_info = [word for word in self.possible_words if word[0] in DICTIONARY]
        words_info.sort(key=lambda x: x[1])

        # remove 'walk' if 'walks' is a word
        if remove_bases:
            all_words = {word[0] for word in words_info}
            words_info = {j for i, j in enumerate(words_info) if all(j[0] not in k for k in all_words)}

        self.words_info = {word: (score, path) for word, score, path in words_info}
        return self.words_info

    def write_words_to_file(self, print_info=False):
        """ Writes all words and initial positions to words.txt. If the board has not yet been solved, will first solve
        it. """
        if not self.words_info:
            self.all_combos()
            self.check_words()

        with open(MAIN_DIR / 'words.txt', 'w') as words_file:
            # take words_info and sort by score first, then sort by length
            # words_info.items() is a list of tuples: [(word, (score, path)) ...]
            high_scores = sorted(self.words_info.items(), key=lambda x: (-x[1][0], len(x[0])))
            for word, info in high_scores:
                print(word, info[0], file=words_file)
            if print_info:
                print('Number of words:', len(high_scores))
                print('Total score:', sum(info[0] for word, info in high_scores))

    def get_points(self):
        """ Gets the points for each letter, including multipliers"""
        points = []
        for i in range(4):  # row
            row_pts = []
            for j in range(4):  # column
                pts = self.get_letter_pts(self.board[i][j])
                mult = self.word_mults[i][j]
                if mult == 'D':
                    pts *= 2
                elif mult == 'T':
                    pts *= 3
                row_pts.append(pts)
            points.append(row_pts)
        return points

    @staticmethod
    def get_letter_pts(l):
        """ Return point value for each letter (no bonuses)"""
        letter_points = {'A': 1, 'B': 4, 'C': 4, 'D': 2, 'E': 1, 'F': 4, 'G': 3, 'H': 4, 'I': 1, 'J': 10, 'K': 5,
                         'L': 1,
                         'M': 3, 'N': 1, 'O': 1, 'P': 4, 'Q': 10, 'R': 1, 'S': 1, 'T': 1, 'U': 2, 'V': 4, 'W': 4,
                         'X': 8,
                         'Y': 4, 'Z': 8}
        return letter_points[l]

    def word_mults_to_int_array(self):
        """ Converts word_mults to an array of integers representing the word score multipliers. """
        int_word_mults = [[1] * self.board_size for _ in range(self.board_size)]
        for i in range(self.board_size):
            for j in range(self.board_size):
                int_word_mults[i][j] = int(self.word_mults[i][j]) if self.word_mults[i][j].isdigit() else 1
        return int_word_mults

    def gen_graph(self):
        """stores grid positions into adjacency list"""
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
        graph = defaultdict(list)
        # for each point (key), store the adjacent points (values) in graph
        for x in range(self.board_size):
            for y in range(self.board_size):
                for cx, cy in directions:
                    if 0 <= x + cx < self.board_size and 0 <= y + cy < self.board_size:
                        graph[(x, y)].append((x + cx, y + cy))

        return graph


def get_dict():
    """ Returns set of words in dictionary (checking to see if a word is in a set is faster than a list) """
    dict_file = MAIN_DIR / 'TWL06Trimmed.txt'
    return set(open(dict_file).read().splitlines())


def get_prefixes():
    """ Returns a list of lists of prefixes of a certain number of letters """
    prefixes = []
    for i in range(PREFIX_LOWER_BOUND, PREFIX_UPPER_BOUND + 1):
        with open(MAIN_DIR / f'prefixes{i}L.txt') as file:
            prefixes.append(set(file.read().splitlines()))
    return prefixes


if __name__ == '__main__':
    # Reading data
    DICTIONARY = get_dict()
    PREFIXES = get_prefixes()

    # Solving
    ruzzleSolver = RuzzleSolver.open(MAIN_DIR / "board.txt")
    ruzzleSolver.write_words_to_file(print_info=PRINT_INFO)
