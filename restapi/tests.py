# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime
from random import random

from django.test import Client
from django.test import TestCase

log = logging.getLogger("TEST")


def create_user(client, add_user=None, add_password=None):
    user_payload = {}
    if add_user is not None:
        user_payload['username'] = f"user_{int(random() * 1e6)}"
    if add_password is not None:
        user_payload['password'] = f"password_{int(datetime.now().timestamp())}"
    print("USER PAYLOAD:", user_payload)
    resp = client.post('/api/v1/users/', user_payload)
    print("POST RESPONSE CODE:", resp.status_code)
    print("POST BODY:", resp.json())
    return user_payload, resp


def get_a_token(client):
    user, resp = create_user(client, add_user=True, add_password=True)
    auth_resp = client.post('/api/v1/auth/login/', user)
    assert 'token' in auth_resp.json()
    return auth_resp.json()['token']


def auth_header(token):
    return {
        'HTTP_AUTHORIZATION': f"Token {token}",
        'content_type': "application/json"
    }


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
            'HTTP_AUTHORIZATION': f"Token {token}"
        }
        auth_resp = self.client.post('/api/v1/auth/login/', user)
        assert 'token' in auth_resp.json()
        token2 = auth_resp.json()['token']
        assert token2 == token
        auth_resp = self.client.post('/api/v1/auth/logout/', **headers)
        assert auth_resp.status_code == 204

    def test_401_logout(self):
        auth_resp = self.client.post('/api/v1/auth/logout/')
        assert auth_resp.status_code == 401


class GroupCRUDTestsLevel1(TestCase):

    def setUp(self):
        self.client = Client()

    def tearDown(self):
        pass

    def test_group_get(self):
        user_headers = auth_header(get_a_token(self.client))
        otherguy_headers = auth_header(get_a_token(self.client))
        x = self.client.post(f"/api/v1/groups/", {"name": "TestGroup"}, **user_headers)
        assert x.status_code == 201
        group = x.json()
        print("GROUP CREATED", group)
        assert 'id' in group
        assert 'members' in group

        x = self.client.get(f"/api/v1/groups/{group['id']}/", **user_headers)
        y = self.client.get(f"/api/v1/groups/{group['id']}/", **otherguy_headers)
        assert x.status_code == 200 and y.status_code == 404

    def test_group_update(self):
        user_headers = auth_header(get_a_token(self.client))
        otherguy_headers = auth_header(get_a_token(self.client))
        x = self.client.post(f"/api/v1/groups/", {"name": "TestGroup"}, **user_headers)
        assert x.status_code == 201
        group = x.json()
        print("GROUP CREATED", group)
        assert 'id' in group
        assert 'members' in group
        group_id = x.json()['id']
        new_name = f"{int(random() * 1e6)}"
        x = self.client.put(f"/api/v1/groups/{group_id}/", {"name": new_name}, **user_headers)
        print(x.json())
        # assert x.status_code == 201
        assert x.json()['name'] == new_name
        x = self.client.put(f"/api/v1/groups/{group_id}/", {"name": new_name}, **otherguy_headers)
        assert x.status_code == 401 or x.status_code == 404  # FIXME is this correct

    def test_group_delete(self):
        user_headers = auth_header(get_a_token(self.client))
        otherguy_headers = auth_header(get_a_token(self.client))
        x = self.client.post(f"/api/v1/groups/", {"name": "TestGroup"}, **user_headers)
        assert x.status_code == 201
        group = x.json()
        print("GROUP CREATED", group)
        assert 'id' in group
        assert 'members' in group

        y = self.client.delete(f"/api/v1/groups/{group['id']}/", **otherguy_headers)
        x = self.client.delete(f"/api/v1/groups/{group['id']}/", **user_headers)
        assert x.status_code == 204 and y.status_code == 404


class ExpenseCRUDTestsLevel1(TestCase):

    def setUp(self):
        self.client = Client()

    def tearDown(self):
        pass

    def test_expense_get(self):
        user_headers = auth_header(get_a_token(self.client))
        otherguy_headers = auth_header(get_a_token(self.client))

    def test_expense_update(self):
        user_headers = auth_header(get_a_token(self.client))
        otherguy_headers = auth_header(get_a_token(self.client))

    def test_expense_delete(self):
        user_headers = auth_header(get_a_token(self.client))
        otherguy_headers = auth_header(get_a_token(self.client))
