from django.db import models

class CustomUser(models.Model):
    # 添加额外字段（示例）
    user_name = models.CharField(
        verbose_name="User Name",
        max_length=100,
        unique=True
    )
    password = models.CharField(
        verbose_name="Password",
        max_length=100,
    )
    email = models.CharField(
        verbose_name="Email",
        max_length=100,
    )

    class Meta:
        db_table = "custom_user"
        verbose_name = "Custom User"  # 修改模型显示名称
        verbose_name_plural = "Custom Users"  # 复数形式