from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

        def setUp(self):
            self.authorized_author_client = Client()
            self.authorized_author_client.force_login(self.user)

        def test_create_post(self):
            posts_count = Post.objects.count()

            form_data = {
                'text': 'Тестовый текст',
                'group': self.group
            }

            response = self.authorized_author_client.post(
                reverse('posts:post_create'),
                data=form_data,
                follow=True
            )
            self.assertRedirects(
                response, reverse(
                    'posts:profile', kwargs={'username': self.user.username}
                )
            )
            self.assertEqual(Post.objects.count(), posts_count + 1)

        def test_edit_post(self):
            form_data = {
                'text': 'Измененный текст',
                'group': self.group
            }
            response = self.authorized_author_client.post(
                reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
                data=form_data,
                follow=True
            )
            self.assertRedirects(
                response, reverse(
                    'posts:post_detail', kwargs={'post_id': self.post.id}
                )
            )
            self.assertEqual(response.context['post'].text, form_data['text'])

        def test_post_with_picture(self):
            count_posts = Post.objects.count()
            small_gif = (
                b'\x47\x49\x46\x38\x39\x61\x02\x00'
                b'\x01\x00\x80\x00\x00\x00\x00\x00'
                b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                b'\x0A\x00\x3B'
            )
            uploaded = SimpleUploadedFile(
                name='small.gif',
                content=small_gif,
                content_type='image/gif'
            )
            form_data = {
                'text': 'Пост с картинкой',
                'group': self.group.id,
                'image': uploaded
            }
            response = self.authorized_client.post(
                reverse('posts:create_post'),
                data=form_data,
                follow=True,
            )
            post_1 = Post.objects.get(id=self.group.id)
            author_1 = User.objects.get(username='mob2556')
            group_1 = Group.objects.get(title='Заголовок для тестовой группы')
            self.assertEqual(Post.objects.count(), count_posts + 1)
            self.assertRedirects(response, reverse('posts:index'))
            self.assertEqual(post_1.text, 'Пост с картинкой')
            self.assertEqual(author_1.username, 'mob2556')
            self.assertEqual(group_1.title, 'Заголовок для тестовой группы')
