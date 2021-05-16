from django.test import TestCase
from posts.models import Group, Post
from django.contrib.auth import get_user_model

User = get_user_model()


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Жора',
            slug='Jora',
            description='Группа для всех Жор'
        )
        cls.post = Post.objects.create(
            text='Олеги правят миром',
            author=User.objects.create_user(username='Oleg',
                                            password='SuperOleg',
                                            email='vseVolega@gmail.com')
        )

    def test_all_models(self):
        """Тест для проверки правильно ли отображается
        значение поля __str__ в объектах моделей."""
        group = GroupModelTest.group
        post = GroupModelTest.post
        objects = {
            post: post.text[:15],
            group: group.title,
        }
        for obj, expected_field in objects.items():
            with self.subTest(obj=obj):
                self.assertEqual(str(obj), expected_field)
