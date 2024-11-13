from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from django.contrib.auth.models import User
from api.models import Author,Follow,InboxEntry
from rest_framework import status
import urllib
import uuid


class TestFollowersEndpoints(APITestCase):
    def setUp(self):
        self.HTTP_REFERER='http://testserver/'
        # Creating user and corresponding author
        self.user1 = User.objects.create_user(username='testuser1', password='testpassword1')
        self.author1 = Author.objects.create(user=self.user1, displayName='Test Author 1')

        # Creating another user and corresponding author
        new_author_id = uuid.uuid4()
        self.user2 = User.objects.create_user(username='testuser2', password='testpassword2')
        self.author2 = Author.objects.create(user=self.user2, displayName='Test Author 2', id=new_author_id, url='http://127.0.0.1:8000/api/v1/authors/'+str(new_author_id)+'/')

        # Creating inbox entries for author1
        self.inbox_entry1 = InboxEntry.objects.create(author=self.author1, entry_json={'type': 'post', 'content': 'Hello World!'}, seen=False)
        self.inbox_entry2 = InboxEntry.objects.create(author=self.author1, entry_json={'type': 'like', 'content': 'Liked your post'}, seen=False)

        self.client = APIClient()
        
        #follow with pending = False for testing
        self.follow = Follow.objects.create(follower=self.author2, followed=self.author1, pending=False)
        self.follow.save()
    

    def test_get_unseen_notifications(self):
        # Authenticate as user1 to test viewing their notifications
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('api:check_new_notifications', kwargs={'author_id': self.author1.id})
        response = self.client.get(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_new'])
        self.assertEqual(response.data['unseen_count'], 2)  # Expecting 2 unseen notifications

    def test_no_unseen_notifications_for_other_user(self):
        # Authenticate as user2, who should not have access to user1's notifications
        self.client.force_authenticate(user=self.user2)

        url = reverse('api:check_new_notifications', kwargs={'author_id': self.author1.id})
        response = self.client.get(url, format='json')

        # Expecting a 403 Forbidden because user2 is trying to access user1's notifications
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_follow_author(self):
        self.client.force_authenticate(user=self.user2)
        url = reverse('api:follow', kwargs={
            'author_id': self.author1.id, 
            'foreign_author_id': urllib.parse.quote(self.author2.url)
        })
        response = self.client.put(url, HTTP_REFERER=self.HTTP_REFERER)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(Follow.objects.filter(follower=self.author2, followed=self.author1).exists())

    def test_unfollow_author(self):
        self.client.force_authenticate(user=self.user2)
        url = reverse('api:follow', kwargs={
            'author_id': self.author1.id, 
            'foreign_author_id': urllib.parse.quote(self.author2.url)
        })
        response = self.client.delete(url, HTTP_REFERER=self.HTTP_REFERER)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Follow.objects.filter(follower=self.author2, followed=self.author1).exists())

    def test_FollowerView_get(self):
        self.client.force_authenticate(user=self.user2)
        url = reverse('api:follow', kwargs={
            'author_id': self.author1.id, 
            'foreign_author_id': urllib.parse.quote(self.author2.url)
        })
        response = self.client.get(url, HTTP_REFERER=self.HTTP_REFERER)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

