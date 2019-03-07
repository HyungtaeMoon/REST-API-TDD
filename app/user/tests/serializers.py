from django.contrib.auth import get_user_model, authenticate

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """유저 객체의 Serializer"""

    class Meta:
        model = get_user_model()
        fields = ('email', 'password', 'name')
        # write_only 옵션을 주면 method:post 에 담기지 않는다.
        # 즉, response 할 때 비밀번호를 제외한 나머지 필드만 body 에 담아서 응답
        #  test_create_valid_user_success 코드 참고
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}

    def create(self, validated_data):
        """암호화(encrypted) 된 비밀번호로 사용자를 생성"""
        return get_user_model().objects.create_user(**validated_data)


class AuthTokenSerializer(serializers.Serializer):
    """유저 인증 객체 직렬화(Serializer)"""
    email = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
    )

    def validate(self, attrs):
        """사용자 확인(validate) 및 인증(authenticate)"""
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password,
        )
        if not user:
            msg = _('제공된 credentials 로는 인증할 수 없습니다.')
            raise serializers.ValidationError(msg, code='authorization')

        # attrs = OrderedDict([('email', 'customer@test.com'), ('password', 'password123'),
    #                                ('user', <User: customer@test.com>)])
        attrs['user'] = user

        return attrs
