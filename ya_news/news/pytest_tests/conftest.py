from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from news.models import Comment, News

pytestmark = pytest.mark.django_db


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
def another_comment(another_user, news):
    return Comment.objects.create(
        news=news, author=another_user, text="Чужой комментарий"
    )


@pytest.fixture
def many_news():
    """Создаёт 10 + 1 новостей для тестов лимита."""
    News.objects.all().delete()
    now = timezone.now()
    count = settings.NEWS_COUNT_ON_HOME_PAGE + 1
    for i in range(count):
        News.objects.create(
            title=f"Новость {i}",
            text=f"Текст новости {i}",
            date=now - timedelta(hours=i),
        )


@pytest.fixture
def many_comments(news, author):
    """Создаёт несколько комментариев."""
    Comment.objects.filter(news=news).delete()
    now = timezone.now()
    for i in range(5):
        comment = Comment.objects.create(
            news=news, author=author, text=f"Комментарий {i}"
        )
        comment.created = now - timedelta(minutes=(5 - i))
        comment.save(update_fields=["created"])


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
def another_comment_edit_url(another_comment):
    """URL для редактирования чужого комментария."""
    return reverse("news:edit", args=(another_comment.id,))


@pytest.fixture
def another_comment_delete_url(another_comment):
    """URL для удаления чужого комментария."""
    return reverse("news:delete", args=(another_comment.id,))


@pytest.fixture
def author_client(author):
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def user_client(user):
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def another_user_client(another_user):
    client = Client()
    client.force_login(another_user)
    return client
