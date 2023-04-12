from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from . import const
from ..models import Group, Post, User

POST_ID = 1


class PostURLTests(TestCase):
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
            group=cls.test_group
        )

        cls.urls_available_for_all = {
            '/': 'posts/index.html',
            f'/group/{cls.test_group.slug}/': 'posts/group_list.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            f'/profile/{cls.post.author}/': 'posts/profile.html',
        }
        cls.urls_available_for_author = {
            f'/posts/{cls.post.id}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
        }
        cls.urls_redirect = {
            f'/posts/{POST_ID}/edit/': '{}?next={}'.format(
                reverse('users:login'),
                reverse('posts:post_edit', kwargs={'post_id': POST_ID})
            ),
            '/create/': '{}?next={}'.format(
                reverse('users:login'),
                reverse('posts:post_create')
            ),
        }

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='mean_tester')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author_client = Client()
        self.post_author_client.force_login(self.post_author)

    def test_urls_available_for_all(self):
        """Проверяем доступность страниц неавторизованному пользователю."""
        for url in self.urls_available_for_all.keys():
            response = self.guest_client.get(url)
            with self.subTest(value=response):
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_urls_redirect_guest_user(self):
        """
        Проверяем редирект неавторизованного пользователя при попытке
        перейти на страницы создания и редактирования постов.
        """
        for url, expected in self.urls_redirect.items():
            response = self.guest_client.get(url)
            with self.subTest(value=response):
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                self.assertRedirects(response, expected)

    def test_private_urls_available_for_author(self):
        """
        Проверяем доступность приватных страниц авторизованному пользователю.
        """
        for url in self.urls_available_for_author.keys():
            response = self.post_author_client.get(url)
            with self.subTest(value=response):
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_public_urls_uses_correct_template(self):
        """Публичные URL-адреса используют соответствующие шаблоны."""
        for url, template in self.urls_available_for_all.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_private_urls_uses_correct_template(self):
        """Приватные URL-адреса используют соответствующие шаблоны."""
        for url, template in self.urls_available_for_author.items():
            with self.subTest(url=url):
                response = self.post_author_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_post_edit_url_redirect(self):
        """Страница /posts/<post_id>/edit/ доступна только автору поста."""
        response = self.authorized_client.get(f'/posts/{POST_ID}/edit/')
        self.assertRedirects(response, f'/posts/{POST_ID}/')

    def test_not_existing_url(self):
        """Ошибка при переходе на несуществующую страницу."""
        response = self.guest_client.get('/not_existing_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_404_page_uses_custom_template(self):
        """Страница 404 использует кастомный шаблон."""
        response = self.guest_client.get('/not_existing_page/')
        template = 'core/404.html'
        self.assertTemplateUsed(response, template)
