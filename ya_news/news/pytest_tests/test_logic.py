from http import HTTPStatus

import pytest

from news.forms import BAD_WORDS, WARNING
from news.models import Comment

pytestmark = pytest.mark.django_db


class TestLogic:
    def test_anonymous_cannot_send_comment(self, client, news_detail_url):
        """
        Анонимный пользователь не может отправить комментарий —
        количество не изменилось.
        """
        initial_count = Comment.objects.count()
        data = {"text": "Тестовый комментарий"}
        response = client.post(news_detail_url, data)
        assert response.status_code == HTTPStatus.FOUND
        assert Comment.objects.count() == initial_count

    def test_authenticated_user_can_send_comment(
        self, user_client, user, news, news_detail_url
    ):
        """Авторизованный пользователь может отправить комментарий."""
        Comment.objects.all().delete()
        initial_count = Comment.objects.count()
        data = {"text": "Тестовый комментарий"}
        response = user_client.post(news_detail_url, data)
        assert response.status_code == HTTPStatus.FOUND
        assert Comment.objects.count() == initial_count + 1

        comment = Comment.objects.get()
        assert comment.text == data["text"]
        assert comment.author == user
        assert comment.news == news

    @pytest.mark.parametrize("bad_word", BAD_WORDS)
    def test_comment_with_bad_words_rejected(
        self, user_client, news_detail_url, bad_word
    ):
        """
        Комментарии с плохими словами отклоняются:
        форма возвращает ошибку в поле 'text'.
        """
        initial_count = Comment.objects.count()
        data = {"text": f"Это {bad_word} слово"}
        response = user_client.post(news_detail_url, data)

        # Форма с ошибкой возвращает 200 OK, а не перенаправление
        assert response.status_code == HTTPStatus.OK
        # Проверяем, что комментарий не создался
        assert Comment.objects.count() == initial_count
        # Проверяем, что в контексте есть форма
        assert "form" in response.context
        form = response.context["form"]
        # Проверяем, что форма содержит ошибки
        assert form.errors
        # Проверяем, что ошибка в поле text
        assert "text" in form.errors
        # Проверяем, что ошибка содержит предупреждение
        text_errors = form.errors["text"]
        assert any(WARNING in str(error) for error in text_errors)

    def test_user_can_edit_own_comments(self, author_client, comment,
                                        comment_edit_url):
        """Авторизованный пользователь может редактировать свои комментарии."""
        edit_data = {"text": "Обновленный комментарий"}
        response = author_client.post(comment_edit_url, edit_data)
        assert response.status_code == HTTPStatus.FOUND

        updated = Comment.objects.get(pk=comment.id)
        assert updated.text == edit_data["text"]
        assert updated.author == comment.author
        assert updated.news == comment.news

    def test_user_can_delete_own_comment(
        self, author_client, comment, comment_delete_url
    ):
        """Авторизованный пользователь может удалять свой комментарий."""
        comment_id = comment.id
        response = author_client.post(comment_delete_url)
        assert response.status_code == HTTPStatus.FOUND
        assert not Comment.objects.filter(pk=comment_id).exists()

    def test_user_cannot_edit_other_comments(
        self, user_client, another_comment, another_comment_edit_url
    ):
        """Пользователь не может редактировать чужие комментарии."""
        edit_data = {"text": "Взломанный комментарий"}
        response = user_client.post(another_comment_edit_url, edit_data)
        assert response.status_code == HTTPStatus.NOT_FOUND

        # Проверяем, что комментарий не изменился
        persisted = Comment.objects.get(pk=another_comment.id)
        assert persisted.text == another_comment.text
        assert persisted.author == another_comment.author
        assert persisted.news == another_comment.news

    def test_user_cannot_delete_other_comments(
        self, user_client, another_comment, another_comment_delete_url
    ):
        """Пользователь не может удалять чужие комментарии."""
        response = user_client.post(another_comment_delete_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert Comment.objects.filter(pk=another_comment.id).exists()
