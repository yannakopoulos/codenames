#!/usr/bin/env python
from __future__ import absolute_import, division, print_function
import numpy as np
import gensim as gs
from itertools import combinations


def verify(clue, words):
    if '_' in clue:
        return False
    for word in words:
        if word.lower() in clue.lower() or clue.lower() in word.lower():
            return False
    return True


print('Who is first: (R)ed or (B)lue?')
first = input()
if first == 'R':
    n_red = 9
    n_blue = 8
elif first == 'B':
    n_red = 8
    n_blue = 9
else:
    raise ValueError('Must input either R or B')

n_neutral = 7
n_assassin = 1

board = {'red': [], 'blue': [], 'neutral': [], 'assassin': []}

print('Which words are red?')
for i in range(n_red):
    board['red'].append(input())

print('Which words are blue?')
for i in range(n_blue):
    board['blue'].append(input())

print('Which words are neutral?')
for i in range(n_neutral):
    board['neutral'].append(input())

print('Which word is the assassin?')
for i in range(n_assassin):
    board['assassin'].append(input())

print('Which team are we: (R)ed or (B)lue?')
team = input()
if team == 'R':
    ours = 'red'
    theirs = 'blue'
elif team == 'B':
    ours = 'blue'
    theirs = 'red'
else:
    raise ValueError('Must input either R or B')

all_words = board['blue'] + board['red'] + \
            board['neutral'] + board['assassin']

model = gs.models.KeyedVectors.load_word2vec_format(
    'wiki.en.vec', binary=False, limit=100000)

# model = gs.models.KeyedVectors.load_word2vec_format(
#     'GoogleNews-vectors-negative300.bin', binary=True, limit=100000)

game_finished = False

while not game_finished:
    clusters = [comb for i in range(len(board[ours]))
                for comb in combinations(board[ours], i + 1)]

    clue_scores = {}
    clue_words = {}
    clue_bad_words = {}

    for cluster in clusters:
        clues = model.most_similar(positive=cluster)
        guesses = len(cluster)

        for clue, _ in clues:
            scores = {}
            if verify(clue, all_words):
                for word in all_words:
                    scores[word] = model.similarity(clue, word)

                sorted_words = sorted(scores, key=scores.get, reverse=True)
                bins = np.histogram(list(scores.values()),
                                    [-1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 1])[0][::-1]

                points = 0
                guesses_left = guesses
                still_our_turn = 1

                good_words = []
                bad_words = []

                for i in range(len(bins)):
                    bin_words = sorted_words[sum(bins[:i]):sum(bins[:i]) + bins[i]]
                    n_good_guesses = 0

                    for word in bin_words:
                        if word in board[ours]:
                            points += 1 * still_our_turn
                            n_good_guesses += 1
                            good_words.append(word)
                        elif word in board[theirs]:
                            points -= 1  # * still_our_turn
                            bad_words.append(word)
                        elif word in board['assassin']:
                            points -= 10  # * still_our_turn
                            bad_words.append(word)
                        else:
                            # points -= 0.5 / bins[i]  # * still_our_turn
                            bad_words.append(word)

                    if bins[i] > 0:
                        still_our_turn *= n_good_guesses / bins[i]

                    guesses_left -= bins[i]
                    if guesses_left <= 0:
                        break

                    if i > len(bins)/2 and points <= 0:
                        break

                clue_with_guesses = clue + ' ' + str(len(good_words))

                clue_scores[clue_with_guesses] = points
                clue_words[clue_with_guesses] = good_words
                clue_bad_words[clue_with_guesses] = bad_words

    print('Clue\tScore')
    print('----\t-----')

    sorted_clues = sorted(clue_scores, key=clue_scores.get, reverse=True)[:10]
    for clue in sorted_clues:
        print('{}\t{}\nour words: {}\nbad words: {}\n'
                .format(clue, clue_scores[clue], clue_words[clue],
                        clue_bad_words[clue]))

    print('What did they guess? Input "#" when finished.')
    still_guessing = True
    guesses = []
    while still_guessing:
        guess = input()
        if guess == '#':
            still_guessing = False
        else:
            guesses.append(guess)

    board[ours] = [word for word in board[ours]
                   if word not in guesses]
    board[theirs] = [word for word in board[theirs]
                     if word not in guesses]
    board['neutral'] = [word for word in board['neutral']
                        if word not in guesses]
    board['assassin'] = [word for word in board['assassin']
                         if word not in guesses]

    if len(board[ours]) == 0 or len(board[theirs]) == 0 \
            or len(board['assassin']) == 0:
        print('Game over!')
        game_finished = True
