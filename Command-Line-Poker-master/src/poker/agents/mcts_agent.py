from abc import ABC

from ..players.player import Player
from ..pokergamestate import PokerGameState
from ..enums.betting_move import BettingMove
import math
import random

import random
import math

class MCTSNode():
    def __init__(self, betting_player, game_state, parent=None, move=None):
        self.game_state = game_state
        self.parent = parent
        self.move = move
        self.wins = 0
        self.visits = 0
        self.untried_actions = game_state.get_legal_actions()
        # Stores (Ta, Na) of each action from this node
        # self.action_utilities = {BettingMove.RAISED: (0, 0), BettingMove.FOLDED: (0, 0), BettingMove.CALLED: (0, 0), BettingMove.ALL_IN: (0, 0)}
        self.player = betting_player

        successors = []
        # for action in game_state.get_legal_actions():
        #   successors.append(game_state.get_successor_state(betting_player, action))
        self.children = successors # should be empty at start, haven't seen anything

    def ucb1(self, exploration_constant=1.41):
        if self.visits == 0:
            return float('inf')
        # accumulatedReward = self.parent.action_utilities # would need to fetch
        return (self.wins / self.visits) + exploration_constant * math.sqrt(math.log(self.parent.visits) / self.visits)

    def is_fully_expanded(self):
        print(f"length of untried action: {len(self.untried_actions)}")
        return len(self.untried_actions) == 0

    def is_leaf(self):
        print(f"Game Over?: {self.game_state.game.check_game_over()}")
        return self.game_state.game.check_game_over()

    def add_child(self, child_node):
        self.children.append(child_node)

    def update(self, win):
        self.visits += 1
        self.wins += win

    def select_child(self):
        return max(self.children, key=lambda node: node.ucb1())

    def expand(self):
        print("Expand called!")
        action = self.untried_actions.pop()
        print(f"ACTION {action}")
        new_state = self.game_state.get_successor_state(self.player, action)
        # new_state.incrementVisits() # Should be incrementing for current node, not next one (indexing for nodes?)
        child_node = MCTSNode(self.player, game_state=new_state, parent=self, move=action) # get_legal_actions, don't pass down untried
        self.add_child(child_node)
        return child_node

    def simulate(self):
        current_state = self.game_state
        players = self.game_state.game.players
        current_player_index = players.index(self.player)
        while not current_state.game.check_game_over():
            possible_moves = current_state.get_legal_actions()
            action = random.choice(possible_moves)
            print(f"Simulating the game with {action}")
            current_state = current_state.get_successor_state(players[current_player_index], action)
            current_player_index = current_player_index % 1 # assumes only two players
            # add something to switch between player
            # pass in all players instead of just our player, and some index, change the index at the end of each while loop
        # return current_state.get_result(self.parent.game_state.current_player)
        return current_state.eval_game_state()


class MCTSTree():
    def __init__(self, root_game_state, betting_player):
        self.root = MCTSNode(betting_player, game_state=root_game_state)
        self.player = betting_player

    def select_promising_node(self):
        """
        Selects a node in the tree to expand. Chooses nodes with a balance of high win rates and unexplored potential.
        """
        current_node = self.root
        while current_node.is_fully_expanded() and not current_node.is_leaf():
            print(f"select child!!")
            current_node = current_node.select_child()
        return current_node

    def expand_node(self, node):
        """
        Expands the given node by adding one child node for each untried action.
        """
        if not node.is_fully_expanded(): # seems redundant
            return node.expand()

    def backpropagate(self, node, result):
        """
        Updates the node and its ancestors with the result of the simulation.
        """
        while node is not None:
            node.update(result)
            node = node.parent
            # update node with vists

        # calc average rewards

    def best_move(self, simulations_number):
        """
        Executes the Monte Carlo Tree Search algorithm for a given number of simulations.
        """
        print("Before Best move loop")
        print(f"Simulations Number: {simulations_number}")
        for _ in range(simulations_number):
            print("In Best move loop")
            promising_node = self.select_promising_node()
            print(f"BEST_MOVE is game over? {promising_node.game_state.game.check_game_over()}")
            if not promising_node.game_state.game.check_game_over():
                print("Expand Node")
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
        print("Entering FOR LOOP")
        print(f"Available children: {self.root.children}")
        for child in self.root.children:
            print("In FOR LOOP")
            print(f" Current child: {child}")
            print(f" Current child: {child.visits}")
            if child.visits > 0:
                print(f" Current child wins: {child.wins}")
                win_rate = child.wins / child.visits
                if win_rate > best_win_rate:
                    best_win_rate = win_rate
                    best_move = child.move
        return best_move


class MCTSAgent():
    def __init__(self, mcts_iterations=10):
        self.mcts_iterations = mcts_iterations

    def choose_action(self, game_state, betting_player):
        """
        Choose an action based on the MCTS algorithm.
        :param game_state: The current state of the game.
        :return: The chosen action.
        """
        print("Entering choose_action")
        mcts_tree = MCTSTree(game_state, betting_player)
        best_move = mcts_tree.best_move(self.mcts_iterations)
        return best_move