class HinglishError(Exception):
    """Compilation galti. `line` 1-based hai."""
    def __init__(self, line, msg_hinglish, msg_english):
        super().__init__(f"Line {line}: {msg_hinglish} / {msg_english}")
        self.line = line
        self.msg_hinglish = msg_hinglish
        self.msg_english = msg_english
