import copy

from .enums.betting_move import BettingMove
from .prompts.text_prompt import show_table
from .enums.phase import Phase

class PokerGameState:
    def __init__(self, curr_player_index, game, table_last_best: int, raise_amount: int, players):
        self.game = game
        self.players = players
        self.table = self.game.table.copy()
        self.current_player = self.players[curr_player_index]
        self.our_hand = self.current_player.hand
        self.last_bet = table_last_best
        self.winnings = -table_last_best
        self.max_player_turn = True
        self.raise_amount = raise_amount
        self.phase = self.game.phase

    def get_legal_actions(self):
        legal_actions = []
        last_bet = self.last_bet
        player_chips = self.current_player.chips

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

    def get_successor_state(self, player_index, action, deck):
        player = self.players[player_index]

        if self.game.show_table:
            print(f"EVALUATE: Player {player.name}; {action}")

        new_state = PokerGameState(player_index, self.game, self.last_bet, self.raise_amount, self.players)
        new_state.apply_action(player, action, deck)

        new_state.max_player_turn = not self.max_player_turn

        if self.game.show_table:
            show_table(new_state.players, new_state.table)

        return new_state

    def incrementVisits(self):
        self.visits += 1
        print(f"New visit value = {self.visits}")


    def eval_game_state(self):
        if self.game.show_table:
            print("Evaluating...")
        community = self.table.community
        if self.current_player.name == "Agent":
            currentHand = self.our_hand
        else:
            currentHand = []
        if self.game.show_table:
            print(f"HAND: {show_cards(currentHand)}")
        deck_copy = self.game.deck.copy()
        value, hand = hand_ranking_utils.estimate_hand(currentHand, deck_copy, community)
        if self.game.show_table:
            print(f"BEST HAND {value}")
        #show_cards(hand)
        return value

    def apply_action(self, player, action, deck):
        if action == BettingMove.FOLDED:
            print(f"{player.name}...locking ON FOLD from {player.is_locked}")
            player.is_locked = True
            print(f"to {player.is_locked}")
            player.fold()  # Mark the player as folded
            self.check_and_update_round(deck)
        elif action == BettingMove.CALLED:
            call_amount = self.raise_amount - self.table.last_bet
            player.chips -= call_amount
            player.bet += call_amount
            if self.game.show_table:
                print(f"pots {self.table.pots[0][0]} added {call_amount}")
            self.table.pots[0][0] += call_amount
            self.raise_amount = self.table.last_bet
            print(f"{player.name}...locking ON CALL from {player.is_locked}")
            player.is_locked = True
            print(f"to {player.is_locked}")
            self.check_and_update_round(deck)
        elif action == BettingMove.RAISED:
            raise_amount = 1000  # Determine the raise amount based on game rules
            player.chips -= raise_amount
            player.bet += raise_amount
            self.table.pots[0][0] += raise_amount
            self.table.last_bet += raise_amount
            self.raise_amount = self.table.last_bet
            for other_player in self.players:
                print(f"{other_player.name}...")
                if other_player.name != player.name and not other_player.is_folded and not other_player.is_all_in:
                    print(f"...unlocking ON RAISE from {player.is_locked}")
                    player.is_locked = False
                    print(f"to {player.is_locked}")
                    self.check_and_update_round(deck)
                else:
                    print(f"...locking on RAISE from {player.is_locked}")
                    player.is_locked = True
                    print(f"to {player.is_locked}")
                    self.check_and_update_round(deck)
        elif action == BettingMove.ALL_IN:
            all_in_amount = player.chips
            player.chips = 0
            self.table.pots[0][0] += all_in_amount
            self.raise_amount += all_in_amount
            print(f"{player.name}...locking on ALL IN from {player.is_locked}")
            player.is_all_in = True
            player.is_locked = True
            print(f"to {player.is_locked}")
            self.check_and_update_round(deck)

    def check_and_update_round(self, deck):
        all_locked = (
            list(map(lambda p: f"{p.name} locked?: {p.is_locked or p.is_folded or p.is_all_in}", self.players)))
        print(f"{all_locked}")
        if all(player.is_locked or player.is_all_in or player.is_folded for player in self.players):
            print(f"ADVANCING ")
            self.advance_to_next_round(deck)

    def advance_to_next_round(self, deck):
        if self.phase == Phase.PREFLOP:
            self.phase = Phase.FLOP
            self.deal_community(3, deck)
        elif self.phase == Phase.FLOP:
            self.phase = Phase.TURN
            self.deal_community(1, deck)
        elif self.phase == Phase.TURN:
            self.phase = Phase.RIVER
            self.deal_community(1, deck)
        elif self.phase == Phase.RIVER:
            self.determine_winners()
            self.reset_for_next_round()

    def update_turn(self):
        self.max_player_turn = not self.max_player_turn
        # active_players = self.get_active_players()
        # current_index = active_players.index(self.current_player)
        # next_index = (current_index + 1) % len(active_players)
        # self.current_player = active_players[next_index]
        #
        # while self.current_player.has_folded or self.current_player.is_all_in:
        #     next_index = (next_index + 1) % len(active_players)
        #     self.current_player = active_players[next_index]

    def handle_game_over(self):
        if self.check_game_over():  # Assuming this method checks if the game is over
            self.determine_winners()
            self.distribute_pot()
            self.reset_game()

    def deal_community(self, n: int, deck) -> None:
        """Deals cards to the community.

        In poker, a card is burned before dealing to the community.

        Args:
            n: The number of cards to deal to the community
        """
        deck.burn()
        cards = deck.deal(n)
        self.table.community.extend(cards)

