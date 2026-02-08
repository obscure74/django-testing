from http import HTTPStatus

from django.contrib.auth import get_user

from notes.tests.base import BaseTestCase


class TestRoutes(BaseTestCase):
    """Тесты маршрутов для приложения заметок."""

    def test_authenticated_user_pages_accessible(self):
        """Аутентифицированному пользователю доступны страницы заметок."""
        urls_to_test = [
            (self.author_client, self.home_url, HTTPStatus.OK),
            (self.author_client, self.list_url, HTTPStatus.OK),
            (self.author_client, self.success_url, HTTPStatus.OK),
            (self.author_client, self.add_url, HTTPStatus.OK),
            (self.author_client, self.detail_url, HTTPStatus.OK),
            (self.author_client, self.edit_url, HTTPStatus.OK),
            (self.author_client, self.delete_url, HTTPStatus.OK),
            (self.client, self.login_url, HTTPStatus.OK),
            (self.client, self.logout_url, HTTPStatus.METHOD_NOT_ALLOWED),
            (self.client, self.signup_url, HTTPStatus.OK),
            (self.author_client, self.login_url, HTTPStatus.OK),
            (
                self.author_client,
                self.logout_url,
                HTTPStatus.METHOD_NOT_ALLOWED,
            ),
            (self.author_client, self.signup_url, HTTPStatus.OK),
            # Дополнительные URL для другого пользователя
            (self.reader_client, self.home_url, HTTPStatus.OK),
            (self.reader_client, self.login_url, HTTPStatus.OK),
        ]

        for client, url, expected_status in urls_to_test:
            user = None
            if hasattr(client, 'session'):
                # Создаем фиктивный request для get_user()
                from django.test import RequestFactory
                factory = RequestFactory()
                request = factory.get(url)
                request.session = client.session
                user = get_user(request)

            username = (user.username
                        if user and user.is_authenticated
                        else 'anonymous')

            with self.subTest(url=url, username=username):
                response = client.get(url)
                self.assertEqual(response.status_code, expected_status)

    def test_author_only_pages(self):
        """Страницы отдельной заметки, удаления и редактирования
        доступны только автору.
        """
        # Автор может получить доступ
        urls = [
            self.detail_url,
            self.edit_url,
            self.delete_url,
        ]

        for url in urls:
            with self.subTest(url=url, user="author"):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

        # Другой пользователь получает 404
        for url in urls:
            with self.subTest(url=url, user="reader"):
                response = self.reader_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_anonymous_redirect_to_login(self):
        """Анонимный пользователь перенаправляется на страницу логина."""
        urls = [
            self.list_url,
            self.success_url,
            self.add_url,
            self.detail_url,
            self.edit_url,
            self.delete_url,
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                expected_url = f"{self.login_url}?next={url}"
                self.assertRedirects(response, expected_url)
