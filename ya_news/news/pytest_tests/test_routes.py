import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from news.models import News, Comment


@pytest.mark.django_db
class TestRoutes:

    @pytest.fixture
    def author(self):
        return User.objects.create_user(
            username='author', password='password123'
        )

    @pytest.fixture
    def reader(self):
        return User.objects.create_user(
            username='reader', password='password123'
        )

    @pytest.fixture
    def news(self):
        return News.objects.create(
            title='Тестовая новость', text='Текст новости'
        )

    @pytest.fixture
    def comment(self, author, news):
        return Comment.objects.create(
            news=news,
            author=author,
            text='Тестовый комментарий'
        )

    def test_home_page_anonymous_accessible(self, client):
        """Главная страница доступна анонимному пользователю."""
        try:
            url = reverse('news:home')
        except NoReverseMatch:
            url = '/'

        response = client.get(url)
        assert response.status_code == 200

    def test_news_detail_page_anonymous_accessible(self, client, news):
        """Страница отдельной новости доступна анонимному пользователю."""
        try:
            url = reverse('news:detail', args=(news.id,))
        except NoReverseMatch:
            url = f'/{news.id}/'

        response = client.get(url)
        assert response.status_code == 200

    def test_comment_author_can_edit_delete(self, client, author, comment):
        """Страницы удаления и редактирования комментария доступны автору."""
        client.login(username='author', password='password123')

        try:
            edit_url = reverse('news:edit', args=(comment.id,))
        except NoReverseMatch:
            edit_url = f'/comment/{comment.id}/edit/'

        response = client.get(edit_url)
        assert response.status_code == 200

        try:
            delete_url = reverse('news:delete', args=(comment.id,))
        except NoReverseMatch:
            delete_url = f'/comment/{comment.id}/delete/'

        response = client.get(delete_url)
        assert response.status_code == 200

    def test_anonymous_redirect_to_login_for_comment_actions(
            self, client, comment):
        """Анонимный пользователь перенаправляется на страницу авторизации."""
        urls = []
        try:
            urls.append(reverse('news:edit', args=(comment.id,)))
            urls.append(reverse('news:delete', args=(comment.id,)))
        except NoReverseMatch:
            urls.append(f'/comment/{comment.id}/edit/')
            urls.append(f'/comment/{comment.id}/delete/')

        try:
            login_url = reverse('users:login')
        except NoReverseMatch:
            login_url = '/auth/login/'

        for url in urls:
            response = client.get(url)
            assert response.status_code == 302
            assert login_url in response.url

    def test_user_cannot_access_other_comments(
            self, client, author, reader, news):
        """Авторизованный пользователь не может редактировать
        чужие комментарии.
        """
        other_comment = Comment.objects.create(
            news=news,
            author=reader,
            text='Чужой комментарий'
        )

        client.login(username='author', password='password123')

        urls = []
        try:
            urls.append(reverse('news:edit', args=(other_comment.id,)))
            urls.append(reverse('news:delete', args=(other_comment.id,)))
        except NoReverseMatch:
            urls.append(f'/comment/{other_comment.id}/edit/')
            urls.append(f'/comment/{other_comment.id}/delete/')

        for url in urls:
            response = client.get(url)
            assert response.status_code == 404

    def test_auth_pages_accessible(self, client):
        """Страницы регистрации, входа и выхода доступны
        анонимным пользователям.
        """
        try:
            login_url = reverse('users:login')
            logout_url = reverse('users:logout')
            signup_url = reverse('users:signup')

            urls = [login_url, logout_url, signup_url]
        except NoReverseMatch:
            urls = ['/auth/login/', '/auth/logout/', '/auth/signup/']

        for url in urls:
            response = client.get(url)
            assert response.status_code in [200, 405]
