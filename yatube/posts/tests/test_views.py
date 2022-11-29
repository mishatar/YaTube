from django import forms
from django.test import Client, TestCase
from django.core.cache import cache
from django.urls import reverse

from ..models import Group, Post, User, Follow, Comment
from ..forms import PostForm


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='bilbo')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        self.client = Client()
        self.auth = Client()
        self.auth.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            (
                reverse('posts:group_list', kwargs={'slug': 'slug_slug'})
            ): 'posts/group_list.html',
            (
                reverse('posts:profile',
                        kwargs={'username': self.user.username})
            ): 'posts/profile.html',
            (
                reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
            ): 'posts/post_detail.html',
            (
                reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=reverse_name):
                response = self.auth.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.auth.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        group_title_0 = first_object.group.title
        post_text_0 = first_object.text
        group_slug_0 = first_object.group.slug
        self.assertEqual(group_title_0, self.group.title)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(group_slug_0, self.group.slug)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.auth.get(reverse(
            'posts:group_list', kwargs={'slug': 'slug_slug'}))
        first_object = response.context['page_obj'][0]
        post_group_0 = first_object.group.title
        self.assertEqual(post_group_0, PostViewsTests.group.title)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.auth.get(reverse(
            'posts:profile', kwargs={'username': 'bilbo'}))
        first_object = response.context['page_obj'][0]
        post_group_0 = first_object.author
        self.assertEqual(post_group_0, PostViewsTests.post.author)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.auth.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}))
        first_object = response.context['post']
        self.assertEqual(first_object.pk, PostViewsTests.post.pk)

    def test_edit_post_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом"""
        response = self.auth.get(reverse('posts:post_edit',
                                         kwargs={'post_id': self.post.pk})
                                 )
        first_object = response.context['form']
        self.assertIsInstance(first_object, PostForm)

    def test_create_post_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.auth.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='bilbo')
        cls.group1 = Group.objects.create(
            title='Тестовая группа',
            slug='slug_slug',
            description='Тестовое описание',
        )
        posts_list = []
        for i in range(13):
            posts_list.append(Post(
                author=cls.user,
                text=f'Текстовый пост {i}',
                group=cls.group1,
                pk=i
            ))
        cls.post = Post.objects.bulk_create(posts_list)

    def setUp(self):
        self.client = Client()
        self.auth = Client()
        self.auth.force_login(self.user)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_group_list_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': 'slug_slug'}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_first_page_profile_contains_ten_records(self):
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': 'bilbo'}))
        self.assertEqual(len(response.context['page_obj']), 10)


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='test_name',
                                            email='test@mail.ru',
                                            password='test_pass',),
            text='Тестовая запись для создания поста')

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='mob2556')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_cache_index(self):
        """Тест кэширования страницы index.html"""
        first_state = self.authorized_client.get(reverse('posts:index'))
        post_1 = Post.objects.get(pk=1)
        post_1.text = 'Измененный текст'
        post_1.save()
        second_state = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first_state.content, second_state.content)
        cache.clear()
        third_state = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first_state.content, third_state.content)


class FollowTests(TestCase):
    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create_user(username='follower',
                                                      email='test_11@mail.ru',
                                                      password='test_pass')
        self.user_following = User.objects.create_user(username='following',
                                                       email='test22@mail.ru',
                                                       password='test_pass')
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовая запись для тестирования ленты'
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_follow(self):
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.client_auth_follower.get(reverse('posts:profile_unfollow',
                                      kwargs={'username':
                                              self.user_following.username}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription_feed(self):
        """запись появляется в ленте подписчиков"""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_follower.get('/follow/')
        post_text_0 = response.context["page_obj"][0].text
        self.assertEqual(post_text_0, 'Тестовая запись для тестирования ленты')
        # в качестве неподписанного пользователя проверяем собственную ленту
        response = self.client_auth_following.get('/follow/')
        self.assertNotContains(response,
                               'Тестовая запись для тестирования ленты')

    def test_authorized_comment_add(self):
        """Тест добавления комментария авториз. пользователем."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий 2'
        }
        self.client_auth_follower.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
