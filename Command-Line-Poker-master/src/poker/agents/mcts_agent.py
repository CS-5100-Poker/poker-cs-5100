import copy
from abc import ABC
import random
import math

class MCTSNode:
    def __init__(self, agent_index, game_state, parent=None, move=None):
        self.game_state = game_state
        self.parent = parent
        self.move = move
        self.wins = 0
        self.visits = 0
        self.untried_actions = game_state.get_legal_actions()
        self.children = []
        self.player_index = agent_index

    def ucb1(self, exploration_constant=1.41):
        if self.visits == 0:
            return float('inf')
        return (self.wins / self.visits) + exploration_constant * math.sqrt(math.log(self.parent.visits) / self.visits)

    def is_fully_expanded(self):
        return len(self.untried_actions) == 0

    def is_leaf(self):
        return self.game_state.game.check_game_over()

    def add_child(self, child_node):
        self.children.append(child_node)

    def update(self, win):
        self.visits += 1
        self.wins += win

    def select_child(self):
        return max(self.children, key=lambda node: node.ucb1())

    def expand(self, simulation_deck):
        print(f"EXPANDING...")
        action = self.untried_actions.pop()
        new_state = self.game_state.get_successor_state(self.player_index, action, simulation_deck)
        child_node = MCTSNode(self.player_index, new_state, self, action)
        self.add_child(child_node)
        return child_node

    def simulate(self, simulation_deck):
        print(f"SIMULATING...")

        current_state = copy.deepcopy(self.children[len(self.children) - 1].game_state)
        index_iteration = self.player_index
        # players = copy.deepcopy(current_state.players)
        print(f"Game over OUTSIDE FOR LOOP?: {current_state.check_game_over()}")
        loopIdx = 1
        while not current_state.check_game_over():
            print(f"Current while loop iteration: {loopIdx}")
            print(f"{len(simulation_deck.cards)} remaining cards in simulation deck")
            possible_moves = current_state.get_legal_actions()
            action = random.choice(possible_moves)
            current_state = current_state.get_successor_state(index_iteration, action, simulation_deck)
            # all_locked = (
            #     list(
            #         map(lambda p: f"{p.name} locked?: {p.is_folded}", current_state.players)))
            # print(f"Current State Player Lock Status in Simulation {all_locked}")
            all_locked_game = (
                list(
                    map(lambda p: f"{p.name} locked?: {p.is_folded}", current_state.players)))
            print(f"Current State Game Active Players Lock Status in Simulation {all_locked_game}")
            index_iteration = (index_iteration + 1) % len(current_state.players)
            loopIdx += 1
        agent_wins = current_state.check_agent_wins()
        if agent_wins:
            self.wins += 1
        return 1 if agent_wins else 0

class MCTSTree:
    def __init__(self, root_game_state, agent_index, deck):
        self.root = MCTSNode(agent_index, root_game_state)
        self.deck = deck

    def select_promising_node(self):
        current_node = self.root
        while current_node.is_fully_expanded() and not current_node.is_leaf():
            current_node = current_node.select_child()
        return current_node

    def expand_node(self, node, simulation_deck):
        if not node.is_fully_expanded():
            return node.expand(simulation_deck)

    def backpropagate(self, node, result):
        while node is not None:
            node.update(result)
            node = node.parent

    def best_move(self, simulations_number):
        for i in range(simulations_number):
            simulation_deck = copy.deepcopy(self.deck)
            print(f"SIMULATION NUMBER {i}")
            promising_node = self.select_promising_node()
            if not promising_node.game_state.game.check_game_over():
                self.expand_node(promising_node, simulation_deck) # pass in copied deck here
            simulation_result = promising_node.simulate(simulation_deck)
            self.backpropagate(promising_node, simulation_result)
        return self.select_best_move()

    def select_best_move(self):
        best_win_rate = -1
        best_move = None
        for child in self.root.children:
            if child.visits > 0:
                win_rate = child.wins / child.visits
                if win_rate > best_win_rate:
                    best_win_rate = win_rate
                    best_move = child.move
        return best_move

class MCTSAgent:
    def __init__(self, game_state, deck, mcts_iterations=10):
        self.mcts_iterations = mcts_iterations
        self.game_state = game_state
        self.deck = deck

    def choose_action(self, agent_index):
        mcts_tree = MCTSTree(self.game_state, agent_index, self.deck)
        return mcts_tree.best_move(self.mcts_iterations)
