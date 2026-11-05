import math
import time
import sys


def init():
    print("CALCULADORA ===========")
    print("digite 1 para soma")
    time.sleep(0.3)
    print("digite 2 para subtração")
    time.sleep(0.3)
    print("digite 3 para multplicacao")
    time.sleep(0.3)
    print("digite 4 para divisao")
    time.sleep(0.3)
    print("==================================================")
    while True:
        try:
            op = int(input("Digite o operador "))
            if op not in (1, 2, 3, 4):
                print("Digite um número valido ")
                continue
            else:
                n1 = int(input("Digite o primeiro número da operação "))
                if op in (6, 8):
                    return op, n1, 1
                else:
                    n2 = int(input("Digite o segundo número da operação "))
                    return op, n1, n2

        except ValueError:
            print("Digite números")
            continue
        except KeyboardInterrupt:
            sys.exit(127)


def calc() -> float:
    op, n1, n2 = init()
    if op == 1:
        resultado = n1 + n2
    elif op == 2:
        resultado = n1 - n2
    elif op == 3:
        resultado = n1 * n2
    elif op == 4:
        if n2 == 0:
            print("Erro: Divisão por zero!")
            return 0.0
        resultado = n1 / n2

    print(f"O resultado é: {resultado}")
    return float(resultado)

if __name__ == "__main__":
  calc()
