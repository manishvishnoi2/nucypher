import datetime
import json
import maya

from base64 import b64encode, b64decode

from nucypher.crypto.kits import UmbralMessageKit
from nucypher.crypto.powers import DecryptingPower
from nucypher.policy.models import TreasureMap


def test_alice_character_control_create_policy(alice_control, federated_bob):
    bob_pubkey_enc = federated_bob.public_keys(DecryptingPower)

    request_data = {
        'bob_encrypting_key': bytes(bob_pubkey_enc).hex(),
        'label': b64encode(bytes(b'test')).decode(),
        'm': 2,
        'n': 3,

    }
    response = alice_control.put('/create_policy', data=json.dumps(request_data))
    assert response.status_code == 200
    assert response.data == b'Policy created!'

    # Send bad data to assert error returns
    response = alice_control.put('/create_policy', data='bad')
    assert response.status_code == 400

    del(request_data['bob_encrypting_key'])
    response = alice_control.put('/create_policy', data=json.dumps(request_data))


def test_alice_character_control_grant(alice_control, federated_bob):
    bob_pubkey_enc = federated_bob.public_keys(DecryptingPower)

    request_data = {
        'bob_encrypting_key': bytes(bob_pubkey_enc).hex(),
        'label': b64encode(bytes(b'test')).decode(),
        'm': 2,
        'n': 3,
        'expiration_time': (maya.now() + datetime.timedelta(days=3)).iso8601(),
    }
    response = alice_control.put('/grant', data=json.dumps(request_data))
    assert response.status_code == 200

    response_data = json.loads(response.data)
    assert 'treasure_map' in response_data['result']

    map_bytes = b64decode(response_data['result']['treasure_map'])
    encrypted_map = TreasureMap.from_bytes(map_bytes)
    assert encrypted_map._hrac is not None

    # Send bad data to assert error returns
    response = alice_control.put('/grant', data='bad')
    assert response.status_code == 400

    del(request_data['bob_encrypting_key'])
    response = alice_control.put('/grant', data=json.dumps(request_data))


def test_bob_character_control_join_policy(bob_control, enacted_federated_policy):
    request_data = {
        'label': b64encode(enacted_federated_policy.label).decode(),
        'alice_signing_pubkey': bytes(enacted_federated_policy.alice.stamp).hex(),
    }

    response = bob_control.post('/join_policy', data=json.dumps(request_data))
    assert response.data == b'Policy joined!'
    assert response.status_code == 200

    # Send bad data to assert error returns
    response = bob_control.post('/join_policy', data='bad')
    assert response.status_code == 400

    del(request_data['alice_signing_pubkey'])
    response = bob_control.put('/join_policy', data=json.dumps(request_data))


def test_bob_character_control_retrieve(bob_control, enacted_federated_policy, capsule_side_channel):
    message_kit, data_source = capsule_side_channel

    request_data = {
        'label': b64encode(enacted_federated_policy.label).decode(),
        'policy_encrypting_pubkey': bytes(enacted_federated_policy.public_key).hex(),
        'alice_signing_pubkey': bytes(enacted_federated_policy.alice.stamp).hex(),
        'message_kit': b64encode(message_kit.to_bytes()).decode(),
        'datasource_signing_pubkey': bytes(data_source.stamp).hex(),
    }

    response = bob_control.post('/retrieve', data=json.dumps(request_data))
    assert response.status_code == 200

    response_data = json.loads(response.data)
    assert 'plaintext' in response_data['result']

    for plaintext in response_data['result']['plaintext']:
        assert b64decode(plaintext) == b'Welcome to the flippering.'

    # Send bad data to assert error returns
    response = bob_control.post('/retrieve', data='bad')
    assert response.status_code == 400

    del(request_data['alice_signing_pubkey'])
    response = bob_control.put('/retrieve', data=json.dumps(request_data))


def test_enrico_character_control_encrypt_message(enrico_control):

    request_data = {
        'message': b64encode(b"The admiration I had for your work has completely evaporated!").decode(),
    }

    response = enrico_control.post('/encrypt_message', data=json.dumps(request_data))
    assert response.status_code == 200

    response_data = json.loads(response.data)
    assert 'message_kit' in response_data['result']
    assert 'signature' in response_data['result']

    # Check that it serializes correctly.
    message_kit = UmbralMessageKit.from_bytes(
                            b64decode(response_data['result']['message_kit']))

    # Send bad data to assert error return
    response = enrico_control.post('/encrypt_message', data='bad')
    assert response.status_code == 400

    del(request_data['message'])
    response = enrico_control.post('/encrypt_message', data=request_data)
    assert response.status_code == 400
