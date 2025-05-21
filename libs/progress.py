import datetime
import time

from api.mail import send_mail

LINE_UP = "\033[1A"
LINE_CLEAR = "\x1b[2K"

def progress_bar(current: float, total: float, prefix: str, title: str, bar_length: int = 20, new_line: bool = False):
    fraction = current / total

    arrow = int(fraction * bar_length - 1) * "-" + ">"
    padding = int(bar_length - len(arrow)) * " "
    ending = "\n" if new_line or current == total else ""

    print("\r", end=LINE_CLEAR)
    print(f"{prefix}: [{arrow}{padding}] {int(fraction*100)}% {current} / {total} {title}", end=ending)


class ProgressBar:
    start: float
    loop: float = 0
    loop_end: float = 0
    item: int
    total: int
    new_line: bool

    def __init__(self, new_line: bool = False):
        self.start = time.time()
        self.new_line = new_line

    def start_sequence(self, total: int, text: str = ""):
        self.loop_end = time.time()

        if self.loop != 0:
            print(
                f"          Finished in: {round(time.time() - self.loop, 3)} sec                                                                  "
            )
        if text != "":
            print(f"{text}")

        self.loop = time.time()
        self.item = 0
        self.total = total

    def step(self, before: str, after: str = "", add: bool = True):
        if add:
            self.item += 1
        avg = round((time.time() - self.loop) / (self.item or 1), 3)
        progress_bar(
            self.item,
            self.total,
            before,
            f"{after} 🕠 {round(time.time() - self.loop_end, 3)} sec, average {avg} sec, finish in {'{:0>8}'.format(str(datetime.timedelta(seconds=int(avg * (self.total - self.item)))))}",
            new_line=self.new_line,
        )
        self.loop_end = time.time()

    def finish(self, sending_mail: bool = False):
        text = f"Finished in {'{:0>8}'.format(str(datetime.timedelta(seconds=int(time.time() - self.start))))} sec"
        print(text)

        if sending_mail:
            send_mail("🚀 [JobFit] Full Data Processing finished", text, "tomi.trescak@gmail.com")
