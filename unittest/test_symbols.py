
import unittest
from mock import Mock
import model
from symbols import Symbol

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
        self.symbol = Symbol()

        # Need to avoid talking to the database
        self.symbol._exec = Mock()
        self.symbol._exec_and_return = Mock()
        self.symbol_list = symbolfile.split("\n")

    def tearDown(self):
        pass

    def test_partition_symbol_records(self):
        self.symbol.record_types = ['module', 'stack']
        split_records = self.symbol.partition_symbol_records(self.symbol_list)
        self.assertEqual(len(split_records['module']), 1)
        self.assertEqual(len(split_records['stack']), 29)


