
import os

from symbolsdb import load

import time
def print_timing(func):
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        print '%s took %0.3f ms' % (func.func_name, (t2-t1)*1000.0)
        return res
    return wrapper

class StressTest(object):
    """ Run a timed data load from data in fixtures/ """
    def __init__(self):
        self.symbols = load.SymbolLoader()

    @print_timing
    def load_linux(self):
        filename = "fixtures/firefox-18.0.2-Linux-20130201065344-x86-symbols.txt"
        path = os.getcwd()

        self.symbols.load_build_file(filename, os.path.join(path, filename))

    @print_timing
    def load_windows(self):
        filename = "fixtures/firefox-18.0.2-WINNT-20130201065344-x86-symbols.txt"
        path = os.getcwd()

        self.symbols.load_build_file(filename, os.path.join(path, filename))

if __name__ == "__main__":
    test = StressTest()

    test.load_linux()
    test.load_windows()
