

# flask
def get_client_ip(request):
    client_ip = request.headers.get('X-Real-IP') or \
                request.headers.get('X-Forwarded-For', '').split(',')[0] or \
                request.remote_addr

    return client_ip


# django버전
# def get_client_ip(request):
#     x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#     if x_forwarded_for:
#         ip = x_forwarded_for.split(',')[-1].strip()
#     else:
#         ip = request.META.get('REMOTE_ADDR')
#     return ip
