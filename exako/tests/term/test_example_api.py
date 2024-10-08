import random

import pytest
from django.urls import reverse_lazy

from exako.apps.core.query import set_url_params
from exako.apps.term.api.schema import TermExampleTranslationView, TermExampleView
from exako.apps.term.constants import Language, Level
from exako.apps.term.models import (
    TermExampleLink,
    TermExampleTranslation,
    TermExampleTranslationLink,
)
from exako.tests.factories.term import (
    TermDefinitionFactory,
    TermExampleFactory,
    TermExampleTranslationFactory,
    TermFactory,
    TermLexicalFactory,
)

pytestmark = pytest.mark.django_db


create_term_example_route = reverse_lazy('api-1.0.0:create_example')
create_term_example_translation_route = reverse_lazy(
    'api-1.0.0:create_example_translation'
)


def list_term_example_route(
    term=None,
    term_definition=None,
    term_lexical=None,
    level=None,
):
    url = str(reverse_lazy('api-1.0.0:list_example'))
    return set_url_params(
        url,
        term=term,
        term_definition=term_definition,
        term_lexical=term_lexical,
        level=level,
    )


def get_term_example_translation_route(
    term_example,
    language,
    term=None,
    term_definition=None,
    term_lexical=None,
):
    url = str(
        reverse_lazy(
            'api-1.0.0:get_example_translation',
            kwargs={'term_example': term_example, 'language': language},
        )
    )
    return set_url_params(
        url,
        term=term,
        term_definition=term_definition,
        term_lexical=term_lexical,
    )


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
@pytest.mark.parametrize(
    'link_factory, link_name',
    [
        (TermFactory, 'term'),
        (TermDefinitionFactory, 'term_definition'),
        (TermLexicalFactory, 'term_lexical'),
    ],
)
def test_create_term_example(
    client, generate_payload, token_header, link_factory, link_name
):
    payload = generate_payload(TermExampleFactory)
    link_model = link_factory()
    payload.update(
        **{link_name: link_model.id},
        highlight=[[1, 3], [5, 6]],
    )

    response = client.post(
        create_term_example_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 201
    assert TermExampleView(**response.json()) == TermExampleView(
        id=response.json()['id'], **payload
    )
    assert TermExampleLink.objects.filter(
        term_example=response.json()['id'],
        **{link_name: link_model.id},
    ).exists()


def test_create_term_example_user_is_not_authenticated(client, generate_payload):
    term = TermFactory()
    payload = generate_payload(TermExampleFactory)
    payload.update(
        term=term.id,
        highlight=[[1, 3], [5, 6]],
    )

    response = client.post(
        create_term_example_route,
        payload,
        content_type='application/json',
    )

    assert response.status_code == 401


def test_create_term_example_user_not_enough_permission(
    client, generate_payload, token_header
):
    term = TermFactory()
    payload = generate_payload(TermExampleFactory)
    payload.update(
        term=term.id,
        highlight=[[1, 3], [5, 6]],
    )

    response = client.post(
        create_term_example_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 403


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
@pytest.mark.parametrize(
    'link_name',
    [
        'term',
        'term_definition',
        'term_lexical',
    ],
)
def test_create_term_example_link_not_found(
    client, generate_payload, token_header, link_name
):
    payload = generate_payload(TermExampleFactory)
    payload.update(
        **{link_name: 519027},
        highlight=[[1, 3], [5, 6]],
    )

    response = client.post(
        create_term_example_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 404


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
@pytest.mark.parametrize(
    'link_factory, link_name',
    [
        (TermFactory, 'term'),
        (TermDefinitionFactory, 'term_definition'),
        (TermLexicalFactory, 'term_lexical'),
    ],
)
def test_create_term_example_with_conflict_link(
    client, generate_payload, token_header, link_factory, link_name
):
    link_model = link_factory()
    payload = generate_payload(TermExampleFactory)
    example = TermExampleFactory(**payload)
    payload.update(
        **{link_name: link_model.id},
        highlight=[[1, 3], [5, 6]],
    )
    TermExampleLink.objects.create(
        **{link_name: link_model.id},
        term_example=example.id,
        highlight=[[1, 3], [5, 6]],
    )

    response = client.post(
        create_term_example_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 409
    assert 'example already linked with this model.' in response.json()['detail']


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
def test_create_term_example_term_lexical_with_value_ref(
    client, generate_payload, token_header
):
    payload = generate_payload(TermExampleFactory)
    term_lexical = TermLexicalFactory(term_value_ref=TermFactory())
    payload.update(
        term_lexical=term_lexical.id,
        highlight=[[1, 3], [5, 6]],
    )

    response = client.post(
        create_term_example_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert (
        response.json()['detail']
        == 'lexical with term_value_ref cannot have a example link.'
    )


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
@pytest.mark.parametrize(
    'link_factory, link_name, language_ref',
    [
        (TermFactory, 'term', 'language'),
        (TermDefinitionFactory, 'term_definition', 'term__language'),
        (TermLexicalFactory, 'term_lexical', 'term__language'),
    ],
)
def test_create_term_example_invalid_language_reference(
    client, generate_payload, token_header, link_factory, link_name, language_ref
):
    payload = generate_payload(TermExampleFactory, language=Language.CHINESE)
    link_model = link_factory(**{language_ref: Language.DEUTSCH})
    payload.update(
        **{link_name: link_model.id},
        highlight=[[1, 3], [5, 6]],
    )

    response = client.post(
        create_term_example_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert (
        response.json()['detail']
        == 'term example language has to be the same as the link models.'
    )


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
def test_create_term_example_model_link_not_set(client, generate_payload, token_header):
    payload = generate_payload(TermExampleFactory)
    payload.update(highlight=[[1, 3], [5, 6]])

    response = client.post(
        create_term_example_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert 'at least one object to link' in response.json()['detail'][0]['msg']


@pytest.mark.parametrize(
    'link_attr',
    [
        {
            'term_definition': 123,
            'term': 5125,
        },
        {
            'term_definition': 123,
            'term_lexical': 400,
        },
    ],
)
@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
def test_create_term_example_multiple_models(
    client, generate_payload, token_header, link_attr
):
    payload = generate_payload(TermExampleFactory)
    payload.update(link_attr, highlight=[[1, 3], [5, 6]])

    response = client.post(
        create_term_example_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert 'you can reference only one object.' in response.json()['detail'][0]['msg']


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
def test_create_term_example_invalid_num_highlight(
    client, generate_payload, token_header
):
    term = TermFactory()
    payload = generate_payload(TermExampleFactory)
    payload.update(
        term=term.id,
        highlight=[[1, 4, 5], [6, 8]],
    )

    response = client.post(
        create_term_example_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert (
        'highlight must consist of pairs of numbers'
        in response.json()['detail'][0]['msg']
    )


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
@pytest.mark.parametrize(
    'highlight', [[[1, 4], [4, 6]], [[10, 14], [13, 16]], [[0, 3], [0, 9]]]
)
def test_create_term_example_invalid_highlight_interval(
    client, generate_payload, token_header, highlight
):
    term = TermFactory()
    payload = generate_payload(TermExampleFactory)
    payload.update(
        term=term.id,
        highlight=highlight,
    )

    response = client.post(
        create_term_example_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert 'highlight interval must not overlap' in response.json()['detail'][0]['msg']


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
@pytest.mark.parametrize('highlight', [[[399, 5]], [[5, 699]]])
def test_create_term_example_invalid_highlight_len(
    client, generate_payload, token_header, highlight
):
    term = TermFactory()
    payload = generate_payload(TermExampleFactory)
    payload.update(
        term=term.id,
        highlight=highlight,
    )

    response = client.post(
        create_term_example_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert (
        'highlight cannot be greater than the length of the example.'
        in response.json()['detail'][0]['msg']
    )


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
@pytest.mark.parametrize('highlight', [[[-1, 5]], [[-5, -1]]])
def test_create_term_example_invalid_highlight_values_lower_than_0(
    client, generate_payload, token_header, highlight
):
    term = TermFactory()
    payload = generate_payload(TermExampleFactory)
    payload.update(
        term=term.id,
        highlight=highlight,
    )

    response = client.post(
        create_term_example_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert (
        'both highlight values must be greater than or equal to 0.'
        in response.json()['detail'][0]['msg']
    )


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
def test_create_term_example_invalid_highlight_value1_greater_than_value2(
    client, generate_payload, token_header
):
    term = TermFactory()
    payload = generate_payload(TermExampleFactory)
    payload.update(
        term=term.id,
        highlight=[[7, 1]],
    )

    response = client.post(
        create_term_example_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert (
        'highlight beginning value cannot be greater than the ending value'
        in response.json()['detail'][0]['msg']
    )


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
@pytest.mark.parametrize(
    'link_factory, link_name',
    [
        (TermFactory, 'term'),
        (TermDefinitionFactory, 'term_definition'),
        (TermLexicalFactory, 'term_lexical'),
    ],
)
def test_create_term_example_translation(
    client, generate_payload, token_header, link_factory, link_name
):
    link_model = link_factory()
    example = TermExampleFactory()
    payload = generate_payload(TermExampleTranslationFactory)
    payload.update(
        **{link_name: link_model.id},
        term_example=example.id,
        highlight=[[1, 3], [5, 7]],
    )

    response = client.post(
        create_term_example_translation_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 201
    assert TermExampleTranslationView(**response.json()) == TermExampleTranslationView(
        **payload
    )
    assert TermExampleTranslationLink.objects.filter(
        **{link_name: link_model.id},
        term_example=example.id,
        language=payload['language'],
    ).exists()


def test_create_term_example_translation_user_is_not_authenticated(
    client, generate_payload
):
    term = TermFactory()
    example = TermExampleFactory()
    payload = generate_payload(TermExampleTranslationFactory)
    payload.update(
        expression=term.expression,
        language=term.language,
        term_example=example.id,
        highlight=[[1, 3], [5, 7]],
    )

    response = client.post(
        create_term_example_translation_route,
        payload,
        content_type='application/json',
    )

    assert response.status_code == 401


def test_create_term_example_translation_user_not_enough_permission(
    client, generate_payload, token_header
):
    term = TermFactory()
    example = TermExampleFactory()
    payload = generate_payload(TermExampleTranslationFactory)
    payload.update(
        term=term.id,
        term_example=example.id,
        highlight=[[1, 3], [5, 7]],
    )

    response = client.post(
        create_term_example_translation_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 403


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
def test_create_term_example_translation_example_not_found(
    client, generate_payload, token_header
):
    term = TermFactory()
    payload = generate_payload(TermExampleTranslationFactory)
    payload.update(
        term=term.id,
        term_example=123,
        highlight=[[1, 3], [5, 7]],
    )

    response = client.post(
        create_term_example_translation_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 404


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
@pytest.mark.parametrize(
    'link_name',
    [
        'term',
        'term_definition',
        'term_lexical',
    ],
)
def test_create_term_example_translation_model_link_not_found(
    client, generate_payload, token_header, link_name
):
    example = TermExampleFactory()
    payload = generate_payload(TermExampleTranslationFactory)
    payload.update(
        **{link_name: 1827945},
        term_example=example.id,
        highlight=[[1, 3], [5, 7]],
    )

    response = client.post(
        create_term_example_translation_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 404


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
@pytest.mark.parametrize(
    'link_factory, link_name',
    [
        (TermFactory, 'term'),
        (TermDefinitionFactory, 'term_definition'),
        (TermLexicalFactory, 'term_lexical'),
    ],
)
def test_create_term_example_translation_conflict(
    client, generate_payload, token_header, link_factory, link_name
):
    link_model = link_factory()
    example = TermExampleFactory()
    payload = generate_payload(TermExampleTranslationFactory)
    TermExampleTranslation.objects.create(**payload, term_example=example)
    payload.update(
        **{link_name: link_model.id},
        term_example=example.id,
        highlight=[[1, 3], [5, 7]],
    )

    response = client.post(
        create_term_example_translation_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 409
    assert 'translation already exists for this example.' in response.json()['detail']


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
def test_create_term_example_translation_term_lexical_with_value_ref(
    client, generate_payload, token_header
):
    term_lexical = TermLexicalFactory(term_value_ref=TermFactory())
    example = TermExampleFactory()
    payload = generate_payload(TermExampleTranslationFactory)
    payload.update(
        term_lexical=term_lexical.id,
        term_example=example.id,
        highlight=[[1, 3], [5, 7]],
    )

    response = client.post(
        create_term_example_translation_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert (
        response.json()['detail']
        == 'lexical with term_value_ref cannot have a example link.'
    )


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
def test_create_term_example_translation_invalid_same_language_term_example(
    client, generate_payload, token_header
):
    example = TermExampleFactory(language=Language.PORTUGUESE_BRASILIAN)
    payload = generate_payload(
        TermExampleTranslationFactory,
        language=Language.PORTUGUESE_BRASILIAN,
    )
    payload.update(
        term=TermFactory(language=Language.CHINESE).id,
        term_example=example.id,
        highlight=[[1, 3], [5, 7]],
    )

    response = client.post(
        create_term_example_translation_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert (
        response.json()['detail']
        == 'translation language reference cannot be same as language.'
    )


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
@pytest.mark.parametrize(
    'link_factory, link_name, language_ref',
    [
        (TermFactory, 'term', 'language'),
        (TermDefinitionFactory, 'term_definition', 'term__language'),
        (TermLexicalFactory, 'term_lexical', 'term__language'),
    ],
)
def test_create_term_example_translation_invalid_same_language(
    client, generate_payload, token_header, link_factory, link_name, language_ref
):
    link_model = link_factory(**{language_ref: Language.CHINESE})
    example = TermExampleFactory()
    payload = generate_payload(
        TermExampleTranslationFactory,
        language=Language.CHINESE,
    )
    payload.update(
        **{link_name: link_model.id},
        term_example=example.id,
        highlight=[[1, 3], [5, 7]],
    )

    response = client.post(
        create_term_example_translation_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert (
        response.json()['detail']
        == 'translation language reference cannot be same as language.'
    )


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
@pytest.mark.parametrize(
    'link_factory, link_name, language_ref',
    [
        (TermFactory, 'term', 'language'),
        (TermDefinitionFactory, 'term_definition', 'term__language'),
        (TermLexicalFactory, 'term_lexical', 'term__language'),
    ],
)
def test_create_term_example_translation_language_invalid_reference(
    client, generate_payload, token_header, link_factory, link_name, language_ref
):
    link_model = link_factory(**{language_ref: Language.PORTUGUESE_BRASILIAN})
    example = TermExampleFactory(language=Language.CHINESE)
    payload = generate_payload(
        TermExampleTranslationFactory,
        language=Language.JAPANESE,
    )
    payload.update(
        **{link_name: link_model.id},
        term_example=example.id,
        highlight=[[1, 3], [5, 7]],
    )

    response = client.post(
        create_term_example_translation_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert (
        response.json()['detail']
        == 'term example language has to be the same as the link models.'
    )


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
def test_create_term_example_translation_model_link_not_set(
    client, generate_payload, token_header
):
    example = TermExampleFactory()
    payload = generate_payload(TermExampleTranslationFactory)
    payload.update(
        term_example=example.id,
        highlight=[[1, 3], [5, 6]],
    )

    response = client.post(
        create_term_example_translation_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert 'at least one object to link' in response.json()['detail'][0]['msg']


@pytest.mark.parametrize(
    'link_attr',
    [
        {
            'term_definition': 123,
            'term': 15902378,
        },
        {
            'term_definition': 123,
            'term_lexical': 400,
        },
    ],
)
@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
def test_create_term_example_translation_model_multiple_models(
    client, generate_payload, token_header, link_attr
):
    example = TermExampleFactory()
    payload = generate_payload(TermExampleTranslationFactory)
    payload.update(link_attr, highlight=[[1, 3], [5, 6]], term_example=example.id)

    response = client.post(
        create_term_example_translation_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert 'you can reference only one object.' in response.json()['detail'][0]['msg']


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
def test_create_term_example_translation_model_invalid_num_highlight(
    client, generate_payload, token_header
):
    term = TermFactory()
    example = TermExampleFactory()
    payload = generate_payload(TermExampleTranslationFactory)
    payload.update(
        term=term.id,
        highlight=[[1, 4, 5], [6, 8]],
        term_example=example.id,
    )

    response = client.post(
        create_term_example_translation_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert (
        'highlight must consist of pairs of numbers'
        in response.json()['detail'][0]['msg']
    )


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
@pytest.mark.parametrize(
    'highlight', [[[1, 4], [4, 6]], [[3, 6], [4, 7]], [[0, 3], [0, 9]]]
)
def test_create_term_example_translation_model_invalid_highlight_interval(
    client, generate_payload, token_header, highlight
):
    term = TermFactory()
    example = TermExampleFactory()
    payload = generate_payload(TermExampleTranslationFactory)
    payload.update(
        term=term.id,
        highlight=highlight,
        term_example=example.id,
    )

    response = client.post(
        create_term_example_translation_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert 'highlight interval must not overlap' in response.json()['detail'][0]['msg']


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
@pytest.mark.parametrize('highlight', [[[399, 5]], [[5, 699]]])
def test_create_term_example_translation_model_invalid_highlight_len(
    client, generate_payload, token_header, highlight
):
    example = TermExampleFactory()
    term = TermFactory()
    payload = generate_payload(TermExampleTranslationFactory)
    payload.update(
        term=term.id,
        highlight=highlight,
        term_example=example.id,
    )

    response = client.post(
        create_term_example_translation_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert (
        'highlight cannot be greater than the length of the example.'
        in response.json()['detail'][0]['msg']
    )


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
@pytest.mark.parametrize('highlight', [[[-1, 5]], [[-5, -1]]])
def test_create_term_example_translation_model_invalid_highlight_values_lower_than_0(
    client, generate_payload, token_header, highlight
):
    term = TermFactory()
    example = TermExampleFactory()
    payload = generate_payload(TermExampleTranslationFactory)
    payload.update(
        term=term.id,
        highlight=highlight,
        term_example=example.id,
    )

    response = client.post(
        create_term_example_translation_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert (
        'both highlight values must be greater than or equal to 0.'
        in response.json()['detail'][0]['msg']
    )


@pytest.mark.parametrize('user', [{'is_superuser': True}], indirect=True)
def test_create_term_example_translation_model_invalid_highlight_value1_greater_than_value2(
    client, generate_payload, token_header
):
    example = TermExampleFactory()
    term = TermFactory()
    payload = generate_payload(TermExampleTranslationFactory)
    payload.update(
        term=term.id,
        highlight=[[7, 1]],
        term_example=example.id,
    )

    response = client.post(
        create_term_example_translation_route,
        payload,
        headers=token_header,
        content_type='application/json',
    )

    assert response.status_code == 422
    assert (
        'highlight beginning value cannot be greater than the ending value'
        in response.json()['detail'][0]['msg']
    )


@pytest.mark.parametrize(
    'link_factory, link_name',
    [
        (TermFactory, 'term'),
        (TermDefinitionFactory, 'term_definition'),
        (TermLexicalFactory, 'term_lexical'),
    ],
)
def test_list_term_example(client, link_factory, link_name):
    link_model = link_factory()
    examples = TermExampleFactory.create_batch(size=5)
    TermExampleFactory.create_batch(size=5)
    links = [
        TermExampleLink.objects.create(
            **{link_name: link_model},
            term_example=example.id,
            highlight=[[random.randint(1, 10), random.randint(1, 10)]],
        )
        for example in examples
    ]

    response = client.get(list_term_example_route(**{link_name: link_model.id}))

    assert response.status_code == 200
    assert [TermExampleView(**example) for example in response.json()['items']] == [
        TermExampleView(
            id=example.id,
            language=example.language,
            example=example.example,
            level=example.level,
            highlight=link.highlight,
            additional_content=example.additional_content,
        )
        for example, link in zip(examples, links)
    ]


def test_list_term_example_empty(client):
    term = TermFactory()
    TermExampleFactory.create_batch(size=10)

    response = client.get(list_term_example_route(term=term.id))

    assert response.status_code == 200


def test_list_term_example_filter_level(client):
    term = TermFactory()
    examples1 = TermExampleFactory.create_batch(size=5, level=Level.ADVANCED)
    examples2 = TermExampleFactory.create_batch(size=5, level=Level.BEGINNER)
    TermExampleFactory.create_batch(size=5)
    links = [
        TermExampleLink.objects.create(
            term_example=example.id,
            term=term,
            highlight=[[random.randint(1, 10), random.randint(1, 10)]],
        )
        for example in [*examples1, *examples2]
    ]

    response = client.get(
        list_term_example_route(
            term=term.id,
            level=Level.ADVANCED,
        )
    )

    assert response.status_code == 200
    assert [TermExampleView(**example) for example in response.json()['items']] == [
        TermExampleView(
            id=example.id,
            language=example.language,
            example=example.example,
            level=example.level,
            highlight=link.highlight,
            additional_content=example.additional_content,
        )
        for example, link in zip(examples1, links)
    ]


@pytest.mark.parametrize(
    'link_factory, link_name',
    [
        (TermFactory, 'term'),
        (TermDefinitionFactory, 'term_definition'),
        (TermLexicalFactory, 'term_lexical'),
    ],
)
def test_get_term_example_translation(client, link_factory, link_name):
    link_model = link_factory()
    example = TermExampleFactory()
    translation = TermExampleTranslationFactory(term_example=example)
    TermExampleTranslationLink.objects.create(
        **{link_name: link_model},
        term_example=example.id,
        language=translation.language,
        highlight=[[1, 4]],
    )

    response = client.get(
        get_term_example_translation_route(
            term_example=example.id,
            language=translation.language,
            **{link_name: link_model.id},
        )
    )

    assert response.status_code == 200
    assert TermExampleTranslationView(**response.json()) == TermExampleTranslationView(
        language=translation.language,
        translation=translation.translation,
        highlight=[[1, 4]],
        additional_content=example.additional_content,
    )


@pytest.mark.parametrize(
    'link_name',
    [
        'term',
        'term_definition',
        'term_lexical',
    ],
)
def test_get_term_example_translation_not_found(client, link_name):
    response = client.get(
        get_term_example_translation_route(
            **{link_name: 15398},
            term_example=123,
            language=Language.CHINESE,
        )
    )

    assert response.status_code == 404
