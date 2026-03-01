class LogRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("User:", request.user)
        print("Path:", request.path)

        response = self.get_response(request)

        return response
