from posts.models import Post, Comment
from django import forms


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        # , 'image'
        labels = {'group': 'Группа', 'text': 'Текст'}
        help_texts = {'group': 'Выбрать группу', 'text': 'Написать текст'}

    def clean_text(self):
        data = self.cleaned_data['text']

        if data == '':
            raise forms.ValidationError('Необходимо заполнить данное поле')

        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea
        }
