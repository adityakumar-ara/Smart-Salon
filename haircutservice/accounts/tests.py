from django.test import TestCase
from django.core import mail
from django.urls import reverse
from .models import CustomUser


class SignupOtpFlowTests(TestCase):
    def test_signup_sends_verification_otp_and_creates_user_after_welcome_otp(self):
        response = self.client.post(
            reverse('signup'),
            {
                'name': 'Alice',
                'username': 'alice',
                'email': 'alice@example.com',
                'mobile': '9876543210',
                'password': 'StrongPass123',
                'confirm_password': 'StrongPass123',
                'role': 'customer',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter the email verification OTP')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('verification OTP', mail.outbox[0].subject)

        otp_body = mail.outbox[0].body
        verification_otp = otp_body.split('OTP: ')[1].split('\n')[0]

        response = self.client.post(
            reverse('verify_otp'),
            {'otp': verification_otp},
            follow=True,
        )

        self.assertContains(response, 'Welcome OTP')
        self.assertEqual(len(mail.outbox), 2)

        welcome_body = mail.outbox[1].body
        welcome_otp = welcome_body.split('OTP: ')[1].split('\n')[0]

        response = self.client.post(
            reverse('verify_otp'),
            {'otp': welcome_otp},
            follow=True,
        )

        self.assertRedirects(response, reverse('home'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, 'alice')


class PasswordResetOtpFlowTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='reset-user', email='reset@example.com', password='OldPassword123',
            name='Reset User', mobile='9876543210',
        )

    def test_user_can_reset_password_after_verifying_email_otp(self):
        response = self.client.post(reverse('forgot_password'), {'email': self.user.email})
        self.assertRedirects(response, reverse('verify_password_reset_otp'))
        self.assertEqual(len(mail.outbox), 1)

        otp = mail.outbox[0].body.split('OTP is: ')[1].split('\n')[0]
        response = self.client.post(reverse('verify_password_reset_otp'), {'otp': otp})
        self.assertRedirects(response, reverse('reset_password_confirm'))

        response = self.client.post(reverse('reset_password_confirm'), {
            'password': 'NewPassword123', 'confirm_password': 'NewPassword123',
        })
        self.assertRedirects(response, reverse('login'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword123'))

    def test_unregistered_email_does_not_send_otp(self):
        response = self.client.post(reverse('forgot_password'), {'email': 'missing@example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No account is registered with this email address.')
        self.assertEqual(len(mail.outbox), 0)
