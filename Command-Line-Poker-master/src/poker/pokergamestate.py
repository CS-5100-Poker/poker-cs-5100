from __future__ import annotations

import random

from src.poker.deck import Deck
from src.poker.enums.betting_move import BettingMove
from src.poker.enums.computer_playing_style import ComputerPlayingStyle
from src.poker.enums.phase import Phase
from src.poker.players.computer import Computer
from src.poker.players.human import Human
from src.poker.players.player import Player
from src.poker.prompts import text_prompt
from src.poker.table import Table
from src.poker.utils import hand_ranking_utils
from src.poker.utils import io_utils
from src.poker.agents.expectiminimax import Expectiminimax
from .prompts.text_prompt import show_table
from .prompts.text_prompt import show_cards



class Game:
    """Control center of the game."""

    def __init__(self, remaining_rounds, log_table):
        self.phase = Phase.PREFLOP
        self.deck = Deck()
        self.players = []
        self.dealer = None
        self.table = Table()
        self.short_pause = 1.0
        self.pause = 2.0
        self.long_pause = 3.0
        self.agent_name = "Agent"
        self.remaining_rounds = remaining_rounds
        self.start = 0
        self.net_wins = []
        self.show_table = log_table
        self.setup()
        self.start_chips = self.get_agent_chips()

    def play(self, games_total) -> None:
        """Runs the main loop of the game."""
        while True:
            print(f"GAMES REMAINING: {games_total}")
            rounds_total = self.remaining_rounds
            self.reset_for_next_round()
            while rounds_total != 0:
                for phase in Phase:
                    self.phase = phase
                    self.deal_cards()
                    self.run_round_of_betting()
                    if self.check_hand_over():
                        # end_chips = self.get_agent_chips()
                        # self.net_wins.append(end_chips - self.start_chips)
                        # print(f"ROUNDS LEFT: {rounds_total}")
                        break
                end_chips = self.get_agent_chips()
                self.net_wins.append(end_chips - self.start_chips)
                print(f"ROUNDS LEFT: {rounds_total}")
                # break
                self.determine_winners()
                self.table.hands_played += 1
                rounds_total -= 1
            if self.check_game_over():
                break
            #games_total -= 1


    def setup(self) -> None:
        """Sets up the game before any rounds are run."""
        num_computer_players = 1
        starting_chips = 100000
        self.create_players(num_computer_players, starting_chips)
        self.table.big_blind = 2000

    def create_players(self, num_computer, starting_chips) -> None:
        playing_style1 = random.choice(list(ComputerPlayingStyle))
        human = Computer(self.agent_name, playing_style1)
        self.players.append(human)
        names = ['Homer', 'Bart', 'Lisa', 'Marge', 'Milhouse', 'Moe', 'Maggie', 'Nelson', 'Ralph']
        computer_names = [n for n in names if n != human.name]
        random.shuffle(computer_names)
        for _ in range(num_computer):
            playing_style = random.choice(list(ComputerPlayingStyle))
            computer = Computer(computer_names.pop(), playing_style)
            self.players.append(computer)
        for player in self.players:
            player.chips = starting_chips

    def reset_for_next_round(self) -> None:
        """Gets players, table, and deck ready to play another hand."""
        active_players = self.get_active_players()
        # if any(player.is_human for player in active_players):
        if any(isinstance(player, Human) for player in active_players):
            self.set_game_speed(is_fast=False)
        else:
            self.set_game_speed(is_fast=True)
        self.reset_players()
        self.reset_table()
        self.reset_deck()

    def reset_players(self) -> None:
        for player in self.players:
            player.reset()
        self.assign_positions()

    def reset_table(self) -> None:
        active_players = self.get_active_players()
        self.table.reset(active_players)
        if self.table.check_increase_big_blind() and self.show_table:
            if self.show_table:
                text_prompt.clear_screen()
                text_prompt.show_table(self.players, self.table)
                text_prompt.show_blind_increase(self.table.big_blind, self.long_pause)

    def reset_deck(self) -> None:
        self.deck.refill()
        self.deck.shuffle()
        if self.show_table:
            if self.show_table:
                text_prompt.clear_screen()
                text_prompt.show_shuffling(self.pause)

    def set_game_speed(self, is_fast: bool) -> None:
        pass
        if is_fast:
            self.short_pause = 0.5
            self.pause = 1.0
            self.long_pause = 1.5
        else:
            self.short_pause = 1.0
            self.pause = 2.0
            self.long_pause = 3.0

    def assign_positions(self) -> None:
        """Assigns the position of the players.

        Definitions:
            first act = the player who bets first
            dealer = the player who will bet last
            small blind = the player to the left of the dealer
            big blind = the player to the left of the small blind
        """
        for player in self.get_active_players():
            player.is_SB = False
            player.is_BB = False
        if self.table.hands_played == 0:
            self.determine_positions_randomly()
        else:
            self.shift_positions_left()

    def determine_positions_randomly(self) -> None:
        active_players = self.get_active_players()
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
        active_players = self.get_active_players()
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

    def deal_cards(self) -> None:
        """Deals cards to the hold and the community."""
        if self.phase is Phase.PREFLOP:
            if self.show_table:
                text_prompt.show_table(self.players, self.table)
                text_prompt.show_phase_change_alert(self.phase, self.dealer.name, self.long_pause)
            self.deal_hole()
        elif self.phase is Phase.FLOP:
            if self.show_table:
                text_prompt.show_phase_change_alert(self.phase, self.dealer.name, self.long_pause)
            self.deal_community(3)
        else:
            if self.show_table:
                text_prompt.show_phase_change_alert(self.phase, self.dealer.name, self.long_pause)
            self.deal_community(1)
        if self.show_table:
            text_prompt.show_table(self.players, self.table)

    def deal_hole(self) -> None:
        """Deals two cards to each player.

        In poker, you deal one card to each player at a time.
        """
        if self.show_table:
            text_prompt.show_table(self.players, self.table, self.short_pause)
            text_prompt.show_dealing_hole(self.dealer.name, self.pause)
        for i in range(2):
            for player in self.get_active_players():
                card = self.deck.deal(1)
                player.hand.extend(card)

    def deal_community(self, n: int) -> None:
        """Deals cards to the community.

        In poker, a card is burned before dealing to the community.

        Args:
            n: The number of cards to deal to the community
        """
        self.deck.burn()
        cards = self.deck.deal(n)
        self.table.community.extend(cards)

    def run_round_of_betting(self):
        """Runs a round of betting."""
        self.table.num_times_raised = 0
        active_players = self.get_active_players()
        if self.phase is Phase.PREFLOP:
            self.run_small_blind_bet()
            self.run_big_blind_bet()
        first_act = self.get_index_first_act()
        # End round of betting when all but one player fold or when all unfolded players have locked in their bets
        self.bet_util_all_locked_in(first_act, active_players)
        for player in active_players:
            if not player.is_folded and not player.is_all_in:
                player.is_locked = False
        self.table.calculate_side_pots(active_players)
        if self.show_table:
            text_prompt.show_table(self.players, self.table)

    def run_small_blind_bet(self) -> None:
        player = next(player for player in self.players if player.is_SB)
        if self.show_table:
            text_prompt.show_bet_blind(player.name, 'small', self.pause)
            wentAllIn = self.table.take_small_blind(player)
            if wentAllIn:
                text_prompt.show_player_move(player, BettingMove.ALL_IN, self.pause)
            text_prompt.show_table(self.players, self.table)

    def run_big_blind_bet(self) -> None:
        player = next(player for player in self.players if player.is_BB)
        if self.show_table:
            text_prompt.show_bet_blind(player.name, 'big', self.pause)
            wentAllIn = self.table.take_big_blind(player)
            if wentAllIn:
                text_prompt.show_player_move(player, BettingMove.ALL_IN, self.pause)
            text_prompt.show_table(self.players, self.table)

    def get_index_first_act(self) -> int:
        """Determines the index of the first act.

        Returns:
            The index of the first act
        """
        active_players = self.get_active_players()
        if len(active_players) == 2:
            if active_players[0].is_dealer:
                return 0
            else:
                return 1
        if self.phase is Phase.PREFLOP:
            BB_index = next(i for i, player in enumerate(active_players) if player.is_BB)
            return (BB_index + 1) % len(active_players)
        else:
            dealer_index = next(i for i, player in enumerate(active_players) if player.is_dealer)
            return (dealer_index + 1) % len(active_players)

    def bet_util_all_locked_in(self, first_act: int, active_players: list[Player]) -> None:
        betting_index = first_act
        while True:
            if all(player.is_locked or player.is_all_in for player in active_players):
                break
            if [player.is_folded for player in active_players].count(False) == 1:
                break
            betting_player = active_players[betting_index % len(active_players)]
            if betting_player.is_folded or betting_player.is_all_in:
                betting_index += 1
                continue
            self.table.update_raise_amount(self.phase)
            if betting_player.name is self.agent_name:
                game_state = PokerGameState(betting_index % len(active_players), self, self.deck.copy(), self.table.last_bet, self.table.raise_amount)
                max_action_value = -9999
                expectiminimax = Expectiminimax()
                max_action = None
                actions = game_state.get_legal_actions()
                for action in actions:
                    if self.show_table:
                        print(f"AGENT CONSIDERS {action}")
                    next_state = game_state.get_successor_state(betting_index % len(active_players), action)
                    next_state_value = expectiminimax.expectiminimax(3, next_state, False, betting_index % len(active_players))
                    if next_state_value > max_action_value:
                        max_action_value = next_state_value
                        max_action = action
                move = max_action
                if self.show_table:
                    print(f"AGENT CHOOSES {max_action}")
            else:
                move = betting_player.choose_next_move(self.table.raise_amount, self.table.num_times_raised,
                                                   self.table.last_bet)
            self.table.take_bet(betting_player, move)
            if self.show_table:
                text_prompt.show_player_move(betting_player, move, self.pause, betting_player.bet)
            if move is BettingMove.RAISED or move is BettingMove.BET:
                for active_player in active_players:
                    if not active_player.is_folded:
                        active_player.is_locked = False
                for person in active_players:
                    if person.is_all_in:
                        person.is_locked = True
            elif move is BettingMove.ALL_IN:
                pass
            # if move is BettingMove.FOLDED and betting_player.is_human:
            if move is BettingMove.FOLDED and isinstance(betting_player, Human):
                self.set_game_speed(is_fast=True)
            betting_player.is_locked = True
            betting_index += 1
            if self.show_table:
                text_prompt.show_table(self.players, self.table)

    def check_hand_over(self) -> bool:
        """Checks if the current hand is over.

        Returns:
            True if hand is over, False otherwise.
        """
        players_able_to_bet = 0
        for player in self.get_active_players():
            if not player.is_all_in and not player.is_folded:
                players_able_to_bet += 1
        if self.show_table:
            print(f"{players_able_to_bet} CAN BET")
        return players_able_to_bet < 2

    def determine_winners(self):
        """Determine the winners of each pot and award them their chips."""
        if self.table.pots[-1][0] == 0:
            self.table.pots = self.table.pots[:-1]
        unfolded_players = [player for player in self.get_active_players() if not player.is_folded]
        if len(unfolded_players) == 1:
            winnings = 0
            for pot in self.table.pots:
                winnings += pot[0]
            winner = unfolded_players[0]
            winner.chips += winnings
            if self.show_table:
                text_prompt.show_table(self.players, self.table)
                text_prompt.show_default_winner_fold(winner.name)
        else:
            # If only 1 player is eligible for last side pot (i.e. other players folded/all-in), award player that pot
            players_eligible_last_pot = []
            for player in self.table.pots[-1][1]:
                if not player.is_folded:
                    players_eligible_last_pot.append(player)
            if len(players_eligible_last_pot) == 1:
                hand_winner = players_eligible_last_pot[0]
                if self.show_table:
                    text_prompt.show_table(self.players, self.table)
                    text_prompt.show_default_winner_eligibility(hand_winner.name, len(self.table.pots) - 1)
                hand_winner.chips += self.table.pots[-1][0]
                self.table.pots = self.table.pots[:-1]
            while len(self.table.community) < 5:
                self.table.community.extend(self.deck.deal(1))
            self.showdown()

    def showdown(self):
        """Runs the showdown phase."""
        if self.show_table:
            text_prompt.show_table(self.players, self.table)

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
                winner.chips += int(self.table.pots[i][0] / len(hand_winners))
            if self.show_table:
                text_prompt.show_showdown_results(self.players, self.table, hand_winners, showdown_players, pot_num=i)

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
                user_choice = io_utils.input_no_return(
                      "Continue on to next hand? Press (enter) to continue or (n) to stop.   ")
                if 'n' in user_choice.lower(): # if self.remaining_rounds != 0:
                    max_chips = max(self.get_active_players(), key=lambda player: player.chips).chips
                    winners_names = [player.name for player in self.get_active_players() if player.chips == max_chips]
                    if self.show_table:
                        text_prompt.show_table(self.players, self.table)
                        text_prompt.show_game_winners(self.players, winners_names)
                    return True
                return False

    def get_agent_chips(self):
        agents = [p for p in self.players if p.name == "Agent"]
        if len(agents) > 0:
            return agents[0].chips
        else:
            return -9999999999999999

    def get_active_players(self) -> list[Player]:
        return [player for player in self.players if player.is_in_game]

