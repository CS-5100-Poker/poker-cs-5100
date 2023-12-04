import copy

from .enums.betting_move import BettingMove
from .prompts.text_prompt import show_table


class PokerGameState:
    def __init__(self, curr_player, game, table_last_best: int, visits=0):
        self.game = game
        self.current_player = curr_player
        self.our_hand = curr_player.hand
        self.last_bet = table_last_best
        self.winnings = -table_last_best
        self.visits = visits

    def max_player_turn(self):
        return True

    def get_legal_actions(self):
        legal_actions = []
        current_bet = self.game.current_bet
        player_chips = self.current_player.chips

        if current_bet == 0:
            legal_actions.append(BettingMove.CHECKED)
        else:
            if player_chips >= current_bet:
                legal_actions.append(BettingMove.CALLED)

        if player_chips > current_bet:
            legal_actions.append(BettingMove.RAISED)

        if player_chips > 0:
            legal_actions.append(BettingMove.FOLDED)

        if current_bet > player_chips > 0:
            legal_actions.append(BettingMove.ALL_IN)

        return legal_actions

    def get_successor_state(self, player, action):
        new_state = copy.deepcopy(self)  # Create a deep copy of the current state
        new_state.apply_action(player, action)

        if new_state.is_round_over():
            new_state.advance_to_next_round()  # Deal new community cards if necessary

        new_state.update_turn()  # Move to the next player

        if new_state.is_game_over():
            new_state.handle_game_over()  # Determine winner, distribute pot, etc.

        print(f"POKERGAMESTATE: Game state visits: {new_state.visits}")

        print("MCTS Table Iteration ")
        show_table(new_state.game.players, new_state.game.table)

        return new_state


        # check if "locked in" - everyone has called/checked
            # deal cards, update the community cards
            # or, we show cards if the community has 5
        # else
            # return

        return state

    def incrementVisits(self):
        self.visits += 1
        print(f"New visit value = {self.visits}")


    def eval_game_state(self):
        community = self.game.table.community
        currentHand = self.our_hand
        if len(community) == 0:
            return self.current_player.best_hand_score
        # calculate based on our hand, and dealt 5
        elif len(community) == 3:
            return self.current_player.best_hand_score + 1
        # calculate based on our hand, and community 3 + dealt 2
        elif len(community) == 4:
            return self.current_player.best_hand_score + 2
        # calculate based on our hand, community 4, and dealt 1
        else:  # all cards are visible
            return self.current_player.best_hand_score + 3
        # determine the value of our hands

    def is_card_draw(self):  # card_drawn if all players have matched bets, or are all in or folded
        active_players = self.game.get_active_players()
        if all(player.is_locked or player.is_all_in for player in active_players):
            return True
        if [player.is_folded for player in active_players].count(False) == 1:
            return True
        return False