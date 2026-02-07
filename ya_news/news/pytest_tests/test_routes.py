from http import HTTPStatus

import pytest

pytestmark = pytest.mark.django_db


class TestRoutes:
    @pytest.mark.parametrize(
        "client_fixture, url_fixture, expected_status",
        [
            # Анонимный пользователь
            ("client", "home_url", HTTPStatus.OK),
            ("client", "login_url", HTTPStatus.OK),
            ("client", "logout_url", HTTPStatus.METHOD_NOT_ALLOWED),
            ("client", "signup_url", HTTPStatus.OK),
            ("client", "news_detail_url", HTTPStatus.OK),
            ("client", "comment_edit_url", HTTPStatus.FOUND),
            ("client", "comment_delete_url", HTTPStatus.FOUND),
            # Автор комментария
            ("author_client", "comment_edit_url", HTTPStatus.OK),
            ("author_client", "comment_delete_url", HTTPStatus.OK),
            # Другой авторизованный пользователь (не автор)
            ("user_client", "comment_edit_url", HTTPStatus.NOT_FOUND),
            ("user_client", "comment_delete_url", HTTPStatus.NOT_FOUND),
        ],
    )
    def test_pages_status_codes(
        self,
        request,
        client_fixture,
        url_fixture,
        expected_status,
    ):
        client = request.getfixturevalue(client_fixture)
        url = request.getfixturevalue(url_fixture)
        response = client.get(url)
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "url_fixture",
        [
            "comment_edit_url",
            "comment_delete_url",
        ],
    )
    def test_anonymous_redirect_to_login(
        self, client, url_fixture, login_url, request
    ):
        url = request.getfixturevalue(url_fixture)
        response = client.get(url)
        assert response.status_code == HTTPStatus.FOUND
        expected_url = f"{login_url}?next={url}"
        assert response.url == expected_url
