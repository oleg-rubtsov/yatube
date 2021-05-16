from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Post, Group
import datetime as dt
import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from http import HTTPStatus

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.group = Group.objects.create(title='Жора',
                                         slug='Jora',
                                         description='Группа для всех Жор')
        cls.test_post = Post.objects.create(
            text='Хорошая жизнь',
            pub_date=dt.datetime.today().replace(second=0, microsecond=0),
            author=User.objects.create_user(username='Oleg3',
                                            password='SuperOleg',
                                            email='vseVolega@gmail.com'),
            group=cls.group,
        )

        # __import__('pdb').set_trace()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='Oleg3')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_authorized_can_publish_post(self):
        """Тест для проверки формы создания нового поста"""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        test_image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст из формы',
            'group': self.group.id,
            'image': test_image
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        post = Post.objects.first()
        # __import__('pdb').set_trace()
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.author.username, 'Oleg3')
        self.assertEqual(post.text, 'Текст из формы')
        self.assertEqual(post.group.title, 'Жора')
        # self.assertTrue(Post.objects.filter(text='Текст из формы', image='posts/small.gif'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_can_edit_post(self):
        """Проверка, что при редактировании поста через форму
        изменяется соответствующая запись в базе данных"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст из формы2',
        }
        response = self.authorized_client.post(
            reverse('post_edit',
                    kwargs={'username':
                            PostFormTests.test_post.author.username,
                            'post_id': PostFormTests.test_post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('post',
                    kwargs={'username':
                            PostFormTests.test_post.author.username,
                            'post_id': PostFormTests.test_post.id}))
        post = Post.objects.first()
        self.assertEqual(Post.objects.count(), posts_count)
        # __import__('pdb').set_trace()
        self.assertEqual(post.text, 'Текст из формы2')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_cannot_publish_post(self):
        """Тест для проверки формы создания нового поста
        анонимный пользователем
        """
        form_data = {
            'text': 'Текст из формы2',
            'group': self.group.id,
        }
        response = self.guest_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        # post = Post.objects.first()
        # __import__('pdb').set_trace()
        self.assertRedirects(response, '/auth/login/?next=/new/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
