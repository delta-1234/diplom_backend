# models.py
from django.db import models

from users.models import CustomUser


class TestResult(models.Model):
    custom_user= models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="hardware_data",
        null=True,
        blank=True,
    )
    model_name = models.CharField(
        verbose_name="Model Name",  # 修改此处
        max_length=100
    )
    test_mode = models.CharField(
        verbose_name="Test Mode",  # 修改此处
        max_length=50
    )
    sample_number = models.IntegerField(
        verbose_name="Sample Number", default=0
    )
    accuracy = models.FloatField(
        verbose_name="Accuracy", default=0.0
    )
    is_baseline = models.BooleanField(
        verbose_name="Is Baseline", default=False
    )
    test_time = models.DateTimeField(
        verbose_name="Test Time",
        null=True,  # 数据库允许存储 NULL
        blank=True,  # 表单验证允许空值
    )

    class Meta:
        db_table = "test_result"
        verbose_name = "Test Result"  # 修改模型显示名称
        verbose_name_plural = "Test Results"  # 复数形式

class HardwareData(models.Model):
    test_result = models.ForeignKey(
        TestResult,
        on_delete=models.CASCADE,
        related_name="hardware_data"
    )
    gpu_name = models.CharField(
        verbose_name="gpu_name", max_length=100
    )
    avg_utilization = models.FloatField(
        verbose_name="Average Utilization",
    )
    avg_memory = models.FloatField(
        verbose_name="Average Memory",
    )
    total_energy = models.FloatField(
        verbose_name="Total Energy",
    )

    class Meta:
        db_table = "hardware_data"
        verbose_name = "Hardware Data"

class ModelData(models.Model):
    test_result = models.ForeignKey(
        TestResult,
        on_delete=models.CASCADE,
        related_name="model_data"
    )
    avg_vision_time = models.FloatField(
        verbose_name="Average Vision Time",
    )
    avg_align_time = models.FloatField(
        verbose_name="Average Align Time",
    )
    avg_text_gen_time = models.FloatField(
        verbose_name="Average Text Generation Time",
    )

    class Meta:
        db_table = "model_data"
        verbose_name = "Model Data"


# 子表 1: Offline 模式数据
class OfflineData(models.Model):
    test_result = models.ForeignKey(
        TestResult,
        on_delete=models.CASCADE,
        related_name="offline_data"
    )
    samples_per_second = models.FloatField(
        verbose_name="Samples per second",
    )
    tokens_per_second = models.FloatField(
        verbose_name="Tokens per second",
    )

    class Meta:
        db_table = "offline_data"
        verbose_name = "Offline Data"


# 子表 2: Server 模式数据
class ServerData(models.Model):
    test_result = models.ForeignKey(
        TestResult,
        on_delete=models.CASCADE,
        related_name="server_data"
    )
    samples_per_second = models.FloatField(
        verbose_name="Samples per second",
    )
    tokens_per_second = models.FloatField(
        verbose_name="Tokens per second",
    )
    avg_first_token_latency = models.FloatField(
        verbose_name="Average First Token Latency",
    )

    class Meta:
        db_table = "server_data"
        verbose_name = "Server Data"


# 子表 3: SingleStream 模式数据
class SingleStreamData(models.Model):
    test_result = models.ForeignKey(
        TestResult,
        on_delete=models.CASCADE,
        related_name="single_stream_data"
    )
    ninety_percent_latency = models.FloatField(
        verbose_name="Ninety Percent Latency",
    )

    class Meta:
        db_table = "single_stream_data"
        verbose_name = "Single Stream Data"


# 子表 4: MultiStream 模式数据
class MultiStreamData(models.Model):
    test_result = models.ForeignKey(
        TestResult,
        on_delete=models.CASCADE,
        related_name="multi_stream_data"
    )
    ninety_percent_latency = models.FloatField(
        verbose_name="Ninety Percent Latency",
    )
    stream_num = models.IntegerField(
        verbose_name="Stream Number",
    )

    class Meta:
        db_table = "multi_stream_data"
        verbose_name = "Multi Stream Data"

