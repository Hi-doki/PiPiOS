allcommands = {}

def register(commands):
    for cmd in allcommands.values():
        commands.command_info[cmd.name] = {
            "description": cmd.desc,
            "syntax": cmd.syntax,
            "example": cmd.example,
            "function": cmd.function,
            "category": cmd.category,
        }

class Commands:
    class Uwu:
        def __init__(self):
            self.name = "uwu"
            self.desc = "Prints uwu"
            self.syntax = "uwu"
            self.example = "uwu"
            self.function = self.uwu
            self.category = "otherstuff"
            allcommands[self.name] = self

        def uwu(self):
            return "uwu"

    class Hello:
        def __init__(self):
            self.name = "hello"
            self.desc = "Prints hello"
            self.syntax = "hello"
            self.example = "hello"
            self.function = self.hello
            self.category = "greetings"
            allcommands[self.name] = self

        def hello(self):
            return "hello"

#initialize commands
Commands.Uwu()
Commands.Hello()