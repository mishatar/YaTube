import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from . import const
from ..models import Comment, Group, Post, User

POST_ID = 1
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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
            group=cls.test_group,
        )
        cls.comment = Comment.objects.create(
            text='комментарий 1',
            author=cls.post_author,
            post_id=POST_ID,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='mean_tester')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author_client = Client()
        self.post_author_client.force_login(self.post_author)

    def test_post_creation(self):
        """Валидная форма создает запись в базе данных."""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=const.SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестируем форму создания поста',
            'group': self.test_group.id,
            'image': uploaded,
        }
        response = self.post_author_client.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        new_post = Post.objects.get(id=2)
        expected = {
            new_post.text: 'Тестируем форму создания поста',
            new_post.group.id: self.test_group.id,
            new_post.author: self.post_author,
            new_post.image: Post.objects.first().image,
        }
        for field, expected_value in expected.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected_value)
        self.assertRedirects(
            response,
            reverse('posts:profile', args=['post_author'])
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_post_edit(self):
        """
        Отправка валидной формы редактирования изменяет запись в базе данных.
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный текст поста',
        }
        response = self.post_author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': POST_ID}),
            data=form_data,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': POST_ID})
        )
        expected = 'Отредактированный текст поста'
        self.assertEqual(Post.objects.get(id=POST_ID).text, expected)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_guest_user_post_edit(self):
        """
        Отправка формы редактирования неавторизованным пользователем
        не меняет данные в базе.
        """
        form_data = {
            'text': 'Пост отредактирован гостем',
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': POST_ID}),
            data=form_data,
        )
        self.assertRedirects(
            response, '{}?next={}'.format(reverse('users:login'),
                                          reverse('posts:post_edit',
                                                  kwargs={'post_id': POST_ID}))
        )
        expected = 'Пост отредактирован гостем'
        self.assertNotEqual(Post.objects.get(id=POST_ID).text, expected)

    def test_guest_user_comment(self):
        """Неавторизованный пользователь не может оставлять комментарии."""
        form_data = {
            'text': 'Комментарий, оставленный гостем',
        }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': POST_ID}),
            data=form_data,
        )
        expected = 'Комментарий, оставленный гостем'
        self.assertNotEqual(Comment.objects.last().text, expected)

    def test_authorized_client_comment(self):
        """Комментировать посты может только авторизованный пользователь."""
        form_data = {
            'text': 'Комментарий, оставленный авторизованным пользователем.',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': POST_ID}),
            data=form_data,
        )
        expected = 'Комментарий, оставленный авторизованным пользователем.'
        self.assertEqual(Comment.objects.first().text, expected)
