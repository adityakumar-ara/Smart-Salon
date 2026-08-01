from django.test import TestCase
from django.urls import reverse
from accounts.models import CustomUser
from shopkeeper.models import Salon


class NearbySalonsApiTests(TestCase):
    def test_nearby_salons_api_returns_close_salons(self):
        owner = CustomUser.objects.create_user(
            username='owner1',
            password='secret123',
            name='Owner One',
            mobile='1234567890',
            is_shopkeeper=True,
        )

        near_salon = Salon.objects.create(
            owner=owner,
            owner_name='Owner One',
            salon_name='Near Salon',
            salon_image='salon_image/test.jpg',
            latitude=28.6139,
            longitude=77.2090,
            open_time='09:00:00',
            close_time='20:00:00',
        )
        far_salon = Salon.objects.create(
            owner=owner,
            owner_name='Owner One',
            salon_name='Far Salon',
            salon_image='salon_image/test2.jpg',
            latitude=28.7000,
            longitude=77.3000,
            open_time='09:00:00',
            close_time='20:00:00',
        )

        response = self.client.get(reverse('nearby_salons_api'), {'lat': 28.6139, 'lng': 77.2090, 'radius': 10})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['salons'][0]['name'], near_salon.salon_name)
        self.assertNotIn(far_salon.salon_name, [item['name'] for item in data['salons']])
