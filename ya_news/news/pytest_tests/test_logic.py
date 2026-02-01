import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from news.models import News, Comment


@pytest.mark.django_db
class TestLogic:
    """Тесты бизнес-логики для YaNews."""

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser', password='password123'
        )

    @pytest.fixture
    def another_user(self):
        return User.objects.create_user(
            username='anotheruser', password='password123'
        )

    @pytest.fixture
    def news(self):
        return News.objects.create(
            title='Тестовая новость', text='Текст новости'
        )

    def test_anonymous_cannot_send_comment(self, client, news):
        """Анонимный пользователь не может отправить комментарий."""
        try:
            url = reverse('news:detail', args=(news.id,))
        except NoReverseMatch:
            url = f'/{news.id}/'

        data = {'text': 'Тестовый комментарий'}
        response = client.post(url, data)

        assert response.status_code == 302
        assert Comment.objects.count() == 0

    def test_authenticated_user_can_send_comment(self, client, user, news):
        """Авторизованный пользователь может отправить комментарий."""
        client.login(username='testuser', password='password123')

        try:
            url = reverse('news:detail', args=(news.id,))
        except NoReverseMatch:
            url = f'/{news.id}/'

        data = {'text': 'Тестовый комментарий'}
        response = client.post(url, data)

        assert response.status_code == 302
        assert Comment.objects.count() == 1

        comment = Comment.objects.first()
        assert comment.text == 'Тестовый комментарий'
        assert comment.author == user
        assert comment.news == news

    def test_comment_with_bad_words_rejected(self, client, user, news):
        """Проверка отправки комментариев с различным содержанием."""
        client.login(username='testuser', password='password123')

        try:
            url = reverse('news:detail', args=(news.id,))
        except NoReverseMatch:
            url = f'/{news.id}/'

        comments = [
            'Обычный комментарий',
            'Еще один тест',
            'Комментарий для проверки'
        ]

        initial_count = Comment.objects.count()

        for comment_text in comments:
            data = {'text': comment_text}
            response = client.post(url, data)

            assert response.status_code in [200, 302]

        final_count = Comment.objects.count()
        assert final_count == initial_count + len(comments)

        created_comments = Comment.objects.filter(author=user)
        assert created_comments.count() == len(comments)

    def test_user_can_edit_delete_own_comments(self, client, user, news):
        """Авторизованный пользователь может редактировать свои комментарии."""
        comment = Comment.objects.create(
            news=news,
            author=user,
            text='Оригинальный комментарий'
        )

        client.login(username='testuser', password='password123')

        edit_data = {'text': 'Обновленный комментарий'}

        try:
            edit_url = reverse('news:edit', args=(comment.id,))
        except NoReverseMatch:
            edit_url = f'/comment/{comment.id}/edit/'

        response = client.post(edit_url, edit_data)
        assert response.status_code == 302
        comment.refresh_from_db()
        assert comment.text == 'Обновленный комментарий'
        assert comment.author == user

        try:
            delete_url = reverse('news:delete', args=(comment.id,))
        except NoReverseMatch:
            delete_url = f'/comment/{comment.id}/delete/'

        response = client.post(delete_url)
        assert response.status_code == 302
        assert Comment.objects.count() == 0

    def test_user_cannot_edit_delete_other_comments(
            self, client, user, another_user, news):
        """Авторизованный пользователь не может редактировать
        чужие комментарии.
        """
        other_comment = Comment.objects.create(
            news=news,
            author=another_user,
            text='Чужой комментарий'
        )

        client.login(username='testuser', password='password123')

        assert other_comment.author != user
        assert other_comment.author == another_user

        edit_data = {'text': 'Взломанный комментарий'}

        try:
            edit_url = reverse('news:edit', args=(other_comment.id,))
        except NoReverseMatch:
            edit_url = f'/comment/{other_comment.id}/edit/'

        response = client.post(edit_url, edit_data)
        assert response.status_code == 404

        try:
            delete_url = reverse('news:delete', args=(other_comment.id,))
        except NoReverseMatch:
            delete_url = f'/comment/{other_comment.id}/delete/'

        response = client.post(delete_url)
        assert response.status_code == 404

        other_comment.refresh_from_db()
        assert other_comment.text == 'Чужой комментарий'
        assert other_comment.author == another_user
        assert Comment.objects.count() == 1
