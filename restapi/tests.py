# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime
from random import random

from django.test import Client
from django.test import TestCase

from restapi.views import get_balances

log = logging.getLogger('TEST')


def create_user(client, add_user=None, add_password=None):
    user_payload = {}
    if add_user is not None:
        user_payload['username'] = f'user_{int(random() * 1e6)}'
    if add_password is not None:
        user_payload['password'] = f'password_{int(datetime.now().timestamp())}'
    # print('USER PAYLOAD:', user_payload)
    resp = client.post('/api/v1/users/', user_payload)
    # print('POST RESPONSE CODE:', resp.status_code)
    # print('POST BODY:', resp.json())
    return user_payload, resp


def get_a_token(client):
    user, resp = create_user(client, add_user=True, add_password=True)
    auth_resp = client.post('/api/v1/auth/login/', user)
    assert 'token' in auth_resp.json()
    return auth_resp.json()['token']


def auth_header(token):
    return {
        'HTTP_AUTHORIZATION': f'Token {token}',
        'content_type': 'application/json'
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
        auth_resp = self.client.post(
            '/api/v1/auth/login/', {'username': 'asdf', 'password': 'asdfadf'})
        assert auth_resp.status_code == 400
        auth_resp = self.client.post(
            '/api/v1/auth/login/', {'username': 'asdf'})
        assert auth_resp.status_code == 400
        auth_resp = self.client.post(
            '/api/v1/auth/login/', {'password': 'asdf'})
        assert auth_resp.status_code == 400

    def test_token_generation(self):
        user, resp = create_user(self.client, add_user=True, add_password=True)
        auth_resp = self.client.post('/api/v1/auth/login/', user)
        assert 'token' in auth_resp.json()
        token = auth_resp.json()['token']
        headers = {
            'HTTP_AUTHORIZATION': f'Token {token}'
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
        x = self.client.post(f'/api/v1/groups/',
                             {'name': 'TestGroup'}, **user_headers)
        assert x.status_code == 201
        group = x.json()
        print('GROUP CREATED', group)
        assert 'id' in group
        assert 'members' in group

        x = self.client.get(f"/api/v1/groups/{group['id']}/", **user_headers)
        y = self.client.get(
            f"/api/v1/groups/{group['id']}/",
            **otherguy_headers)
        assert x.status_code == 200 and y.status_code == 404

    def test_group_update(self):
        user_headers = auth_header(get_a_token(self.client))
        otherguy_headers = auth_header(get_a_token(self.client))
        x = self.client.post(f'/api/v1/groups/',
                             {'name': 'TestGroup'}, **user_headers)
        assert x.status_code == 201
        group = x.json()
        print('GROUP CREATED', group)
        assert 'id' in group
        assert 'members' in group
        group_id = x.json()['id']
        new_name = f'{int(random() * 1e6)}'
        x = self.client.put(
            f'/api/v1/groups/{group_id}/', {'name': new_name}, **user_headers)
        print(x.json())
        # assert x.status_code == 201
        assert x.json()['name'] == new_name
        x = self.client.put(
            f'/api/v1/groups/{group_id}/', {'name': new_name}, **otherguy_headers)
        assert x.status_code == 401 or x.status_code == 404  # FIXME is this correct

    def test_group_delete(self):
        user_headers = auth_header(get_a_token(self.client))
        otherguy_headers = auth_header(get_a_token(self.client))
        x = self.client.post(f'/api/v1/groups/',
                             {'name': 'TestGroup'}, **user_headers)
        assert x.status_code == 201
        group = x.json()
        print('GROUP CREATED', group)
        assert 'id' in group
        assert 'members' in group

        y = self.client.delete(
            f"/api/v1/groups/{group['id']}/",
            **otherguy_headers)
        x = self.client.delete(
            f"/api/v1/groups/{group['id']}/",
            **user_headers)
        assert x.status_code == 204 and y.status_code == 404


class ExpenseCRUDTestsLevel1(TestCase):

    def setUp(self):
        self.client = Client()
        self.a_auth = auth_header(get_a_token(self.client))
        self.b_auth = auth_header(get_a_token(self.client))
        self.c_auth = auth_header(get_a_token(self.client))
        self.cat = self.client.post(
            f'/api/v1/categories/', {'name': 'Dummy Cat'}, **self.a_auth)

        self.expense = self.client.post(f'/api/v1/expenses/',
                                        {
                                            'category': 1,
                                            'description': 'culpa',
                                            'total_amount': '150',
                                            'users': [
                                                {
                                                    'amount_lent': '100',
                                                    'amount_owed': '100',
                                                    'user': 1
                                                },
                                                {
                                                    'amount_lent': '50',
                                                    'amount_owed': '50',
                                                    'user': 2
                                                }
                                            ]
                                        }, **self.a_auth)
        print(self.expense.json())
        print(self.cat, self.expense.json())

    def tearDown(self):
        pass

    def test_duplicate_user_expense(self):
        a_post = self.client.post(f'/api/v1/expenses/',
                                  {
                                      'category': 1,
                                      'description': 'culpa',
                                      'total_amount': '150',
                                      'users': [
                                          {
                                              'amount_lent': '100',
                                              'amount_owed': '100',
                                              'user': 1
                                          },
                                          {
                                              'amount_lent': '50',
                                              'amount_owed': '50',
                                              'user': 1
                                          }
                                      ]
                                  }, **self.a_auth)
        print(a_post)
        assert a_post.status_code != 200

    def test_expenses_get(self):
        a_get = self.client.get('/api/v1/expenses/', **self.a_auth)
        b_get = self.client.get('/api/v1/expenses/', **self.b_auth)
        c_get = self.client.get('/api/v1/expenses/', **self.c_auth)
        print(a_get, b_get, c_get)
        assert a_get.json()['count'] == 1 \
            and b_get.json()['count'] == 1 \
            and c_get.json()['count'] == 0
        assert a_get.json() == b_get.json()

    def test_single_expense_get(self):
        a_get = self.client.get('/api/v1/expenses/1/', **self.a_auth)
        c_get = self.client.get('/api/v1/expenses/1/', **self.c_auth)
        assert a_get.status_code == 200 and c_get.status_code == 404

    def test_expense_search(self):
        a_get = self.client.get('/api/v1/expenses/?q=cu', **self.a_auth)
        assert a_get.status_code == 200 and a_get.json()['count'] == 1
        a_get = self.client.get('/api/v1/expenses/?q=cud', **self.a_auth)
        assert a_get.status_code == 200 and a_get.json()['count'] == 0

    def test_expense_update(self):
        updated_expense = {
            'category': 1,
            'description': 'culpa',
            'total_amount': '200',
            'users': [
                {
                    'amount_lent': '150',
                    'amount_owed': '100',
                    'user': 1
                },
                {
                    'amount_lent': '50',
                    'amount_owed': '100',
                    'user': 2
                }
            ]
        }

        c_put = self.client.put(
            '/api/v1/expenses/1/',
            updated_expense,
            **self.c_auth)
        b_put = self.client.put(
            '/api/v1/expenses/1/',
            updated_expense,
            **self.b_auth)
        a_put = self.client.put(
            '/api/v1/expenses/1/',
            updated_expense,
            **self.a_auth)

        updated_reponse = a_put.json()
        print(updated_reponse)
        print(c_put, b_put, a_put)
        assert c_put.status_code != 200 and b_put.status_code == 200 and a_put.status_code == 200

    def test_expense_delete(self):
        c_del = self.client.delete('/api/v1/expenses/1/', **self.c_auth)
        b_del = self.client.delete('/api/v1/expenses/1/', **self.b_auth)
        a_del = self.client.delete('/api/v1/expenses/1/', **self.a_auth)
        print(a_del, b_del, c_del)
        assert c_del.status_code == 404 and b_del.status_code == 204 and a_del.status_code == 404

    def test_expense_duplicate_update(self):
        updated_expense = {
            'category': 1,
            'description': 'culpa',
            'total_amount': '200',
            'users': [
                {
                    'amount_lent': '150',
                    'amount_owed': '150',
                    'user': 1
                },
                {
                    'amount_lent': '50',
                    'amount_owed': '100',
                    'user': 1
                }
            ]
        }
        a_put = self.client.put(
            '/api/v1/expenses/1/',
            updated_expense,
            **self.a_auth)
        print(a_put, a_put.json())
        assert a_put.status_code == 400

    def test_expense_unauthorized_create(self):
        group = self.client.post(
            f'/api/v1/groups/', {'name': 'Dummy Group'}, **self.a_auth)
        print("GROUP:", group.json())
        expense = {
            'category': 1,
            'description': 'culpa',
            'total_amount': '200',
            'users': [
                {
                    'amount_lent': '150',
                    'amount_owed': '100',
                    'user': 1
                },
                {
                    'amount_lent': '50',
                    'amount_owed': '100',
                    'user': 2
                }
            ]
        }
        a_put = self.client.put('/api/v1/expenses/1/', expense, **self.a_auth)
        c_put = self.client.put('/api/v1/expenses/1/', expense, **self.c_auth)
        assert a_put.status_code == 200 and c_put.status_code == 404

    def test_expense_bad(self):
        expense = {
            'category': 1,
            'description': 'culpa',
            'total_amount': '200',
            'users': [
                {
                    'amount_lent': '150',
                    'amount_owed': '100',
                    'user': 2
                },
                {
                    'amount_lent': '50',
                    'amount_owed': '100',
                    'user': 3
                }
            ]
        }
        a_put = self.client.put('/api/v1/expenses/1/', expense, **self.a_auth)
        print(a_put)
        assert a_put.status_code == 400

    def test_expense_incorrect_update(self):
        updated_expense = {
            'category': 1,
            'description': 'culpa',
            'total_amount': '200',
            'users': [
                {
                    'amount_lent': '200',
                    'amount_owed': '150',
                    'user': 1
                },
                {
                    'amount_lent': '50',
                    'amount_owed': '100',
                    'user': 1
                }
            ]
        }
        a_put = self.client.put(
            '/api/v1/expenses/1/',
            updated_expense,
            **self.a_auth)
        print(a_put, a_put.json())
        assert a_put.status_code == 400

    def test_group_expenses(self):
        x = self.client.post(f'/api/v1/groups/',
                             {'name': 'TestGroup'}, **self.a_auth)
        assert x.status_code == 201
        group = x.json()
        print('GROUP CREATED', group)
        assert 'id' in group
        assert 'members' in group
        expense = {
            'group': 1,
            'category': 1,
            'description': 'culpa',
            'total_amount': '200',
            'users': [
                {
                    'amount_lent': '150',
                    'amount_owed': '150',
                    'user': 1
                },
                {
                    'amount_lent': '50',
                    'amount_owed': '100',
                    'user': 2
                }
            ]
        }
        exp = self.client.post("/api/v1/expenses/", expense, **self.a_auth)
        group_expenses = self.client.get(
            "/api/v1/groups/1/expenses/", **self.a_auth)
        # print(group_expenses.json())


def make_transaction(data):
    return {"from_user": data[0], "to_user": data[1], "amount": data[2]}


class UserTests(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_simple_one_guy_pays(self):
        payments = [{'user_id': 1, 'amount': -100},
                    {'user_id': 2, 'amount': 100}]

        print(get_balances(payments))
        payments = [{'user_id': 1, 'amount': -100},
                    {'user_id': 2, 'amount': 100}]
        assert get_balances(payments) == [
            make_transaction([1, 2, 100])
        ]

    def test_simple_3_guy(self):
        payments = [{'user_id': 1, 'amount': -100},
                    {'user_id': 2, 'amount': 0},
                    {'user_id': 3, 'amount': 100}]
        assert get_balances(payments) == [
            make_transaction([1, 3, 100])
        ]

    def test_alter_3_guy(self):
        payments = [{'user_id': 1, 'amount': -200},
                    {'user_id': 2, 'amount': -100},
                    {'user_id': 3, 'amount': 300}]
        assert get_balances(payments) == [
            make_transaction([1, 3, 200]),
            make_transaction([2, 3, 100])
        ]

    def test_doc_example(self):
        payments = [{'user_id': 1, 'amount': -200},
                    {'user_id': 2, 'amount': -100},
                    {'user_id': 3, 'amount': 75},
                    {'user_id': 4, 'amount': 225}]
        balances = get_balances(payments)
        print(balances)
        assert balances == [
            make_transaction([1, 4, 200]),
            make_transaction([2, 4, 25]),
            make_transaction([2, 3, 75])
        ]


class GroupBalanceTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.a_auth = auth_header(get_a_token(self.client))
        self.b_auth = auth_header(get_a_token(self.client))
        self.c_auth = auth_header(get_a_token(self.client))
        self.cat = self.client.post(
            f'/api/v1/categories/', {'name': 'Dummy Cat'}, **self.a_auth)
        x = self.client.post(f'/api/v1/groups/',
                             {'name': 'TestGroup'}, **self.a_auth)

    def test_transitive_addition(self):
        b_add = self.client.put(f'/api/v1/groups/1/members/', {
            'add': {'user_ids': [2]}
        }, **self.a_auth)
        c_add = self.client.put(f'/api/v1/groups/1/members/', {
            'add': {'user_ids': [3]}
        }, **self.b_auth)
        print(b_add, c_add)

    def test_removal(self):
        self.test_transitive_addition()
        c_b_remove = self.client.put(f'/api/v1/groups/1/members/', {
            'remove': {'user_ids': [2, 3]}
        }, **self.b_auth)
        print(c_b_remove)

    def test_balances(self):
        self.test_transitive_addition()
        expense = {
            'group': 1,
            'category': 1,
            'description': 'culpa',
            'total_amount': '300',
            'users': [
                {
                    'amount_lent': '300',
                    'amount_owed': '100',
                    'user': 1
                },
                {
                    'amount_lent': '0',
                    'amount_owed': '100',
                    'user': 2
                },
                {
                    'amount_lent': '0',
                    'amount_owed': '100',
                    'user': 3
                },
            ]
        }

        a_expense = self.client.post(
            f'/api/v1/expenses/', expense, **self.a_auth)
        expense = {
            'group': 1,
            'category': 1,
            'description': 'culpa',
            'total_amount': '300',
            'users': [
                {
                    'amount_lent': '50',
                    'amount_owed': '100',
                    'user': 1
                },
                {
                    'amount_lent': '50',
                    'amount_owed': '100',
                    'user': 2
                },
                {
                    'amount_lent': '200',
                    'amount_owed': '100',
                    'user': 3
                },
            ]
        }
        b_expense = self.client.post(
            f'/api/v1/expenses/', expense, **self.b_auth)
        print(a_expense, b_expense)
        balances = self.client.get(
            f'/api/v1/groups/1/balances/', **self.a_auth)
        print(balances, balances.json())

    def test_balances_2way(self):
        self.test_transitive_addition()
        expense = {
            'group': 1,
            'category': 1,
            'description': 'culpa',
            'total_amount': '300',
            'users': [
                {
                    'amount_lent': '300',
                    'amount_owed': '100',
                    'user': 1
                },
                {
                    'amount_lent': '0',
                    'amount_owed': '100',
                    'user': 2
                },
                {
                    'amount_lent': '0',
                    'amount_owed': '100',
                    'user': 3
                },
            ]
        }

        a_expense = self.client.post(
            f'/api/v1/expenses/', expense, **self.a_auth)
        expense = {
            'group': 1,
            'category': 1,
            'description': 'culpa',
            'total_amount': '300',
            'users': [
                {
                    'amount_lent': '200',
                    'amount_owed': '100',
                    'user': 1
                },
                {
                    'amount_lent': '90',
                    'amount_owed': '100',
                    'user': 2
                },
                {
                    'amount_lent': '10',
                    'amount_owed': '100',
                    'user': 3
                },
            ]
        }

        b_expense = self.client.post(
            f'/api/v1/expenses/', expense, **self.b_auth)
        print(a_expense, b_expense)
        balances = self.client.get(
            f'/api/v1/groups/1/balances/', **self.a_auth)
        print(balances, balances.json())


class BalancesTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.a_auth = auth_header(get_a_token(self.client))
        self.b_auth = auth_header(get_a_token(self.client))
        self.c_auth = auth_header(get_a_token(self.client))
        self.cat = self.client.post(
            f'/api/v1/categories/', {'name': 'Dummy Cat'}, **self.a_auth)
        x = self.client.post(f'/api/v1/groups/',
                             {'name': 'TestGroup'}, **self.a_auth)

    def test_transitive_addition(self):
        b_add = self.client.put(f'/api/v1/groups/1/members/', {
            'add': {'user_ids': [2]}
        }, **self.a_auth)
        c_add = self.client.put(f'/api/v1/groups/1/members/', {
            'add': {'user_ids': [3]}
        }, **self.b_auth)
        print(b_add, c_add)

    def test_balances_2way(self):
        self.test_transitive_addition()
        expense = {
            'group': 1,
            'category': 1,
            'description': 'culpa',
            'total_amount': '300',
            'users': [
                {
                    'amount_lent': '50',
                    'amount_owed': '100',
                    'user': 1
                },
                {
                    'amount_lent': '75',
                    'amount_owed': '100',
                    'user': 2
                },
                {
                    'amount_lent': '175',
                    'amount_owed': '100',
                    'user': 3
                },
            ]
        }

        a_expense = self.client.post(
            f'/api/v1/expenses/', expense, **self.a_auth)
        expense = {
            'group': 1,
            'category': 1,
            'description': 'culpa',
            'total_amount': '300',
            'users': [
                {
                    'amount_lent': '250',
                    'amount_owed': '0',
                    'user': 1
                },
                {
                    'amount_lent': '50',
                    'amount_owed': '100',
                    'user': 2
                },
                {
                    'amount_lent': '0',
                    'amount_owed': '200',
                    'user': 3
                },
            ]
        }
        b_expense = self.client.post(
            f'/api/v1/expenses/', expense, **self.b_auth)
        print(a_expense, b_expense)
        asdf = self.client.get("/api/v1/balances/", **self.a_auth)
        print(asdf, asdf.json())

        asdf = self.client.get("/api/v1/balances/", **self.b_auth)
        print(asdf, asdf.json())

        asdf = self.client.get("/api/v1/balances/", **self.b_auth)
        print(asdf, asdf.json())
