from abc import ABC

from .player import Player
from ..enums.betting_move import BettingMove
import math
import random

import random
import math

class MCTSNode:
    def __init__(self, game_state, parent=None, move=None):
        self.game_state = game_state
        self.parent = parent
        self.move = move
        self.children = []
        self.wins = 0
        self.visits = 0
        self.untried_actions = game_state.get_legal_actions()

    def ucb1(self, exploration_constant=1.41):
        if self.visits == 0:
            return float('inf')
        return (self.wins / self.visits) + exploration_constant * math.sqrt(math.log(self.parent.visits) / self.visits)

    def is_fully_expanded(self):
        return len(self.untried_actions) == 0

    def add_child(self, child_node):
        self.children.append(child_node)
        self.untried_actions.remove(child_node.move)

    def update(self, win):
        self.visits += 1
        self.wins += win

    def select_child(self):
        return max(self.children, key=lambda node: node.ucb1())

    def expand(self):
        action = self.untried_actions.pop()
        new_state = self.game_state.apply_action(action)
        child_node = MCTSNode(game_state=new_state, parent=self, move=action)
        self.add_child(child_node)
        return child_node

    def simulate(self):
        current_state = self.game_state
        while not current_state.is_terminal():
            possible_moves = current_state.get_legal_actions()
            action = random.choice(possible_moves)
            current_state = current_state.apply_action(action)
        return current_state.get_result(self.parent.game_state.current_player)


class MCTSTree:
    def __init__(self, root_game_state):
        self.root = MCTSNode(game_state=root_game_state)

    def select_promising_node(self):
        """
        Selects a node in the tree to expand. Chooses nodes with a balance of high win rates and unexplored potential.
        """
        current_node = self.root
        while current_node.is_fully_expanded() and not current_node.is_leaf():
            current_node = current_node.select_child()
        return current_node

    def expand_node(self, node):
        """
        Expands the given node by adding one child node for each untried action.
        """
        if not node.is_fully_expanded():
            return node.expand()

    def backpropagate(self, node, result):
        """
        Updates the node and its ancestors with the result of the simulation.
        """
        while node is not None:
            node.update(result)
            node = node.parent

    def best_move(self, simulations_number):
        """
        Executes the Monte Carlo Tree Search algorithm for a given number of simulations.
        """
        for _ in range(simulations_number):
            promising_node = self.select_promising_node()
            if not promising_node.game_state.is_terminal():
                self.expand_node(promising_node)
            simulation_result = promising_node.simulate()
            self.backpropagate(promising_node, simulation_result)

        return self.select_best_move()

    def select_best_move(self):
        """
        Selects the best move from the root node, based on the highest win rate among its children.
        """
        best_win_rate = -1
        best_move = None
        for child in self.root.children:
            if child.visits > 0:
                win_rate = child.wins / child.visits
                if win_rate > best_win_rate:
                    best_win_rate = win_rate
                    best_move = child.move
        return best_move


class MCTSAgent(Player, ABC):
    def __init__(self, name, mcts_iterations=100):
        super().__init__(name)
        self.mcts_iterations = mcts_iterations

    def choose_action(self, game_state):
        """
        Choose an action based on the MCTS algorithm.
        :param game_state: The current state of the game.
        :return: The chosen action.
        """
        mcts_tree = MCTSTree(game_state)
        best_move = mcts_tree.best_move(self.mcts_iterations)
        return best_move