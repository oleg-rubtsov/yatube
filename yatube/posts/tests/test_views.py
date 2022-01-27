from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
import datetime as dt
from posts.models import Group, Post, Follow
import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
import os
from http import HTTPStatus
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key

User = get_user_model()


class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.list_dir = os.listdir(os.getcwd())
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
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.group = Group.objects.create(title='Жора',
                                         slug='Jora',
                                         description='Группа для всех Жор')

        cls.group2 = Group.objects.create(title='Жора2',
                                          slug='Jora2',
                                          description='Группа для всех Жор2')

        cls.user = User.objects.create_user(username='Oleg3')

        cls.test_post = Post.objects.create(
            text='Хорошая жизнь',
            author=cls.user,
            group=cls.group,
            image=test_image,
        )

        cls.templates_pages_names = {
            'index.html': reverse('index'),
            'group.html': reverse('group_posts', kwargs={'slug': 'Jora'}),
            'new.html': reverse('new_post'),
            'about/tech.html': reverse('about:tech'),
            'about/author.html': reverse('about:author'),
        }

        cls.available_for_guest = {
            reverse('about:author'): HTTPStatus.OK,
            reverse('about:tech'): HTTPStatus.OK,
        }

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='Oleg3')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        for path in os.listdir(os.getcwd()):
            if path not in cls.list_dir:
                shutil.rmtree(path, ignore_errors=True)
        super().tearDownClass()

    def test_views_correct_template(self):
        """Тест для проверки какой шаблон будет вызван при обращении
        к view-классам через соответствующий name
        """
        for template, reverse_name in ViewsTests.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_about_correct_status_code(self):
        """Тест для проверки что страницы tech/ и author/
        достпны неавторизованному пользователю
        """
        for reverse_name, code in ViewsTests.available_for_guest.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, code)

    def test_index_correct_context(self):
        """Тест для проверки контекста передаваемого
        в шаблон главной страницы
        """
        response = self.authorized_client.get(reverse('index'))
        first_object = response.context['page'][0]
        task_text_0 = first_object.text
        task_pub_date_0 = first_object.pub_date.replace(second=0,
                                                        microsecond=0)
        task_author_0 = first_object.author.username
        task_image_0 = first_object.image.name
        time = dt.datetime.today().replace(second=0, microsecond=0)
        #__import__('pdb').set_trace()
        self.assertEqual(task_image_0, 'posts/small.gif')
        self.assertEqual(task_text_0, 'Хорошая жизнь')
        self.assertEqual(task_pub_date_0, time)
        self.assertEqual(task_author_0, 'Oleg3')

    def test_group_correct_context(self):
        """Тест для проверки контекста передаваемого
        в шаблон страницы группы
        """
        response = self.authorized_client.get(reverse('group_posts',
                                                      kwargs={'slug': 'Jora'}))
        first_object = response.context['page'][0]
        task_text_0 = first_object.text
        task_pub_date_0 = first_object.pub_date.replace(second=0,
                                                        microsecond=0)
        task_author_0 = first_object.author.username
        time = dt.datetime.today().replace(second=0, microsecond=0)
        group = response.context['group'].title
        task_image_0 = first_object.image.name
        self.assertEqual(task_image_0, 'posts/small.gif')
        self.assertEqual(group, 'Жора')
        self.assertEqual(task_text_0, 'Хорошая жизнь')
        self.assertEqual(task_pub_date_0, time)
        self.assertEqual(task_author_0, 'Oleg3')

    def test_new_post_correct_context(self):
        """Тест для проверки контекста передаваемого
        в шаблон страницы создания нового поста
        """
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_edit_post_correct_context(self):
        """Тест для проверки контекста передаваемого
        в шаблон страницы редактирования поста
        """
        response = self.authorized_client.get(
            reverse('post_edit',
                    kwargs={'username': ViewsTests.test_post.author.username,
                            'post_id': ViewsTests.test_post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_correct_context(self):
        """Тест для проверки контекста передаваемого
        в шаблон страницы профайла пользователя
        """
        response = self.authorized_client.get(reverse(
            'profile',
            kwargs={'username': ViewsTests.test_post.author.username}))
        first_object = response.context['page'][0]
        task_text_0 = first_object.text
        task_pub_date_0 = first_object.pub_date.replace(second=0,
                                                        microsecond=0)
        task_author_0 = first_object.author.username
        time = dt.datetime.today().replace(second=0, microsecond=0)
        task_image_0 = first_object.image.name
        self.assertEqual(task_image_0, 'posts/small.gif')
        self.assertEqual(response.context['profile'].username, 'Oleg3')
        self.assertEqual(response.context['count'], 1)
        self.assertEqual(task_text_0, 'Хорошая жизнь')
        self.assertEqual(task_pub_date_0, time)
        self.assertEqual(task_author_0, 'Oleg3')

    def test_post_view_correct_context(self):
        """Тест для проверки контекста передаваемого
        в шаблон страницы отдельного поста
        """
        response = self.authorized_client.get(reverse(
            'post',
            kwargs={'username': ViewsTests.test_post.author.username,
                    'post_id': ViewsTests.test_post.id}))
        first_object = response.context['post']
        task_text_0 = first_object.text
        task_pub_date_0 = first_object.pub_date.replace(second=0,
                                                        microsecond=0)
        task_author_0 = first_object.author.username
        time = dt.datetime.today().replace(second=0, microsecond=0)
        task_image_0 = first_object.image.name
        self.assertEqual(task_image_0, 'posts/small.gif')
        self.assertEqual(response.context['count'], 1)
        self.assertEqual(task_text_0, 'Хорошая жизнь')
        self.assertEqual(task_pub_date_0, time)
        self.assertEqual(task_author_0, 'Oleg3')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Oleg')
        cls.group = Group.objects.create(
            title='Жора', description='Группа для всех Жор', slug='Jora'
        )
        cls.post = Post.objects.create(
            text='Хорошая жизнь', author=cls.user, group=cls.group
        )
        for step in range(12):
            Post.objects.create(
                text=f'Хорошая жизнь {step}', author=cls.user,
                group=cls.group
            )
        cls.authorized_client = Client()

    def test_first_page_containse_ten_records(self):
        """Тест для проверки паджинатора"""
        response = self.client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_containse_three_records(self):
        """Тест для проверки паджинатора"""
        response = self.client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)


class ViewsAdditionalTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(title='Жора',
                                         slug='Jora',
                                         description='Группа для всех Жор')

        cls.group2 = Group.objects.create(title='Жора2',
                                          slug='Jora2',
                                          description='Группа для всех Жор2')

        cls.user = User.objects.create_user(username='Oleg3')

        cls.test_post = Post.objects.create(
            text='Хорошая жизнь',
            author=cls.user,
            group=cls.group,
        )

        cls.test_post2 = Post.objects.create(
            text='Хорошая жизнь2',
            author=cls.user,
            group=cls.group2,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='Oleg3')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_new_post_group_correct_context(self):
        """Тест для проверки что пост не попадает в группу,
        для которой не был предназначен
        """
        response = self.authorized_client.get(reverse('group_posts',
                                                      kwargs={'slug':
                                                              'Jora2'}))
        first_object = response.context['page'][0]
        task_text_0 = first_object.group.title
        self.assertNotEqual(task_text_0, 'Жора')

    def test_cache(self):
        self.authorized_client.get(reverse('index'))
        key = make_template_fragment_key('index_page')
        result = cache.get(key)
        self.assertNotEqual(result, None)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='Oleg1')
        cls.user2 = User.objects.create_user(username='Oleg2')
        cls.user3 = User.objects.create_user(username='Oleg3')
        cls.test_post = Post.objects.create(
            text='Хорошая жизнь',
            author=cls.user2,
        )
        cls.comment = 'Тестовый коммент'

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='Oleg1')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_authorized_can_follow(self):
        """Тест для проверки, что авторизованный пользователь может
        подписываться на других пользователей
        """
        person = User.objects.create_user(username='Alex')
        response = self.authorized_client.get(
            reverse('profile_follow', kwargs={'username': person}))
        count = Follow.objects.count()
        follow = Follow.objects.first()
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(count, 1)
        self.assertEqual(follow.user.username, 'Oleg1')
        self.assertEqual(follow.author.username, 'Alex')

    def test_authorized_can_unfollow(self):
        """Тест для проверки, что авторизованный пользователь может
        удалять других пользователей из подписок
        """
        person = User.objects.create_user(username='Alex2')
        Follow.objects.create(user=FollowTests.user1, author=person)
        count1 = Follow.objects.count()
        response = self.authorized_client.get(reverse('profile_unfollow',
                                                      kwargs={'username':
                                                              person}))
        count2 = Follow.objects.count()
        self.assertNotEqual(count1, count2)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_anonymous_cannot_comment(self):
        """Тест для проверки что, анонимный пользователь
        не может оставить комментарий
        """
        response = self.guest_client.post(
            reverse('add_comment',
                    kwargs={'username': FollowTests.user2.username,
                            'post_id': FollowTests.test_post.pk}),
            {'text': FollowTests.comment}, follow=True)
        self.assertNotContains(response, FollowTests.comment)

    def test_new_post_appears_subscriber(self):
        """Тест для проверки что новая запись пользователя
        появляется в ленте тех, кто на него подписан
        """
        self.authorized_client.get(
            reverse('profile_follow', kwargs={'username': FollowTests.user2}))
        response = self.authorized_client.get(reverse('follow_index'))
        first_object = response.context['page'][0]
        task_text_0 = first_object.text
        task_author_0 = first_object.author.username
        # __import__('pdb').set_trace()
        self.assertEqual(task_text_0, 'Хорошая жизнь')
        self.assertEqual(task_author_0, 'Oleg2')

    def test_new_post_appears_subscriber(self):
        """Тест для проверки что новая запись пользователя
        не появляется в ленте тех, кто на него не подписан
        """
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertEqual(response.context.get('page').object_list.count(), 0)
