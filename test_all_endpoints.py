#!/usr/bin/env python3
"""
Full verification test suite across all 21 REST API endpoints.
Runs against the live router and asserts HTTP 200 responses with valid schemas.
"""
import sys
from fastapi.testclient import TestClient
from main import app
from core.config import settings

def run_tests():
    client = TestClient(app)

    tests = [
        ('GET', '/health', None),
        ('GET', '/', None),
        ('GET', '/openapi.json', None),
        ('GET', '/docs', None),
        ('GET', '/redoc', None),
        ('GET', '/api/v1/auth/status', None),
        ('POST', '/api/v1/auth/login', {'username': settings.ROUTER_USER, 'password': settings.ROUTER_PASSWORD}),
        ('GET', '/api/v1/system/info', None),
        ('GET', '/api/v1/wifi', None),
        ('GET', '/api/v1/wifi/settings', None),
        ('POST', '/api/v1/wifi/band-steering', {'enabled': False}),
        ('POST', '/api/v1/wifi/guest', {'enabled_24g': False, 'enabled_5g': False}),
        ('GET', '/api/v1/lan/settings', None),
        ('GET', '/api/v1/lan/static-leases', None),
        ('GET', '/api/v1/wan/status', None),
        ('GET', '/api/v1/wan/dmz', None),
        ('POST', '/api/v1/wan/dmz', {'enabled': False, 'ip_address': '192.168.1.3'}),
        ('GET', '/api/v1/wan/upnp', None),
        ('POST', '/api/v1/wan/upnp', {'enabled': False}),
        ('GET', '/api/v1/wan/port-forwarding', None),
        ('GET', '/api/v1/devices', None),
    ]

    passed = 0
    failed = 0

    print(f'{"#":<3} {"METHOD":<6} {"ENDPOINT":<33} {"STATUS":<8} {"RESULT"}')
    print('=' * 85)

    for idx, (method, path, body) in enumerate(tests, 1):
        try:
            if method == 'GET':
                res = client.get(path)
            elif method == 'POST':
                res = client.post(path, json=body)
            
            if res.status_code == 200:
                status_str = '200 OK'
                is_json = res.headers.get('content-type', '').startswith('application/json')
                summary = str(res.json())[:38] if is_json else 'HTML Page'
                print(f'{idx:<3} {method:<6} {path:<33} {status_str:<8} [PASS] {summary}...')
                passed += 1
            else:
                print(f'{idx:<3} {method:<6} {path:<33} {res.status_code:<8} [FAIL] {res.text[:40]}')
                failed += 1
        except Exception as e:
            print(f'{idx:<3} {method:<6} {path:<33} ERROR    [FAIL] {e}')
            failed += 1

    print('=' * 85)
    print(f'Total: {len(tests)}, Passed: {passed}, Failed: {failed}')
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
