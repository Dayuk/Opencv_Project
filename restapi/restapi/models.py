from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in

class CustomUser(AbstractUser):
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'custom_user'

    groups = models.ManyToManyField(
        Group,
        verbose_name=('groups'),
        blank=True,
        help_text=('The groups this user belongs to. A user will get all permissions granted to each of their groups.'),
        related_name="customuser_groups",
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=('user permissions'),
        blank=True,
        help_text=('Specific permissions for this user.'),
        related_name="customuser_permissions",
        related_query_name="customuser",
    )

    def save(self, *args, **kwargs):
        # 필요한 경우 여기에 추가 로직을 구현할 수 있습니다.
        super().save(*args, **kwargs)

@receiver(user_signed_up)
def populate_profile(request, user, sociallogin=None, **kwargs):
    if sociallogin:
        provider = sociallogin.account.provider
        user_data = sociallogin.account.extra_data

        # Google과 GitHub 모두 'first_name'과 'last_name'을 제공하지 않을 수 있으므로,
        # 이를 고려한 처리가 필요합니다.
        first_name = user_data.get('given_name', '')
        last_name = user_data.get('family_name', '')

        # 사용자 이름을 이름과 성의 조합으로 설정
        # 사용자 이름이 제공되지 않았거나 'user'로 설정된 경우에만 새로운 사용자 이름을 생성합니다.
        if not user.username or user.username == 'user':
            new_username = f"{first_name}{last_name}".strip()
            user.username = new_username if new_username else user.username

        # 이메일 설정
        user.email = user_data.get('email', '') if not user.email else user.email

        # IP 주소 설정
        ip_address = get_client_ip(request)
        user.last_login_ip = ip_address

        # 필요한 경우 여기에 추가적인 필드 설정
        user.save()

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
