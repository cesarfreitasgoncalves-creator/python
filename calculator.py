"""A terminal calculator with persistent progress and a quiet horror story."""

import ast
import json
import math
import operator
from pathlib import Path

import colors


PROGRESS_FILE = Path(__file__).with_name("progress.json")
MAX_EXPRESSION_LENGTH = 180
MAX_AST_NODES = 60
MAX_INTEGER_BITS = 4096

_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_CONSTANTS = {"pi": math.pi, "e": math.e, "tau": math.tau}
_FUNCTIONS = {
    name: getattr(math, name)
    for name in (
        "acos", "asin", "atan", "ceil", "cos", "degrees", "exp", "fabs",
        "floor", "factorial", "gcd", "log", "log10", "radians", "sin",
        "sqrt", "tan",
    )
    if hasattr(math, name)
}
_FUNCTIONS["abs"] = abs

STORY_CHAPTERS = [
    (
        "A compra",
        "Você precisava de uma calculadora para voltar a estudar. A antiga tinha "
        "parado no meio de uma prova simulada, então a compra pareceu prática: "
        "uma calculadora científica usada, numa loja pequena perto do terminal. "
        "O recibo marca 23:17, embora você se lembre de ter ido à loja no fim da "
        "tarde. No rodapé, alguém escreveu a lápis: 'Confira o total antes de "
        "levar.' Você riu da frase. A calculadora ligou no primeiro toque. Em "
        "casa, porém, você percebeu que não lembrava de ter escolhido aquele "
        "modelo. Só lembrava de já estar segurando a sacola.",
    ),
    (
        "O total",
        "Ao conferir o recibo, a conta não fecha: uma calculadora por R$ 33,00, "
        "duas pilhas por R$ 3,00 cada, total impresso de R$ 33,00. Pode ser um "
        "desconto, um erro de caixa ou uma linha que a impressora cortou. Você "
        "tenta lembrar se perguntou pelas pilhas. A lembrança vem com a voz do "
        "atendente dizendo 'já estão incluídas', mas a loja não incluía pilhas "
        "em nada. No verso, quase apagado, há um segundo total: R$ 39,00. A letra "
        "parece familiar. Você decide que é sua, embora não se lembre de ter "
        "escrito aquilo.",
    ),
    (
        "A loja",
        "Você liga para a loja usando o número impresso no recibo. A pessoa que "
        "atende consulta o caixa e não encontra a venda. O número do recibo "
        "pertence, segundo ela, a uma compra de pilhas feita meses antes. Você "
        "olha para a calculadora enquanto ela pede desculpas pela confusão. No "
        "plástico sob a tampa, há uma etiqueta com o mesmo número. Talvez seja "
        "lote, patrimônio ou etiqueta de conserto. A atendente pergunta se você "
        "tem certeza de que comprou o aparelho ali. Você responde que sim rápido "
        "demais. Depois da ligação, não consegue recordar o rosto de ninguém da "
        "loja, só o som de uma gaveta fechando.",
    ),
    (
        "A devolução",
        "Você procura a garantia na caixa e encontra um papel dobrado entre o "
        "manual e o isopor. É um formulário de devolução sem nome, sem data e "
        "sem assinatura: 'motivo: não reconhece os resultados'. A frase pode "
        "ser uma anotação interna, talvez uma piada de funcionário. Você ri, "
        "mas confere o visor mesmo assim. Está desligado. No recibo, a anotação "
        "a lápis já não parece sua; você não consegue imaginar sua própria letra "
        "fazendo aqueles números. A explicação mais simples continua sendo um "
        "erro da loja. Você repete isso até a frase soar como algo que leu, não "
        "como algo em que acredita.",
    ),
]


class CalculationError(ValueError):
    """Raised when an expression is not an allowed calculator expression."""


