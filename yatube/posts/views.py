from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Post, Group, Follow
from .forms import PostForm, CommentForm
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "group.html", {"group": group, 'page': page})


@login_required
def new_post(request):
    form = PostForm(request.POST or None)
    if not form.is_valid():
        return render(request, 'new.html',
                      {'form': form, 'is_edit': False})
    else:
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("index")


def profile(request, username):
    profile = get_object_or_404(User, username=username)
    posts = profile.posts.all()
    # __import__('pdb').set_trace()
    paginator = Paginator(posts, 10)
    count = paginator.count
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user,
        author=profile).exists()
    return render(request,
                  'profile.html',
                  {'profile': profile, "page": page, "count": count,
                   'following': following})


def post_view(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    # count = Post.objects.filter(author__username=username).count()
    author = get_object_or_404(User, username=username)
    count = author.posts.count()
    comments = post.comments.all()
    form = CommentForm()
    # __import__('pdb').set_trace()
    return render(request, 'post.html',
                  {'post': post, 'author': post.author,
                   "count": count, 'form': form, 'comments': comments})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if request.user != post.author:
        return redirect("post", username=username, post_id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect("post", username=username, post_id=post_id)
    return render(request, 'new.html',
                  {'form': PostForm(instance=post),
                   'is_edit': True, 'post': post})


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if not form.is_valid():
        return render(request, 'post.html',
                      {'form': form})
    else:
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('post', username, post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)

    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author and Follow.objects.get(user=request.user,
                                                     author=author):
        Follow.objects.filter(user=request.user, author=author).delete()

    return redirect('profile', username)
