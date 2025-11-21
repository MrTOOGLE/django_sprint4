from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.urls import reverse
from django.views.generic import (
    CreateView, UpdateView, DeleteView, ListView, DetailView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, UserEditForm

User = get_user_model()

POSTS_PER_PAGE = 10


def get_published_posts():
    """Возвращает QuerySet опубликованных постов с аннотациями."""
    return Post.objects.select_related(
        'author',
        'location',
        'category'
    ).filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')


class IndexListView(ListView):
    """Главная страница со списком постов."""

    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'page_obj'
    paginate_by = POSTS_PER_PAGE

    def get_queryset(self):
        return get_published_posts()


index = IndexListView.as_view()


class PostDetailView(DetailView):
    """Детальная страница поста."""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'id'

    def get_object(self, queryset=None):
        post = get_object_or_404(
            Post.objects.select_related('author', 'location', 'category'),
            pk=self.kwargs['id']
        )

        # Если пост не опубликован или категория не опубликована
        # или дата публикации в будущем
        if (not post.is_published
                or not post.category.is_published
                or post.pub_date > timezone.now()):
            # Разрешаем просмотр только автору
            if self.request.user != post.author:
                from django.http import Http404
                raise Http404("Публикация не найдена")

        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related('author')
        return context


post_detail = PostDetailView.as_view()


class CategoryPostsListView(ListView):
    """Страница постов категории."""

    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'page_obj'
    paginate_by = POSTS_PER_PAGE

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return get_published_posts().filter(category=self.category)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


category_posts = CategoryPostsListView.as_view()


class ProfileListView(ListView):
    """Страница профиля пользователя."""

    model = Post
    template_name = 'blog/profile.html'
    context_object_name = 'page_obj'
    paginate_by = POSTS_PER_PAGE

    def get_queryset(self):
        self.author = get_object_or_404(
            User,
            username=self.kwargs['username']
        )

        # Если это страница текущего пользователя, показываем все его посты
        if self.request.user == self.author:
            return Post.objects.select_related(
                'author', 'location', 'category'
            ).filter(
                author=self.author
            ).annotate(
                comment_count=Count('comments')
            ).order_by('-pub_date')

        # Для других пользователей показываем только опубликованные
        return get_published_posts().filter(author=self.author)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.author
        return context


profile = ProfileListView.as_view()


class PostCreateView(LoginRequiredMixin, CreateView):
    """Создание нового поста."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


create_post = PostCreateView.as_view()


class PostUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование поста."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', id=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'id': self.object.pk}
        )


edit_post = PostUpdateView.as_view()


class PostDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление поста."""

    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', id=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Переопределяем, чтобы не передавать форму в контекст."""
        context = super().get_context_data(**kwargs)
        context.pop('form', None)
        return context

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


delete_post = PostDeleteView.as_view()


@login_required
def add_comment(request, post_id):
    """Добавление комментария к посту."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', id=post_id)


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование комментария."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return redirect('blog:post_detail', id=comment.post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'id': self.object.post.pk}
        )


edit_comment = CommentUpdateView.as_view()


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление комментария."""

    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return redirect('blog:post_detail', id=comment.post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Переопределяем, чтобы не передавать форму в контекст."""
        context = super().get_context_data(**kwargs)
        context.pop('form', None)
        return context

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'id': self.object.post.pk}
        )


delete_comment = CommentDeleteView.as_view()


class UserEditView(LoginRequiredMixin, UpdateView):
    """Редактирование профиля пользователя."""

    model = User
    form_class = UserEditForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


edit_profile = UserEditView.as_view()
