from django.test import TestCase, Client
from posts.models import Group
from django.contrib.auth import get_user_model
import datetime as dt
from posts.models import Group, Post
from http import HTTPStatus

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Жора',
            slug='Jora',
            description='Группа для всех Жор'
        )
        User.objects.create_user(username='Oleg3',
                                 password='SuperOleg',
                                 email='vseVolega@gmail.com')
        Post.objects.create(
            text='Хорошая жизнь',
            pub_date=dt.datetime.today().replace(second=0, microsecond=0),
            author=User.objects.get(username='Oleg3'),
            group=cls.group,
        )
        User.objects.create_user(username='Oleg4',
                                 password='SuperOleg',
                                 email='vseVolega@gmail.com')
        Post.objects.create(
            text='Хорошая жизнь2',
            pub_date=dt.datetime.today().replace(second=0, microsecond=0),
            author=User.objects.get(username='Oleg4'),
            group=cls.group,
        )
        cls.code_urls_anonymous = {
            '/wrqwe/': HTTPStatus.NOT_FOUND,
            '/': HTTPStatus.OK,
            '/new/': HTTPStatus.FOUND,
            '/group/Jora/': HTTPStatus.OK,
            '/Oleg3/': HTTPStatus.OK,
            '/Oleg3/1/': HTTPStatus.OK,
            '/Oleg3/1/edit/': HTTPStatus.FOUND,
            '/Oleg4/2/edit/': HTTPStatus.FOUND,
        }
        cls.code_urls_authorized = {
            '/': HTTPStatus.OK,
            '/group/Jora/': HTTPStatus.OK,
            '/new/': HTTPStatus.OK,
            '/Oleg3/': HTTPStatus.OK,
            '/Oleg3/1/': HTTPStatus.OK,
            '/Oleg3/1/edit/': HTTPStatus.OK,
            '/Oleg4/2/edit/': HTTPStatus.FOUND,
        }
        cls.templates_urls = {
            '/': 'index.html',
            '/group/Jora/': 'group.html',
            '/new/': 'new.html',
            '/Oleg3/1/edit/': 'new.html',
        }
        cls.redirect_urls = {
            '/new/': '/auth/login/?next=/new/',
            '/Oleg3/1/edit/': '/auth/login/?next=/Oleg3/1/edit/',
        }

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='Oleg3')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_all_urls_templates(self):
        """Тест для проверки вызова ожидаемых запросу шаблонов"""
        for adress, template in StaticURLTests.templates_urls.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_all_status_code_guest(self):
        """Тест для проверки доступности страниц
        для анонимного пользователя
        """
        for adress, code in StaticURLTests.code_urls_anonymous.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, code)

    def test_all_status_code_authorized(self):
        """Тест для проверки доступности страниц
        для авторизованного пользователя
        """
        for adress, code in StaticURLTests.code_urls_authorized.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, code)

    def test_redirect_anonymous_on_admin_login(self):
        """Тест проверки что неавторизованного пользователя
        редиректит на правильную страницы
        """
        for adress, redirect in StaticURLTests.redirect_urls.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress, follow=True)
                self.assertRedirects(response, redirect)
