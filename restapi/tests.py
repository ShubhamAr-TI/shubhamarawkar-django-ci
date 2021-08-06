# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime

from django.test import Client
from django.test import TestCase

log = logging.getLogger("TEST")


def create_user(client, add_user=None, add_password=None):
    user_payload = {}
    if add_user is not None:
        user_payload['username'] = f"user_{int(datetime.now().timestamp())}"
    if add_password is not None:
        user_payload['password'] = f"password_{int(datetime.now().timestamp())}"
    print("USER PAYLOAD:", user_payload)
    resp = client.post('/api/v1/users/', user_payload)
    print("POST RESPONSE CODE:", resp.status_code)
    print("POST BODY:", resp.json())
    return user_payload, resp


# Create your tests here.
class UserTests(TestCase):

    def setUp(self):
        self.client = Client()

    def tearDown(self):
        pass

    def test_create_user(self):
        resp = self.client.get('/api/v1/users/')
        user_count_before = resp.json()['count']
        user, resp = create_user(self.client)
        assert resp.status_code == 400
        user, resp = create_user(self.client, add_user=True)
        assert resp.status_code == 400
        user, resp = create_user(self.client, add_password=True)
        assert resp.status_code == 400
        user, resp = create_user(self.client, add_user=True, add_password=True)
        print(resp, user)
        assert resp.status_code == 201
        resp = self.client.get('/api/v1/users/')
        user_count_after = resp.json()['count']
        assert user_count_after == user_count_before + 1

    def test_get_users(self):
        resp = self.client.get('/api/v1/users/')
        print(resp.json())
        assert resp.status_code == 200
        _ = create_user(self.client, add_user=True, add_password=True)
        resp = self.client.get('/api/v1/users/1/')
        print(resp)
        assert resp.status_code == 200
        resp = self.client.get('/api/v1/users/10000/')
        print(resp)
        assert resp.status_code == 404


class AuthTests(TestCase):

    def setUp(self):
        self.client = Client()

    def tearDown(self):
        pass

    def test_bad_response(self):
        auth_resp = self.client.post('/api/v1/auth/login/', {'username': 'asdf', 'password': 'asdfadf'})
        assert auth_resp.status_code == 400
        auth_resp = self.client.post('/api/v1/auth/login/', {'username': 'asdf'})
        assert auth_resp.status_code == 400
        auth_resp = self.client.post('/api/v1/auth/login/', {'password': 'asdf'})
        assert auth_resp.status_code == 400

    def test_token_generation(self):
        user, resp = create_user(self.client, add_user=True, add_password=True)
        auth_resp = self.client.post('/api/v1/auth/login/', user)
        assert 'token' in auth_resp.json()
        token = auth_resp.json()['token']
        headers = {
            'HTTP_AUTHORIZATION': f"Bearer {token}"
        }
        auth_resp = self.client.post('/api/v1/auth/login/', user)
        assert 'token' in auth_resp.json()
        token2 = auth_resp.json()['token']
        assert  token2 == token
        auth_resp = self.client.post('/api/v1/auth/logout/', **headers)
        assert auth_resp.status_code == 204

        auth_resp = self.client.post('/api/v1/auth/logout/', **headers)
        assert auth_resp.status_code == 404

    def test_404_logout(self):
        auth_resp = self.client.post('/api/v1/auth/logout/')
        assert auth_resp.status_code == 404



