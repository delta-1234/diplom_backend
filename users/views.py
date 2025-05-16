# views.py
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import CustomUser


@api_view(['POST'])
def register(request):
    """
    用户注册接口
    请求示例：
    {
        "user_name": "alice",
        "password": "p@ssw0rd",
        "email": "alice@example.com"
    }
    """
    required_fields = ['user_name', 'password', 'email']
    missing_fields = [field for field in required_fields if field not in request.data]

    # 验证必填字段
    if missing_fields:
        return Response({
            "code": 400,
            "msg": f"缺少必填字段: {', '.join(missing_fields)}",
            "data": None
        }, status=400)

    # 检查用户是否存在
    if CustomUser.objects.filter(user_name=request.data['user_name']).exists():
        return Response({
            "code": 400,
            "msg": "用户名已被占用",
            "data": None
        }, status=400)

    # 检查邮箱是否存在
    if CustomUser.objects.filter(email=request.data['email']).exists():
        return Response({
            "code": 400,
            "msg": "邮箱已注册",
            "data": None
        }, status=400)

    # 创建用户
    try:
        user = CustomUser(
            user_name=request.data['user_name'],
            email=request.data['email'],
            password=make_password(request.data['password'])  # 密码加密
        )
        user.save()
    except Exception as e:
        return Response({
            "code": 500,
            "msg": f"用户创建失败: {str(e)}",
            "data": None
        }, status=500)

    return Response({
        "code": 200,
        "msg": "注册成功",
        "data": {
            "user_id": user.id,
            "user_name": user.user_name
        }
    })

from django.core.cache import cache
@api_view(['POST'])
def login(request):
    """
    用户登录接口
    请求示例：
    {
        "user_name": "alice",
        "password": "p@ssw0rd"
    }
    """
    required_fields = ['user_name', 'password']
    missing_fields = [field for field in required_fields if field not in request.data]

    # 验证必填字段
    if missing_fields:
        return Response({
            "code": 400,
            "msg": f"缺少必填字段: {', '.join(missing_fields)}",
            "data": None
        }, status=400)

    # 查找用户
    try:
        user = CustomUser.objects.get(user_name=request.data['user_name'])
    except CustomUser.DoesNotExist:
        return Response({
            "code": 404,
            "msg": "用户不存在",
            "data": None
        }, status=404)

    # 验证密码
    if not check_password(request.data['password'], user.password):
        return Response({
            "code": 401,
            "msg": "密码错误",
            "data": None
        }, status=401)
    else:
        cache.set('user.user_id', user.id, 60 * 60)

    # 返回登录结果
    return Response({
        "code": 200,
        "msg": "登录成功",
        "data": {
            "user_id": user.id,
            "user_name": user.user_name,
            "email": user.email
        }
    })