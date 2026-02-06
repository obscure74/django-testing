from http import HTTPStatus

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestRoutes:
    @pytest.mark.parametrize(
        "parametrized_client, url_name, args, expected_status",
        [
            ("client", "news:home", None, HTTPStatus.OK),
            ("client", "users:login", None, HTTPStatus.OK),
            ("client", "users:logout", None, HTTPStatus.METHOD_NOT_ALLOWED),
            ("client", "users:signup", None, HTTPStatus.OK),
            ("client", "news:detail", "news", HTTPStatus.OK),
            ("client", "news:edit", "comment", HTTPStatus.FOUND),
            ("client", "news:delete", "comment", HTTPStatus.FOUND),
            ("author_client", "news:edit", "comment", HTTPStatus.OK),
            ("author_client", "news:delete", "comment", HTTPStatus.OK),
            ("user_client", "news:edit", "comment", HTTPStatus.NOT_FOUND),
            ("user_client", "news:delete", "comment", HTTPStatus.NOT_FOUND),
        ],
    )
    def test_pages_status_codes(
        self,
        request,
        news,
        comment,
        parametrized_client,
        url_name,
        args,
        expected_status,
    ):
        client = request.getfixturevalue(parametrized_client)

        if args == "news":
            url_args = (news.id,)
        elif args == "comment":
            url_args = (comment.id,)
        else:
            url_args = ()

        url = reverse(url_name, args=url_args)
        response = client.get(url)
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "url_name, args",
        [
            ("news:edit", "comment"),
            ("news:delete", "comment"),
        ],
    )
    def test_anonymous_redirect_to_login(
        self, client, comment, url_name, args, login_url
    ):
        url_args = (comment.id,) if args == "comment" else ()
        url = reverse(url_name, args=url_args)
        response = client.get(url)
        assert response.status_code == HTTPStatus.FOUND
        expected_url = f"{login_url}?next={url}"
        assert response.url == expected_url

    @pytest.mark.parametrize(
        "reverse_name, expected_status",
        [
            ("users:login", HTTPStatus.OK),
            ("users:logout", HTTPStatus.METHOD_NOT_ALLOWED),
            ("users:signup", HTTPStatus.OK),
        ],
    )
    def test_auth_pages_accessible(self, client, reverse_name,
                                   expected_status):
        """Страницы регистрации, входа и выхода доступны анонимам."""
        url = reverse(reverse_name)
        response = client.get(url)
        assert response.status_code == expected_status
