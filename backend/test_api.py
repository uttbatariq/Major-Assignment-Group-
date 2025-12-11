"""
Simple test suite for the Tourism API.
Run with: python -m pytest test_api.py -v
"""
import sys
import sqlite3
import json
from init_db import DB, init_db
import app as app_module

def test_db_initialized():
    """Test that DB is created with tables."""
    init_db()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in c.fetchall()]
    conn.close()
    assert 'admins' in tables
    assert 'tours' in tables
    assert 'users' in tables
    assert 'registrations' in tables


def test_flask_server_runs():
    """Test that Flask server starts."""
    init_db()
    client = app_module.app.test_client()
    response = client.get('/')
    assert response.status_code == 200
    assert b'Tourism Flask API running' in response.data


def test_admin_login():
    """Test admin login endpoint."""
    init_db()
    client = app_module.app.test_client()
    # invalid credentials
    response = client.post('/admin/login', json={'username': 'invalid', 'password': 'bad'})
    assert response.status_code == 401
    # valid credentials
    response = client.post('/admin/login', json={'username': 'admin', 'password': 'adminpass'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'token' in data
    return data['token']


def test_tour_crud():
    """Test tour CRUD operations."""
    init_db()
    client = app_module.app.test_client()
    token = test_admin_login()
    
    # Create tour
    response = client.post('/tours', 
        headers={'X-ADMIN-TOKEN': token},
        json={'title': 'Paris Trip', 'price': 999.99, 'description': 'Visit Paris', 'date': '2024-06-15'}
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    tour_id = data['id']
    
    # List tours
    response = client.get('/tours')
    assert response.status_code == 200
    tours = json.loads(response.data)
    assert len(tours) > 0
    assert any(t['id'] == tour_id for t in tours)
    
    # Get tour
    response = client.get(f'/tours/{tour_id}')
    assert response.status_code == 200
    tour = json.loads(response.data)
    assert tour['title'] == 'Paris Trip'
    
    # Update tour
    response = client.put(f'/tours/{tour_id}',
        headers={'X-ADMIN-TOKEN': token},
        json={'price': 1299.99}
    )
    assert response.status_code == 200
    
    # Delete tour
    response = client.delete(f'/tours/{tour_id}',
        headers={'X-ADMIN-TOKEN': token}
    )
    assert response.status_code == 200


def test_registration():
    """Test user registration for tours."""
    init_db()
    client = app_module.app.test_client()
    token = test_admin_login()
    
    # Create a tour
    response = client.post('/tours',
        headers={'X-ADMIN-TOKEN': token},
        json={'title': 'Beach Day', 'price': 49.99}
    )
    tour_id = json.loads(response.data)['id']
    
    # Register user
    response = client.post('/registrations',
        json={
            'tourId': tour_id,
            'seats': 2,
            'user': {'name': 'Alice', 'email': 'alice@test.com', 'phone': '555-1234'}
        }
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total_price'] == 99.98  # 2 seats * 49.99


def test_analytics():
    """Test analytics endpoints."""
    init_db()
    client = app_module.app.test_client()
    token = test_admin_login()
    
    # Create tour and register
    response = client.post('/tours',
        headers={'X-ADMIN-TOKEN': token},
        json={'title': 'Mountain Hike', 'price': 75.00}
    )
    tour_id = json.loads(response.data)['id']
    
    client.post('/registrations',
        json={'tourId': tour_id, 'seats': 3, 'user': {'name': 'Bob', 'email': 'bob@test.com'}}
    )
    
    # Check registrations count
    response = client.get(f'/analytics/tour/{tour_id}/registrations',
        headers={'X-ADMIN-TOKEN': token}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total_seats'] == 3
    assert data['bookings'] == 1
    
    # Check revenue
    response = client.get(f'/analytics/tour/{tour_id}/revenue',
        headers={'X-ADMIN-TOKEN': token}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['revenue'] == 225.00


if __name__ == '__main__':
    print("Running Tourism API tests...")
    try:
        test_db_initialized()
        print("✓ DB initialized")
        test_flask_server_runs()
        print("✓ Flask server runs")
        test_admin_login()
        print("✓ Admin login works")
        test_tour_crud()
        print("✓ Tour CRUD works")
        test_registration()
        print("✓ Registration works")
        test_analytics()
        print("✓ Analytics work")
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
