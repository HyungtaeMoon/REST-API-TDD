from django.contrib.auth.models import BaseUserManager, PermissionsMixin, AbstractBaseUser
from django.db import models


class UserManager(BaseUserManager):
    '''User 에서 사용하기 위한 UserManager 생성'''
    def create_user(self, email, password=None, **extra_fields):
        '''일반 유저로 생성할 경우'''
        if not email:
            raise ValueError('이메일을 입력해주세요')

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        '''superuser 로 user 를 생성할 경우 필드값을 True 로 변경'''
        user = self.create_user(email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    '''UserManager 을 objects 필드에 사용'''
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()
    # USERNAME 를 email 로 사용
    USERNAME_FIELD = 'email'
