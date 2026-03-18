"""
Tests for the Mergington High School Activities API
Using AAA (Arrange-Act-Assert) testing pattern
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client with fresh app state"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to default state before each test"""
    # Arrange: Set up initial state
    original = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
    }
    
    activities.clear()
    activities.update(original)
    
    yield
    
    # Cleanup
    activities.clear()
    activities.update(original)


class TestGetActivities:
    """Test GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Should return all activities with their details"""
        # Arrange
        expected_activity = "Chess Club"
        expected_max_participants = 12
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert expected_activity in data
        assert data[expected_activity]["max_participants"] == expected_max_participants
        assert len(data[expected_activity]["participants"]) == 2

    def test_get_activities_contains_required_fields(self, client):
        """Each activity should have required fields"""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity in data.items():
            for field in required_fields:
                assert field in activity
            assert isinstance(activity["participants"], list)


class TestSignupForActivity:
    """Test POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_success(self, client):
        """Should successfully sign up a student for an activity"""
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup?email={new_email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "message" in response.json()
        assert new_email in response.json()["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        assert new_email in activities_response.json()[activity_name]["participants"]

    def test_signup_for_nonexistent_activity(self, client):
        """Should return 404 when activity doesn't exist"""
        # Arrange
        nonexistent_activity = "NonexistentClub"
        email = "student@mergington.edu"
        expected_status = 404
        expected_error_text = "Activity not found"
        
        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == expected_status
        assert expected_error_text in response.json()["detail"]

    def test_signup_duplicate_student(self, client):
        """Should return 400 when student already signed up"""
        # Arrange
        activity_name = "Chess Club"
        already_registered_email = "michael@mergington.edu"
        expected_status = 400
        expected_error_text = "already signed up"
        
        # Act
        response = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup?email={already_registered_email}"
        )
        
        # Assert
        assert response.status_code == expected_status
        assert expected_error_text in response.json()["detail"]

    def test_signup_with_url_encoded_activity_name(self, client):
        """Should handle URL-encoded activity names"""
        # Arrange
        activity_name = "Programming Class"
        new_email = "newstudent@mergington.edu"
        encoded_name = activity_name.replace(" ", "%20")
        
        # Act
        response = client.post(
            f"/activities/{encoded_name}/signup?email={new_email}"
        )
        
        # Assert
        assert response.status_code == 200

    def test_signup_multiple_students_same_activity(self, client):
        """Should allow multiple different students to sign up"""
        # Arrange
        activity_name = "Chess Club"
        student1 = "student1@mergington.edu"
        student2 = "student2@mergington.edu"
        encoded_name = activity_name.replace(" ", "%20")
        
        # Act
        response1 = client.post(f"/activities/{encoded_name}/signup?email={student1}")
        response2 = client.post(f"/activities/{encoded_name}/signup?email={student2}")
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert student1 in participants
        assert student2 in participants


class TestUnregisterParticipant:
    """Test DELETE /activities/{activity_name}/participants endpoint"""

    def test_unregister_participant_success(self, client):
        """Should successfully remove a participant"""
        # Arrange
        activity_name = "Chess Club"
        participant_to_remove = "michael@mergington.edu"
        encoded_name = activity_name.replace(" ", "%20")
        
        # Act
        response = client.delete(
            f"/activities/{encoded_name}/participants?email={participant_to_remove}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "message" in response.json()
        assert participant_to_remove in response.json()["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert participant_to_remove not in participants

    def test_unregister_nonexistent_activity(self, client):
        """Should return 404 when activity doesn't exist"""
        # Arrange
        nonexistent_activity = "NonexistentClub"
        email = "student@mergington.edu"
        expected_status = 404
        expected_error_text = "Activity not found"
        
        # Act
        response = client.delete(
            f"/activities/{nonexistent_activity}/participants?email={email}"
        )
        
        # Assert
        assert response.status_code == expected_status
        assert expected_error_text in response.json()["detail"]

    def test_unregister_nonexistent_participant(self, client):
        """Should return 404 when participant not in activity"""
        # Arrange
        activity_name = "Chess Club"
        nonexistent_email = "ghost@mergington.edu"
        encoded_name = activity_name.replace(" ", "%20")
        expected_status = 404
        expected_error_text = "Participant not found"
        
        # Act
        response = client.delete(
            f"/activities/{encoded_name}/participants?email={nonexistent_email}"
        )
        
        # Assert
        assert response.status_code == expected_status
        assert expected_error_text in response.json()["detail"]

    def test_unregister_then_signup_again(self, client):
        """Should allow signup again after unregistering"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        encoded_name = activity_name.replace(" ", "%20")
        
        # Act: Unregister
        unregister_response = client.delete(
            f"/activities/{encoded_name}/participants?email={email}"
        )
        
        # Act: Sign up again
        signup_response = client.post(
            f"/activities/{encoded_name}/signup?email={email}"
        )
        
        # Assert: Both operations succeeded
        assert unregister_response.status_code == 200
        assert signup_response.status_code == 200
        
        # Assert: Participant is back
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email in participants


class TestRootRedirect:
    """Test GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Should redirect to /static/index.html"""
        # Arrange
        expected_status = 307
        expected_location = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == expected_status
        assert response.headers["location"] == expected_location
