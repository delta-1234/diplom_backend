import math

from django.contrib.auth.hashers import check_password
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from api.models import TestResult, HardwareData, ModelData, OfflineData, ServerData, SingleStreamData, MultiStreamData
from users.models import CustomUser
from django.core.cache import cache
from django.db.models import Q


@api_view(['POST'])
def upload_data(request):
    data = request.data
    try:
        user = CustomUser.objects.get(user_name=data['user_name'])
    except CustomUser.DoesNotExist:
        return Response({
            "code": 404,
            "msg": "用户不存在",
            "data": None
        }, status=404)
    # 验证密码
    if not check_password(data['password'], user.password):
        return Response({
            "code": 401,
            "msg": "密码错误",
            "data": None
        }, status=401)
    test_mode = data['summary']['scenario']
    test_result = TestResult.objects.create(
        model_name=data['model_name'],
        test_mode=test_mode,
        sample_number=data['sample_number'],
        accuracy=data['accuracy'],
        is_baseline=False,
        custom_user=user,
        test_time=timezone.now(),
    )
    for i in range(0, 5):
        gpu_id = "cuda:" + str(i)
        if gpu_id not in data.keys():
            break
        gpu_data = data[gpu_id]
        if gpu_data['avg_utilization'] < 10:
            continue
        HardwareData.objects.create(
            test_result=test_result,
            gpu_name=gpu_data['gpu_name'],
            avg_utilization=gpu_data['avg_utilization'],
            avg_memory=gpu_data['avg_memory_used_mb'],
            total_energy=gpu_data['total_energy_j'],
        )

    ModelData.objects.create(
        test_result=test_result,
        avg_vision_time=data['avg_vision_ns'],
        avg_align_time=data['avg_align_ns'],
        avg_text_gen_time=data['avg_text_gen_ns'],
    )
    if test_mode == "Offline":
        summary = data['summary']
        OfflineData.objects.create(
            test_result=test_result,
            samples_per_second=summary['samples_per_sec'],
            tokens_per_second=summary['tokens_per_sec'],
        )
    elif test_mode == "Server":
        summary = data['summary']
        addition_stats = data['additional_stats']
        ServerData.objects.create(
            test_result=test_result,
            samples_per_second=summary['completed_samples_per_sec'],
            tokens_per_second=summary['completed_tokens_per_sec'],
            avg_first_token_latency=addition_stats['Mean First Token latency (ns)'],
        )
    elif test_mode == "SingleStream":
        summary = data['summary']
        SingleStreamData.objects.create(
            test_result=test_result,
            ninety_percent_latency=summary['90_per_latency_ns'],
        )
    elif test_mode == "MultiStream":
        addition_stats = data['additional_stats']
        MultiStreamData.objects.create(
            test_result=test_result,
            ninety_percent_latency=addition_stats['90.00 percentile latency (ns)'],
            stream_num=addition_stats['samples_per_query'],
        )
    return Response({'message': '成功'}, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_result_all(request):
    user_id = cache.get('user.user_id')
    queryset = TestResult.objects.filter(Q(custom_user=user_id) | Q(custom_user__isnull=True))

    # 将 QuerySet 转换为字典列表
    data_list = list(queryset.values(
        'id',
        'model_name',
        'test_mode',
        'sample_number',
        'is_baseline'
    ))

    for data in data_list:
        hardware = HardwareData.objects.get(test_result=data['id'])
        data.update({'hardware_name': hardware.gpu_name})

    # 返回 JSON 响应
    return Response({
        "code": 200,
        "msg": "success",
        "data": data_list
    })

@api_view(['POST'])
def get_hardware_data(request):
    test_result_id = request.data.get('test_result_id')
    item = TestResult.objects.get(id=test_result_id)
    data = {}
    hardware_data = HardwareData.objects.filter(test_result=item.id)
    data['id'] = item.id
    data['model_name'] = item.model_name
    data['hardware_name'] = hardware_data[0].gpu_name + "*" + str(len(hardware_data))
    data['avg_utilization'] = hardware_data.avg_utilization
    data['avg_memory'] = hardware_data.avg_memory
    data['energy_per_query'] = round(hardware_data.total_energy / item.sample_number, 2)
    return Response(
        {
            "code": 200,
            "msg": "success",
            "data": data
        }
    )

@api_view(['POST'])
def get_model_data(request):
    # 从请求体获取参数
    test_result_id = request.data.get('test_result_id')
    item = TestResult.objects.get(id=test_result_id)

    data = {}
    hardware_data = HardwareData.objects.filter(test_result=item.id)
    model_data = ModelData.objects.get(test_result=item.id)
    data['id'] = item.id
    data['model_name'] = item.model_name
    data['hardware_name'] = hardware_data[0].gpu_name + "*" + str(len(hardware_data))
    data['avg_vision_tim'] = model_data.avg_vision_time
    data['avg_align_time'] = model_data.avg_align_time
    data['avg_text_gen_time'] = model_data.avg_text_gen_time
    return Response(
        {
            "code": 200,
            "msg": "success",
            "data": data
        }
    )

# 定义模式与模型的映射关系
MODE_MODEL_MAPPING = {
    "Offline": (OfflineData, ['samples_per_second', 'tokens_per_second']),
    "Server": (ServerData, ['samples_per_second', 'tokens_per_second', 'avg_first_token_latency']),
    "SingleStream": (SingleStreamData, ['ninety_percent_latency']),
    "MultiStream": (MultiStreamData, ['ninety_percent_latency', 'stream_num'])
}

@api_view(['POST'])
def get_mode_data(request):
    # 从请求体获取参数
    test_result_id = request.data.get('test_result_id')
    item = TestResult.objects.get(id=test_result_id)

    data = {}
    hardware_data = HardwareData.objects.filter(test_result=item.id)
    data['id'] = item.id
    data['model_name'] = item.model_name
    data['hardware_name'] = hardware_data[0].gpu_name + "*" + str(len(hardware_data))
    data['accuracy'] = item.accuracy
    if item.test_mode == "Offline":
        offline_data = OfflineData.objects.get(test_result=item.id)
        data['samples_per_second'] = offline_data.samples_per_second
        data['tokens_per_second'] = offline_data.tokens_per_second
    elif item.test_mode == "Server":
        server_data = ServerData.objects.get(test_result=item.id)
        data['samples_per_second'] = server_data.samples_per_second
        data['tokens_per_second'] = server_data.tokens_per_second
        data['avg_first_token_latency'] = server_data.avg_first_token_latency
    elif item.test_mode == "SingleStream":
        single_stream_data = SingleStreamData.objects.get(test_result=item.id)
        data['ninety_percent_latency'] = single_stream_data.ninety_percent_latency
    elif item.test_mode == "MultiStream":
        multi_stream_data = MultiStreamData.objects.get(test_result=item.id)
        data['ninety_percent_latency'] = multi_stream_data.ninety_percent_latency
        data['stream_num'] = multi_stream_data.stream_num
    return Response(
        {
            "code": 200,
            "msg": "success",
            "data": data
        }
    )

@api_view(['POST'])
def get_score_suggestion(request):
    test_result_id = request.data.get('test_result')
    test_result = TestResult.objects.get(id=test_result_id)
    if test_result.is_baseline:
        return Response(
            {
                "code": 200,
                "msg": "success",
                "score": 60,
                "suggestion": "此为基线模型"
            }
        )
    score = 0
    base_hardware_data = None
    base_model_data = None
    base_test = None
    if '13b' in test_result.model_name:
        temp = 4
    else:
        temp = 0
    if test_result.test_mode == "Offline":
        offline_data = OfflineData.objects.get(test_result=test_result_id)
        base_offline = OfflineData.objects.get(test_result=1+temp)
        base_hardware_data = HardwareData.objects.get(test_result=1+temp)
        base_model_data = ModelData.objects.get(test_result=1+temp)
        base_test = TestResult.objects.get(id=1+temp)
        score = 60+10*math.log2(offline_data.samples_per_second/base_offline.samples_per_second)
    elif test_result.test_mode == "Server":
        server_data = ServerData.objects.get(test_result=test_result_id)
        base_server = ServerData.objects.get(test_result=2+temp)
        base_hardware_data = HardwareData.objects.get(test_result=2+temp)
        base_model_data = ModelData.objects.get(test_result=2+temp)
        base_test = TestResult.objects.get(id=2+temp)
        score = 60+10*math.log2(server_data.samples_per_second/base_server.samples_per_second)+10*math.log2(base_server.avg_first_token_latency/server_data.avg_first_token_latency)
    elif test_result.test_mode == "SingleStream":
        single_stream_data = SingleStreamData.objects.get(test_result=test_result_id)
        base_single_stream = SingleStreamData.objects.get(test_result=3+temp)
        base_hardware_data = HardwareData.objects.get(test_result=3+temp)
        base_model_data = ModelData.objects.get(test_result=3+temp)
        base_test = TestResult.objects.get(id=3+temp)
        score = 60+10*math.log2(base_single_stream.ninety_percent_latency/single_stream_data.ninety_percent_latency)
    elif test_result.test_mode == "MultiStream":
        multi_stream_data = MultiStreamData.objects.get(test_result=test_result_id)
        base_multi_stream = MultiStreamData.objects.get(test_result=4+temp)
        base_hardware_data = HardwareData.objects.get(test_result=4+temp)
        base_model_data = ModelData.objects.get(test_result=4+temp)
        base_test = TestResult.objects.get(id=4+temp)
        score = 60+10*math.log2(multi_stream_data.stream_num/base_multi_stream.stream_num)

    suggestion = ''
    hardware_tmp = HardwareData.objects.filter(test_result=test_result_id)
    hardware_data = {}
    hardware_data['avg_utilization'] = sum(obj.avg_utilization for obj in hardware_tmp) / len(hardware_tmp)
    hardware_data['avg_memory'] = sum(obj.avg_memory for obj in hardware_tmp)
    hardware_data['total_energy'] = sum(obj.total_energy for obj in hardware_tmp)

    model_data = ModelData.objects.get(test_result=test_result_id)
    if score >= 60:
        suggestion = "系统综合能力高于基线。"
        energy_per_sample = hardware_data['total_energy'] / test_result.sample_number
        base_energy_per_sample = base_hardware_data.total_energy / base_test.sample_number
        if base_energy_per_sample < energy_per_sample:
            per = 100*(energy_per_sample-base_energy_per_sample) / base_energy_per_sample
            per = round(per, 2)
            suggestion += f"系统能耗高于基线{per}%。"
        return Response(
                {
                    "code": 200,
                    "msg": "success",
                    "score": round(score, 2),
                    "suggestion": suggestion
                }
            )
    suggestion = "系统综合能力低于基线。"
    if test_result.model_name == base_test.model_name:
        # if hardware_data['avg_utilization'] > base_hardware_data.avg_utilization or hardware_data['avg_memory'] > base_hardware_data.avg_memory:
        #     suggestion += "GPU占用过高，建议升级GPU硬件。"
        if model_data.avg_vision_time > base_model_data.avg_vision_time:
            suggestion += "处理速度过慢，建议升级GPU硬件。"
    else:
        if model_data.avg_vision_time > base_model_data.avg_vision_time:
            suggestion += "平均视觉处理时间高于基线，建议更换模型视觉编码器。"
        if model_data.avg_align_time > base_model_data.avg_align_time:
            suggestion += "跨模态对齐耗时高于基线，建议提高模型跨模态交互与特征融合的计算效率。"
        if model_data.avg_text_gen_time > base_model_data.avg_text_gen_time:
            suggestion += "平均文本生成时间高于基线，建议更换或改进模型文本解码器。"
    energy_per_sample = hardware_data['total_energy'] / test_result.sample_number
    base_energy_per_sample = base_hardware_data.total_energy / base_test.sample_number
    if base_energy_per_sample < energy_per_sample:
        per = 100 * (energy_per_sample - base_energy_per_sample) / base_energy_per_sample
        per = round(per, 2)
        suggestion += f"系统能耗高于基线{per}%\n"
    return Response(
        {
            "code": 200,
            "msg": "success",
            "score": round(score, 2),
            "suggestion": suggestion
        }
    )

@api_view(['GET'])
def get_hardware_all(request):
    user_id = cache.get('user.user_id')
    # user_id = 1
    queryset = TestResult.objects.filter(Q(custom_user=user_id) | Q(custom_user__isnull=True))
    offline = []
    server = []
    single_stream = []
    multi_stream = []
    for item in queryset:
        data = {}
        hardware_data = HardwareData.objects.filter(test_result=item.id)
        data['id'] = item.id
        data['model_name'] = item.model_name
        data['hardware_name'] = hardware_data[0].gpu_name + "*" + str(len(hardware_data))
        data['avg_utilization'] = sum(obj.avg_utilization for obj in hardware_data) / len(hardware_data)
        data['avg_memory'] = sum(obj.avg_memory for obj in hardware_data)
        data['energy_per_query'] = round(sum(obj.total_energy for obj in hardware_data) / (item.sample_number), 2)
        if item.test_mode == "Offline":
            offline.append(data)
        elif item.test_mode == "Server":
            server.append(data)
        elif item.test_mode == "SingleStream":
            single_stream.append(data)
        elif item.test_mode == "MultiStream":
            multi_stream.append(data)
        if item.test_time is None:
            data['test_time'] = "基线"
        else:
            local_time = timezone.localtime(item.test_time)
            data['test_time'] = local_time.strftime("%Y-%m-%d %H:%M:%S")
    return Response(
        {
            "code": 200,
            "msg": "success",
            "Offline": offline,
            "Server": server,
            "SingleStream": single_stream,
            "MultiStream": multi_stream
        }
    )

@api_view(['GET'])
def get_model_all(request):
    user_id = cache.get('user.user_id')
    queryset = TestResult.objects.filter(Q(custom_user=user_id) | Q(custom_user__isnull=True))
    offline = []
    server = []
    single_stream = []
    multi_stream = []
    for item in queryset:
        data = {}
        hardware_data = HardwareData.objects.filter(test_result=item.id)
        model_data = ModelData.objects.get(test_result=item.id)
        data['id'] = item.id
        data['model_name'] = item.model_name
        data['hardware_name'] = hardware_data[0].gpu_name + "*" + str(len(hardware_data))
        data['avg_vision_tim'] = model_data.avg_vision_time
        data['avg_align_time'] = model_data.avg_align_time
        data['avg_text_gen_time'] = model_data.avg_text_gen_time
        if item.test_mode == "Offline":
            offline.append(data)
        elif item.test_mode == "Server":
            server.append(data)
        elif item.test_mode == "SingleStream":
            single_stream.append(data)
        elif item.test_mode == "MultiStream":
            multi_stream.append(data)
        if item.test_time is None:
            data['test_time'] = "基线"
        else:
            local_time = timezone.localtime(item.test_time)
            data['test_time'] = local_time.strftime("%Y-%m-%d %H:%M:%S")
    return Response(
        {
            "code": 200,
            "msg": "success",
            "Offline": offline,
            "Server": server,
            "SingleStream": single_stream,
            "MultiStream": multi_stream
        }
    )

@api_view(['GET'])
def get_mode_all(request):
    user_id = cache.get('user.user_id')
    queryset = TestResult.objects.filter(Q(custom_user=user_id) | Q(custom_user__isnull=True))
    offline = []
    server = []
    single_stream = []
    multi_stream = []
    for item in queryset:
        data = {}
        hardware_data = HardwareData.objects.filter(test_result=item.id)
        data['id'] = item.id
        data['model_name'] = item.model_name
        data['hardware_name'] = hardware_data[0].gpu_name + "*" + str(len(hardware_data))
        data['accuracy'] = item.accuracy
        if item.test_mode == "Offline":
            offline_data = OfflineData.objects.get(test_result=item.id)
            data['samples_per_second'] = offline_data.samples_per_second
            data['tokens_per_second'] = offline_data.tokens_per_second
            offline.append(data)
        elif item.test_mode == "Server":
            server_data = ServerData.objects.get(test_result=item.id)
            data['samples_per_second'] = server_data.samples_per_second
            data['tokens_per_second'] = server_data.tokens_per_second
            data['avg_first_token_latency'] = server_data.avg_first_token_latency
            server.append(data)
        elif item.test_mode == "SingleStream":
            single_stream_data = SingleStreamData.objects.get(test_result=item.id)
            data['ninety_percent_latency'] = single_stream_data.ninety_percent_latency
            single_stream.append(data)
        elif item.test_mode == "MultiStream":
            multi_stream_data = MultiStreamData.objects.get(test_result=item.id)
            data['ninety_percent_latency'] = multi_stream_data.ninety_percent_latency
            data['stream_num'] = multi_stream_data.stream_num
            multi_stream.append(data)
        if item.test_time is None:
            data['test_time'] = "基线"
        else:
            local_time = timezone.localtime(item.test_time)
            data['test_time'] = local_time.strftime("%Y-%m-%d %H:%M:%S")
    return Response(
        {
            "code": 200,
            "msg": "success",
            "Offline": offline,
            "Server": server,
            "SingleStream": single_stream,
            "MultiStream": multi_stream
        }
    )

@api_view(['POST'])
def get_baseline_id(request):
    test_mode = request.data.get('test_mode')
    model_name = request.data.get('model_name')
    if '7b' in model_name:
        temp = 0
    else:
        temp = 4
    baseline_id = 0
    if test_mode == "Offline":
        baseline_id = 1+temp
    elif test_mode == "Server":
        baseline_id = 2+temp
    elif test_mode == "SingleStream":
        baseline_id = 3+temp
    elif test_mode == "MultiStream":
        baseline_id = 4+temp
    return Response(
        {
            "code": 200,
            "msg": "success",
            "baseline_id": baseline_id,
        }
    )
