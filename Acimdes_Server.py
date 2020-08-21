# Vesion 1.0

# run with "python Acimdes_Client.py"
# for logging run with "python Acimdes_Client.py > log.txt"

# Copyright 2020 Ivan Derdić

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import random
from typing import List
import socket as soc
import select as sel
import threading as thrd
import sys

HEADER_LENGTH = 10
IP = soc.gethostbyname(soc.gethostname())
# IP = '192.168.5.128'
PORT = 7777
ADDR = (IP, PORT)
FORMAT = 'utf-8'
soc_list = []
clients = {}
player_lobby = {}
STOP = '!Stop'


class Server:
    def start_server(self):
        print("[STARTING_SERVER]Server is starting...")
        server = soc.socket(soc.AF_INET, soc.SOCK_STREAM)
        server.bind(ADDR)
        server.listen()
        print(f"[LISTENING]Listening on: {IP}:{PORT}")
        soc_list.append(server)
        self.handle_clients()

    @staticmethod
    def send_msg(conn, msg: str):
        msg = msg.encode(FORMAT)
        msg_head = f"{len(msg):<{HEADER_LENGTH}}".encode(FORMAT)
        msg_send = msg_head + msg
        conn.send(msg_send)

    @staticmethod
    def recv_msg(csoc):
        try:
            msg_head = csoc.recv(HEADER_LENGTH)

            if not len(msg_head):
                return False

            msg_len = int(msg_head.decode(FORMAT))

            return csoc.recv(msg_len).decode(FORMAT)

        except:
            return False

    def handle_clients(self):
        while True:
            read_soc, _, exception_soc = sel.select(soc_list, [], soc_list)

            for not_soc in read_soc:
                if not_soc == soc_list[0]:
                    csoc, caddr = soc_list[0].accept()

                    usr = self.recv_msg(csoc)
                    if usr is False:
                        continue

                    soc_list.append(csoc)
                    clients[csoc] = usr

                    if not lobby.isLobbyFull():
                        lobby.addPlayer(usr, csoc)
                        player_lobby[csoc] = lobby
                    else:
                        print("Lobby is full!")
                        server.send_msg(csoc, "Lobby is full!")
                        csoc.close()

                    print(f"[NEW_CONNECTION]Accepted new connection from: {caddr[0]}:{caddr[1]}, username: "f"{usr}")
                else:
                    msg = self.recv_msg(not_soc)
                    if msg is False:
                        print(f"Closed connection from {clients[not_soc]}")
                        soc_list.remove(not_soc)
                        player_lobby[not_soc].deletePlayer(clients[not_soc])
                        del clients[not_soc]
                        del player_lobby[not_soc]
                        continue

                    if msg == '!Start' and player_lobby[not_soc].isLobbyFull():
                        # t = thrd.Thread(target=player_lobby[not_soc].startGame)
                        # t.start()
                        player_lobby[not_soc].startGame()
                    else:
                       print("Lobby not full!")
                       server.send_msg(not_soc, "Lobby not full!")

                    if msg == STOP:
                        for i in soc_list:
                            i.close()
                        sys.exit("[SERVER_CLOSED]Server closed")

            for not_soc in exception_soc:
                soc_list.remove(not_soc)
                del clients[not_soc]


class Lobby:
    def __init__(self):
        self.players = []
        self.player_sockets = []
        self.g: GameOnline = None

    def addPlayer(self, player_username, player_socket):
        self.players.append(Player(player_username))
        self.player_sockets.append(player_socket)

    def deletePlayer(self, username):
        self.player_sockets.pop(self.players.index(username))
        self.players.pop(self.players.index(username))

    def clearPlayers(self):
        self.players = []
        self.player_sockets = []

    def isLobbyFull(self):
        if len(self.players) == 4:
            return True
        return False

    def isLobbyEmpty(self):
        if len(self.players) == 0:
            return True
        return False

    def startGame(self):
        self.g = GameOnline(self.players, self.player_sockets)
        self.g.playgame()


class KillGame:
    def __init__(self):
        self.isKilled = False

    def setToKill(self):
        self.isKilled = True

    def reset(self):
        self.isKilled = False

    def isSet(self):
        return self.isKilled


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
    def __init__(self, username):
        self.username = username
        self.cardsInHand = []
        self.score = 0
        self.isLast = False
        self.isFirst = False
        self.takesTheHand = False

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


