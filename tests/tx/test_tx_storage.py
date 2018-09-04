import unittest
import tempfile
import shutil
from hathor.transaction.storage import TransactionJSONStorage, TransactionMemoryStorage, TransactionMetadata
from hathor.transaction.storage.exceptions import TransactionDoesNotExist
from hathor.transaction import Block, Transaction, TxOutput, TxInput


class _BaseTransactionStorageTest:

    class _TransactionStorageTest(unittest.TestCase):
        def setUp(self, tx_storage):
            self.tx_storage = tx_storage
            self.genesis = self.tx_storage.get_all_genesis()
            self.genesis_blocks = [tx for tx in self.genesis if tx.is_block]
            self.genesis_txs = [tx for tx in self.genesis if not tx.is_block]

            block_parents = [tx.hash for tx in self.genesis]
            output = TxOutput(200, bytes.fromhex('1e393a5ce2ff1c98d4ff6892f2175100f2dad049'))
            self.block = Block(
                timestamp=1535885967,
                weight=19,
                outputs=[output],
                parents=block_parents,
                nonce=100781,
                hash=bytes.fromhex('0000184e64683b966b4268f387c269915cc61f6af5329823a93e3696cb0fe902'),
                storage=tx_storage
            )

            tx_parents = [tx.hash for tx in self.genesis_txs]
            tx_input = TxInput(
                tx_id=bytes.fromhex('0000184e64683b966b4268f387c269915cc61f6af5329823a93e3696cb0fe902'),
                index=0,
                data=bytes.fromhex('46304402203470cb9818c9eb842b0c433b7e2b8aded0a51f5903e971649e870763d0266a'
                                   'd2022049b48e09e718c4b66a0f3178ef92e4d60ee333d2d0e25af8868acf5acbb35aaa583'
                                   '056301006072a8648ce3d020106052b8104000a034200042ce7b94cba00b654d4308f8840'
                                   '7345cacb1f1032fb5ac80407b74d56ed82fb36467cb7048f79b90b1cf721de57e942c5748'
                                   '620e78362cf2d908e9057ac235a63')
            )

            self.tx = Transaction(
                timestamp=1535886380,
                weight=17,
                nonce=932049,
                hash=bytes.fromhex('0000344407e176e61279970f44785f93ff95198b22efb46daf69588204229a4b'),
                inputs=[tx_input],
                outputs=[output],
                parents=tx_parents,
                storage=tx_storage
            )

        def test_genesis(self):
            self.assertEqual(1, len(self.genesis_blocks))
            self.assertEqual(2, len(self.genesis_txs))
            self.assertEqual(1, len(self.genesis_blocks[0].outputs))
            for tx in self.genesis:
                tx.verify()

        def test_storage_basic(self):
            self.assertEqual(1, self.tx_storage.count_blocks())

            block_parents_hash = self.tx_storage.get_tip_blocks()
            self.assertEqual(1, len(block_parents_hash))
            self.assertEqual(block_parents_hash[0], self.genesis_blocks[0].hash)

            tx_parents_hash = self.tx_storage.get_tip_transactions()
            self.assertEqual(2, len(tx_parents_hash))
            self.assertEqual(tx_parents_hash[0], self.genesis_txs[1].hash)
            self.assertEqual(tx_parents_hash[1], self.genesis_txs[0].hash)

        def validate_save(self, obj):
            self.tx_storage.save_transaction(obj)

            loaded_obj1 = self.tx_storage.get_transaction_by_hash_bytes(obj.hash)

            self.assertTrue(self.tx_storage.transaction_exists_by_hash_bytes(obj.hash))

            self.assertEqual(obj, loaded_obj1)
            self.assertEqual(obj.is_block, loaded_obj1.is_block)

            loaded_obj2 = self.tx_storage.get_transaction_by_hash(obj.hash.hex())

            self.assertEqual(obj, loaded_obj2)
            self.assertEqual(obj.is_block, loaded_obj2.is_block)

        def test_save_block(self):
            self.validate_save(self.block)

        def test_save_tx(self):
            self.validate_save(self.tx)

        def test_get_wrong_tx(self):
            hex_error = '00001c5c0b69d13b05534c94a69b2c8272294e6b0c536660a3ac264820677024'
            with self.assertRaises(TransactionDoesNotExist):
                self.tx_storage.get_transaction_by_hash(hex_error)

        def test_save_metadata(self):
            metadata = TransactionMetadata(
                spent_outputs=[1],
                hash=self.genesis_blocks[0].hash
            )
            self.tx_storage.save_metadata(metadata)
            metadata_read = self.tx_storage.get_metadata_by_hash_bytes(self.genesis_blocks[0].hash)
            self.assertEqual(metadata, metadata_read)

        def test_get_latest_blocks(self):
            self.tx_storage.save_transaction(self.block)

            latest_blocks = self.tx_storage.get_latest_blocks(count=3)

            self.assertEqual(len(latest_blocks), 2)
            self.assertEqual(latest_blocks[0].hash, self.block.hash)
            self.assertEqual(latest_blocks[1].hash, self.genesis_blocks[0].hash)

        def test_get_latest_tx(self):
            self.tx_storage.save_transaction(self.tx)

            latest_tx = self.tx_storage.get_latest_transactions(count=3)

            self.assertEqual(len(latest_tx), 3)
            self.assertEqual(latest_tx[0].hash, self.tx.hash)
            self.assertEqual(latest_tx[1].hash, self.genesis_txs[1].hash)
            self.assertEqual(latest_tx[2].hash, self.genesis_txs[0].hash)


class TransactionJSONStorageTest(_BaseTransactionStorageTest._TransactionStorageTest):
    def setUp(self):
        self.directory = tempfile.mkdtemp(dir='/tmp/')
        super().setUp(TransactionJSONStorage(self.directory))

    def tearDown(self):
        shutil.rmtree(self.directory)


class TransactionMemoryStorageTest(_BaseTransactionStorageTest._TransactionStorageTest):
    def setUp(self):
        super().setUp(TransactionMemoryStorage())