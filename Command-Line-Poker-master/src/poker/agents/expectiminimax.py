from ..pokergamestate import PokerGameState

class Expectiminimax:

    def getAction(self, gameState: PokerGameState):
        legalMoves = gameState.getLegalActions()

        for action in legalMoves:
            newState = gameState.getSuccessorState(0, action)
            actionCost = gameState.players[0]

    def getMaxAction(self, gameState: PokerGameState, depth):
        depth += 1

        if gameState.check_game_over():
            return self.evaluationFunction(gameState)

        bestScore = -999

        for action in gameState.getLegalActions():
            newState = gameState.getSuccessorState(0, action)
            bestScore = max(bestScore, self.getExpectedCost(newState, depth))

        return bestScore

    def getOpponentMaxAction(self, gameState, depth):
        if gameState.check_game_over():
            return self.evaluationFunction(gameState)

        probability = 0.25 # this would be pulled into another method to calculate based on cards to be played
        expectedValue = 0

        for action in gameState.getLegalActions():
            currentState = gameState.getSuccessorState(0, action)
            newScore = self.getMaxAction(currentState, depth)
            expectedValue += probability * newScore
        return expectedValue


    def evaluationFunction(self, gameState): # this is where we evaluate based on hand value and table value
        pots = gameState.table.pots
        lastBet = gameState.table.last_bet

        visibleCards = gameState.table.community

        return 1


