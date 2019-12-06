#!/usr/bin/env python3
"""
Generates identity tokens for users Alice and Bob,
and a profyle_member claim token for Alice.
"""
from datetime import datetime, timedelta
import jwt

def create_token(subject, claims_dict=None):
    now = datetime.utcnow()
    later = datetime.utcnow() + timedelta(hours=2)

    token = {
        'iat': now,
        'nbf': now,
        'exp': later,
        'sub': subject
    }

    # add claims if provided
    if claims_dict:
        token = {**token, **claims_dict}

    return jwt.encode(token, 'secret', algorithm='HS256')

def write_demo_tokens():
    alice_identity = create_token('alice')
    bob_identity = create_token('bob')
    alice_profyle = create_token('alice', {'profyle_member': True})

    with open('alice_id.jwt', 'w') as aliceid:
        aliceid.write(alice_identity.decode('utf-8'))
    with open('bob_id.jwt', 'w') as bobid:
        bobid.write(bob_identity.decode('utf-8'))
    with open('alice_claim.jwt', 'w') as aliceclaim:
        aliceclaim.write(alice_profyle.decode('utf-8'))

if __name__ == "__main__":
    write_demo_tokens()