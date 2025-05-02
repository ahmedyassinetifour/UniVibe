import requests
import json
from datetime import date, timedelta
import time
import random
import string

# Base URL for the API
BASE_URL = "http://localhost:8000"

# Colors for console output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_test(message):
    print(f"{Colors.HEADER}[TEST] {message}{Colors.ENDC}")

def print_success(message):
    print(f"{Colors.OKGREEN}[SUCCESS] {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.FAIL}[ERROR] {message}{Colors.ENDC}")

def print_info(message):
    print(f"{Colors.OKBLUE}[INFO] {message}{Colors.ENDC}")

def print_response(response):
    try:
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except:
        print(f"Status Code: {response.status_code}")
        print("Response: Unable to parse JSON")
        print(response.text)
    print()

def random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def test_auth_endpoints():
    # Generate random credentials for testing
    username = f"testuser_{random_string()}"
    email = f"test_{random_string()}@example.com"
    password = "password123"
    
    print_test("Testing Auth Endpoints")
    
    # Test signup
    print_test("POST /auth/signup - Creating a new user")
    signup_data = {
        "username": username,
        "email": email,
        "password": password,
        "role": "student",
        "first_name": "Test",
        "last_name": "User",
        "date_of_birth": str(date.today() - timedelta(days=365*20))  # 20 years ago
    }
    
    response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
    print_response(response)
    
    if response.status_code == 200:
        print_success("User created successfully")
        user_id = response.json().get("user_id")
        print_info(f"User ID: {user_id}")
    else:
        print_error("Failed to create user")
        # If signup fails, try with a different username
        if response.status_code == 400:
            username = f"testuser_{random_string()}"
            email = f"test_{random_string()}@example.com"
            signup_data["username"] = username
            signup_data["email"] = email
            print_info(f"Retrying with new username: {username}")
            response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
            print_response(response)
            if response.status_code == 200:
                print_success("User created successfully on retry")
                user_id = response.json().get("user_id")
                print_info(f"User ID: {user_id}")
            else:
                print_error("Failed to create user on retry, continuing with tests")
    
    # Test login
    print_test("POST /auth/login - Logging in with created user")
    login_data = {
        "username": username,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print_response(response)
    
    if response.status_code == 200:
        print_success("Login successful")
        token = response.json().get("auth_token")
        print_info(f"Auth Token: {token}")
        
        # Set the authorization header for subsequent requests
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        # Test verify token
        print_test("POST /auth/verify-token - Verifying token")
        verify_data = {
            "token": token
        }
        
        response = requests.post(f"{BASE_URL}/auth/verify-token", json=verify_data)
        print_response(response)
        
        if response.status_code == 200:
            print_success("Token verification successful")
            return headers, user_id
        else:
            print_error("Token verification failed")
    else:
        print_error("Login failed")
    
    return None, None

def test_user_endpoints(headers, user_id):
    print_test("Testing User Endpoints")
    
    # Test get current user
    print_test("GET /users/me - Getting current user")
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        print_success("Got current user successfully")
    else:
        print_error("Failed to get current user")
    
    # Test get students
    print_test("GET /students - Getting all students")
    response = requests.get(f"{BASE_URL}/students", headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        print_success("Got students successfully")
        students = response.json()
        if students:
            print_info(f"Found {len(students)} students")
    else:
        print_error("Failed to get students")
    
    # Test get user clubs
    print_test(f"GET /users/{user_id}/clubs - Getting clubs for user")
    response = requests.get(f"{BASE_URL}/users/{user_id}/clubs", headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        print_success("Got user clubs successfully")
    else:
        print_error("Failed to get user clubs")
    
    # Test get my clubs
    print_test("GET /users/me/clubs - Getting clubs for current user")
    response = requests.get(f"{BASE_URL}/users/me/clubs", headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        print_success("Got current user clubs successfully")
    else:
        print_error("Failed to get current user clubs")
    
    # Create an admin user to test role assignment
    admin_username = f"admin_{random_string()}"
    admin_email = f"admin_{random_string()}@example.com"
    admin_password = "adminpass123"
    
    admin_data = {
        "username": admin_username,
        "email": admin_email,
        "password": admin_password,
        "role": "admin",
        "first_name": "Admin",
        "last_name": "User",
        "date_of_birth": str(date.today() - timedelta(days=365*30))  # 30 years ago
    }
    
    print_test("POST /auth/signup - Creating an admin user for role testing")
    response = requests.post(f"{BASE_URL}/auth/signup", json=admin_data)
    print_response(response)
    
    if response.status_code == 200:
        print_success("Admin user created successfully")
        admin_id = response.json().get("user_id")
        
        # Login as admin
        print_test("POST /auth/login - Logging in as admin")
        login_data = {
            "username": admin_username,
            "password": admin_password
        }
        
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print_response(response)
        
        if response.status_code == 200:
            print_success("Admin login successful")
            admin_token = response.json().get("auth_token")
            admin_headers = {
                "Authorization": f"Bearer {admin_token}"
            }
            
            # Test assign role
            print_test(f"POST /admin/assign_role - Assigning club_leader role to user {user_id}")
            role_data = {
                "user_id": user_id,
                "role": "club_leader"
            }
            
            response = requests.post(f"{BASE_URL}/admin/assign_role", json=role_data, headers=admin_headers)
            print_response(response)
            
            if response.status_code == 200:
                print_success("Role assigned successfully")
            else:
                print_error("Failed to assign role")
            
            return admin_headers, admin_id
        else:
            print_error("Admin login failed")
    else:
        print_error("Failed to create admin user")
    
    return None, None

def test_club_endpoints(headers, user_id):
    print_test("Testing Club Endpoints")
    
    # Test get clubs
    print_test("GET /clubs - Getting all clubs")
    response = requests.get(f"{BASE_URL}/clubs", headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        print_success("Got clubs successfully")
        clubs = response.json()
        existing_club_id = None
        if clubs:
            print_info(f"Found {len(clubs)} clubs")
            existing_club_id = clubs[0].get("club_id")
    else:
        print_error("Failed to get clubs")
    
    # Test create club
    print_test("POST /clubs - Creating a new club")
    club_data = {
        "club_name": f"Test Club {random_string()}",
        "description": "A test club for API testing",
        "pic": "https://example.com/club.jpg",
        "leader_id": user_id
    }
    
    response = requests.post(f"{BASE_URL}/clubs", json=club_data, headers=headers)
    print_response(response)
    
    club_id = None
    if response.status_code == 200:
        print_success("Club created successfully")
        club_id = response.json().get("club_id")
        print_info(f"Club ID: {club_id}")
    else:
        print_error("Failed to create club")
        # If we have an existing club from earlier, use that
        club_id = existing_club_id
        if club_id:
            print_info(f"Using existing club with ID: {club_id}")
    
    if club_id:
        # Test get club
        print_test(f"GET /clubs/{club_id} - Getting club details")
        response = requests.get(f"{BASE_URL}/clubs/{club_id}", headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            print_success("Got club details successfully")
        else:
            print_error("Failed to get club details")
        
        # Test get club members
        print_test(f"GET /clubs/{club_id}/members - Getting club members")
        response = requests.get(f"{BASE_URL}/clubs/{club_id}/members", headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            print_success("Got club members successfully")
        else:
            print_error("Failed to get club members")
        
        # Test join club
        print_test(f"POST /clubs/{club_id}/join - Joining club")
        response = requests.post(f"{BASE_URL}/clubs/{club_id}/join", headers=headers)
        print_response(response)
        
        join_success = False
        if response.status_code == 200:
            print_success("Joined club successfully")
            join_success = True
        elif response.status_code == 400 and "Already a member" in response.text:
            print_info("Already a member of this club")
            join_success = True
        else:
            print_error("Failed to join club")
        
        # If join was successful, test leave club
        if join_success:
            print_test(f"DELETE /clubs/{club_id}/leave - Leaving club")
            response = requests.delete(f"{BASE_URL}/clubs/{club_id}/leave", headers=headers)
            print_response(response)
            
            if response.status_code == 204:
                print_success("Left club successfully")
            else:
                print_error("Failed to leave club")
    else:
        print_error("No club ID available for testing club endpoints")
    
    return club_id

def test_join_request_system(student_headers, leader_headers, student_id, club_id):
    """Test the join request system for clubs."""
    print_test("Testing Club Join Request System")
    
    # First, ensure the student is not a member of the club
    print_test(f"DELETE /clubs/{club_id}/leave - Ensuring student is not a member")
    requests.delete(f"{BASE_URL}/clubs/{club_id}/leave", headers=student_headers)
    
    # 1. Student requests to join the club
    print_test(f"POST /clubs/{club_id}/request-join - Student requesting to join club")
    request_data = {
        "request_message": "I would like to join this club for testing purposes."
    }
    
    response = requests.post(f"{BASE_URL}/clubs/{club_id}/request-join", 
                          json=request_data, 
                          headers=student_headers)
    print_response(response)
    
    if response.status_code == 200:
        print_success("Join request created successfully")
        request_id = response.json().get("request_id")
        print_info(f"Request ID: {request_id}")
        
        # 2. Student views their own join requests
        print_test("GET /users/me/join-requests - Student viewing their join requests")
        response = requests.get(f"{BASE_URL}/users/me/join-requests", headers=student_headers)
        print_response(response)
        
        if response.status_code == 200:
            print_success("Retrieved student's join requests successfully")
            if response.json():
                print_info(f"Found {len(response.json())} join requests for student")
        else:
            print_error("Failed to retrieve student's join requests")
        
        # 3. Club leader views pending join requests for the club
        print_test(f"GET /clubs/{club_id}/join-requests - Club leader viewing pending join requests")
        response = requests.get(f"{BASE_URL}/clubs/{club_id}/join-requests", headers=leader_headers)
        print_response(response)
        
        if response.status_code == 200:
            print_success("Retrieved club's join requests successfully")
            if response.json():
                print_info(f"Found {len(response.json())} pending join requests for club")
                
                # Find the request ID if not already known
                if not request_id and response.json():
                    for req in response.json():
                        if req.get("user_id") == student_id:
                            request_id = req.get("request_id")
                            print_info(f"Found request ID: {request_id}")
        else:
            print_error("Failed to retrieve club's join requests")
        
        # 4. Test student (unauthorized) trying to view club join requests
        print_test(f"GET /clubs/{club_id}/join-requests - Student trying to view club join requests (should fail)")
        response = requests.get(f"{BASE_URL}/clubs/{club_id}/join-requests", headers=student_headers)
        print_response(response)
        
        if response.status_code == 403:
            print_success("Permission check working - student cannot view club join requests")
        else:
            print_error("Permission check failed - student was able to view club join requests")
        
        # 5. Club leader approves the join request
        if request_id:
            print_test(f"POST /clubs/join-requests/{request_id}/action - Club leader approving join request")
            action_data = {
                "action": "approve"
            }
            
            response = requests.post(f"{BASE_URL}/clubs/join-requests/{request_id}/action", 
                                  json=action_data, 
                                  headers=leader_headers)
            print_response(response)
            
            if response.status_code == 200:
                print_success("Join request approved successfully")
                
                # 6. Verify student is now a member of the club
                print_test(f"GET /clubs/{club_id}/members - Verifying student is now a club member")
                response = requests.get(f"{BASE_URL}/clubs/{club_id}/members", headers=leader_headers)
                print_response(response)
                
                if response.status_code == 200:
                    members = response.json()
                    is_member = any(member.get("user_id") == student_id for member in members)
                    
                    if is_member:
                        print_success(f"Student (ID: {student_id}) is now a member of the club")
                    else:
                        print_error(f"Student (ID: {student_id}) was not added as a club member")
                else:
                    print_error("Failed to retrieve club members")
            else:
                print_error("Failed to approve join request")
        else:
            print_error("No request ID available for testing approval")
    else:
        print_error("Failed to create join request")

def test_event_endpoints(headers):
    print_test("Testing Event Endpoints")
    
    # Test get events
    print_test("GET /events - Getting all events")
    response = requests.get(f"{BASE_URL}/events", headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        print_success("Got events successfully")
        events = response.json()
        existing_event_id = None
        if events:
            print_info(f"Found {len(events)} events")
            existing_event_id = events[0].get("event_id")
    else:
        print_error("Failed to get events")
    
    # We need a club ID to create an event
    print_test("GET /clubs - Getting clubs for event creation")
    response = requests.get(f"{BASE_URL}/clubs", headers=headers)
    
    club_id = None
    if response.status_code == 200:
        clubs = response.json()
        if clubs:
            club_id = clubs[0].get("club_id")
            print_info(f"Using club with ID: {club_id} for event creation")
            
            # Join the club first to have permission to create events
            print_test(f"POST /clubs/{club_id}/join - Joining club to get event creation permission")
            join_response = requests.post(f"{BASE_URL}/clubs/{club_id}/join", headers=headers)
            print_response(join_response)
            
            if join_response.status_code == 200 or (join_response.status_code == 400 and "Already a member" in join_response.text):
                print_success("Successfully joined or already a member of the club")
            else:
                print_error("Failed to join club for event creation")
    
    if club_id:
        # Test create event
        print_test("POST /events - Creating a new event")
        event_data = {
            "event_name": f"Test Event {random_string()}",
            "event_description": "A test event for API testing",
            "event_date": str(date.today() + timedelta(days=7)),  # 1 week from now
            "event_image": "https://example.com/event.jpg",
            "club_id": club_id
        }
        
        response = requests.post(f"{BASE_URL}/events", json=event_data, headers=headers)
        print_response(response)
        
        event_id = None
        if response.status_code == 200:
            print_success("Event created successfully")
            event_id = response.json().get("event_id")
            print_info(f"Event ID: {event_id}")
        else:
            print_error("Failed to create event")
            # If we have an existing event from earlier, use that
            event_id = existing_event_id
            if event_id:
                print_info(f"Using existing event with ID: {event_id}")
        
        if event_id:
            # Test get event
            print_test(f"GET /events/{event_id} - Getting event details")
            response = requests.get(f"{BASE_URL}/events/{event_id}", headers=headers)
            print_response(response)
            
            if response.status_code == 200:
                print_success("Got event details successfully")
            else:
                print_error("Failed to get event details")
        else:
            print_error("No event ID available for testing event endpoints")
    else:
        print_error("No club ID available for event creation")

def run_all_tests():
    print_test("Starting API Tests")
    print_info("Testing against: " + BASE_URL)
    
    # Test auth endpoints and get headers for subsequent requests
    student_headers, student_id = test_auth_endpoints()
    
    if student_headers and student_id:
        # Run user tests and create admin user
        leader_headers, leader_id = test_user_endpoints(student_headers, student_id)
        
        # Run club tests
        club_id = test_club_endpoints(student_headers, student_id)
        
        # Test join request system
        if leader_headers and leader_id and club_id:
            test_join_request_system(student_headers, leader_headers, student_id, club_id)
        else:
            print_error("Missing leader headers, leader ID, or club ID for join request tests")
        
        # Run event tests
        test_event_endpoints(student_headers)
    else:
        print_error("Authentication failed, cannot continue with other tests")
    
    print_test("API Tests Completed")

if __name__ == "__main__":
    run_all_tests() 