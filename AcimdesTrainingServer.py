import random
from typing import List
import NeuralNetwork as nn
import os
import multiprocessing as mp
import threading as thrd
import pickle
import time

class Cards:
    def __init__(self):
        self.cards = []
        for _ in range(4):
            temp = random.sample(range(8), 8)
            for j in temp:
                self.cards.append(j)

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
    def generateInputList(cardsInHand: list[int], hand: list[int], takenCards: list[int], scoreUs: int, scoreThem: int):
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
        for i in players:
            i.cardsInHand.append(cards.lastcard())

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
        if not first:
            print("Bačene karte: ")

            for n in hand:
                handOut += self.cardsRoman[n] + ' | '
            print(handOut)

    def printPlayer(self, i):
        cardsInHandOut = '| '
        print(i.__str__())
        for n in i.cardsInHand:
            cardsInHandOut += self.cardsRoman[n] + ' | '
        print("Ruka: " + cardsInHandOut)
        return i.playingNetwork.runNetwork()

    def printOrder(self):
        print("Redoslijed igre: ")
        for i in self.players:
            print(f"\t- {i}")

    @staticmethod
    def cardTakesTheHand(thrownCard, cardToBeat, i, players):
        if thrownCard == cardToBeat or thrownCard == 0:
            for j in players:
                j.takesTheHand = False
                j.isFirst = False
            i.takesTheHand = True
            i.isFirst = True

    @staticmethod
    def pointSum(hand, players):
        sumPoints = 0
        for i in hand:
            if i == 3 or i == 7:
                sumPoints += 10
        for i in players:
            if i.takesTheHand:
                i.score += sumPoints
                players[players.index(i)-2].score += sumPoints
                for j in hand:
                    i.takenCards[j] += 1
                    players[players.index(i) - 2].takenCards[j] += 1
                break

    def pointReset(self):
        for i in self.players:
            i.score = 0

    def contDeal(self, firstPlayer):
        if len(self.cards.cards) != 0:
            for i in range(min(4-len(firstPlayer.cardsInHand), int(len(self.cards.cards)/4))):
                self.draw(self.cards, self.players)

    def checkCardInput(self, cardToThrow, cardToBeat, first, a, i, firstPlayer):
        if cardToThrow not in self.allowedInput:
            #print(f"Nedozvoljeni ulaz.")
            return False

        if cardToThrow == 'end':
            if i != firstPlayer or first:
                #print("Trenutno nije moguće završiti rundu!")
                return False
            return True

        if int(cardToThrow) > (3-a):
            #print(f"Odabrana karta nije unutar raspona.")
            return False
        try:
            if i.cardsInHand[int(cardToThrow)] != cardToBeat and i.cardsInHand[int(cardToThrow)] != 0 and not first and i == firstPlayer:
                #print(f"Odabrana karta nije ispravna.")
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

        i: Player
        for i in self.players:
            i.cardsInHand.sort()
        # Sortiranje igrača
        self.sortPlayers(self.players)

        firstPlayer = self.players[0]

        # Početak ruke
        if len(firstPlayer.cardsInHand) != 0:
            # self.printOrder()
            # Krugovi
            for a in range(4):
                if len(self.cards.cards)%2:
                    killCommand = True
                    break
                # Igrači
                for i in self.players:
                    # Provjera može li prvi igrač nastaviti ruku
                    breakHand = self.canPlayerContinue(cardToBeat, first, i)
                    if breakHand:
                        # self.printHand(hand, first)
                        break

                    # self.printHand(hand, first)
                    #print(self.generateInputList(i.cardsInHand, hand, i.takenCards, i.score, self.players[self.players.index(i)-1].score))
                    cardToThrowList = i.playingNetwork.runNetwork(self.generateInputList(i.cardsInHand, hand, i.takenCards, i.score, self.players[self.players.index(i)-1].score))
                    cardToThrow = cardToThrowList.index(max(cardToThrowList))
                    if cardToThrow == 4:
                        cardToThrow = "end"
                    # print(f"{os.getpid()} {cardToThrow}")
                    # Provjera da li je ulaz dobar
                    if not self.checkCardInput(str(cardToThrow), cardToBeat, first, a, i, firstPlayer):
                        breakHand = True
                        killCommand = True
                        break

                    if cardToThrow == 'end':
                        breakHand = True
                        break

                    # Postavlja kartu za uzimanje
                    thrownCard = i.throwcard(int(cardToThrow))
                    if first:
                        cardToBeat = thrownCard
                        first = False

                    print(f"{os.getpid()} {i.username} {thrownCard}")

                    # Provjerava da li bačena karta uzima ruku
                    self.cardTakesTheHand(thrownCard, cardToBeat, i, self.players)

                    # Bačene karte
                    hand.append(thrownCard)

                if breakHand:
                    print("Runda je završila.")
                    break


            # Zbrajanje bodova
            self.pointSum(hand, self.players)

            # Dijeljenje karata
            self.contDeal(firstPlayer)
            if killCommand:
                print(f"Remainig cards: {self.cards.cards}")
                return True

            if not breakHand:
                print("Runda je završila.")
                pass
            return False
        else:
            print(f"Remainig cards: {self.cards.cards}")
            return True

    def playgame(self):

        self.pointReset()

        # print("[STARTING]Starting game.")
        # print(f"Timovi: \n\t-{self.players[0]} i {self.players[2]}\n\t-{self.players[1]} i {self.players[3]}")
        timeStart = time.time()
        while not self.handplay:
            pass

        f = open("generationResults.txt", "ab")
        save = []

        if self.players[0].score > self.players[1].score:
            save.append(self.players[0].playingNetwork.neuralNetwork)
            save.append(self.players[2].playingNetwork.neuralNetwork)
            save.append(self.players[0].score + 1 + time.time() - timeStart - len(self.cards.cards))
        elif self.players[0].score < self.players[1].score:
            save.append(self.players[1].playingNetwork.neuralNetwork)
            save.append(self.players[3].playingNetwork.neuralNetwork)
            save.append(self.players[1].score + 1 + time.time() - timeStart - len(self.cards.cards))
        else:
            if self.players[0].takesTheHand + self.players[2].takesTheHand:
                save.append(self.players[0].playingNetwork.neuralNetwork)
                save.append(self.players[2].playingNetwork.neuralNetwork)
                save.append(self.players[0].score + 1 + time.time() - timeStart - len(self.cards.cards))
            else:
                save.append(self.players[1].playingNetwork.neuralNetwork)
                save.append(self.players[3].playingNetwork.neuralNetwork)
                save.append(self.players[1].score + 1 + time.time() - timeStart - len(self.cards.cards))

        pickle.dump(save, f)
        f.close()

