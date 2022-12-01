from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        label = {'text': 'Текст записи', 'group': 'Группа'}
        help_text = {'text': 'Введите текст записи',
                     'group': 'Выберите группу'
                     }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        label = {'text': 'Текст', }
        help_text = {'text': 'Текст комментария', }