class PokerGameState:
    def __init__(self, curr_player_index, game, deck, table_last_best: int, raise_amount: int):
        self.game = game
        self.players = (list(map(lambda p: p.copy(), self.game.get_active_players())))
        self.table = self.game.table.copy()
        self.current_player = self.players[curr_player_index]
        self.our_hand = self.current_player.hand
        self.last_bet = table_last_best
        self.winnings = -table_last_best
        self.deck = deck
        self.max_player_turn = True
        self.raise_amount = raise_amount
        self.phase = self.game.phase


    def max_player_turn(self):
        return self.max_player_turn

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

    def get_successor_state(self, player_index, action):
        player = self.players[player_index]

        if self.game.show_table:
            print(f"EVALUATE: Player {player.name}; {action}")

        new_state = PokerGameState(player_index, self.game, self.deck, self.last_bet, self.raise_amount)
        new_state.apply_action(player, action)

        new_state.max_player_turn = not self.max_player_turn

        if self.game.show_table:
            show_table(new_state.players, new_state.table)

        return new_state

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
        value, hand = hand_ranking_utils.estimate_hand(currentHand, self.deck, community)
        if self.game.show_table:
            print(f"BEST HAND {value}")
        #show_cards(hand)
        return value

    def is_card_draw(self): # card_drawn if all players have matched bets, or are all in or folded
        active_players = self.players
        if all(player.is_locked or player.is_all_in for player in active_players):
            return True
        if [player.is_folded for player in active_players].count(False) == 1:
            return True
        return False

    def apply_action(self, player, action):
        if action == BettingMove.FOLDED:
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
                if other_player != player and not other_player.is_folded and not other_player.is_all_in:
                    player.is_locked = False
                else:
                    player.is_locked = True

        elif action == BettingMove.ALL_IN:
            all_in_amount = player.chips
            player.chips = 0
            self.table.pots[0][0] += all_in_amount
            self.raise_amount += all_in_amount
            player.is_all_in = True


        #self.update_round_status()

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
