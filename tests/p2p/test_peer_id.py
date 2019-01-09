import unittest
from hathor.p2p.peer_id import PeerId, InvalidPeerIdException

from hathor.p2p.peer_storage import PeerStorage

import tempfile
import shutil
import os
import json


class PeerIdTest(unittest.TestCase):
    def test_invalid_id(self):
        p1 = PeerId()
        p1.id = p1.id[::-1]
        self.assertRaises(InvalidPeerIdException, p1.validate)

    def test_invalid_public_key(self):
        p1 = PeerId()
        p2 = PeerId()
        p1.public_key = p2.public_key
        self.assertRaises(InvalidPeerIdException, p1.validate)

    def test_invalid_private_key(self):
        p1 = PeerId()
        p2 = PeerId()
        p1.private_key = p2.private_key
        self.assertRaises(InvalidPeerIdException, p1.validate)

    def test_no_private_key(self):
        p1 = PeerId()
        p1.private_key = None
        p1.validate()

    def test_create_from_json(self):
        p1 = PeerId()
        data1 = p1.to_json(include_private_key=True)
        p2 = PeerId.create_from_json(data1)
        data2 = p2.to_json(include_private_key=True)
        self.assertEqual(data1, data2)
        p2.validate()

    def test_create_from_json_without_private_key(self):
        p1 = PeerId()
        data1 = p1.to_json()
        # Just to test a part of the code
        del data1['entrypoints']
        p2 = PeerId.create_from_json(data1)
        data2 = p2.to_json()
        self.assertEqual(data2['entrypoints'], [])
        data1['entrypoints'] = []
        self.assertEqual(data1, data2)
        p2.validate()

    def test_sign_verify(self):
        data = b'abacate'
        p1 = PeerId()
        signature = p1.sign(data)
        self.assertTrue(p1.verify_signature(signature, data))

    def test_sign_verify_fail(self):
        data = b'abacate'
        p1 = PeerId()
        signature = p1.sign(data)
        signature = signature[::-1]
        self.assertFalse(p1.verify_signature(signature, data))

    def test_merge_peer(self):
        # Testing peer storage with merge of peers
        peer_storage = PeerStorage()

        p1 = PeerId()
        p2 = PeerId()
        p2.id = p1.id
        p2.public_key = p1.public_key
        p1.public_key = ''

        peer_storage.add_or_merge(p1)
        self.assertEqual(len(peer_storage), 1)

        peer_storage.add_or_merge(p2)

        peer = peer_storage[p1.id]
        self.assertEqual(peer.id, p1.id)
        self.assertEqual(peer.private_key, p1.private_key)
        self.assertEqual(peer.public_key, p1.public_key)
        self.assertEqual(peer.entrypoints, [])

        p3 = PeerId()
        p3.entrypoints.append('1')
        p3.entrypoints.append('3')
        p3.public_key = ''

        p4 = PeerId()
        p4.public_key = ''
        p4.private_key = ''
        p4.id = p3.id
        p4.entrypoints.append('2')
        p4.entrypoints.append('3')
        peer_storage.add_or_merge(p4)

        self.assertEqual(len(peer_storage), 2)

        peer_storage.add_or_merge(p3)
        self.assertEqual(len(peer_storage), 2)

        peer = peer_storage[p3.id]
        self.assertEqual(peer.id, p3.id)
        self.assertEqual(peer.private_key, p3.private_key)
        self.assertEqual(peer.entrypoints, ['2', '3', '1'])

        with self.assertRaises(ValueError):
            peer_storage.add(p1)

    def test_save_peer_file(self):
        p = PeerId()
        tmpdir = tempfile.mkdtemp()
        path = os.path.join(tmpdir, 'peer.json')

        p.save_to_file(path)

        with open(path, 'r') as f:
            peer_from_file = json.loads(f.read())

        self.assertEqual(p.to_json(include_private_key=True), peer_from_file)

        # Removing tmpdir
        shutil.rmtree(tmpdir)


if __name__ == '__main__':
    unittest.main()
