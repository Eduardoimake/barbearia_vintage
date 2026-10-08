"""Views públicas, autenticação e administração da API.

Este módulo implementa todas as operações HTTP da API v1:

- catálogo público;
- autenticação administrativa;
- configuração do CSRF;
- dashboard;
- gerenciamento administrativo.

As views públicas não exigem autenticação. As views administrativas exigem
sessão Django válida, usuário ativo e ``is_staff=True``.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.db.models import Q, QuerySet
from django.db.models.deletion import ProtectedError
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import generics, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView, exception_handler

from .models import (
    Barber,
    Promotion,
    Service,
    ServiceCategory,
    StoreConfiguration,
)
from .pagination import CatalogPagination
from .permissions import IsStaffAuthenticated
from .serializers import (
    AdminBarberSerializer,
    AdminCategorySerializer,
    AdminPromotionSerializer,
    AdminServiceSerializer,
    AdminStoreSerializer,
    AdminUserSerializer,
    PublicBarberDetailSerializer,
    PublicBarberListSerializer,
    PublicCategorySerializer,
    PublicPromotionSerializer,
    PublicServiceDetailSerializer,
    PublicServiceListSerializer,
    PublicStoreSerializer,
)


def api_exception_handler(
    exc: Exception,
    context: dict[str, Any],
) -> Response | None:
    """Converte erros comuns da API para mensagens em português.

    O DRF continua responsável pela maior parte dos erros. Esta função trata
    principalmente erros de validação do Django e conflitos de integridade.

    Args:
        exc: Exceção que ocorreu durante o processamento da requisição.
        context: Contexto fornecido pelo Django REST Framework.

    Returns:
        Resposta HTTP personalizada ou ``None`` para que o DRF use seu
        tratamento padrão.
    """
    response = exception_handler(exc, context)

    if response is not None:
        return response

    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "message_dict"):
            detail: Any = exc.message_dict
        else:
            detail = {"detail": exc.messages}

        return Response(
            detail,
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, IntegrityError):
        return Response(
            {
                "detail": (
                    "Não foi possível salvar os dados porque existe "
                    "um conflito de integridade."
                )
            },
            status=status.HTTP_409_CONFLICT,
        )

    return None


def eligible_promotions_queryset() -> QuerySet[Promotion]:
    """Retorna promoções elegíveis para exibição pública.

    Uma promoção pública precisa estar:

    - ativa;
    - dentro do intervalo de datas;
    - sem serviço vinculado, ou vinculada a serviço publicado;
    - vinculada a categoria ativa quando houver serviço relacionado.

    Returns:
        QuerySet filtrado de promoções elegíveis.
    """
    now = timezone.now()

    return (
        Promotion.objects
        .filter(is_active=True)
        .filter(
            Q(start_date__isnull=True)
            | Q(start_date__lte=now)
        )
        .filter(
            Q(end_date__isnull=True)
            | Q(end_date__gte=now)
        )
        .filter(
            Q(linked_service__isnull=True)
            | Q(
                linked_service__is_published=True,
                linked_service__category__is_active=True,
            )
        )
    )


class PublicStoreView(APIView):
    """Retorna os dados públicos da barbearia."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(
        self,
        request: Request,
    ) -> Response:
        """Consulta a configuração única da barbearia.

        Args:
            request: Requisição HTTP recebida.

        Returns:
            Dados públicos da loja ou erro 404 quando não configurada.
        """
        store = (
            StoreConfiguration.objects
            .filter(pk=1)
            .first()
        )

        if store is None:
            return Response(
                {
                    "detail": (
                        "As informações da barbearia ainda não "
                        "foram configuradas."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PublicStoreSerializer(
            store,
            context={"request": request},
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class PublicCategoryListView(generics.ListAPIView):
    """Lista somente categorias ativas."""

    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = PublicCategorySerializer
    pagination_class = None

    def get_queryset(self) -> QuerySet[ServiceCategory]:
        """Retorna categorias ativas na ordem configurada.

        Returns:
            QuerySet público de categorias.
        """
        return (
            ServiceCategory.objects
            .filter(is_active=True)
            .order_by("display_order", "name")
        )


class PublicServiceListView(generics.ListAPIView):
    """Lista serviços publicados com filtros e paginação."""

    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = PublicServiceListSerializer
    pagination_class = CatalogPagination

    allowed_ordering: dict[str, tuple[str, ...]] = {
        "name": ("name", "id"),
        "-name": ("-name", "id"),
        "price": ("price", "id"),
        "-price": ("-price", "id"),
    }

    def get_queryset(self) -> QuerySet[Service]:
        """Monta a consulta pública de serviços.

        São considerados somente serviços publicados associados a categorias
        ativas. Os parâmetros ``featured`` e ``ordering`` são validados aqui,
        e os erros são devolvidos como listas de mensagens por campo.

        Returns:
            QuerySet filtrado, ordenado e preparado com ``select_related``.

        Raises:
            ValidationError: Quando um parâmetro de filtro possui formato
                inválido.
        """
        query_params = self.request.query_params

        featured = query_params.get("featured")

        if featured is not None and featured.lower() != "true":
            raise ValidationError(
                {
                    "featured": [
                        "Utilize featured=true ou omita "
                        "este parâmetro."
                    ]
                }
            )

        ordering = query_params.get("ordering")

        if ordering is not None and ordering not in self.allowed_ordering:
            raise ValidationError(
                {
                    "ordering": [
                        "Utilize name, -name, price ou -price."
                    ]
                }
            )

        queryset = (
            Service.objects
            .filter(
                is_published=True,
                category__is_active=True,
            )
            .select_related("category")
        )

        search = query_params.get("search", "").strip()

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(short_description__icontains=search)
            )

        category_slug = query_params.get("category", "").strip()

        if category_slug:
            queryset = queryset.filter(
                category__slug=category_slug,
            )

        if featured is not None:
            queryset = queryset.filter(is_featured=True)

        if ordering is None:
            return queryset.order_by("display_order", "name", "id")

        return queryset.order_by(
            *self.allowed_ordering[ordering],
        )


class PublicServiceDetailView(generics.RetrieveAPIView):
    """Retorna o detalhe de um serviço publicamente visível."""

    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = PublicServiceDetailSerializer
    lookup_field = "slug"

    def get_queryset(self) -> QuerySet[Service]:
        """Retorna somente serviços publicados em categorias ativas.

        Returns:
            QuerySet para o detalhe público.
        """
        return (
            Service.objects
            .filter(
                is_published=True,
                category__is_active=True,
            )
            .select_related("category")
        )


class PublicBarberListView(generics.ListAPIView):
    """Lista barbeiros ativos na ordem configurada."""

    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = PublicBarberListSerializer
    pagination_class = None

    def get_queryset(self) -> QuerySet[Barber]:
        """Retorna somente barbeiros ativos.

        Returns:
            QuerySet público de barbeiros.
        """
        return (
            Barber.objects
            .filter(is_active=True)
            .order_by("display_order", "name")
        )


class PublicBarberDetailView(generics.RetrieveAPIView):
    """Retorna o detalhe de um barbeiro ativo."""

    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = PublicBarberDetailSerializer
    lookup_field = "slug"

    def get_queryset(self) -> QuerySet[Barber]:
        """Retorna barbeiros ativos para a busca por slug.

        Returns:
            QuerySet de barbeiros ativos.
        """
        return Barber.objects.filter(is_active=True)


class PublicPromotionListView(generics.ListAPIView):
    """Lista promoções atualmente elegíveis."""

    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = PublicPromotionSerializer
    pagination_class = None

    def get_queryset(self) -> QuerySet[Promotion]:
        """Retorna promoções elegíveis com os relacionamentos carregados.

        Returns:
            QuerySet público de promoções.
        """
        return (
            eligible_promotions_queryset()
            .select_related(
                "linked_service",
                "linked_service__category",
            )
        )


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfTokenView(APIView):
    """Inicializa o cookie CSRF e devolve o token ao frontend."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(
        self,
        request: Request,
    ) -> Response:
        """Retorna um token CSRF válido.

        Args:
            request: Requisição HTTP recebida.

        Returns:
            Token CSRF em JSON.
        """
        return Response(
            {
                "csrfToken": get_token(request),
            },
            status=status.HTTP_200_OK,
        )


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    """Realiza login administrativo com sessão Django."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(
        self,
        request: Request,
    ) -> Response:
        """Autentica um usuário staff e cria sua sessão.

        A requisição precisa conter o header ``X-CSRFToken`` correspondente ao
        cookie CSRF previamente obtido pelo frontend.

        Args:
            request: Requisição HTTP contendo ``username`` e ``password``.

        Returns:
            Dados do usuário e novo token CSRF ou erro de autenticação.
        """
        username: Any = request.data.get("username")
        password: Any = request.data.get("password")

        if not isinstance(username, str) or not isinstance(password, str):
            return Response(
                {
                    "detail": (
                        "Informe username e password "
                        "como textos."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not username.strip() or not password:
            return Response(
                {
                    "detail": (
                        "Username e password são obrigatórios."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(
            request=request,
            username=username,
            password=password,
        )

        if (
            user is None
            or not user.is_active
            or not user.is_staff
        ):
            return Response(
                {
                    "detail": (
                        "Credenciais inválidas ou acesso "
                        "administrativo não autorizado."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        django_login(request, user)

        user_serializer = AdminUserSerializer(user)

        return Response(
            {
                "user": user_serializer.data,
                "csrfToken": get_token(request),
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """Retorna os dados do usuário staff autenticado."""

    permission_classes = [IsStaffAuthenticated]
    authentication_classes = [SessionAuthentication]

    def get(
        self,
        request: Request,
    ) -> Response:
        """Retorna os dados básicos do administrador autenticado.

        Args:
            request: Requisição HTTP autenticada.

        Returns:
            Identificador, nome de usuário e indicador de staff.
        """
        user = request.user

        return Response(
            {
                "id": user.pk,
                "username": user.get_username(),
                "is_staff": user.is_staff,
            }
        )


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    """Encerra a sessão administrativa atual."""

    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]

    def post(
        self,
        request: Request,
    ) -> Response:
        """Destrói a sessão Django do usuário autenticado.

        Args:
            request: Requisição HTTP autenticada.

        Returns:
            Resposta 204 sem corpo.
        """
        django_logout(request)

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class AdminDashboardView(APIView):
    """Fornece contagens reais do catálogo administrativo."""

    permission_classes = [IsStaffAuthenticated]
    authentication_classes = [SessionAuthentication]

    def get(
        self,
        request: Request,
    ) -> Response:
        """Retorna contagens do conteúdo cadastrado.

        Não são inventadas métricas de vendas, faturamento, acessos ou
        agendamentos.

        Args:
            request: Requisição HTTP autenticada.

        Returns:
            Contagens reais de serviços, categorias, barbeiros e promoções.
        """
        del request

        active_promotions_count = (
            eligible_promotions_queryset().count()
        )

        return Response(
            {
                "services_count": Service.objects.count(),
                "categories_count": ServiceCategory.objects.count(),
                "barbers_count": Barber.objects.count(),
                "active_promotions_count": active_promotions_count,
            },
            status=status.HTTP_200_OK,
        )


class AdminCategoryListCreateView(generics.ListCreateAPIView):
    """Lista e cria categorias administrativas."""

    permission_classes = [IsStaffAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = AdminCategorySerializer
    queryset = ServiceCategory.objects.all()
    pagination_class = CatalogPagination


class AdminCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Consulta, altera ou exclui uma categoria administrativa."""

    permission_classes = [IsStaffAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = AdminCategorySerializer
    queryset = ServiceCategory.objects.all()
    http_method_names = [
        "get",
        "patch",
        "delete",
        "head",
        "options",
    ]

    def destroy(
        self,
        request: Request,
        *args: Any,
        **kwargs: Any,
    ) -> Response:
        """Impede a exclusão de categoria com serviços vinculados.

        Args:
            request: Requisição HTTP autenticada.
            *args: Argumentos posicionais herdados.
            **kwargs: Argumentos nomeados herdados.

        Returns:
            ``204`` quando a exclusão é possível ou ``409`` quando existem
            serviços relacionados.
        """
        del request
        instance = self.get_object()

        try:
            self.perform_destroy(instance)
        except ProtectedError:
            return Response(
                {
                    "detail": (
                        "Não é possível excluir uma categoria que "
                        "possui serviços vinculados."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class AdminServiceListCreateView(generics.ListCreateAPIView):
    """Lista e cria serviços administrativos."""

    permission_classes = [IsStaffAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = AdminServiceSerializer
    queryset = (
        Service.objects
        .select_related("category")
        .all()
    )
    pagination_class = CatalogPagination


class AdminServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Consulta, altera ou exclui um serviço administrativo."""

    permission_classes = [IsStaffAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = AdminServiceSerializer
    queryset = (
        Service.objects
        .select_related("category")
        .all()
    )
    http_method_names = [
        "get",
        "patch",
        "delete",
        "head",
        "options",
    ]


class AdminBarberListCreateView(generics.ListCreateAPIView):
    """Lista e cria barbeiros administrativos."""

    permission_classes = [IsStaffAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = AdminBarberSerializer
    queryset = Barber.objects.all()
    pagination_class = CatalogPagination


class AdminBarberDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Consulta, altera ou exclui um barbeiro administrativo."""

    permission_classes = [IsStaffAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = AdminBarberSerializer
    queryset = Barber.objects.all()
    http_method_names = [
        "get",
        "patch",
        "delete",
        "head",
        "options",
    ]


class AdminStoreView(APIView):
    """Consulta ou altera a configuração única da barbearia."""

    permission_classes = [IsStaffAuthenticated]
    authentication_classes = [SessionAuthentication]

    def get(
        self,
        request: Request,
    ) -> Response:
        """Retorna a configuração atual da barbearia.

        Args:
            request: Requisição HTTP autenticada.

        Returns:
            Configuração administrativa ou ``404`` se ainda não existir.
        """
        store = (
            StoreConfiguration.objects
            .filter(pk=1)
            .first()
        )

        if store is None:
            return Response(
                {
                    "detail": (
                        "As informações da barbearia ainda "
                        "não foram configuradas."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AdminStoreSerializer(
            store,
            context={"request": request},
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def patch(
        self,
        request: Request,
    ) -> Response:
        """Atualiza ou inicializa a configuração singleton.

        A criação por ``PATCH`` é permitida somente para tornar o backend
        recuperável quando o banco ainda não recebeu o seed. O registro sempre
        utilizará a chave primária 1.

        Args:
            request: Requisição HTTP autenticada.

        Returns:
            Configuração salva com status 200 ou 201.
        """
        store = (
            StoreConfiguration.objects
            .filter(pk=1)
            .first()
        )

        if store is None:
            serializer = AdminStoreSerializer(
                data=request.data,
                context={"request": request},
            )
            response_status = status.HTTP_201_CREATED
        else:
            serializer = AdminStoreSerializer(
                store,
                data=request.data,
                partial=True,
                context={"request": request},
            )
            response_status = status.HTTP_200_OK

        serializer.is_valid(raise_exception=True)

        try:
            serializer.save()
        except DjangoValidationError as exc:
            return Response(
                {
                    "detail": exc.messages,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except IntegrityError:
            return Response(
                {
                    "detail": (
                        "Não foi possível salvar a configuração "
                        "da barbearia."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            serializer.data,
            status=response_status,
        )


class AdminPromotionListCreateView(generics.ListCreateAPIView):
    """Lista e cria promoções administrativas."""

    permission_classes = [IsStaffAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = AdminPromotionSerializer
    queryset = (
        Promotion.objects
        .select_related(
            "linked_service",
            "linked_service__category",
        )
        .all()
    )
    pagination_class = CatalogPagination


class AdminPromotionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Consulta, altera ou exclui uma promoção administrativa."""

    permission_classes = [IsStaffAuthenticated]
    authentication_classes = [SessionAuthentication]
    serializer_class = AdminPromotionSerializer
    queryset = (
        Promotion.objects
        .select_related(
            "linked_service",
            "linked_service__category",
        )
        .all()
    )
    http_method_names = [
        "get",
        "patch",
        "delete",
        "head",
        "options",
    ]