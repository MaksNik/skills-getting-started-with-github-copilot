"""Unit tests for FastAPI activities application

Tests follow the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and state
- Act: Execute the action being tested
- Assert: Verify the results
"""

import pytest


class TestRootEndpoint:
    """Tests for the GET / endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static/index.html
        
        Arrange: Client is ready to make requests
        Act: Send GET request to root endpoint
        Assert: Response should redirect to /static/index.html
        """
        # Arrange
        # (client fixture is provided by conftest.py)
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint"""
    
    def test_get_all_activities(self, client):
        """Test retrieving all activities
        
        Arrange: Activities data is initialized with 9 activities
        Act: Send GET request to /activities endpoint
        Assert: Response contains all 9 activities with correct structure
        """
        # Arrange
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class",
            "Basketball Team", "Tennis Club", "Drama Club",
            "Art Studio", "Debate Team", "Science Club"
        ]
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        for activity_name in expected_activities:
            assert activity_name in data
            # Verify each activity has required fields
            activity = data[activity_name]
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity
    
    def test_activities_have_empty_participants_initially(self, client):
        """Test that activities start with no participants
        
        Arrange: Activities are reset (via reset_activities fixture)
        Act: Send GET request to /activities endpoint
        Assert: All participant lists should be empty
        """
        # Arrange
        # (reset_activities fixture ensures clean state)
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        for activity_name, activity_data in data.items():
            assert activity_data["participants"] == []


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client):
        """Test successful student signup for activity
        
        Arrange: Valid activity name and email
        Act: Send POST request to signup endpoint
        Assert: Student should be added to activity participants
        """
        # Arrange
        activity_name = "Chess Club"
        email = "student1@school.com"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup", 
                              params={"email": email})
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
        
        # Verify student is in participants
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]
    
    def test_signup_invalid_activity(self, client):
        """Test signup with non-existent activity
        
        Arrange: Invalid activity name
        Act: Send POST request with invalid activity
        Assert: Should return 404 error
        """
        # Arrange
        invalid_activity = "Nonexistent Activity"
        email = "student1@school.com"
        
        # Act
        response = client.post(f"/activities/{invalid_activity}/signup",
                              params={"email": email})
        
        # Assert
        assert response.status_code == 404
        assert response.json() == {"detail": "Activity not found"}
    
    def test_signup_duplicate_student(self, client):
        """Test that same student cannot sign up twice for same activity
        
        Arrange: Student already signed up for an activity
        Act: Try to sign up the same student again
        Assert: Should return 400 error
        """
        # Arrange
        activity_name = "Chess Club"
        email = "student1@school.com"
        # First signup
        client.post(f"/activities/{activity_name}/signup", 
                   params={"email": email})
        
        # Act - attempt duplicate signup
        response = client.post(f"/activities/{activity_name}/signup",
                              params={"email": email})
        
        # Assert
        assert response.status_code == 400
        assert response.json() == {"detail": "Student is already signed up for this activity"}
    
    def test_signup_multiple_students_same_activity(self, client):
        """Test multiple different students can sign up for same activity
        
        Arrange: Activity ready for multiple signups
        Act: Sign up multiple students
        Assert: All students should be in participants list
        """
        # Arrange
        activity_name = "Basketball Team"
        emails = ["alice@school.com", "bob@school.com", "charlie@school.com"]
        
        # Act
        for email in emails:
            response = client.post(f"/activities/{activity_name}/signup",
                                  params={"email": email})
            assert response.status_code == 200
        
        # Assert
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        participants = activities_data[activity_name]["participants"]
        assert len(participants) == 3
        for email in emails:
            assert email in participants
    
    def test_signup_at_capacity(self, client):
        """Test signup when activity is at max capacity
        
        Arrange: Activity filled to max capacity (e.g., Chess Club has max 12)
        Act: Try to sign up one more student
        Assert: Should be allowed (capacity check not shown in requirements)
        """
        # Arrange
        activity_name = "Chess Club"
        max_capacity = 12
        
        # Sign up 12 students to fill capacity
        for i in range(max_capacity):
            email = f"student{i}@school.com"
            response = client.post(f"/activities/{activity_name}/signup",
                                  params={"email": email})
            assert response.status_code == 200
        
        # Act - try to add one more
        response = client.post(f"/activities/{activity_name}/signup",
                              params={"email": "overflow@school.com"})
        
        # Assert - based on code review, capacity limit is not enforced
        # This test documents current behavior (capacity not enforced)
        assert response.status_code == 200  # Currently accepts overflow


class TestUnregisterEndpoint:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_successful(self, client):
        """Test successful student unregistration from activity
        
        Arrange: Student is signed up for an activity
        Act: Send DELETE request to unregister
        Assert: Student should be removed from participants
        """
        # Arrange
        activity_name = "Drama Club"
        email = "student1@school.com"
        # First sign up
        client.post(f"/activities/{activity_name}/signup",
                   params={"email": email})
        
        # Act
        response = client.delete(f"/activities/{activity_name}/unregister",
                                params={"email": email})
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
        
        # Verify student is removed from participants
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data[activity_name]["participants"]
    
    def test_unregister_invalid_activity(self, client):
        """Test unregister from non-existent activity
        
        Arrange: Invalid activity name
        Act: Send DELETE request with invalid activity
        Assert: Should return 404 error
        """
        # Arrange
        invalid_activity = "Nonexistent Activity"
        email = "student1@school.com"
        
        # Act
        response = client.delete(f"/activities/{invalid_activity}/unregister",
                                params={"email": email})
        
        # Assert
        assert response.status_code == 404
        assert response.json() == {"detail": "Activity not found"}
    
    def test_unregister_not_enrolled_student(self, client):
        """Test unregister attempt by student not enrolled in activity
        
        Arrange: Student has never signed up for activity
        Act: Try to unregister student
        Assert: Should return 400 error
        """
        # Arrange
        activity_name = "Art Studio"
        email = "not_enrolled@school.com"
        
        # Act
        response = client.delete(f"/activities/{activity_name}/unregister",
                                params={"email": email})
        
        # Assert
        assert response.status_code == 400
        assert response.json() == {"detail": "Student is not signed up for this activity"}
    
    def test_unregister_after_signup_and_signup_again(self, client):
        """Test student can sign up again after unregistering
        
        Arrange: Student signs up, unregisters, then attempts to sign up again
        Act: Execute signup -> unregister -> signup sequence
        Assert: All operations should succeed with correct state
        """
        # Arrange
        activity_name = "Science Club"
        email = "student1@school.com"
        
        # First signup
        response1 = client.post(f"/activities/{activity_name}/signup",
                               params={"email": email})
        assert response1.status_code == 200
        
        # Unregister
        response2 = client.delete(f"/activities/{activity_name}/unregister",
                                 params={"email": email})
        assert response2.status_code == 200
        
        # Act - Sign up again
        response3 = client.post(f"/activities/{activity_name}/signup",
                               params={"email": email})
        
        # Assert
        assert response3.status_code == 200
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]


class TestActivitySignupUnregisterFlow:
    """Integration tests for signup/unregister workflows"""
    
    def test_multiple_students_signup_and_unregister(self, client):
        """Test complex flow with multiple students and activities
        
        Arrange: Set up multiple students and activities
        Act: Sign up students, have some unregister, add more
        Assert: Final state should match expected participants
        """
        # Arrange
        activity1 = "Programming Class"
        activity2 = "Tennis Club"
        students = ["alice@school.com", "bob@school.com", "charlie@school.com"]
        
        # Act - Sign up all for activity1
        for email in students:
            client.post(f"/activities/{activity1}/signup", params={"email": email})
        
        # Act - Some unregister from activity1
        client.delete(f"/activities/{activity1}/unregister", 
                     params={"email": students[0]})
        
        # Act - Sign up some for activity2
        client.post(f"/activities/{activity2}/signup", 
                   params={"email": students[0]})
        client.post(f"/activities/{activity2}/signup",
                   params={"email": students[1]})
        
        # Assert
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        # activity1 should have students[1] and students[2]
        assert students[0] not in activities_data[activity1]["participants"]
        assert students[1] in activities_data[activity1]["participants"]
        assert students[2] in activities_data[activity1]["participants"]
        
        # activity2 should have students[0] and students[1]
        assert students[0] in activities_data[activity2]["participants"]
        assert students[1] in activities_data[activity2]["participants"]
        assert students[2] not in activities_data[activity2]["participants"]
