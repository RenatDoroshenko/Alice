class Calculator:
    def __init__(self):
        self.result = 0

    def add(self, a, b):
        self.result = a + b
        return self.result

    def subtract(self, a, b):
        self.result = a - b
        return self.result


calc = Calculator()
print(calc.add(10, 5))
print(calc.subtract(20, 8))