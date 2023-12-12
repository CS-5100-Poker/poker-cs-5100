import copy
import random

from .enums.betting_move import BettingMove
from .prompts.text_prompt import show_table, show_cards
from .prompts import text_prompt
from .enums.phase import Phase
from .utils import hand_ranking_utils


class PokerGameState:
    def __init__(self, curr_player_index, game, table_last_best: int, raise_amount: int, players, last_action = None, phase = Phase.PREFLOP):
        self.game = game
        self.players = players
        # self.table = copy.deepcopy(self.game.table)
        self.table = self.game.table
        self.current_player = self.players[curr_player_index]
        self.our_hand = self.current_player.hand
        self.last_bet = table_last_best
        self.winnings = -table_last_best
        self.max_player_turn = True
        self.raise_amount = raise_amount
        self.phase = phase
        self.last_action = last_action
        self.agentWins = False

    def get_legal_actions(self):
        legal_actions = []
        last_bet = self.last_bet
        player_chips = self.current_player.chips

        if player_chips > 0:
            legal_actions.append(BettingMove.FOLDED)

        if player_chips > self.last_bet:
            legal_actions.append(BettingMove.RAISED)

        if self.last_bet == 0:
            legal_actions.append(BettingMove.CHECKED)
        else:
            if player_chips >= self.last_bet:
                legal_actions.append(BettingMove.CALLED)

        if self.last_bet > player_chips > 0:
            legal_actions.append(BettingMove.ALL_IN)

        return legal_actions

    def get_successor_state(self, player_index, action, simulation_deck):
        player = self.players[player_index]

        #if self.game.show_table:
        # print(f"EVALUATE: Player {player.name}; {action}")

        new_state = PokerGameState(player_index, self.game, self.last_bet, self.raise_amount,
                                   self.players, action, self.phase)
        new_state.apply_action(player, action, simulation_deck)

        # if self.game.show_table:
        # show_table(new_state.players, new_state.table)

        return new_state

    def incrementVisits(self):
        self.visits += 1
        # print(f"New visit value = {self.visits}")


    def eval_game_state(self, player_index):
        # # if self.game.show_table:
        # print("Evaluating...")
        # community = self.table.community
        # if self.current_player.name == "Agent":
        #     currentHand = self.our_hand
        # else:
        #     currentHand = []
        # if self.game.show_table:
        #     print(f"HAND: {show_cards(currentHand)}")
        # deck_copy = self.game.deck.copy()
        # value, hand = hand_ranking_utils.estimate_hand(currentHand, deck_copy, community)
        # if self.game.show_table:
        #     print(f"BEST HAND {value}")
        # #show_cards(hand)
        # return value

        player = self.players[player_index]
        start_chips = player.start_chips

        # if self.game.show_table:
            # print("Evaluating...")
            # print(f"{player.name} started with {start_chips}")
        community = self.table.community
        if self.current_player.name == "Agent":
            currentHand = self.our_hand
        else:
            currentHand = []

        # if self.game.show_table:
            #print(f"HAND: {show_cards(currentHand)}")

        value, hand = hand_ranking_utils.estimate_hand(currentHand, community)
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
        # if self.game.show_table:
            # print(f"EVAL VALUE: {ret}")
        #show_cards(hand)
        return ret

    def apply_action(self, player, action, simulation_deck):
        if action == BettingMove.FOLDED:
            #print(f"{player.name}...locking ON FOLD from {player.is_locked}")
            player.is_locked = True
            #print(f"to {player.is_locked}")
            player.fold()  # Mark the player as folded
            self.check_and_update_round(simulation_deck)
        elif action == BettingMove.CALLED:
            call_amount = self.raise_amount - self.table.last_bet
            player.chips -= call_amount
            player.bet += call_amount
            #if self.game.show_table:
                #print(f"pots {self.table.pots[0][0]} added {call_amount}")
            self.table.pots[0][0] += call_amount
            self.raise_amount = self.table.last_bet
            # print(f"{player.name}...locking ON CALL from {player.is_locked}")
            player.is_locked = True
            # print(f"to {player.is_locked}")
            self.check_and_update_round(simulation_deck)
        elif action == BettingMove.RAISED:
            raise_amount = 1000  # Determine the raise amount based on game rules
            player.chips -= raise_amount
            player.bet += raise_amount
            self.table.pots[0][0] += raise_amount
            self.table.last_bet += raise_amount
            self.raise_amount = self.table.last_bet
            for other_player in self.players:
                # print(f"{other_player.name}...")
                if other_player.name != player.name and not other_player.is_folded and not other_player.is_all_in:
                    # print(f"...unlocking ON RAISE from {player.is_locked}")
                    player.is_locked = False
                    # print(f"to {player.is_locked}")
                    self.check_and_update_round(simulation_deck)
                else:
                    # print(f"...locking on RAISE from {player.is_locked}")
                    player.is_locked = True
                    # print(f"to {player.is_locked}")
                    self.check_and_update_round(simulation_deck)
        elif action == BettingMove.ALL_IN:
            all_in_amount = player.chips
            player.chips = 0
            self.table.pots[0][0] += all_in_amount
            self.raise_amount += all_in_amount
            # print(f"{player.name}...locking on ALL IN from {player.is_locked}")
            player.is_all_in = True
            player.is_locked = True
            # print(f"to {player.is_locked}")
            self.check_and_update_round(simulation_deck)

    def check_and_update_round(self, deck):
        all_locked = (
            list(map(lambda p: f"{p.name} locked?: {p.is_locked or p.is_folded or p.is_all_in}", self.players)))
        #print(f"{all_locked}")
        if all(player.is_locked or player.is_all_in or player.is_folded for player in self.players):
            # print(f"ADVANCING from {self.phase}")
            self.advance_to_next_round(deck)

    def advance_to_next_round(self, deck):
        #print(f"{len(deck.cards)} remaining cards in deck")
        if self.phase == Phase.PREFLOP or len(self.table.community) == 0:
            self.phase = Phase.FLOP
            self.deal_community(3, deck)
        elif self.phase == Phase.FLOP or len(self.table.community) == 3:
            self.phase = Phase.TURN
            self.deal_community(1, deck)
        elif self.phase == Phase.TURN or len(self.table.community) == 4:
            self.phase = Phase.RIVER
            self.deal_community(1, deck)
        elif self.phase == Phase.RIVER or len(self.table.community) >= 5:
            self.determine_winners(deck)
            for player in self.players:
                player.fold()
        # print(f"to {self.phase}")
            # self.reset_for_next_round(deck)

    def update_turn(self):
        self.max_player_turn = not self.max_player_turn
        active_players = self.game.get_active_players()
        current_index = active_players.index(self.current_player)
        next_index = (current_index + 1) % len(active_players)
        self.current_player = active_players[next_index]

        while self.current_player.has_folded or self.current_player.is_all_in:
            next_index = (next_index + 1) % len(active_players)
            self.current_player = active_players[next_index]

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

    def is_card_draw(self):  # card_drawn if all players have matched bets, or are all in or folded
        active_players = self.game.get_active_players()
        if all(player.is_locked or player.is_all_in for player in active_players):
            return True
        if [player.is_folded for player in active_players].count(False) == 1:
            return True
        return False

    def check_game_over(self):
        """Checks if the game is over.

        If the game is not over (i.e. all but one player has no chips), ask the user if they would
        like to continue the game.

        Returns:
            bool: True if the game is over, False otherwise.
        """
        countNotFolded = 0
        for player in self.players:
            if not player.is_folded:
                countNotFolded += 1
                #print(f"Number of Players not folded: {countNotFolded}")
        if countNotFolded <= 1:
            return True

        for player in self.players:
            if player.chips == 0:
                player.is_in_game = False
        active_players = self.players
        if len(active_players) == 1:
            # text_prompt.show_table(self.players, self.table)
            # text_prompt.show_game_winners(self.players, [active_players[0].name])
            return True
        else:
            while True:
                # text_prompt.clear_screen()
                # user_choice = io_utils.input_no_return(
                #     "Continue on to next hand? Press (enter) to continue or (n) to stop.   ")
                # if 'n' in user_choice.lower():
                #     max_chips = max(self.get_active_players(), key=lambda player: player.chips).chips
                #     winners_names = [player.name for player in self.get_active_players() if player.chips == max_chips]
                #     text_prompt.show_table(self.players, self.table)
                #     text_prompt.show_game_winners(self.players, winners_names)
                #     return True
                return False

    def determine_winners(self, simulation_deck):
        """Determine the winners of each pot and award them their chips."""
        unfolded_players = [player for player in self.players if not player.is_folded]
        if len(unfolded_players) == 1:
            winnings = 0
            for pot in self.table.pots:
                winnings += pot[0]
            winner = unfolded_players[0]
            if winner.name == "Agent":
                self.agentWins = True
        else:
            # If only 1 player is eligible for last side pot (i.e. other players folded/all-in), award player that pot
            players_eligible_last_pot = []
            for player in self.players:
                if not player.is_folded:
                    players_eligible_last_pot.append(player)
            if len(players_eligible_last_pot) == 1:
                hand_winner = players_eligible_last_pot[0]
            while len(self.table.community) < 5:
                self.table.community.extend(simulation_deck.deal(1))
            self.showdown()

    def showdown(self):
        """Runs the showdown phase."""

        # Need to fix this
        # text_prompt.show_phase_change_alert('Showdown', self.dealer, self.pause)

        # Divvy chips to the winner(s) of each pot/side pot
        for i in reversed(range(len(self.table.pots))):
            showdown_players = []
            for player in self.table.pots[i][1]:
                if not player.is_folded:
                    showdown_players.append(player)
            hand_winners = hand_ranking_utils.determine_showdown_winner(showdown_players, self.table.community)
            for winner in hand_winners:
                if winner.name == "Agent":
                    self.agentWins = True

    def check_agent_wins(self):
        return self.agentWins

    def reset_for_next_round(self, simulation_deck) -> None:
        """Gets players, table, and deck ready to play another hand."""
        active_players = self.players
        # if any(player.is_human for player in active_players):
        self.reset_players()
        self.reset_table()
        self.reset_deck(simulation_deck)

    def reset_players(self) -> None:
        for player in self.players:
            player.reset()
        self.assign_positions()

    def reset_table(self) -> None:
        active_players = self.players
        self.table.reset(active_players)

    def reset_deck(self, simulation_deck) -> None:
        simulation_deck.refill()
        simulation_deck.shuffle()

    def assign_positions(self) -> None:
        """Assigns the position of the players.

        Definitions:
            first act = the player who bets first
            dealer = the player who will bet last
            small blind = the player to the left of the dealer
            big blind = the player to the left of the small blind
        """
        for player in self.players:
            player.is_SB = False
            player.is_BB = False
        if self.table.hands_played == 0:
            self.determine_positions_randomly()
        else:
            self.shift_positions_left()

    def determine_positions_randomly(self) -> None:
        active_players = self.players
        dealer_index = random.randrange(0, len(active_players))
        active_players[dealer_index].is_dealer = True
        self.dealer = active_players[dealer_index]
        # In 2 player poker, the dealer is SB and acts first pre-flop
        if len(active_players) == 2:
            active_players[dealer_index].is_SB = True
            active_players[(dealer_index + 1) % len(active_players)].is_BB = True
        else:
            active_players[(dealer_index + 2) % len(active_players)].is_BB = True
            active_players[(dealer_index + 1) % len(active_players)].is_SB = True

    def shift_positions_left(self) -> None:
        active_players = self.players
        old_dealer_index = [player is self.dealer for player in self.players].index(True)
        while True:
            old_dealer_index += 1
            player_to_left = self.players[old_dealer_index % len(self.players)]
            if player_to_left in active_players:
                self.dealer = player_to_left
                player_to_left.is_dealer = True
                new_dealer_index = next(i for i, player in enumerate(active_players) if player.is_dealer)
                # in 2 player poker, the dealer is SB and acts first pre-flop
                if len(active_players) == 2:
                    active_players[new_dealer_index].is_SB = True
                    active_players[(new_dealer_index + 1) % len(active_players)].is_BB = True
                else:
                    active_players[(new_dealer_index + 2) % len(active_players)].is_BB = True
                    active_players[(new_dealer_index + 1) % len(active_players)].is_SB = True
                break