def _checked(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CalculationError("Use apenas valores numéricos.")
    if isinstance(value, int) and value.bit_length() > MAX_INTEGER_BITS:
        raise CalculationError("O resultado é grande demais para esta calculadora.")
    if isinstance(value, float) and not math.isfinite(value):
        raise CalculationError("O resultado não é um número finito.")
    return value


def evaluate(expression):
    """Evaluate arithmetic and selected math functions without Python eval."""
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise CalculationError("A expressão ultrapassa o limite de tamanho.")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise CalculationError("Expressão inválida. Verifique os parênteses.") from error

    if sum(1 for _ in ast.walk(tree)) > MAX_AST_NODES:
        raise CalculationError("A expressão tem operações demais.")

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return _checked(node.value)
        if isinstance(node, ast.Name):
            if node.id in _CONSTANTS:
                return _CONSTANTS[node.id]
            raise CalculationError(f"Nome não permitido: {node.id}")
        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
            left = visit(node.left)
            right = visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 1000:
                raise CalculationError("O expoente deve estar entre -1000 e 1000.")
            return _checked(_BINARY_OPERATORS[type(node.op)](left, right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
            return _checked(_UNARY_OPERATORS[type(node.op)](visit(node.operand)))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            function = _FUNCTIONS.get(node.func.id)
            if function is None or node.keywords:
                raise CalculationError("Função não permitida.")
            arguments = [visit(argument) for argument in node.args]
            if node.func.id == "factorial" and arguments and arguments[0] > 1000:
                raise CalculationError("O fatorial está limitado a 1000.")
            return _checked(function(*arguments))
        raise CalculationError("Operação não permitida.")

    try:
        return visit(tree)
    except (TypeError, OverflowError) as error:
        raise CalculationError("Não foi possível calcular essa expressão.") from error


def _default_progress():
    return {"sessions": 0, "calculations": 0, "story_stage": 0, "history": []}


def load_progress():
    try:
        data = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return _default_progress()
        progress = _default_progress()
        for key in ("sessions", "calculations", "story_stage"):
            value = data.get(key, 0)
            progress[key] = value if isinstance(value, int) and value >= 0 else 0
        history = data.get("history", [])
        progress["history"] = history[-40:] if isinstance(history, list) else []
        return progress
    except (OSError, json.JSONDecodeError):
        return _default_progress()


def save_progress(progress):
    temporary_file = PROGRESS_FILE.with_suffix(".json.tmp")
    try:
        temporary_file.write_text(
            json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary_file.replace(PROGRESS_FILE)
    except OSError:
        colors.typewrite("Não foi possível salvar o progresso.", delay=0)


def _format_result(result):
    if isinstance(result, float):
        return f"{result:.12g}"
    return str(result)


def _record_calculation(progress, expression, result):
    progress["calculations"] += 1
    progress["history"].append(
        {"expression": expression, "result": _format_result(result)}
    )
    progress["history"] = progress["history"][-40:]
    save_progress(progress)

    unlocked_stage = min(progress["calculations"] // 4, len(STORY_CHAPTERS) - 1)
    if unlocked_stage > progress["story_stage"]:
        progress["story_stage"] = unlocked_stage
        save_progress(progress)
        show_story_chapter(unlocked_stage)


def show_story_chapter(index):
    title, text = STORY_CHAPTERS[index]
    colors.typewrite(colors.paint(f"\n{title}", colors.DIM), delay=0.04)
    colors.typewrite(text, delay=0.03)


def show_dossier(progress):
    print(colors.paint("\nDossiê da compra", colors.CYAN))
    for index in range(min(progress["story_stage"] + 1, len(STORY_CHAPTERS))):
        title, text = STORY_CHAPTERS[index]
        print(f"\n{title}\n{text}")


def _read_number(prompt):
    return evaluate(input(prompt).strip())


def calculate_expression(progress):
    expression = input("Expressão: ").strip()
    result = evaluate(expression)
    colors.typewrite(colors.paint(f"= {_format_result(result)}", colors.GREEN))
    _record_calculation(progress, expression, result)


def calculate_chain(progress):
    current = _read_number("Valor inicial (número ou expressão): ")
    starting_value = current
    steps = []
    while True:
        print("\n" + colors.paint("Operação", colors.CYAN))
        print("1  Somar       2  Subtrair     3  Multiplicar")
        print("4  Dividir     5  Potência     6  Resto")
        print("7  Raiz        8  Fatorial     9  Finalizar")
        choice = input("> ").strip()
        if choice == "9":
            break
        if choice not in {"1", "2", "3", "4", "5", "6", "7", "8"}:
            colors.typewrite("Escolha uma operação da lista.", delay=0)
            continue

        operation_names = {
            "1": ("+", operator.add),
            "2": ("-", operator.sub),
            "3": ("*", operator.mul),
            "4": ("/", operator.truediv),
            "5": ("**", operator.pow),
            "6": ("%", operator.mod),
        }
        if choice in operation_names:
            symbol, operation = operation_names[choice]
            operand = _read_number("Próximo valor: ")
            if choice == "5" and abs(operand) > 1000:
                raise CalculationError("O expoente deve estar entre -1000 e 1000.")
            current = _checked(operation(current, operand))
            steps.append(f"{symbol} {_format_result(operand)}")
        elif choice == "7":
            current = _checked(math.sqrt(current))
            steps.append("raiz")
        else:
            if not isinstance(current, int) or current < 0 or current > 1000:
                raise CalculationError("O fatorial exige um inteiro entre 0 e 1000.")
            current = _checked(math.factorial(current))
            steps.append("!")
        colors.typewrite(colors.paint(f"= {_format_result(current)}", colors.GREEN), delay=0)

    expression = f"{_format_result(starting_value)} {' '.join(steps)}".strip()
    _record_calculation(progress, expression or "operação em cadeia", current)


def show_history(progress):
    history = progress["history"]
    if not history:
        colors.typewrite("Nenhum cálculo salvo ainda.", delay=0)
        return
    print(colors.paint("\nÚltimos cálculos", colors.CYAN))
    for entry in history[-8:]:
        if isinstance(entry, dict):
            print(f"{entry.get('expression', '?')} = {entry.get('result', '?')}")


def show_progress(progress):
    print(colors.paint("\nProgresso", colors.CYAN))
    print(f"Sessões: {progress['sessions']}")
    print(f"Cálculos: {progress['calculations']}")
    print(f"Memórias recuperadas: {progress['story_stage']}/3")


def main():
    progress = load_progress()
    progress["sessions"] += 1
    if not progress.get("intro_seen", False):
        progress["intro_seen"] = True
        save_progress(progress)
        show_story_chapter(0)
        input("\nPressione Enter para continuar...")
    save_progress(progress)
    colors.clear_screen()
    colors.typewrite(colors.paint("CALCULADORA", colors.CYAN), delay=0.04)

    while True:
        print("\n1  Expressão completa (PEMDAS)")
        print("2  Operações em cadeia")
        print("3  Histórico")
        print("4  Progresso")
        print("5  Dossiê da compra")
        print("6  Sair")
        choice = input("\nSelecione: ").strip()
        try:
            if choice == "1":
                calculate_expression(progress)
            elif choice == "2":
                calculate_chain(progress)
            elif choice == "3":
                show_history(progress)
            elif choice == "4":
                show_progress(progress)
            elif choice == "5":
                show_dossier(progress)
            elif choice == "6":
                save_progress(progress)
                colors.typewrite("Até a próxima.", delay=0.04)
                break
            else:
                colors.typewrite("Seleção inválida.", delay=0)
        except (CalculationError, ValueError, ZeroDivisionError, OverflowError) as error:
            colors.typewrite(colors.paint(f"Erro: {error}", colors.RED), delay=0)
        if choice != "6":
            input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    main()