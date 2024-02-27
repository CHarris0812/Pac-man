import torch

class TestAI():
    model = ""
    modelToChoice = ["left", "right", "up", "down"]

    def __init__(self):
        return

    def loadModel(self, preloadedModel):
        self.model = preloadedModel

    def getModel(self):
        return model

    def createModel(self):
        self.model = torch.nn.Sequential(
            torch.nn.Linear(18, 48, True),
            torch.nn.Linear(48, 24, True),
            torch.nn.Linear(24, 12, True),
            torch.nn.Linear(12, 8, True),
            torch.nn.Linear(8, 4, True)
        )

    def run(self, input):
        result = self.model(input)
        probability = torch.nn.Softmax(dim = 0)(result)
        print(probability)
        choice = probability.argmax(0)
        return self.modelToChoice[choice]

