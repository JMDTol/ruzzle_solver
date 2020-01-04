"""
A bare minimum ruzzle solver that takes a board as input and finds all words.

This program requires a file called board.txt in the same directory as the program, and board.txt will 
contain the letters in the board and information about multipliers (optional). It will write all words
sorted by score into a file called words.txt. The 5 prefix files (prefixes2L.txt -> prefixes6L.txt)
are required, as well as the dictionary (TWL06.txt). At the bottom of this file, set main_dir to the path to the 
directory with all the files. Type the board into board.txt, copying the format of the attached example board.
The first 4 lines of board.txt should contain the letters of the board, all caps and separated by spaces.
Line 5 is blank, and lines 6-9 contain information about multipliers. 2, 3, D, T, and - are DW, TW, DL, TL, and nothing
respectively. If you don't want to input multipliers just set all 16 characters to - (scores and word order won't be
accurate). There are additional configuration options towards the bottom of the file with explanations.

Author: David Chen
"""
from collections import defaultdict
from pathlib import Path


def read_board_from_file():
    """read board from board.txt"""
    with open(main_dir / 'board.txt') as file:
        lines = file.read().splitlines()
        board = [row.split() for row in lines[:4]]
        word_mults = [row.split() for row in lines[5:9]]

    return board, word_mults


def get_points(board, word_mults):
    """gets the points for each letter, including multipliers"""
    points = []
    for i in range(4):  # row
        row_pts = []
        for j in range(4):  # column
            pts = get_letter_pts(board[i][j])
            mult = word_mults[i][j]
            if mult == 'D':
                pts *= 2
            elif mult == 'T':
                pts *= 3
            row_pts.append(pts)
        points.append(row_pts)
    return points


def gen_graph():
    """stores grid positions into adjacency list"""
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    graph = defaultdict(list)
    # for each point (key), store the adjacent points (values) in graph
    for x in range(4):
        for y in range(4):
            for cx, cy in directions:
                if 0 <= x + cx < 4 and 0 <= y + cy < 4:
                    graph[(x, y)].append((x + cx, y + cy))

    return graph


def dfs(graph, visited, s, word, word_pts, word_mult, path):
    """Start at point s and search for words, keeping track of the word, points, and multiplier"""
    global words_info, points, word_int_mults
    len_word = len(word)

    # store all >2 letter possible words in words_info if they are actual words
    if len_word >= 2:
        # ex) if a word begins with TTH, this doesn't exist so we can stop adding letters
        if len_word <= 9 and word not in prefixes[len_word - 2]:
            return

        if word in dictionary:
            score = word_pts * word_mult
            bonus = 0 if len_word < 4 else 5 * (len_word - 4)  # length bonus
            words_info.append((word, score + bonus, path[:]))  # append copy of path

        # there are no words greater than 12 letters (based on ruzzle database), so stop searching
        if len_word == 12:
            return

    visited[s] = True  # begin DFS, make sure no overlaps
    path.append(None)

    for v in graph[s]:  # graph[s] contains the adjacent points

        if not visited[v]:
            x, y = v
            path[-1] = v  # add position to path list
            visited[v] = True

            # search from this new point
            dfs(graph, visited, v, word + board[x][y], word_pts + points[x][y], word_mult * word_int_mults[x][y], path)

            # reset everything to continue to search in other directions
            visited[v] = False

    del path[-1]


def all_combos(board, points, word_int_mults):
    """returns all possible combinations of letters in board"""
    graph = gen_graph()

    for x in range(4):
        for y in range(4):
            visited = {(i, j): False for i in range(4) for j in range(4)}
            word_mult = word_int_mults[x][y]
            dfs(graph, visited, (x, y), board[x][y], points[x][y], word_mult, [(x, y)])


def get_dict():
    """returns set of words in dictionary (checking to see if a word is in a set is faster than a list)"""
    dict_file = main_dir / 'TWL06Trimmed.txt'
    return set(open(dict_file).read().splitlines())


def check_words(words_info, remove_bases=False):
    """returns actual words and points and removes base words if True (removes 'sleep' if 'sleeping' is a word)"""
    # Keep actual words and sort by score (to keep the best words).
    words_info = [word for word in words_info if word[0] in dictionary]
    words_info.sort(key=lambda x: x[1])

    # remove 'walk' if 'walks' is a word
    if remove_bases:
        all_words = {word[0] for word in words_info}
        words_info = {j for i, j in enumerate(words_info) if all(j[0] not in k for k in all_words)}

    words_info = {word: (score, path) for word, score, path in words_info}
    return words_info


def write_words_to_file(words_info, print_info=False):
    """writes all words and initial positions to words.txt"""
    with open(main_dir / 'words.txt', 'w') as words_file:
        # take words_info and sort by score first, then sort by length
        # words_info.items() is a list of tuples: [(word, (score, path)) ...]
        high_scores = sorted(words_info.items(), key=lambda x: (-x[1][0], len(x[0])))
        for word, info in high_scores:
            print(word, info[0], file=words_file)
        if print_info:
            print('Number of words:', len(high_scores))
            print('Total score:', sum(info[0] for word, info in high_scores))


def get_letter_pts(l):
    """Return point value for each letter (no bonuses)"""
    letter_points = {'A': 1, 'B': 4, 'C': 4, 'D': 2, 'E': 1, 'F': 4, 'G': 3, 'H': 4, 'I': 1, 'J': 10, 'K': 5, 'L': 1,
                     'M': 3, 'N': 1, 'O': 1, 'P': 4, 'Q': 10, 'R': 1, 'S': 1, 'T': 1, 'U': 2, 'V': 4, 'W': 4, 'X': 8,
                     'Y': 4, 'Z': 8}
    return letter_points[l]


def get_prefixes():
    """returns a list of lists of prefixes of a certain number of letters"""
    prefixes = []
    for i in range(2, 9):
        with open(main_dir / f'prefixes{i}L.txt') as file:
            prefixes.append(set(file.read().splitlines()))
    return prefixes


def word_mults_to_int_array():
    """ Converts word_mults to an array of integers representing the word score multipliers. """
    int_word_mults = [[1] * 4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            int_word_mults[i][j] = int(word_mults[i][j]) if word_mults[i][j] in '23' else 1
    return int_word_mults



if __name__ == '__main__':
    # configs
    print_info = True  # if True, outputs information about board: number of words and total score

    # directory with all necessary files 
    main_dir = Path('./')
    
    # Reading data
    dictionary = get_dict()
    prefixes = get_prefixes()
    board, word_mults = read_board_from_file()

    # Solving
    word_int_mults = word_mults_to_int_array()
    points = get_points(board, word_mults)
    words_info = []
    all_combos(board, points, word_int_mults)
    words_info = check_words(words_info)
    
    # Writing results to file
    write_words_to_file(words_info, print_info=print_info)
