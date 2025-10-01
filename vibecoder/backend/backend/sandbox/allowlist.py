ALLOWED_COMMANDS = {
    "npm": {"ci", "run", "start", "build"},
    "next": {"build", "start"},
    "node": set(),
}


def is_allowed(command: list[str]) -> bool:
    if not command:
        return False
    binary = command[0]
    allowed_args = ALLOWED_COMMANDS.get(binary)
    if allowed_args is None:
        return False
    if not allowed_args:
        return True
    return all(arg in allowed_args or arg.startswith("--") for arg in command[1:])
