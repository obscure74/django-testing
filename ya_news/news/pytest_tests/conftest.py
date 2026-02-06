from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from news.models import Comment, News

pytestmark = pytest.mark.django_db

# Константа лимита новостей
NEWS_COUNT_ON_HOME_PAGE = getattr(settings, "NEWS_COUNT_ON_HOME_PAGE", 10)


@pytest.fixture
def author():
    return User.objects.create_user(username="author", password="password123")


@pytest.fixture
def reader():
    return User.objects.create_user(username="reader", password="password123")


@pytest.fixture
def user():
    return User.objects.create_user(
        username="testuser", password="password123"
    )


@pytest.fixture
def another_user():
    return User.objects.create_user(
        username="anotheruser", password="password123"
    )


@pytest.fixture
def news():
    return News.objects.create(
        title="Тестовая новость", text="Текст новости"
    )


@pytest.fixture
def comment(author, news):
    return Comment.objects.create(
        news=news, author=author, text="Тестовый комментарий"
    )


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def many_news():
    """Создаёт NEWS_COUNT_ON_HOME_PAGE + 1 новостей для тестов лимита."""
    News.objects.all().delete()
    now = timezone.now()
    count = NEWS_COUNT_ON_HOME_PAGE + 1
    for i in range(count):
        News.objects.create(
            title=f"Новость {i}",
            text=f"Текст новости {i}",
            date=now - timedelta(hours=i),
        )
    return News.objects.all()


@pytest.fixture
def comments_factory(news, author):
    """Фабрика для создания нескольких комментариев."""

    def _create_comments(count=5):
        Comment.objects.filter(news=news).delete()
        created = []
        now = timezone.now()
        for i in range(count):
            c = Comment.objects.create(
                news=news, author=author, text=f"Комментарий {i}"
            )
            c.created = now - timedelta(minutes=(count - i))
            c.save(update_fields=["created"])
            created.append(c)
        return created

    return _create_comments


# Фикстуры для URL-адресов
@pytest.fixture
def home_url():
    return reverse("news:home")


@pytest.fixture
def login_url():
    return reverse("users:login")


@pytest.fixture
def logout_url():
    return reverse("users:logout")


@pytest.fixture
def signup_url():
    return reverse("users:signup")


@pytest.fixture
def news_detail_url(news):
    return reverse("news:detail", args=(news.id,))


@pytest.fixture
def comment_edit_url(comment):
    return reverse("news:edit", args=(comment.id,))


@pytest.fixture
def comment_delete_url(comment):
    return reverse("news:delete", args=(comment.id,))


@pytest.fixture
def author_client(author):
    client = Client()
    client.login(username="author", password="password123")
    return client


@pytest.fixture
def user_client(user):
    client = Client()
    client.login(username="testuser", password="password123")
    return client


@pytest.fixture
def another_user_client(another_user):
    client = Client()
    client.login(username="anotheruser", password="password123")
    return client
