from django.shortcuts import render
from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy
from blog.forms import CustomUserCreationForm


class AboutView(TemplateView):
    """Страница О проекте."""

    template_name = 'pages/about.html'


about = AboutView.as_view()


class RulesView(TemplateView):
    """Страница Наши правила."""

    template_name = 'pages/rules.html'


rules = RulesView.as_view()


class UserRegistrationView(CreateView):
    """Регистрация нового пользователя."""

    form_class = CustomUserCreationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('blog:index')


registration = UserRegistrationView.as_view()


def page_not_found(request, exception):
    """Обработчик ошибки 404."""
    return render(request, 'pages/404.html', status=404)


def server_error(request):
    """Обработчик ошибки 500."""
    return render(request, 'pages/500.html', status=500)


def csrf_failure(request, reason=''):
    """Обработчик ошибки 403 CSRF."""
    return render(request, 'pages/403csrf.html', status=403)
