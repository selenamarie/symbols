import datetime
import unittest
from mock import Mock, MagicMock
import symbolsdb.model
from symbolsdb.load import SymbolLoader

symbolfile = """MODULE mac x86_64 761889B42181CD979921A004C41061500 XUL
FILE 0 ../../../../../../dist/include/mozilla/mozalloc.h
FILE 1 ../../../../../../dist/include/nsAlgorithm.h
FUNC 1c60 43 0 __static_initialization_and_destruction_0
1c60 18 3966 4690
1c78 2b 612 4690
FUNC 1cb0 f 0 _GLOBAL__I_gArgc
1cb0 f 3967 4690
FUNC 1cc0 30 0 __static_initialization_and_destruction_0
1cc0 4 296 4107
1cc4 14 296 4107
1cd8 13 55 4107
1ceb 5 296 4107
FUNC 1cf0 f 0 _GLOBAL__I__ZN27nsAsyncRedirectVerifyHelper6AddRefEv
1cf0 f 297 4107
FUNC 1d00 39 0 __static_initialization_and_destruction_0
1d00 4 2313 4274
1d04 14 2313 4274
1d18 5 1552 4274
1d1d 17 1555 4274
1d34 5 2313 4274
FUNC 1d40 f 0 _GLOBAL__I__ZN10nsFtpState14QueryInterfaceERK4nsIDPPv
1d40 f 2314 4274
STACK CFI INIT 1c60 43 .cfa: $rsp 8 + .ra: .cfa -8 + ^
STACK CFI INIT 1cb0 f .cfa: $rsp 8 + .ra: .cfa -8 + ^
STACK CFI INIT de50 4c .cfa: $rsp 8 + .ra: .cfa -8 + ^
STACK CFI de5e $r12: .cfa -16 + ^ $rbx: .cfa -24 + ^ .cfa: $rsp 48 +
STACK CFI INIT dea0 17 .cfa: $rsp 8 + .ra: .cfa -8 + ^
STACK CFI INIT dec0 1e .cfa: $rsp 8 + .ra: .cfa -8 + ^
STACK CFI dec4 .cfa: $rsp 16 +
STACK CFI INIT dee0 10 .cfa: $rsp 8 + .ra: .cfa -8 + ^
STACK CFI dee4 .cfa: $rsp 16 +
STACK CFI INIT def0 17b .cfa: $rsp 8 + .ra: .cfa -8 + ^
STACK CFI def2 .cfa: $rsp 16 +
STACK CFI def4 .cfa: $rsp 24 +
STACK CFI def6 .cfa: $rsp 32 +
STACK CFI def8 .cfa: $rsp 40 +
STACK CFI def9 .cfa: $rsp 48 +
STACK CFI defa .cfa: $rsp 56 +
STACK CFI defe $r12: .cfa -40 + ^ $r13: .cfa -32 + ^ $r14: .cfa -24 + ^ $r15: .cfa -16 + ^ $rbp: .cfa -48 + ^ $rbx: .cfa -56 + ^ .cfa: $rsp 80 +
STACK CFI INIT e070 1ea .cfa: $rsp 8 + .ra: .cfa -8 + ^
STACK CFI e08d $r12: .cfa -32 + ^ $r13: .cfa -24 + ^ $r14: .cfa -16 + ^ $rbp: .cfa -40 + ^ $rbx: .cfa -48 + ^ .cfa: $rsp 128 +
STACK CFI INIT e270 b .cfa: $rsp 8 + .ra: .cfa -8 + ^
STACK CFI INIT e280 9a .cfa: $rsp 8 + .ra: .cfa -8 + ^
STACK CFI e287 .cfa: $rsp 224 +
STACK CFI INIT e320 1f .cfa: $rsp 8 + .ra: .cfa -8 + ^
STACK CFI e324 .cfa: $rsp 16 +
STACK CFI INIT e340 23 .cfa: $rsp 8 + .ra: .cfa -8 + ^
STACK CFI e344 .cfa: $rsp 16 +
STACK CFI INIT e370 1f .cfa: $rsp 8 + .ra: .cfa -8 + ^
STACK CFI e374 .cfa: $rsp 16 +
"""

