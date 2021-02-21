import os
import pickle
import random
from typing import List
import NeuralNetwork as nn
import shutil

class Cards:
    def __init__(self):
        self.cards = []
        for _ in range(4):
            temp = random.sample(range(8), 8)
            for m in temp:
                self.cards.append(m)

    def lastcard(self):
        last = self.cards[-1]
        self.cards.pop()
        return last


class Player:
    def __init__(self, username, nn: nn.NeuralNetwork):
        self.username = username
        self.cardsInHand = []
        self.takenCards = [0]*8
        self.score = 0
        self.isLast = False
        self.isFirst = False
        self.takesTheHand = False
        self.playingNetwork = nn

    def __str__(self):
        return self.username

    def __eq__(self, other):
        if isinstance(other, str):
            return self.username == other

        if isinstance(other, Player):
            return self.username == other.username
        return False

    def throwcard(self, n):
        card = self.cardsInHand[n]
        self.cardsInHand.pop(n)
        return card


class Game:
    def __init__(self, players: List[Player]):
        self.cardsRoman = ['VII', 'VIII', 'IX', 'X', 'D', 'B', 'K', 'A']
        self.allowedInput: List[str] = ['0', '1', '2', '3', 'end']
        self.players: List[Player] = players
        self.players[random.randint(0, 3)].isFirst = True
        self.cards: Cards = Cards()
        self.dealCards(self.cards, self.players)

    @staticmethod
    def generateInputList(cardsInHand: list, hand: list, takenCards: list, scoreUs: int, scoreThem: int):
        inputList = cardsInHand.copy()
        while len(inputList) < 4:
            inputList.append(-1)
        inputList += hand
        while len(inputList) < 19:
            inputList.append(-1)
        inputList += takenCards + [scoreUs, scoreThem]
        return inputList

    @staticmethod
    def draw(cards, players):
        for player in players:
            player.cardsInHand.append(cards.lastcard())

    @staticmethod
    def dealCards(cards, players):
        for _ in range(2):
            for j in range(4):
                players[j].cardsInHand.append(cards.lastcard())
                players[j].cardsInHand.append(cards.lastcard())

    @staticmethod
    def sortPlayers(players: List[Player]):
        for _ in range(4):
            if players[0].isFirst:
                break
            else:
                temp_p = players[0]
                players.pop(0)
                players.append(temp_p)

    def canPlayerContinue(self, cardToBeat, first, i):
        if (cardToBeat not in self.players[0].cardsInHand and not first and i == self.players[0] and
                0 not in self.players[0].cardsInHand):
            return True
        return False

    def printHand(self, hand, first):
        handOut = '| '
        print("Bačene karte: ")

        for n in hand:
            handOut += self.cardsRoman[n] + ' | '
        print(handOut)

    def printPlayer(self, player):
        cardsInHandOut = '| '
        print(player.__str__())
        for n in player.cardsInHand:
            cardsInHandOut += self.cardsRoman[n] + ' | '
        print("Ruka: " + cardsInHandOut)
        if not player.playingNetwork:
            return input(f"Odaberite kartu (0 - {len(player.cardsInHand) - 1}): ")


    def printOrder(self):
        print("Redoslijed igre: ")
        for player in self.players:
            print(f"\t- {player}")

    @staticmethod
    def cardTakesTheHand(thrownCard, cardToBeat, player, players: list):
        if thrownCard == cardToBeat or thrownCard == 0:
            for j in players:
                j.takesTheHand = False
                j.isFirst = False
            player.takesTheHand = True
            player.isFirst = True

    @staticmethod
    def pointSum(hand, players):
        sumPoints = 0
        for card in hand:
            if card == 3 or card == 7:
                sumPoints += 10
        for player in players:
            if player.takesTheHand:
                player.score += sumPoints
                players[players.index(player)-2].score += sumPoints
                for j in hand:
                    player.takenCards[j] += 1
                    players[players.index(player) - 2].takenCards[j] += 1
                break

    def pointReset(self):
        for player in self.players:
            player.score = 0

    def contDeal(self, firstPlayer):
        if len(self.cards.cards) != 0:
            for _ in range(min(4-len(firstPlayer.cardsInHand), int(len(self.cards.cards)/4))):
                self.draw(self.cards, self.players)

    def checkCardInput(self, cardToThrow, cardToBeat, first, a, i, firstPlayer):
        if cardToThrow not in self.allowedInput:
            print(f"Nedozvoljeni ulaz.")
            return False

        if cardToThrow == 'end':
            if i != firstPlayer or first:
                print("Trenutno nije moguće završiti rundu!")
                return False
            return True

        if int(cardToThrow) > (3-a):
            print(f"Odabrana karta nije unutar raspona.")
            return False
        try:
            if i.cardsInHand[int(cardToThrow)] != cardToBeat and i.cardsInHand[int(cardToThrow)] != 0 and not first and i == firstPlayer:
                print(f"Odabrana karta nije ispravna.")
                return False
        except:
            return False

        return True

    @property
    def handplay(self):
        hand = []
        killCommand = False
        breakHand = False
        first = True
        cardToBeat = None

        player: Player
        for player in self.players:
            player.cardsInHand.sort()
        # Sortiranje igrača
        self.sortPlayers(self.players)

        firstPlayer = self.players[0]

        # Početak ruke
        if len(firstPlayer.cardsInHand) != 0:
            self.printOrder()
            # Krugovi
            for a in range(4):
                if len(self.cards.cards)%2:
                    killCommand = True
                    break
                # Igrači
                for player in self.players:
                    # Provjera može li prvi igrač nastaviti ruku
                    breakHand = self.canPlayerContinue(cardToBeat, first, player)
                    if breakHand:
                        # self.printHand(hand, first)
                        break

                    self.printHand(hand, first)
                    #print(self.generateInputList(player.cardsInHand, hand, player.takenCards, player.score, self.players[self.players.index(player)-1].score))
                    if player.playingNetwork:
                        self.printPlayer(player)
                        cardToThrowList = player.playingNetwork.runNetwork(self.generateInputList(player.cardsInHand, hand, player.takenCards, player.score, self.players[self.players.index(player)-1].score))
                        cardToThrow = cardToThrowList.index(max(cardToThrowList))

                    if not player.playingNetwork:
                        cardToThrow = self.printPlayer(player)

                    if cardToThrow == 4:
                        cardToThrow = "end"
                    # print(f"{os.getpid()} {cardToThrow}")
                    # Provjera da li je ulaz dobar

                    if player.playingNetwork:
                        if not self.checkCardInput(str(cardToThrow), cardToBeat, first, a, player, firstPlayer):
                            print("Bot je krivo odigrao. Odabrana slučajna karta.")
                            cardToThrow = random.randint(0, len(player.cardsInHand))

                    if not player.playingNetwork:
                        while not self.checkCardInput(str(cardToThrow), cardToBeat, first, a, player, firstPlayer):
                            cardToThrow = self.printPlayer(player)

                    if cardToThrow == 'end':
                        breakHand = True
                        break

                    # Postavlja kartu za uzimanje
                    thrownCard = player.throwcard(int(cardToThrow))
                    if first:
                        cardToBeat = thrownCard
                        first = False

                    # print(f"{os.getpid()} {player.username} {thrownCard}")

                    # Provjerava da li bačena karta uzima ruku
                    self.cardTakesTheHand(thrownCard, cardToBeat, player, self.players)

                    # Bačene karte
                    hand.append(thrownCard)

                if breakHand:
                    print("Runda je završila.")
                    break


            # Zbrajanje bodova
            self.pointSum(hand, self.players)

            # Dijeljenje karata
            self.contDeal(firstPlayer)
            # if killCommand:
                # print(f"Remainig cards: {self.cards.cards}")
                # return True

            if not breakHand:
                print("Runda je završila.")
                pass
            return False
        else:
            # print(f"Remainig cards: {self.cards.cards}")
            return True

    def playgame(self):

        self.pointReset()

        print("[STARTING]Starting game.")
        print(f"Timovi: \n\t-{self.players[0]} i {self.players[2]}\n\t-{self.players[1]} i {self.players[3]}")
        while not self.handplay:
            pass

        print("Kraj partije.")
        if self.players[0].score > self.players[1].score:
            print(f"Pobijedili su: {self.players[0]} i {self.players[2]}")
            print("Bodovi:")
            print(f"\t{self.players[0]} i {self.players[2]}: {self.players[0].score}")
            print(f"\t{self.players[1]} i {self.players[3]}: {self.players[1].score}")
        elif self.players[0].score < self.players[1].score:
            print(f"Pobijedili su: {self.players[1]} i {self.players[3]}")
            print("Bodovi:")
            print(f"\t{self.players[0]} i {self.players[2]}: {self.players[0].score}")
            print(f"\t{self.players[1]} i {self.players[3]}: {self.players[1].score}")
        else:
            if self.players[0].takesTheHand + self.players[2].takesTheHand:
                print(f"Pobijedili su: {self.players[0]} i {self.players[2]}")
                print("Uzeli su zadnji štih.")
                print("Bodovi:")
                print(f"\t{self.players[0]} i {self.players[2]}: {self.players[0].score}")
                print(f"\t{self.players[1]} i {self.players[3]}: {self.players[1].score}")
            else:
                print(f"Pobijedili su: {self.players[1]} i {self.players[3]}")
                print("Uzeli su zadnji štih.")
                print("Bodovi:")
                print(f"\t{self.players[0]} i {self.players[2]}: {self.players[0].score}")
                print(f"\t{self.players[1]} i {self.players[3]}: {self.players[1].score}")



def runGame(x: Game):
    x.playgame()


if __name__ == "__main__":
    shutil.copy("trainingResultToUse.txt", "tempResult.txt")
    f = open("tempResult.txt", "rb")

    trainedNetwork = pickle.load(f)
    f.close()

    os.remove("tempResult.txt")

    players = [Player("Ivan", None)]
    for i in range(3):
        players.append(Player("Bot" + str(i+1), nn.NeuralNetwork()))
    players[1].playingNetwork.neuralNetwork = trainedNetwork[0]
    players[2].playingNetwork.neuralNetwork = trainedNetwork[1]
    players[3].playingNetwork.neuralNetwork = trainedNetwork[1]

    game = Game(players)
    game.playgame()
