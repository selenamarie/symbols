
import os

from symbolsdb import load

class StressTest(object):
    """ Run a timed data load from data in fixtures/ """
    def __init__(self):
        self.symbols = load.SymbolLoader()

    def load_linux(self):
        filename = "fixtures/firefox-18.0.2-Linux-20130201065344-x86-symbols.txt"
        path = os.getcwd()

        self.symbols.load_build_file(filename, os.path.join(path, filename))

if __name__ == "__main__":
    test = StressTest()

    test.load_linux()
