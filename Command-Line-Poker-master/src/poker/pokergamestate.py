import copy

from .enums.betting_move import BettingMove
from .prompts.text_prompt import show_table
from src.poker.utils import hand_ranking_utils


class PokerGameState:
    def __init__(self, game, deck, table_last_best: int, raise_amount: int, players, last_action = None, curr_player_index=None):
        self.game = game
        self.players = players
        self.table = copy.deepcopy(self.game.table)
        self.current_player = self.players[curr_player_index] if curr_player_index else None
        self.our_hand = self.current_player.hand if curr_player_index else []
        self.our_chips = self.current_player.chips if curr_player_index else []
        self.last_bet = table_last_best
        self.winnings = -table_last_best
        self.deck = deck
        self.max_player_turn = True
        self.raise_amount = raise_amount
        self.phase = self.game.phase
        self.last_action = last_action


    def max_player_turn(self):
        return self.max_player_turn

    def get_legal_actions(self):
        legal_actions = []

        if all(player.is_locked or player.is_all_in for player in self.players):
            return legal_actions

        last_bet = self.last_bet
        player_chips = self.current_player.chips if self.current_player else 0

        if self.last_bet == 0:
            legal_actions.append(BettingMove.CHECKED)
        else:
            if player_chips >= self.last_bet:
                legal_actions.append(BettingMove.CALLED)

        if player_chips > self.last_bet:
            legal_actions.append(BettingMove.RAISED)

        if player_chips > 0:
            legal_actions.append(BettingMove.FOLDED)

        if self.last_bet > player_chips > 0:
            legal_actions.append(BettingMove.ALL_IN)

        return legal_actions

    def get_successor_state(self, player_index, action):
        player = self.players[player_index]

        if self.game.show_table:
            print(f"EVALUATE: Player {player.name}; {action}")

        new_state = PokerGameState(self.game, self.deck, self.last_bet, self.raise_amount, self.players, action, player_index)
        new_state.apply_action(player, action)

        new_state.max_player_turn = not self.max_player_turn

        if self.game.show_table:
            show_table(new_state.players, new_state.table)

        return new_state

    def eval_game_state(self, player_index):
        player = self.players[player_index]
        start_chips = player.start_chips

        if self.game.show_table:
            print("Evaluating...")
            print(f"{player.name} started with {start_chips}")
        community = self.table.community
        if self.current_player.name == "Agent":
            currentHand = self.our_hand
        else:
            currentHand = []

        if self.game.show_table:
            print(f"HAND: {show_cards(currentHand)}")

        value, hand = hand_ranking_utils.estimate_hand(currentHand, self.deck, community)
        # print(f"{len(self.deck.cards)} remaining cards in deck")
        prob_win = value / 100000000000  # lol make this better
        end_chips = self.game.get_agent_chips()
        ret = 0
        if self.last_action is None:
            ret = end_chips - start_chips
        elif self.last_action == BettingMove.FOLDED:
            ret = end_chips - start_chips
        elif self.last_action == BettingMove.RAISED:
            raise_amt = 1000
            num_if_win = self.table.pots[0][0] + len(self.players) * raise_amt
            num_if_lose = end_chips - start_chips - raise_amt
            ret = prob_win * num_if_win + (1-prob_win) * num_if_lose
        elif self.last_action == BettingMove.CALLED:
            num_if_win = self.table.pots[0][0] + len(self.players) * self.last_bet
            num_if_lose = end_chips - start_chips - self.last_bet
            ret = prob_win * num_if_win + (1 - prob_win) * num_if_lose
        else:
            num_if_win = 2 * start_chips
            num_if_lose = - 2 * start_chips
            ret = prob_win * num_if_win + (1 - prob_win) * num_if_lose
        #
        if self.game.show_table:
            print(f"EVAL VALUE: {ret}")
        # #show_cards(hand)
        return ret

    def is_card_draw(self): # card_drawn if all players have matched bets, or are all in or folded
        active_players = self.players
        if all(player.is_locked or player.is_all_in for player in active_players):
            return True
        if [player.is_folded for player in active_players].count(False) == 1:
            return True
        return False

    def apply_action(self, player, action):
        if action == BettingMove.FOLDED:
            player.is_locked = True
            player.fold()  # Mark the player as folded
        elif action == BettingMove.CALLED:
            call_amount = self.raise_amount - self.table.last_bet
            player.chips -= call_amount
            player.bet += call_amount
            if self.game.show_table:
                print(f"pots {self.table.pots[0][0]} added {call_amount}")
            self.table.pots[0][0] += call_amount
            self.raise_amount = self.table.last_bet
            player.is_locked = True
        elif action == BettingMove.RAISED:
            raise_amount = 1000  # Determine the raise amount based on game rules
            player.chips -= raise_amount
            player.bet += raise_amount
            self.table.pots[0][0] += raise_amount
            self.table.last_bet += raise_amount
            self.raise_amount = self.table.last_bet
            for other_player in self.players:
                if other_player.name != player.name and not other_player.is_folded and not other_player.is_all_in:
                    player.is_locked = False
                else:
                    player.is_locked = True
        elif action == BettingMove.ALL_IN:
            all_in_amount = player.chips
            player.chips = 0
            self.table.pots[0][0] += all_in_amount
            self.raise_amount += all_in_amount
            player.is_all_in = True
            player.is_locked = True

        #self.update_round_status()
    # def check_and_update_round(self, deck):
    #     all_locked = (
    #         list(map(lambda p: f"{p.name} locked?: {p.is_locked or p.is_folded or p.is_all_in}", self.players)))
    #     print(f"{all_locked}")
    #     if all(player.is_locked or player.is_all_in or player.is_folded for player in self.players):
    #         print(f"ADVANCING ")
    #         self.advance_to_next_round(deck)

    def advance_to_next_round(self):
        if self.phase == Phase.PREFLOP:
            self.phase = Phase.FLOP
            self.game.deal_community(3)
        elif self.phase == Phase.FLOP:
            self.phase = Phase.TURN
            self.game.deal_community(1)
        elif self.phase == Phase.TURN:
            self.phase = Phase.RIVER
            self.game.deal_community(1)
        elif self.phase == Phase.RIVER:
            self.game.determine_winners()
            self.game.reset_for_next_round()

    def update_turn(self):
        self.max_player_turn = not self.max_player_turn
        # active_players = self.game.get_active_players()
        # current_index = active_players.index(self.current_player)
        # next_index = (current_index + 1) % len(active_players)
        # self.current_player = active_players[next_index]
        #
        # while self.current_player.is_folded or self.current_player.is_all_in:
        #     next_index = (next_index + 1) % len(active_players)
        #     self.current_player = active_players[next_index]

    # def handle_game_over(self):
    #     if self.game.check_game_over():  # Assuming this method checks if the game is over
    #         self.game.determine_winners()
    #         #self.distribute_pot()
    #         self.game.reset_game()

    def check_game_over(self):
        """Checks if the game is over.

        If the game is not over (i.e. all but one player has no chips), ask the user if they would
        like to continue the game.

        Returns:
            bool: True if the game is over, False otherwise.
        """
        end_chips = self.get_agent_chips()
        print(f"NET: {end_chips - self.start_chips}")
        for player in self.get_active_players():
            if player.chips <= 0:
                player.is_in_game = False
        active_players = self.get_active_players()
        if len(active_players) == 1 and self.show_table:
            text_prompt.show_table(self.players, self.table)
            text_prompt.show_game_winners(self.players, [active_players[0].name])
            return True
        else:
            while True:
                if self.show_table:
                    text_prompt.clear_screen()
                # user_choice = io_utils.input_no_return(
                #       "Continue on to next hand? Press (enter) to continue or (n) to stop.   ")
                # if 'n' in user_choice.lower(): # if self.remaining_rounds != 0:
                #     max_chips = max(self.get_active_players(), key=lambda player: player.chips).chips
                #     winners_names = [player.name for player in self.get_active_players() if player.chips == max_chips]
                #     if self.show_table:
                #         text_prompt.show_table(self.players, self.table)
                #         text_prompt.show_game_winners(self.players, winners_names)
                #     return True
                return False

    def make_features(self):
        # our hand & shared cards
        community = self.table.community
        currentHand = self.our_hand
        hand_value = hand_ranking_utils.estimate_hand(currentHand, self.deck, community)[0]
        cards_array = [0] * 4
        if 5000000000 <= hand_value < 10000000000:
            cards_array[0] = 1
        elif 10000000000 <= hand_value < 15000000000:
            cards_array[1] = 1
        elif 15000000000 <= hand_value < 20000000000:
            cards_array[2] = 1
        elif 20000000000 <= hand_value:
            cards_array[3] = 1

        # pot size
        # [0, 0, 0, 0] based on ranges
        pots = self.game.table.pots[0] if len(self.game.table.pots) > 0 else 100000
        pot_size = [0] * 4
        if 50000 <= pots < 100000:
            pot_size[0] = 1
        elif 100000 <= pots < 150000:
            pot_size[1] = 1
        elif 150000 <= pots < 200000:
            pot_size[2] = 1
        elif 200000 <= pots:
            pot_size[3] = 1

        # our chips based on ranges
        chips = self.our_chips
        our_chips = [0] * 4
        if 50000 <= chips < 100000:
            our_chips[0] = 1
        elif 100000 <= chips < 150000:
            our_chips[1] = 1
        elif 150000 <= chips < 200000:
            our_chips[2] = 1
        elif 200000 <= chips:
            our_chips[3] = 1

        return cards_array + pot_size + our_chips # track order