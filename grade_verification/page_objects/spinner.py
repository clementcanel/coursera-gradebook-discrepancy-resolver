import sys, time, threading

"""Simple terminal spinner animation used to indicate a waiting period in the program flow"""
class Spinner:
    def __init__(self, message="Working..."):
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._spin)
        self.message = message
        self.chars = "|/-\\"
        self._last_render_length = 0

    def _spin(self):
        i = 0
        while not self._stop_event.is_set():
            spin_text = f"\r{self.message} {self.chars[i % len(self.chars)]}"
            self._last_render_length = len(spin_text)
            sys.stdout.write(spin_text)
            sys.stdout.flush()
            i += 1
            time.sleep(0.1)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()
        # Clear full line — based on last length written
        sys.stdout.write("\r" + " " * self._last_render_length + "\r")
        sys.stdout.flush()