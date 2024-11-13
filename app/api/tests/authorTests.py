from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from api.models.author import Author
from django.conf import settings

class AuthorTests(APITestCase):

    def setUp(self):
        self.HTTP_REFERER = 'http://testserver/'
        # Create a user and author for test cases
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.author = Author.objects.create(user=self.user, displayName='Test Author')

    def test_get_authors_list(self):
        """
        Ensure we can retrieve a list of authors.
        """
        url = reverse('api:author_list')
        response = self.client.get(url, format='json', HTTP_REFERER=self.HTTP_REFERER)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Assuming this is the only author

    def test_create_author(self):
        """
        Ensure we can create a new author.
        """
        self.client.login(username='testuser', password='testpassword')
        url = reverse('api:author_list')
        data = {
            'displayName': 'New Author',
            'username': 'newauthor',
            'password': 'newpassword',
            'github': 'https://github.com/newauthor',
            'profile_image': 'http://example.com/image.png'
        }
        response = self.client.post(url, data, format='json', HTTP_REFERER=self.HTTP_REFERER)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Author.objects.count(), 2)  # Including the setUp author

    def test_get_author_detail(self):
        """
        Ensure we can retrieve a single author by id.
        """
        url = reverse('api:author_detail', kwargs={'author_id': self.author.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['displayName'], 'Test Author')

    def test_update_author(self):
        """
        Ensure we can update an author.
        """
        self.client.login(username='testuser', password='testpassword')
        url = reverse('api:author_detail', kwargs={'author_id': self.author.id})
        data = {
            'displayName': 'Updated Author',
            'github': 'https://github.com/updatedauthor',
            'profile_image': 'http://example.com/newimage.png'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.author.refresh_from_db()
        self.assertEqual(self.author.displayName, 'Updated Author')

# Add more tests as needed for other endpoints and scenarios