def runGame(x: Game):
    x.playgame()


if __name__ == "__main__":
    # random.seed(2)

    trainingTimeStart = time.time()

    print(f"Generation: 0")
    genTimeStart = time.time()

    numberOfGames = 25
    numberOfPlayers = numberOfGames * 4

    botPlayers = [Player("bot" + str(i), nn.NeuralNetwork()) for i in range(numberOfPlayers)]
    for i in range(numberOfPlayers):
        botPlayers[i].playingNetwork.addInputLayer(29)
        botPlayers[i].playingNetwork.addLayer(15)
        botPlayers[i].playingNetwork.addLayer(15)
        botPlayers[i].playingNetwork.addLayer(5)

    numberOfGeneration = 1000

    games = [Game([botPlayers.pop() for _ in range(4)]) for _ in range(numberOfGames)]

    pool = mp.Pool()
    results = pool.map(runGame, games)

    print(f"Time of generation 0: {time.time() - genTimeStart}")

    """processes = []
    for i in games:
        processes.append(mp.Process(target=i.playgame))
        processes[-1].start()
        processes[-1].join()"""

    """threads = []
    for i in games:
        threads.append(thrd.Thread(target=i.playgame))
        threads[-1].start()
        threads[-1].join()"""

    for i in range(numberOfGeneration):
        print(f"Generation: {i + 1}")
        genTimeStart = time.time()
        generationResults = []
        f = open("generationResults.txt", "rb")
        for _ in range(numberOfGames):
            try:
                generationResults.append(pickle.load(f))
            except:
                pass
        f.close()
        f = open("generationResults.txt", "w")
        f.close()
        bestInGeneration = generationResults[0]
        for j in generationResults:
            if j[2] > bestInGeneration[2]:
                bestInGeneration = j

        botPlayers = [Player("bot" + str(j) + "_" + str(i), nn.NeuralNetwork()) for j in range(numberOfPlayers)]
        for j in range(numberOfPlayers):
            if j < numberOfPlayers/2:
                botPlayers[j].playingNetwork.neuralNetwork = bestInGeneration[0]
            else:
                botPlayers[j].playingNetwork.neuralNetwork = bestInGeneration[1]

        random.shuffle(botPlayers)

        games = [Game([botPlayers.pop() for _ in range(4)]) for _ in range(numberOfGames)]

        pool = mp.Pool()
        results = pool.map(runGame, games)

        print(f"Time of generation {i+1}: {time.time() - genTimeStart}")

        """threads = []
        for j in games:
            threads.append(thrd.Thread(target=j.playgame))
            threads[-1].start()
            threads[-1].join()"""

        """processes = []
        for j in games:
            processes.append(mp.Process(target=j.playgame))
            processes[-1].start()
            processes[-1].join()"""

    print(f"Training time: {time.time() - trainingTimeStart}")

    generationResults = []
    f = open("generationResults.txt", "rb")
    for _ in range(numberOfGames):
        generationResults.append(pickle.load(f))
    f.close()
    bestInGeneration = generationResults[0]
    for j in generationResults:
        if j[2] > bestInGeneration[2]:
            bestInGeneration = j
    f.close()
    f = open("generationResults.txt", "wb")
    pickle.dump(bestInGeneration, f)
    f.close()