class TestSymbol(unittest.TestCase):
    """ Test the symbols class """

    def setUp(self):
        self.symbol = SymbolLoader()

        # Need to avoid talking to the database
        self.symbol._exec = Mock()
        self.symbol_list = symbolfile.split("\n")

    def tearDown(self):
        pass


    ## Helper functions
    def function_returning_list(x, y):
        return [1]

    ## Tests

    def test_partition_symbol_records(self):
        self.symbol.record_types = ['module', 'stack']
        split_records = self.symbol.partition_symbol_records(self.symbol_list)
        self.assertEqual(len(split_records['module']), 1)
        self.assertEqual(len(split_records['stack']), 29)

    def test_create_record_inserts(self):
        self.symbol.build = (1, 'symupload', '1.0', 'Linux', '20120709194529',
            '', datetime.date(2012, 7, 9))
        res_expected = { 'module': [('mac', 'x86_64', '761889B42181CD979921A004C41061500', 'XUL', 1)]
            , 'func': [
                (7264, 67, 0, '__static_initialization_and_destruction_0'),
                (7344, 15, 0, '_GLOBAL__I_gArgc'),
                (7360, 48, 0, '__static_initialization_and_destruction_0'),
                (7408, 15, 0, '_GLOBAL__I__ZN27nsAsyncRedirectVerifyHelper6AddRefEv'),
                (7424, 57, 0, '__static_initialization_and_destruction_0'),
                (7488, 15, 0, '_GLOBAL__I__ZN10nsFtpState14QueryInterfaceERK4nsIDPPv')
            ]
        }
        self.symbol.record_types = ['module', 'func']
        split_records = self.symbol.partition_symbol_records(self.symbol_list)
        for record_type, res in self.symbol.create_record_inserts(split_records):
            self.assertEqual(res_expected[record_type], res)

    def test__parse_build(self):
        res_expected = ('symupload', '1.0', 'Linux', '20120709194529', '',
            datetime.date(2012, 7, 9))
        build_tuple = self.symbol._parse_build('symupload-1.0-Linux-20120709194529-symbols.txt')
        self.assertEqual(res_expected, build_tuple)

    def test__add_build(self):
        res_expected = (1, 'symupload', '1.0', 'Linux', '20120709194529', '',
            datetime.date(2012, 7, 9))
        self.symbol._exec_and_return_one = MagicMock(return_value=[1])
        self.symbol._add_build('symupload-1.0-Linux-20120709194529-symbols.txt')
        self.assertEqual(res_expected, self.symbol.build)

    def test__add_module_pile(self):
        line = 'MODULE mac x86_64 761889B42181CD979921A004C41061500 XUL'
        self.symbol.build = (1, 'symupload', '1.0', 'Linux', '20120709194529',
            '', datetime.date(2012, 7, 9))
        res_expected_list = [('mac', 'x86_64',
            '761889B42181CD979921A004C41061500', 'XUL', 1)]
        for res_expected, res in \
            zip(res_expected_list, self.symbol._add_module_pile(line)):
            self.assertEqual(res_expected, res)

    def test__add_file_pile(self):
        line = 'FILE 1 ../../../../../../dist/include/nsAlgorithm.h'
        res_expected_list = [(1, '../../../../../../dist/include/nsAlgorithm.h')]
        for res_expected, res in zip(res_expected_list, self.symbol._add_file_pile(line)):
            self.assertEqual(res_expected, res)

    def test__add_func_pile(self):
        line = 'FUNC 1c60 43 0 __static_initialization_and_destruction_0'
        res_expected_list = [(0x1c60, int('43', 16), 0, '__static_initialization_and_destruction_0')]
        for res_expected, res in zip(res_expected_list, self.symbol._add_func_pile(line)):
            self.assertEqual(res_expected, res)

    def test__add_stack_pile(self):
        line = 'STACK CFI INIT 1c60 43 .cfa: $rsp 8 + .ra: .cfa -8 + ^'
        res_expected_list = [('CFI INIT', 0x1c60, int('43', 16), '.cfa: $rsp 8 + .ra: .cfa -8 + ^')]
        for res_expected, res in zip(res_expected_list, self.symbol._add_stack_pile(line)):
            self.assertEqual(res_expected, res)

        line = 'STACK CFI de5e $r12: .cfa -16 + ^ $rbx: .cfa -24 + ^ .cfa: $rsp 48 +'
        res_expected_list = [('CFI', 0xde5e, None, '$r12: .cfa -16 + ^ $rbx: .cfa -24 + ^ .cfa: $rsp 48 +')]
        for res_expected, res in zip(res_expected_list, self.symbol._add_stack_pile(line)):
            self.assertEqual(res_expected, res)

    def test__add_line_pile(self):
        line = '1cc0 4 296 4107'
        res_expected_list = [(0x1cc0, 4, 296, 4107)]
        for res_expected, res in zip(res_expected_list, self.symbol._add_line_pile(line)):
            self.assertEqual(res_expected, res)

    def test__add_public_pile(self):
        # Need to dig up some test data
        pass
