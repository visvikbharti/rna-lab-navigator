import requests
import json

# Get access token first
login_resp = requests.post('http://localhost:8000/api/auth/login/', 
    json={'username': 'admin', 'password': 'admin123'})
    
if login_resp.status_code == 200:
    access_token = login_resp.json()['access']
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Create a new session
    session_resp = requests.post('http://localhost:8000/api/chat/sessions/', 
        headers=headers,
        json={'title': 'Test Session'})
    
    if session_resp.status_code == 201:
        session_id = session_resp.json()['id']
        print(f'Session created: {session_id}')
        
        # Try to send a message
        msg_resp = requests.post(
            f'http://localhost:8000/api/chat/sessions/{session_id}/messages/',
            headers=headers,
            json={'content': 'What is RNA?'}
        )
        
        print(f'Message status: {msg_resp.status_code}')
        if msg_resp.status_code != 200:
            print(f'Error: {msg_resp.text[:500]}')
    else:
        print(f'Session creation failed: {session_resp.text}')
else:
    print(f'Login failed: {login_resp.text}')