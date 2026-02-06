from http import HTTPStatus

import pytest
from news.forms import BAD_WORDS
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
        data = {"text": "Тестовый комментарий"}
        response = user_client.post(news_detail_url, data)
        assert response.status_code == HTTPStatus.FOUND
        assert Comment.objects.count() == 1

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

        # Используем assertFormError правильно
        assert response.status_code == HTTPStatus.OK
        # Проверяем, что форма содержит ошибку
        assert "form" in response.context
        # Проверяем ошибку в поле text
        assert "text" in response.context["form"].errors
        # Проверяем, что комментарий не создался
        assert Comment.objects.count() == initial_count

    def test_user_can_edit_delete_own_comments(
        self, author_client, author, news, comment, comment_edit_url, comment_delete_url
    ):
        """
        Авторизованный пользователь может редактировать
        и удалять свои комментарии.
        """
        # Тест редактирования
        edit_data = {"text": "Обновленный комментарий"}
        response = author_client.post(comment_edit_url, edit_data)
        assert response.status_code == HTTPStatus.FOUND

        updated = Comment.objects.get(pk=comment.id)
        assert updated.text == edit_data["text"]
        assert updated.author == author
        assert updated.news == news

        # Тест удаления
        response = author_client.post(comment_delete_url)
        assert response.status_code == HTTPStatus.FOUND
        assert not Comment.objects.filter(pk=comment.id).exists()

    def test_user_cannot_edit_delete_other_comments(
        self, user_client, author, news, comment, comment_edit_url, comment_delete_url
    ):
        """Пользователь не может редактировать/удалять чужие комментарии."""
        # Тест редактирования чужого комментария
        edit_data = {"text": "Взломанный комментарий"}
        response = user_client.post(comment_edit_url, edit_data)
        assert response.status_code == HTTPStatus.NOT_FOUND

        # Проверяем, что комментарий не изменился
        persisted = Comment.objects.get(pk=comment.id)
        assert persisted.text == comment.text
        assert persisted.author == author
        assert persisted.news == news

        # Тест удаления чужого комментария
        response = user_client.post(comment_delete_url)
        assert response.status_code == HTTPStatus.NOT_FOUND

        # Проверяем, что комментарий не удалился
        assert Comment.objects.filter(pk=comment.id).exists()
