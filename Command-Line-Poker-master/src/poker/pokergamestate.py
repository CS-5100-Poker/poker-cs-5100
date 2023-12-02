from .enums.betting_move import BettingMove


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
        return [BettingMove.FOLDED, BettingMove.RAISED, BettingMove.CALLED, BettingMove.ALL_IN]

    def get_successor_state(self, player, action):
        if self.game.check_game_over():
            raise Exception("Game over, no successor state")

        state = PokerGameState(self.current_player, self.game, self.last_bet)
        print(f"POKERGAMESTATE: Game state visits: {state.visits}")
        active_players = state.game.get_active_players()

        #  table_raise_amount: int, num_times_table_raised: int, table_last_best: int
        state.game.table.take_bet(player, action)  # update game
        # if action is BettingMove.FOLDED:
        #     self.our_hand = []
        #     self.winnings -= self.last_bet
        # elif action is BettingMove.RAISED:
        #     self.winnings

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
