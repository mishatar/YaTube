from django.test import TestCase

from . import const
from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_group = Group.objects.create(
            title=const.GROUP_TITLE,
            slug=const.GROUP_SLUG,
            description=const.GROUP_DESCRIPTION,
        )
        cls.post_author = User.objects.create_user(username=const.POST_AUTHOR)
        cls.post = Post.objects.create(
            text=const.POST_TEXT,
            author=cls.post_author,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        group = PostModelTest.test_group
        object_names = {
            post: const.POST_TEXT[:15],
            group: const.GROUP_TITLE,
        }
        for value, expected in object_names.items():
            with self.subTest(value=value):
                self.assertEqual(str(value), expected)

    def test_post_model_fields_verbose_names(self):
        """Проверяем соответствие verbose_name в модели Post."""
        post = PostModelTest.post
        field_verboses = {
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_post_models_fields_help_text(self):
        """Проверяем соответствие help_text в моделях."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)
