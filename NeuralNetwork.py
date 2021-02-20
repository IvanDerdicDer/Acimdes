import random
import sys
import math

class LinearActivationNode:
    def __init__(self, weight, bias):
        self.weight = weight
        self.bias = bias

    def output(self, x):
        output = self.weight * x + self.bias
        if output > 0:
            return output
        return 0

class NeuralNetwork:
    def __init__(self):
        self.neuralNetwork = []
        self.nodeOutputPerLayer = []
        self.mutationRate = 0.05

    @staticmethod
    def softmaxActivation(inputLayer: list[int]):
        suma = 0
        output = inputLayer.copy()
        largest = max(output)
        for i in range(len(output)):
            output[i] -= largest
        for i in output:
            suma += math.exp(i)
        for i in range(len(output)):
            output[i] = math.exp(output[i]) / suma

        return output

    def addLayer(self, numberOfNeurons):
        tmp = []
        self.nodeOutputPerLayer.append([None] * numberOfNeurons)
        for _ in range(numberOfNeurons):
            weight = random.random()
            bias = random.random()
            tmp.append(LinearActivationNode(weight, bias))
        self.neuralNetwork.append(tmp)

    def addInputLayer(self, numberOfNeurons):
        self.nodeOutputPerLayer.append([None] * numberOfNeurons)
        self.neuralNetwork.append([LinearActivationNode(1, 0)]*numberOfNeurons)

    def mutate(self):
        for i in self.neuralNetwork:
            for j in i:
                mutation = random.random() * random.randint(-100, 100) / 100
                if abs(mutation) < self.mutationRate:
                    j.weight *= (1 - mutation)
                    j.bias *= (1 - mutation)

    def sumOfLayer(self, inputLayer, layer):
        output = 0
        inputLayerTmp = inputLayer
        if layer == 0:
            for i in range(len(self.neuralNetwork[layer])):
                output += self.neuralNetwork[layer][i].output(inputLayerTmp[i])
                # self.nodeOutputPerLayer[layer][i] = self.neuralNetwork[layer][i].output(inputLayerTmp[i])

            return output

        if layer == len(self.neuralNetwork) - 1:
            output = []
            for i in range(len(self.neuralNetwork[layer])):
                output.append(self.neuralNetwork[layer][i].output(inputLayerTmp))
                # self.nodeOutputPerLayer[layer][i] = self.neuralNetwork[layer][i].output(inputLayerTmp)

            return output

        for i in range(len(self.neuralNetwork[layer])):
            output += self.neuralNetwork[layer][i].output(inputLayerTmp)
            # self.nodeOutputPerLayer[layer][i] = self.neuralNetwork[layer][i].output(inputLayerTmp)

        return output

    def runNetwork(self, inputLayer: list[int]):
        newInput = inputLayer.copy()
        #print(newInput)
        if len(newInput) != len(self.neuralNetwork[0]):
            raise IndexError("Input length doesn't match the length of input player")

        for i in range(len(self.neuralNetwork)):
            newInput = self.sumOfLayer(newInput, i)

        return self.softmaxActivation(newInput)



"""if __name__ == "__main__":
    neuralNet = NeuralNetwork()
    neuralNet.addInputLayer(27)
    neuralNet.addLayer(15)
    neuralNet.addLayer(15)
    neuralNet.addLayer(4)
    input = [random.randint(1, 4)]
    [input.append(random.randint(0, 7)) for _ in range(15)]
    [input.append(random.randint(0, 4)*random.randint(0, 8)) for _ in range(8)]

    input = [0,1,2,3, 1,2,4,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,0,0,0,0,0,0,0,0]

    a = neuralNet.runNetwork(input)
    print(a)
    neuralNet.mutate()
    print(neuralNet.runNetwork(input))"""