class GameOnline:
    def __init__(self, players: List[Player], player_sockets):
        self.cardsRoman = ['VII', 'VIII', 'IX', 'X', 'D', 'B', 'K', 'A']
        self.allowedInput: List[str] = ['0', '1', '2', '3', 'end']
        self.players: List[Player] = players
        self.player_sockets = player_sockets
        self.players[random.randint(0, 3)].isFirst = True
        self.cards: Cards = Cards()
        self.deal(self.cards, self.players)

    @staticmethod
    def draw(cards, players):
        for i in players:
            i.cardsInHand.append(cards.lastcard())

    @staticmethod
    def deal(cards, players):
        for _ in range(2):
            for j in range(4):
                players[j].cardsInHand.append(cards.lastcard())
                players[j].cardsInHand.append(cards.lastcard())

    @staticmethod
    def sortPlayers(players: List[Player], player_sockets):
        for _ in range(4):
            if players[0].isFirst:
                break
            else:
                temp_p = players[0]
                players.pop(0)
                players.append(temp_p)
                temp_s = player_sockets[0]
                player_sockets.pop(0)
                player_sockets.append(temp_s)

    def canPlayerContinue(self, cardToBeat, first, i):
        if (cardToBeat not in self.players[0].cardsInHand and not first and i == self.players[0] and
                0 not in self.players[0].cardsInHand):
            return True
        else:
            return False

    def printHand(self, hand, first):
        handOut = '| '
        if not first:
            print("Bačene karte: ")
            for i in self.player_sockets:
                server.send_msg(i, "Bačene karte: ")

            for n in hand:
                handOut += self.cardsRoman[n] + ' | '
            print(handOut)
            for i in self.player_sockets:
                server.send_msg(i, handOut)

    def printPlayer(self, i):
        cardsInHandOut = '| '
        print(i.__str__())
        server.send_msg(self.player_sockets[self.players.index(i)], i.__str__())
        for n in i.cardsInHand:
            cardsInHandOut += self.cardsRoman[n] + ' | '
        print("Ruka: " + cardsInHandOut)
        server.send_msg(self.player_sockets[self.players.index(i)], "Ruka: " + cardsInHandOut)
        server.send_msg(self.player_sockets[self.players.index(i)], f"Odaberite kartu (0 - {len(i.cardsInHand) - 1}): ")
        # return input(f"Odaberite kartu (0 - {len(i.cardsInHand) - 1}): ")
        return server.recv_msg(self.player_sockets[self.players.index(i)])

    def printOrder(self):
        print("Redoslijed igre: ")
        for i in self.players:
            print(f"\t- {i}")

        for i in self.player_sockets:
            server.send_msg(i, "Redoslijed igre: ")
            for j in self.players:
                server.send_msg(i, f"\t- {j}")

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
                break

    def pointReset(self):
        for i in self.players:
            i.score = 0

    def contDeal(self, firstPlayer):
        if len(self.cards.cards) != 0:
            for i in range(min(4-len(firstPlayer.cardsInHand), len(self.cards.cards)/4)):
                self.draw(self.cards, self.players)

    def checkCardInput(self, cardToThrow, cardToBeat, first, a, i, firstPlayer):
        if cardToThrow not in self.allowedInput:
            print(f"Nedozvoljeni ulaz.")
            server.send_msg(self.player_sockets[self.players.index(i)], f"Nedozvoljeni ulaz.")
            return False

        if cardToThrow == 'end':
            if i != firstPlayer or first:
                print("Trenutno nije moguće završiti rundu!")
                server.send_msg(self.player_sockets[self.players.index(i)],
                                "Trenutno nije moguće završiti rundu!")
                return False
            else:
                return True

        if int(cardToThrow) > (3-a):
            print(f"Odabrana karta nije unutar raspona.")
            server.send_msg(self.player_sockets[self.players.index(i)], f"Odabrana karta nije unutar raspona.")
            return False

        if i.cardsInHand[int(cardToThrow)] != cardToBeat and i.cardsInHand[int(cardToThrow)] != 0 and not first and i == firstPlayer:
            print(f"Odabrana karta nije ispravna.")
            server.send_msg(self.player_sockets[self.players.index(i)], f"Odabrana karta nije ispravna.")
            return False

        return True

    @property
    def handplay(self):
        hand = []
        breakHand = False
        first = True
        cardToBeat = None

        for i in self.players:
            i.cardsInHand.sort()
        # Sortiranje igrača
        self.sortPlayers(self.players, self.player_sockets)

        firstPlayer = self.players[0]

        # Početak ruke
        if len(firstPlayer.cardsInHand) != 0:
            self.printOrder()
            # Krugovi
            for a in range(4):
                # Igrači
                for i in self.players:
                    # Provjera može li prvi igrač nastaviti ruku
                    breakHand = self.canPlayerContinue(cardToBeat, first, i)
                    if breakHand:
                        self.printHand(hand, first)
                        break

                    self.printHand(hand, first)
                    cardToThrow = self.printPlayer(i)

                    # Provjera da li je ulaz dobar

                    while not self.checkCardInput(cardToThrow, cardToBeat, first, a, i, firstPlayer):
                        server.send_msg(self.player_sockets[self.players.index(i)],
                                        f"Odaberite kartu (0 - {len(i.cardsInHand) - 1}): ")
                        cardToThrow = server.recv_msg(self.player_sockets[self.players.index(i)])

                    if cardToThrow == 'end':
                        breakHand = True
                        break

                    # Postavlja kartu za uzimanje
                    if first:
                        thrownCard = i.throwcard(int(cardToThrow))
                        cardToBeat = thrownCard
                        first = False
                    else:
                        thrownCard = i.throwcard(int(cardToThrow))

                    # Provjerava da li bačena karta uzima ruku
                    self.cardTakesTheHand(thrownCard, cardToBeat, i, self.players)

                    # Bačene karte
                    hand.append(thrownCard)

                if breakHand:
                    print("Runda je završila.")
                    for i in self.player_sockets:
                        server.send_msg(i, "Runda je završila.")
                    break

            # Zbrajanje bodova
            self.pointSum(hand, self.players)

            # Dijeljenje karata
            self.contDeal(firstPlayer)

            if not breakHand:
                print("Runda je završila.")
                for i in self.player_sockets:
                    server.send_msg(i, "Runda je završila.")
            return False
        else:
            # Ispis pobjednika
            print("Kraj partije.")
            if (self.players[0].score + self.players[2].score) > (self.players[1].score + self.players[3].score):
                print(f"Pobijedili su: {self.players[0]} i {self.players[2]}")
                print("Bodovi:")
                print(f"\t{self.players[0]} i {self.players[2]}: {self.players[0].score + self.players[2].score}")
                print(f"\t{self.players[1]} i {self.players[3]}: {self.players[1].score + self.players[3].score}")
            elif (self.players[0].score + self.players[2].score) < (self.players[1].score + self.players[3].score):
                print(f"Pobijedili su: {self.players[1]} i {self.players[3]}")
                print("Bodovi:")
                print(f"\t{self.players[0]} i {self.players[2]}: {self.players[0].score + self.players[2].score}")
                print(f"\t{self.players[1]} i {self.players[3]}: {self.players[1].score + self.players[3].score}")
            else:
                if self.players[0].takesTheHand + self.players[2].takesTheHand:
                    print(f"Pobijedili su: {self.players[0]} i {self.players[2]}")
                    print("Uzeli su zadnji štih.")
                    print("Bodovi:")
                    print(f"\t{self.players[0]} i {self.players[2]}: {self.players[0].score + self.players[2].score}")
                    print(f"\t{self.players[1]} i {self.players[3]}: {self.players[1].score + self.players[3].score}")
                else:
                    print(f"Pobijedili su: {self.players[1]} i {self.players[3]}")
                    print("Uzeli su zadnji štih.")
                    print("Bodovi:")
                    print(f"\t{self.players[0]} i {self.players[2]}: {self.players[0].score + self.players[2].score}")
                    print(f"\t{self.players[1]} i {self.players[3]}: {self.players[1].score + self.players[3].score}")
            for i in self.player_sockets:
                server.send_msg(i, "Kraj partije.")
                if (self.players[0].score + self.players[2].score) > (self.players[1].score + self.players[3].score):
                    server.send_msg(i, f"Pobijedili su: {self.players[0]} i {self.players[2]}")
                    server.send_msg(i, "Bodovi:")
                    server.send_msg(i, f"\t{self.players[0]} i {self.players[2]}: {self.players[0].score + self.players[2].score}")
                    server.send_msg(i, f"\t{self.players[1]} i {self.players[3]}: {self.players[1].score + self.players[3].score}")
                elif (self.players[0].score + self.players[2].score) < (self.players[1].score + self.players[3].score):
                    server.send_msg(i, f"Pobijedili su: {self.players[1]} i {self.players[3]}")
                    server.send_msg(i, "Bodovi:")
                    server.send_msg(i, f"\t{self.players[0]} i {self.players[2]}: {self.players[0].score + self.players[2].score}")
                    server.send_msg(i, f"\t{self.players[1]} i {self.players[3]}: {self.players[1].score + self.players[3].score}")
                else:
                    if self.players[0].takesTheHand + self.players[2].takesTheHand:
                        server.send_msg(i, f"Pobijedili su: {self.players[0]} i {self.players[2]}")
                        server.send_msg(i, "Uzeli su zadnji štih.")
                        server.send_msg(i, "Bodovi:")
                        server.send_msg(i, f"\t{self.players[0]} i {self.players[2]}: {self.players[0].score + self.players[2].score}")
                        server.send_msg(i, f"\t{self.players[1]} i {self.players[3]}: {self.players[1].score + self.players[3].score}")
                    else:
                        server.send_msg(i, f"Pobijedili su: {self.players[1]} i {self.players[3]}")
                        server.send_msg(i, "Uzeli su zadnji štih.")
                        server.send_msg(i, "Bodovi:")
                        server.send_msg(i, f"\t{self.players[0]} i {self.players[2]}: {self.players[0].score + self.players[2].score}")
                        server.send_msg(i, f"\t{self.players[1]} i {self.players[3]}: {self.players[1].score + self.players[3].score}")

            return True

    def playgame(self):

        self.pointReset()

        print("[STARTING]Starting game.")
        killGame: KillGame = KillGame()
        print(f"Timovi: \n\t-{self.players[0]} i {self.players[2]}\n\t-{self.players[1]} i {self.players[3]}")

        for i in self.player_sockets:
            server.send_msg(i, f"Timovi: \n\t- {self.players[0]} i {self.players[2]}\n\t- {self.players[1]} i {self.players[3]}")
        while not killGame.isSet():
            try:
                if self.handplay:
                    break
            except:
                print("[ENDING]Ending game.")
                killGame.setToKill()


lobby: Lobby = Lobby()

server: Server = Server()
server.start_server()
