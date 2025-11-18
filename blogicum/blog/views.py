from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Post, Category


def index(request):
    """Главная страница с последними 5 публикациями."""
    post_list = Post.objects.select_related(
        'author',
        'location',
        'category'
    ).filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    ).order_by('-pub_date')[:5]

    context = {'post_list': post_list}
    return render(request, 'blog/index.html', context)


def post_detail(request, id):
    """Страница отдельной публикации."""
    post = get_object_or_404(
        Post.objects.select_related(
            'author',
            'location',
            'category'
        ),
        pk=id
    )

    # Проверка условий публикации
    if (not post.is_published
            or not post.category.is_published
            or post.pub_date > timezone.now()):
        from django.http import Http404
        raise Http404("Публикация не найдена")

    context = {'post': post}
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    """Страница категории со всеми её публикациями."""
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )

    post_list = Post.objects.select_related(
        'author',
        'location',
        'category'
    ).filter(
        category=category,
        is_published=True,
        pub_date__lte=timezone.now()
    ).order_by('-pub_date')

    context = {
        'category': category,
        'post_list': post_list
    }
    return render(request, 'blog/category.html', context)
