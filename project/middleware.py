from django.http import HttpResponse
import time

request_counts = {}  # { caller_key: {"count": int, "window_start": float} }



class RateLimiterMiddleware:
    def __init__(self,get_response):
        self.get_response = get_response
        self.limit = 5 
        self.window = 60
    def __call__(self, request):
        caller_key = request.META.get('REMOTE_ADDR')
        now = time.time()
        record = request_counts.get(caller_key)

        if record is None or now - record["window_start"] > self.window:
            # first request ever, OR the old window has expired — start fresh
            request_counts[caller_key] = {"count": 1, "window_start": now}
            allowed = True
        else:
            record["count"] += 1
            allowed = record["count"] <= self.limit

        if not allowed:
            retry_after = int(self.window - (now - record["window_start"]))
            response = HttpResponse("Too Many Requests", status=429)
            response["Retry-After"] = retry_after
            response["X-RateLimit-Remaining"] = 0
            return response

        remaining = self.limit - request_counts[caller_key]["count"]
        response = self.get_response(request)
        response["X-RateLimit-Remaining"] = max(remaining, 0)
        return response