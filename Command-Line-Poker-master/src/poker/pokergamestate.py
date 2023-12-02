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
        return [BettingMove.RAISED, BettingMove.FOLDED, BettingMove.CALLED]

    def get_successor_state(self, player, action):
        print(f"ACTION: {action}")
        print(f"PLAYER: {player}")
        if self.game.check_game_over():
            raise Exception("Game over, no successor state")

        state = PokerGameState(self.current_player, self.game, self.last_bet)
        state.game.table.take_bet(player, action)
        active_players = state.game.get_active_players()

        # check status of all players, to see if locked in or not
        for active_player in active_players:
            if not active_player.is_folded:
                active_player.is_locked = False
        for person in active_players:
            if person.is_all_in:
                person.is_locked = True

        if all(player.is_locked or player.is_all_in for player in active_players):
            state.game.deal_cards()


        # check if "locked in" - everyone has called/checked
            # deal cards, update the community cards
            # or, we show cards if the community has 5
        # else
            # return

        print(f"POKERGAMESTATE: Game state visits: {state.visits}")

        show_table(state.game.players, state.game.table)

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
