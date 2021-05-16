from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="posts")
    group = models.ForeignKey('Group', on_delete=models.SET_NULL,
                              related_name="posts", blank=True, null=True)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ['-pub_date']


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, unique=True, db_index=True,
                            verbose_name="URL", blank=True, null=True)
    description = models.TextField('Описание', max_length=200,
                                   blank=True, null=True)

    def __str__(self):
        return self.title

    def get_absolut_url(self):
        return reverse("post", kwargs={"post_slug": self.slug})


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="comments")
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.post

    class Meta:
        ordering = ['-created']


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="follower")
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="following")

    def __str__(self):
        return self.user
