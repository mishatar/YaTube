import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.test import override_settings
from django.urls import reverse

from . import const
from ..models import Follow, Group, Post, User

POSTS_ON_PAGE_1 = 10
POSTS_ON_PAGE_2 = 3
POSTS_TOTAL = 13
LAST_POST_ID = 13
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_group = Group.objects.create(
            title=const.GROUP_TITLE,
            slug=const.GROUP_SLUG,
            description=const.GROUP_DESCRIPTION,
        )
        cls.test_group_2 = Group.objects.create(
            title=const.GROUP_TITLE_2,
            slug=const.GROUP_SLUG_2,
            description=const.GROUP_DESCRIPTION_2,
        )
        cls.post_author = User.objects.create_user(username=const.POST_AUTHOR)
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=const.SMALL_GIF,
            content_type='image/gif'
        )
        posts_list = []
        for i in range(POSTS_TOTAL):
            posts_list.append(Post(
                text=f'Тестовый текст {i + 1} поста',
                author=cls.post_author,
                group=cls.test_group,
                image=uploaded,
            ))
        Post.objects.bulk_create(posts_list)
        cls.url_use_template = (
            ('posts/index.html', 'posts:index', None),
            ('posts/group_list.html', 'posts:group_posts', ('test_slug',)),
            ('posts/profile.html', 'posts:profile', ('post_author',)),
            ('posts/post_detail.html', 'posts:post_detail', (1,)),
            ('posts/post_create.html', 'posts:post_create', None),
            ('posts/post_create.html', 'posts:post_edit', (1,))
        )
        cls.urls = (
            ('posts:index', None),
            ('posts:group_posts', ('test_slug',)),
            ('posts:profile', ('post_author',))
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.post = Post.objects.get(id=LAST_POST_ID)
        self.guest_client = Client()
        self.user = User.objects.create_user(username='mean_tester')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author_client = Client()
        self.post_author_client.force_login(self.post_author)
        cache.clear()

    def test_view_function_uses_correct_template(self):
        """VIEW-функция использует соответствующий шаблон."""
        for template, name, args in self.url_use_template:
            with self.subTest(name=name):
                response = self.post_author_client.get(
                    reverse(name, args=args))
                self.assertTemplateUsed(response, template)

    def test_context_passed_to_template(self):
        """
        Проверяем корректность контекста, передаваемого в шаблоны
        index.html, post_list.html, profile.html.
        """
        for name, args in self.urls:
            page = self.guest_client.get(reverse(name, args=args))
            self.assertEqual(page.context['page_obj'][0], self.post)
            first_post = page.context['page_obj'][0]
            first_post_content = {
                first_post.text: f'Тестовый текст {LAST_POST_ID} поста',
                first_post.author: self.post_author,
                first_post.group: self.test_group,
                first_post.image.size: Post.objects.last().image.size,
            }
            for field, value in first_post_content.items():
                with self.subTest(field=field):
                    self.assertEqual(field, value)

    def test_paginator(self):
        """
        Проверяем пагинатор в шаблонах index.html, post_list.html,
        profile.html.
        """
        for name, args in self.urls:
            page_1 = self.guest_client.get(reverse(name, args=args))
            page_2 = self.guest_client.get(
                f'{reverse(name, args=args)}?page=2')
        self.assertEqual(
            page_1.context['page_obj'].paginator.page('1').object_list.count(),
            POSTS_ON_PAGE_1
        )
        self.assertEqual(
            page_2.context['page_obj'].paginator.page('2').object_list.count(),
            POSTS_ON_PAGE_2
        )

    def test_context_passed_to_post_detail_template(self):
        """
        Проверяем корректность контекста, передаваемого в шаблон
        post_detail.html.
        """
        post = Post.objects.get(id=LAST_POST_ID)
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': LAST_POST_ID})
        )
        self.assertEqual(response.context['post'], post)
        self.assertEqual(response.context['post'].image, post.image)

    def test_form_passed_to_post_create_template(self):
        """
        Проверяем корректность форм при создании и редактировании поста.
        """
        name_list = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': 1}),
        ]
        for name in name_list:
            response = self.post_author_client.get(name)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)

    def test_post_appears_on_correct_page(self):
        """Пост отображается на нужных страницах."""
        page_list = [
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': 'test_slug'}),
            reverse('posts:profile', kwargs={'username': 'post_author'})
        ]
        post = Post.objects.get(id=LAST_POST_ID)
        for page in page_list:
            response = self.guest_client.get(page)
            object_list = response.context.get('page_obj')
            self.assertIn(post, object_list)

    def test_post_does_not_appear_on_wrong_page(self):
        """
        Пост не отображается на странице группы, к которой не отностится.
        """
        response = self.guest_client.get(
            reverse('posts:group_posts', kwargs={'slug': 'test_slug_2'}))
        post = Post.objects.get(id=LAST_POST_ID)
        object_list = response.context.get('page_obj')
        self.assertNotIn(post, object_list)

    def test_comment_appears_on_post_detail_page(self):
        """Комментарий появляется на странице поста."""
        form_data = {
            'text': 'Комментарий к посту.',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': LAST_POST_ID}),
            data=form_data,
        )
        expected = 'Комментарий к посту.'
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': LAST_POST_ID})
        )
        self.assertEqual(response.context['comments'][0].text, expected)

    def test_index_page_cache(self):
        """Удаленный пост сохраняется в кеше главной страницы."""
        post = Post.objects.create(
            text='Тестируем кеш',
            author=self.post_author,
            group=self.test_group
        )
        page_content = self.guest_client.get(reverse('posts:index')).content
        post.delete()
        cached_content = self.guest_client.get(reverse('posts:index')).content
        self.assertEqual(page_content, cached_content)
        cache.clear()
        cleared_cache = self.guest_client.get(reverse('posts:index')).content
        self.assertNotEqual(cached_content, cleared_cache)

    def test_authorised_user_subscribe(self):
        """
        Авторизованный пользователь может подписываться на других
        пользователей.
        """
        self.authorized_client.get(
            reverse('posts:profile_follow', args=[const.POST_AUTHOR])
        )
        self.assertTrue(
            Follow.objects.filter(user=self.user,
                                  author=self.post_author).exists()
        )

    def test_authorised_user_subscribe(self):
        """
        Авторизованный пользователь может удалять пользователей из подписок.
        """
        self.authorized_client.get(
            reverse('posts:profile_follow', args=[const.POST_AUTHOR])
        )
        self.authorized_client.get(
            reverse('posts:profile_unfollow', args=[const.POST_AUTHOR])
        )
        self.assertFalse(
            Follow.objects.filter(user=self.user,
                                  author=self.post_author).exists()
        )

    def test_new_post_appears_on_subscriber_page(self):
        """Новая запись пользователя появляется только в ленте подписчиков."""
        self.subscribed_user = User.objects.create_user(username='subscriber')
        self.subscribed_client = Client()
        self.subscribed_client.force_login(self.subscribed_user)
        self.subscribed_client.get(
            reverse('posts:profile_follow', args=[const.POST_AUTHOR])
        )
        post = Post.objects.create(
            text='Тестируем систему подписок',
            author=self.post_author,
            group=self.test_group
        )
        response = self.subscribed_client.get(reverse('posts:follow_index'))
        object_list = response.context.get('page_obj')
        self.assertIn(post, object_list)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        object_list = response.context.get('page_obj')
        self.assertNotIn(post, object_list)
